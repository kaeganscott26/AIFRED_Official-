import { HttpError, bounded } from "./http.js";

function finiteNumber(value, name) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new HttpError(400, "invalid_browser_analysis", `metrics.${name} must be a finite number`);
  }
  return number;
}

function bandScore(value, idealMin, idealMax, acceptMin, acceptMax) {
  if (value >= idealMin && value <= idealMax) return 100;
  if (value < acceptMin || value > acceptMax) return 0;
  if (value < idealMin) return Math.round(((value - acceptMin) / Math.max(0.0001, idealMin - acceptMin)) * 100);
  return Math.round(((acceptMax - value) / Math.max(0.0001, acceptMax - idealMax)) * 100);
}

function floorScore(value, idealMin, acceptMin) {
  if (value >= idealMin) return 100;
  if (value <= acceptMin) return 0;
  return Math.round(((value - acceptMin) / Math.max(0.0001, idealMin - acceptMin)) * 100);
}

function ceilingScore(value, idealMax, acceptMax) {
  if (value <= idealMax) return 100;
  if (value > acceptMax) return 0;
  return Math.round(((acceptMax - value) / Math.max(0.0001, acceptMax - idealMax)) * 100);
}

export function normalizeBrowserMetrics(body) {
  const metrics = body?.metrics;
  if (!metrics || typeof metrics !== "object" || Array.isArray(metrics)) {
    throw new HttpError(400, "invalid_browser_analysis", "browser analysis metrics are required");
  }
  return {
    tone_balance: finiteNumber(metrics.tone_balance, "tone_balance"),
    integrated_lufs: finiteNumber(metrics.integrated_lufs, "integrated_lufs"),
    peak_dbfs: finiteNumber(metrics.peak_dbfs, "peak_dbfs"),
    crest_factor_db: finiteNumber(metrics.crest_factor_db, "crest_factor_db"),
    stereo_width: finiteNumber(metrics.stereo_width, "stereo_width"),
    low_end_control: finiteNumber(metrics.low_end_control, "low_end_control"),
    harshness_control: finiteNumber(metrics.harshness_control, "harshness_control"),
    spectral_centroid_hz: finiteNumber(metrics.spectral_centroid_hz ?? 0, "spectral_centroid_hz")
  };
}

export function classifyBrowserReference(metrics) {
  const checks = [
    { id: "integrated_lufs", score: bandScore(metrics.integrated_lufs, -16, -7, -24, -3), target: "Loudness review lane: -24 to -3 LUFS" },
    { id: "peak_dbfs", score: ceilingScore(metrics.peak_dbfs, -0.7, 0.05), target: "Peak ceiling: around -1 dBFS target, accepted to 0 dBFS when not clipping" },
    { id: "tone_balance", score: bandScore(metrics.tone_balance, 30, 100, 8, 100), target: "Tone balance: rejects only broken ranges" },
    { id: "crest_factor_db", score: bandScore(metrics.crest_factor_db, 2, 22, 0.5, 28), target: "Dynamics: wide crest range" },
    { id: "stereo_width", score: bandScore(metrics.stereo_width, 0.12, 1, 0, 1), target: "Stereo width: broad acceptance; mono-safe and wide records can both pass" },
    { id: "low_end_control", score: floorScore(metrics.low_end_control, 18, 3), target: "Low-end control: reject only severe mud" },
    { id: "harshness_control", score: floorScore(metrics.harshness_control, 16, 3), target: "Harshness control: reject only severe upper-mid failure" }
  ];
  const weights = {
    integrated_lufs: 0.24,
    peak_dbfs: 0.18,
    tone_balance: 0.18,
    crest_factor_db: 0.14,
    stereo_width: 0.12,
    low_end_control: 0.07,
    harshness_control: 0.07
  };
  const score = Math.round(checks.reduce((sum, check) => sum + check.score * weights[check.id], 0));
  const clipping = metrics.peak_dbfs > 0.05;
  const noSevereToneFailure = metrics.tone_balance >= 8 && metrics.low_end_control >= 3 && metrics.harshness_control >= 3;
  const essentialPass = metrics.integrated_lufs >= -24 && metrics.integrated_lufs <= -3 && metrics.peak_dbfs <= 0 && noSevereToneFailure;
  let classification = "Poor Reference";
  let referenceUtility = Math.max(0, Math.min(100, score));
  let technicalCaution = 100 - Math.min(checks.find((check) => check.id === "peak_dbfs")?.score || 0, checks.find((check) => check.id === "harshness_control")?.score || 0);
  const styleTag = metrics.integrated_lufs > -8 ? "modern-hot" : metrics.stereo_width > 0.75 ? "wide" : metrics.crest_factor_db < 8 ? "dense-limited" : "balanced";
  let bestUse = "Use only as a cautionary comparison.";
  let caution = "Several measured values sit outside the useful reference lane.";

  if (clipping && !noSevereToneFailure) {
    classification = "Reject";
    referenceUtility = 0;
    technicalCaution = 100;
    bestUse = "Do not use this material as a reference.";
    caution = "The file is clipped with severe balance failure or is otherwise unusable.";
  } else if (clipping || metrics.peak_dbfs > -0.3 || metrics.integrated_lufs > -7) {
    classification = score >= 30 && noSevereToneFailure ? "Technically Hot Reference" : "Poor Reference";
    bestUse = "Useful for modern loudness, density, and competitive ceiling behavior.";
    caution = "Treat peak and limiter behavior as a caution, not a default rejection.";
  } else if (score >= 78) {
    classification = "Strong Reference";
    bestUse = "Useful for broad tone, loudness, dynamics, and stereo alignment.";
    caution = "No major technical caution detected.";
  } else if (score >= 56 || essentialPass) {
    classification = "Usable Reference";
    bestUse = "Useful for comparison after checking style and section context.";
    caution = "Some dimensions are outside the center lane but remain analytically useful.";
  } else if (score >= 36 && noSevereToneFailure) {
    classification = "Style-Specific Reference";
    bestUse = "Useful when the target intentionally matches this style tag.";
    caution = "Do not average this against unrelated genres without tagging it.";
  }

  return {
    accepted: classification !== "Reject" && classification !== "Poor Reference",
    score,
    classification,
    reference_utility: referenceUtility,
    technical_caution: technicalCaution,
    style_tag: styleTag,
    best_use: bestUse,
    caution,
    why: `${classification}: score ${score}/100, loudness ${metrics.integrated_lufs} LUFS, peak ${metrics.peak_dbfs} dBFS, crest ${metrics.crest_factor_db} dB, width ${metrics.stereo_width}.`,
    checks: checks.map((check) => ({ id: check.id, ok: check.score >= 20, score: check.score, target: check.target }))
  };
}

export function browserReferenceName(id) {
  return `Website reference ${bounded(id, 12)}`;
}

#include "AnalysisContextSerializer.h"

#include <array>
#include <cmath>
#include <memory>

namespace aifred::services
{
namespace
{
struct ContextSpectrumBand final
{
    const char* name;
    double lowHz;
    double highHz;
};

constexpr std::array<ContextSpectrumBand, 8> contextBands {{
    { "sub", 20.0, 60.0 },
    { "bass", 60.0, 250.0 },
    { "low_mid", 250.0, 500.0 },
    { "mid", 500.0, 2000.0 },
    { "high_mid", 2000.0, 4000.0 },
    { "presence", 4000.0, 6000.0 },
    { "treble", 6000.0, 12000.0 },
    { "air", 12000.0, 20000.0 }
}};

juce::var objectVar(std::unique_ptr<juce::DynamicObject> object)
{
    return juce::var(object.release());
}

juce::var metricVar(const analysis::MetricValue& metric, const char* unit)
{
    auto object = std::make_unique<juce::DynamicObject>();
    object->setProperty("available", metric.valid && std::isfinite(metric.value));
    object->setProperty("value", metric.valid && std::isfinite(metric.value)
                                     ? juce::var(metric.value) : juce::var());
    object->setProperty("unit", unit);
    return objectVar(std::move(object));
}

analysis::MetricValue summarizeSpectrumBand(const analysis::AnalysisSnapshot& snapshot,
                                            const double lowHz,
                                            const double highHz) noexcept
{
    if (! snapshot.spectrumBinWidthHz.valid
        || ! std::isfinite(snapshot.spectrumBinWidthHz.value)
        || snapshot.spectrumBinWidthHz.value <= 0.0)
        return {};

    double powerSum = 0.0;
    std::size_t count = 0;
    for (std::size_t index = 1; index < snapshot.spectrumBins.size(); ++index)
    {
        const auto frequency = static_cast<double>(index) * snapshot.spectrumBinWidthHz.value;
        if (frequency < lowHz || frequency >= highHz)
            continue;
        const auto& bin = snapshot.spectrumBins[index];
        if (! bin.valid || ! std::isfinite(bin.value))
            continue;
        powerSum += std::pow(10.0, bin.value / 10.0);
        ++count;
    }

    if (count == 0 || powerSum <= 0.0 || ! std::isfinite(powerSum))
        return {};
    return { 10.0 * std::log10(powerSum / static_cast<double>(count)), true };
}

juce::var spectrumVar(const analysis::AnalysisSnapshot& snapshot)
{
    auto spectrum = std::make_unique<juce::DynamicObject>();
    spectrum->setProperty("representation", "mean_fft_bin_power_dbfs");
    spectrum->setProperty("source", "authoritative_2048_point_fft");
    juce::Array<juce::var> bands;
    for (const auto& definition : contextBands)
    {
        auto band = std::make_unique<juce::DynamicObject>();
        band->setProperty("name", definition.name);
        band->setProperty("low_hz", definition.lowHz);
        band->setProperty("high_hz", definition.highHz);
        band->setProperty("level", metricVar(
            summarizeSpectrumBand(snapshot, definition.lowHz, definition.highHz), "dBFS"));
        bands.add(objectVar(std::move(band)));
    }
    spectrum->setProperty("bands", bands);
    return objectVar(std::move(spectrum));
}

juce::var snapshotVar(const analysis::AnalysisSnapshot* snapshot,
                      const double sampleRate,
                      const char* freshness)
{
    auto result = std::make_unique<juce::DynamicObject>();
    const auto available = snapshot != nullptr;
    result->setProperty("available", available);
    result->setProperty("freshness", available ? freshness : "unavailable");
    if (! available)
        return objectVar(std::move(result));

    result->setProperty("signal_active", snapshot->hasSignal);
    result->setProperty("sequence", static_cast<juce::int64>(snapshot->sequence));
    result->setProperty("elapsed_seconds", snapshot->elapsedSeconds);
    result->setProperty("sample_rate_hz", sampleRate > 0.0 && std::isfinite(sampleRate)
                                                   ? juce::var(sampleRate) : juce::var());

    auto metrics = std::make_unique<juce::DynamicObject>();
    metrics->setProperty("sample_peak_dbfs", metricVar(snapshot->samplePeakDbfs, "dBFS"));
    metrics->setProperty("rms_dbfs", metricVar(snapshot->rmsDbfs, "dBFS"));
    metrics->setProperty("crest_db", metricVar(snapshot->crestDb, "dB"));
    metrics->setProperty("short_term_lufs", metricVar(snapshot->shortTermLufs, "LUFS"));
    metrics->setProperty("width", metricVar(snapshot->width, "normalized_ratio"));
    metrics->setProperty("correlation", metricVar(snapshot->correlation, "coefficient"));
    metrics->setProperty("max_sample_over_db", metricVar(snapshot->maxSampleOverDb, "dBFS_over"));

    auto clip = std::make_unique<juce::DynamicObject>();
    clip->setProperty("available", true);
    clip->setProperty("active", snapshot->sampleClipActive);
    clip->setProperty("count", static_cast<juce::int64>(snapshot->sampleClipCount));
    metrics->setProperty("sample_clip", objectVar(std::move(clip)));

    result->setProperty("metrics", objectVar(std::move(metrics)));
    result->setProperty("spectrum", spectrumVar(*snapshot));
    return objectVar(std::move(result));
}

juce::var metricDeltaObject(const analysis::SnapshotComparison& comparison)
{
    auto deltas = std::make_unique<juce::DynamicObject>();
    deltas->setProperty("sample_peak_dbfs", metricVar(comparison.samplePeakDbfs.delta, "dB"));
    deltas->setProperty("rms_dbfs", metricVar(comparison.rmsDbfs.delta, "dB"));
    deltas->setProperty("crest_db", metricVar(comparison.crestDb.delta, "dB"));
    deltas->setProperty("short_term_lufs", metricVar(comparison.shortTermLufs.delta, "LU"));
    deltas->setProperty("width", metricVar(comparison.width.delta, "normalized_ratio"));
    deltas->setProperty("correlation", metricVar(comparison.correlation.delta, "coefficient"));
    return objectVar(std::move(deltas));
}

juce::var compareSpectrumDeltaVar(const analysis::AnalysisSnapshot* a,
                                  const analysis::AnalysisSnapshot* b)
{
    auto spectrum = std::make_unique<juce::DynamicObject>();
    spectrum->setProperty("operation", "mix_b_minus_mix_a");
    juce::Array<juce::var> bands;
    for (const auto& definition : contextBands)
    {
        const auto valueA = a != nullptr
            ? summarizeSpectrumBand(*a, definition.lowHz, definition.highHz)
            : analysis::MetricValue {};
        const auto valueB = b != nullptr
            ? summarizeSpectrumBand(*b, definition.lowHz, definition.highHz)
            : analysis::MetricValue {};
        const analysis::MetricValue delta = valueA.valid && valueB.valid
            ? analysis::MetricValue { valueB.value - valueA.value, true }
            : analysis::MetricValue {};
        auto band = std::make_unique<juce::DynamicObject>();
        band->setProperty("name", definition.name);
        band->setProperty("delta", metricVar(delta, "dB"));
        bands.add(objectVar(std::move(band)));
    }
    spectrum->setProperty("bands", bands);
    return objectVar(std::move(spectrum));
}

juce::var referenceVar(const ReferenceProfile* reference)
{
    auto result = std::make_unique<juce::DynamicObject>();
    const auto available = reference != nullptr && reference->available;
    result->setProperty("available", available);
    if (! available)
        return objectVar(std::move(result));

    result->setProperty("id", juce::String(reference->id));
    result->setProperty("name", juce::String(reference->name));
    result->setProperty("version", juce::String(reference->version));
    result->setProperty("freshness", "stored_reference");
    auto metrics = std::make_unique<juce::DynamicObject>();
    metrics->setProperty("sample_peak_dbfs", metricVar(reference->metrics.samplePeakDbfs, "dBFS"));
    metrics->setProperty("true_peak_dbtp", metricVar(reference->metrics.truePeakDbtp, "dBTP"));
    metrics->setProperty("rms_dbfs", metricVar(reference->metrics.rmsDbfs, "dBFS"));
    metrics->setProperty("crest_db", metricVar(reference->metrics.crestDb, "dB"));
    metrics->setProperty("momentary_lufs", metricVar(reference->metrics.momentaryLufs, "LUFS"));
    metrics->setProperty("short_term_lufs", metricVar(reference->metrics.shortTermLufs, "LUFS"));
    metrics->setProperty("integrated_lufs", metricVar(reference->metrics.integratedLufs, "LUFS"));
    metrics->setProperty("lra_lu", metricVar(reference->metrics.loudnessRangeLu, "LU"));
    metrics->setProperty("width", metricVar(reference->metrics.stereoWidth, "normalized_ratio"));
    metrics->setProperty("correlation", metricVar(reference->metrics.correlation, "coefficient"));
    result->setProperty("metrics", objectVar(std::move(metrics)));

    auto legacySpectrum = std::make_unique<juce::DynamicObject>();
    legacySpectrum->setProperty("representation", "legacy_nine_band_dbfs");
    juce::Array<juce::var> bands;
    for (std::size_t index = 0; index < reference->metrics.legacySpectrumBandDbfs.size(); ++index)
    {
        auto band = std::make_unique<juce::DynamicObject>();
        band->setProperty("centre_hz", ReferenceMetrics::legacySpectrumCentresHz[index]);
        band->setProperty("level", metricVar(
            reference->metrics.legacySpectrumBandDbfs[index], "dBFS"));
        bands.add(objectVar(std::move(band)));
    }
    legacySpectrum->setProperty("bands", bands);
    result->setProperty("spectrum", objectVar(std::move(legacySpectrum)));
    return objectVar(std::move(result));
}
} // namespace

juce::var buildConversationContext(const ConversationContextInput& input)
{
    auto root = std::make_unique<juce::DynamicObject>();
    root->setProperty("schema", "aifred.context.v1");

    if (input.mode == ConversationMode::analyze)
    {
        root->setProperty("mode", "Analyze");
        const auto freshness = input.current != nullptr && input.current->hasSignal
            ? "live" : input.current != nullptr && input.current->sequence > 0 ? "recent" : "waiting";
        root->setProperty("current", snapshotVar(input.current, input.sampleRate, freshness));
    }
    else if (input.mode == ConversationMode::compare)
    {
        root->setProperty("mode", "Compare");
        const auto* a = input.captures != nullptr ? input.captures->a().get() : nullptr;
        const auto* b = input.captures != nullptr ? input.captures->b().get() : nullptr;
        root->setProperty("mix_a", snapshotVar(a, input.sampleRate, "captured"));
        root->setProperty("mix_b", snapshotVar(b, input.sampleRate, "captured"));
        const auto comparison = input.captures != nullptr
            ? analysis::ComparisonEngine::compare(*input.captures)
            : analysis::SnapshotComparison {};
        auto delta = std::make_unique<juce::DynamicObject>();
        delta->setProperty("operation", "mix_b_minus_mix_a");
        delta->setProperty("metrics", metricDeltaObject(comparison));
        delta->setProperty("spectrum", compareSpectrumDeltaVar(a, b));
        root->setProperty("delta", objectVar(std::move(delta)));
    }
    else
    {
        root->setProperty("mode", "Reference");
        const auto freshness = input.current != nullptr && input.current->hasSignal
            ? "live" : input.current != nullptr && input.current->sequence > 0 ? "recent" : "waiting";
        root->setProperty("current", snapshotVar(input.current, input.sampleRate, freshness));
        root->setProperty("reference", referenceVar(input.reference));
        const auto comparable = input.reference != nullptr
            ? referenceAsComparableSnapshot(*input.reference) : analysis::AnalysisSnapshot {};
        const auto comparison = input.current != nullptr && input.reference != nullptr
            && input.reference->available
            ? analysis::ComparisonEngine::compare(*input.current, comparable)
            : analysis::SnapshotComparison {};
        auto delta = std::make_unique<juce::DynamicObject>();
        delta->setProperty("operation", "reference_minus_current");
        delta->setProperty("metrics", metricDeltaObject(comparison));
        delta->setProperty("spectrum", juce::var());
        root->setProperty("delta", objectVar(std::move(delta)));
    }

    return objectVar(std::move(root));
}

juce::String serializeConversationContext(const ConversationContextInput& input)
{
    return juce::JSON::toString(buildConversationContext(input), false);
}
} // namespace aifred::services

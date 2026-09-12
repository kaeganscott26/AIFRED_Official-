const RELEASES = Object.freeze({
  beta: Object.freeze({
    channel: "beta",
    version: "0.3.6",
    tag: "v0.3.6-beta-stable",
    source_repository: "kaeganscott26/AIFRED",
    release_url: "https://github.com/kaeganscott26/AIFRED/releases/tag/v0.3.6-beta-stable",
    published_at: "2026-09-07T01:30:42Z",
    artifact_source: "out/windows-x64/current",
    artifact_git_sha: "ec922b930205f7dc0accdefa733fa357df95bcf6",
    published: true,
    assets: Object.freeze({
      setup: Object.freeze({
        logical_name: "setup",
        r2_key: "releases/beta/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe",
        filename: "AIFRED-VST3-Setup.exe",
        content_type: "application/vnd.microsoft.portable-executable",
        size_bytes: 53930848,
        sha256: "d0731bfa6afdf5af02e9429bd03a847d7d06df1e549760c04fe5548bb3ae3421",
        published: true
      }),
      zip: Object.freeze({
        logical_name: "zip",
        r2_key: "releases/beta/v0.3.6-beta-stable/AIFRED-VST3-windows.zip",
        filename: "AIFRED-VST3-windows.zip",
        content_type: "application/zip",
        size_bytes: 2363132,
        sha256: "9cbcebbefe1928bbd7f5fd533abbc3136d7fcbcd6059ec72fbb3d108305a8d36",
        published: true
      })
    })
  }),
  flagship: Object.freeze({
    channel: "flagship",
    version: "4.0.0-alpha.2",
    tag: "v4.0.0-alpha.2",
    source_repository: "kaeganscott26/AIFRED_Official-",
    release_url: "https://north3rnlight3r.com",
    published_at: null,
    published: false,
    assets: Object.freeze({})
  })
});

const ASSET_ALIASES = Object.freeze({
  setup: "setup",
  installer: "setup",
  exe: "setup",
  zip: "zip",
  windows: "zip",
  "windows-zip": "zip"
});

export function releaseForChannel(channel) {
  return RELEASES[String(channel || "").trim().toLowerCase()] || null;
}

export function releaseAsset(channel, requestedAsset) {
  const release = releaseForChannel(channel);
  if (!release) return { release: null, asset: null, logicalName: "" };
  const logicalName = ASSET_ALIASES[String(requestedAsset || "").trim().toLowerCase()] || "";
  return { release, asset: logicalName ? release.assets[logicalName] || null : null, logicalName };
}

export function publicRelease(release) {
  if (!release?.published) return null;
  return {
    channel: release.channel,
    version: release.version,
    tag: release.tag,
    url: release.release_url,
    published_at: release.published_at,
    published: release.published,
    artifacts: Object.fromEntries(Object.entries(release.assets).map(([name, asset]) => [name, {
      logical_name: asset.logical_name,
      filename: asset.filename,
      content_type: asset.content_type,
      size_bytes: asset.size_bytes,
      sha256: asset.sha256,
      download_url: `/api/v1/downloads/plugin?channel=${encodeURIComponent(release.channel)}&asset=${encodeURIComponent(name)}`,
      published: asset.published
    }]))
  };
}

export function publicReleaseManifest() {
  return Object.values(RELEASES).filter((release) => release.published).map(publicRelease);
}

export { RELEASES };

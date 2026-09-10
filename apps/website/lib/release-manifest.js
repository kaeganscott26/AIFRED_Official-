const RELEASES = Object.freeze({
  beta: Object.freeze({
    channel: "beta",
    version: "0.3.6",
    tag: "v0.3.6-beta-stable",
    source_repository: "kaeganscott26/AIFRED",
    release_url: "https://github.com/kaeganscott26/AIFRED/releases/tag/v0.3.6-beta-stable",
    published_at: "2026-09-07T01:30:42Z",
    published: true,
    assets: Object.freeze({
      setup: Object.freeze({
        logical_name: "setup",
        r2_key: "releases/beta/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe",
        filename: "AIFRED-VST3-Setup.exe",
        content_type: "application/vnd.microsoft.portable-executable",
        size_bytes: 53964697,
        sha256: "ce9664d2cb3632cf72c3af930377cf3f0b6d15282c5ed1f33c8ec31aa829e71f",
        github_fallback_url: "https://github.com/kaeganscott26/AIFRED/releases/download/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe",
        published: true
      }),
      zip: Object.freeze({
        logical_name: "zip",
        r2_key: "releases/beta/v0.3.6-beta-stable/AIFRED-VST3-windows.zip",
        filename: "AIFRED-VST3-windows.zip",
        content_type: "application/zip",
        size_bytes: 2323863,
        sha256: "3bde33e7f30386d29baec937ed0613f2ee09cf5e322f1c76d758c6d78c6f2ea9",
        github_fallback_url: "https://github.com/kaeganscott26/AIFRED/releases/download/v0.3.6-beta-stable/AIFRED-VST3-windows.zip",
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
  if (!release) return null;
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
  return Object.values(RELEASES).map(publicRelease);
}

export { RELEASES };

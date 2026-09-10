const __base = String(window.AIFRED_API_BASE_URL || "https://north3rnlight3r.com/api").replace(/\/+$/, "");
const __apiV1Base = __base.endsWith("/v1") ? __base : `${__base}/v1`;
window.AIFRED_CONFIG = {
  apiBase: __base,
  apiV1Base: __apiV1Base,
  contactEmail: "north3rnlight3rofficial@outlook.com",
  downloadUrls: {
    windowsInstaller: `${__apiV1Base}/downloads/plugin?channel=beta&asset=setup`,
    windowsZip: `${__apiV1Base}/downloads/plugin?channel=beta&asset=zip`,
    macosZip: `${__apiV1Base}/downloads/plugin?channel=beta&asset=macos`,
    releaseNotes: "https://github.com/kaeganscott26/AIFRED"
  },
  productPrice: "$149.99"
};

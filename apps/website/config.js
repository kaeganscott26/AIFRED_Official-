function __aifredOrigin(value) {
  const fallback = "https://north3rnlight3r.com";
  try {
    const url = new URL(String(value || fallback), window.location.origin);
    url.pathname = url.pathname.replace(/\/+$/, "").replace(/\/(?:api\/v1|api|v1)$/i, "") || "/";
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/+$/, "");
  } catch {
    return fallback;
  }
}

const __origin = __aifredOrigin(window.AIFRED_API_BASE_URL);
window.AIFRED_CONFIG = {
  origin: __origin,
  apiBase: __origin,
  apiV1Base: `${__origin}/api/v1`,
  providerV1Base: `${__origin}/api/v1`,
  contactEmail: "north3rnlight3rofficial@outlook.com",
  downloadUrls: {
    windowsInstaller: `${__origin}/api/v1/downloads/plugin?channel=beta&asset=setup`,
    windowsZip: `${__origin}/api/v1/downloads/plugin?channel=beta&asset=zip`,
    releaseNotes: "https://github.com/kaeganscott26/AIFRED"
  },
  productPrice: "FREE",
  
};

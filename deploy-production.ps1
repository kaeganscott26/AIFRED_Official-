$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host " AIFRED PRODUCTION DEPLOYMENT"
Write-Host "========================================"
Write-Host ""

$Project = "aifred-site"
$Domain  = "https://north3rnlight3r.com"

# ------------------------------------------------------------
# 1. REQUIRE CORRECT REPO
# ------------------------------------------------------------

if (-not (Test-Path "apps/website/_worker.js")) {
    throw "Run this from the root of AIFRED_Official-. apps/website/_worker.js was not found."
}

if (-not (Test-Path "apps/website/wrangler.toml")) {
    throw "apps/website/wrangler.toml was not found."
}

if (-not (Test-Path "tools/deploy-website.mjs")) {
    throw "tools/deploy-website.mjs was not found."
}

Write-Host "[1/8] Repository"
git status --short
$Commit = (git rev-parse HEAD).Trim()
Write-Host "Commit: $Commit"

# ------------------------------------------------------------
# 2. VERIFY CLOUDFLARE LOGIN
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/8] Cloudflare authentication"

$Wrangler = "apps/node_modules/.bin/wrangler.cmd"

if (-not (Test-Path $Wrangler)) {
    Write-Host "Installing app dependencies..."
    npm --prefix apps install
}

& $Wrangler whoami

if ($LASTEXITCODE -ne 0) {
    throw "Wrangler is not authenticated. Run: npx wrangler login"
}

# ------------------------------------------------------------
# 3. VERIFY WE ARE TARGETING AIFRED-SITE
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/8] Deployment configuration"

$Config = Get-Content "apps/website/wrangler.toml" -Raw

if ($Config -notmatch 'name\s*=\s*"aifred-site"') {
    throw "wrangler.toml is not targeting aifred-site."
}

if ($Config -match 'AIFRED_PAGES_PROJECT\s*=\s*"aifred-api-staging"') {
    throw "STOP: wrangler.toml still points at aifred-api-staging."
}

Write-Host "Target: $Project"
Write-Host "Source: apps/website"
Write-Host "Router: apps/website/_worker.js"

# ------------------------------------------------------------
# 4. RUN THE TEST SUITE THAT ALREADY PASSED PREVIEW
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/8] Website/backend checks"

npm --prefix apps run website:check

if ($LASTEXITCODE -ne 0) {
    throw "website:check failed. Production deployment cancelled."
}

# ------------------------------------------------------------
# 5. SHOW EXISTING PRODUCTION SECRETS
#    DO NOT ROTATE OR DELETE THEM.
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/8] Existing Pages secrets"

& $Wrangler pages secret list --project-name $Project

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not list secrets, but no secret was modified."
}

# ------------------------------------------------------------
# 6. DEPLOY MAIN -> PRODUCTION
#
# This calls the deployment helper Codex just created.
# It packages ONLY the public website + bundled _worker.js,
# then deploys branch=main to aifred-site.
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/8] DEPLOYING PRODUCTION"
Write-Host ""
Write-Host "Project : $Project"
Write-Host "Branch  : main"
Write-Host "Commit  : $Commit"
Write-Host ""

npm --prefix apps run website:deploy

if ($LASTEXITCODE -ne 0) {
    throw "Cloudflare production deployment failed."
}

# ------------------------------------------------------------
# 7. WAIT BRIEFLY FOR THE CUSTOM DOMAIN TO PICK UP DEPLOYMENT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/8] Waiting for production edge..."
Start-Sleep -Seconds 8

# ------------------------------------------------------------
# 8. PRODUCTION SMOKE TEST
# ------------------------------------------------------------

Write-Host ""
Write-Host "[8/8] Production smoke test"
Write-Host ""

$Checks = @(
    "/",
    "/styles.css",
    "/app.js",
    "/config.js",
    "/assets/data/beat_catalog.json",
    "/ops",
    "/ops.css",
    "/ops.js",
    "/health",
    "/api/v1/reference/pool",
    "/v1/reference/pool",
    "/api/v1/releases"
)

$Failures = 0

foreach ($Path in $Checks) {
    try {
        $Response = Invoke-WebRequest `
            -Uri "$Domain$Path" `
            -Method GET `
            -MaximumRedirection 5 `
            -TimeoutSec 30 `
            -UseBasicParsing

        $Type = $Response.Headers["Content-Type"]

        Write-Host ("{0,-38} {1,-4} {2}" -f `
            $Path,
            $Response.StatusCode,
            $Type)

        if ($Response.StatusCode -lt 200 -or $Response.StatusCode -ge 400) {
            $Failures++
        }
    }
    catch {
        Write-Host ("{0,-38} FAIL {1}" -f $Path, $_.Exception.Message)
        $Failures++
    }
}

# ------------------------------------------------------------
# DOWNLOAD CHECKS
# ------------------------------------------------------------

Write-Host ""
Write-Host "Checking Beta downloads..."

$Downloads = @(
    "/api/v1/downloads/plugin?channel=beta&asset=setup",
    "/api/v1/downloads/plugin?channel=beta&asset=zip"
)

foreach ($Path in $Downloads) {
    try {
        $Response = Invoke-WebRequest `
            -Uri "$Domain$Path" `
            -Method HEAD `
            -MaximumRedirection 5 `
            -TimeoutSec 30 `
            -UseBasicParsing

        $Disposition = $Response.Headers["Content-Disposition"]
        $Length      = $Response.Headers["Content-Length"]

        Write-Host "$Path"
        Write-Host "  HTTP:     $($Response.StatusCode)"
        Write-Host "  Filename: $Disposition"
        Write-Host "  Bytes:    $Length"

        if ($Response.StatusCode -ne 200) {
            $Failures++
        }
    }
    catch {
        Write-Host "$Path FAIL: $($_.Exception.Message)"
        $Failures++
    }
}

Write-Host ""
Write-Host "========================================"

if ($Failures -eq 0) {
    Write-Host " PRODUCTION DEPLOYMENT PASSED"
    Write-Host ""
    Write-Host " $Domain"
    Write-Host " Project: $Project"
    Write-Host " Commit : $Commit"
}
else {
    Write-Warning "$Failures production smoke test(s) failed."
    Write-Warning "The deployment itself completed; inspect the failed route(s)."
}

Write-Host "========================================"
Write-Host ""
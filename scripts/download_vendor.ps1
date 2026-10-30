# Downloads third-party front-end files so the site works without CDNs:
#   - MapLibre GL JS 5.24.0 (BSD-3-Clause)        -> site/vendor/maplibre-gl/
#   - Noto Sans glyphs (SIL OFL) from OpenFreeMap  -> site/assets/glyphs/
# Run via download_vendor.bat (Win+R -> path to the .bat -> Enter).
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$log = Join-Path $PSScriptRoot 'download_vendor_log.txt'
"Vendor download log $(Get-Date -Format s)" | Out-File $log -Encoding utf8

$files = @()
$ml = 'https://unpkg.com/maplibre-gl@5.24.0'
$files += ,@("$ml/dist/maplibre-gl.js",  'site/vendor/maplibre-gl/maplibre-gl.js')
$files += ,@("$ml/dist/maplibre-gl.css", 'site/vendor/maplibre-gl/maplibre-gl.css')
$files += ,@("$ml/LICENSE.txt",          'site/vendor/maplibre-gl/LICENSE.txt')
foreach ($font in @('Noto Sans Regular', 'Noto Sans Bold')) {
  foreach ($range in @('0-255', '256-511', '1024-1279', '8192-8447')) {
    $u = 'https://tiles.openfreemap.org/fonts/' + [uri]::EscapeDataString($font) + "/$range.pbf"
    $files += ,@($u, "site/assets/glyphs/$font/$range.pbf")
  }
}

$failed = 0
foreach ($f in $files) {
  $url = $f[0]; $out = Join-Path $root $f[1]
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
  Write-Host "Downloading $($f[1]) ..."
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out
    "OK  $url  ->  $($f[1])  ($((Get-Item $out).Length) bytes)" | Out-File $log -Append -Encoding utf8
  } catch {
    $failed++
    Write-Host "  !!! FAILED: $url" -ForegroundColor Red
    "FAILED  $url  $($_.Exception.Message)" | Out-File $log -Append -Encoding utf8
  }
}
Write-Host ""
if ($failed -eq 0) { Write-Host "Done. All files downloaded." -ForegroundColor Green }
else { Write-Host "Done with $failed error(s). See scripts\download_vendor_log.txt" -ForegroundColor Yellow }

@echo off
rem ---------------------------------------------------------------
rem  Downloads the raw geodata used by the build pipeline into raw\
rem  Sources and licenses: docs\ARCHITECTURE.md, section 4
rem  A log is written to scripts\download_log.txt
rem ---------------------------------------------------------------
setlocal
cd /d "%~dp0.."
set LOG=%~dp0download_log.txt
echo Download log %DATE% %TIME% > "%LOG%"
echo Project folder: %CD% >> "%LOG%"
if not exist raw mkdir raw
if exist raw (echo raw folder OK >> "%LOG%") else (echo raw folder NOT CREATED >> "%LOG%")

set NE=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson

call :get "https://icr.ethz.ch/data/cshapes/CShapes-2.0.geojson" "raw\CShapes-2.0.geojson"
call :get "%NE%/ne_10m_admin_0_disputed_areas.geojson" "raw\ne_10m_admin_0_disputed_areas.geojson"
call :get "%NE%/ne_10m_admin_0_countries.geojson" "raw\ne_10m_admin_0_countries.geojson"
call :get "%NE%/ne_50m_admin_0_countries.geojson" "raw\ne_50m_admin_0_countries.geojson"
call :get "%NE%/ne_10m_admin_1_states_provinces.geojson" "raw\ne_10m_admin_1_states_provinces.geojson"

echo. >> "%LOG%"
dir /-C raw >> "%LOG%" 2>&1
echo.
echo ===== Files in raw\ =====
dir /-C raw
echo.
echo Done. A log was saved to scripts\download_log.txt. You can close this window.
pause
exit /b 0

:get
echo.
echo Downloading %~2 ...
echo. >> "%LOG%"
echo === %~1 >> "%LOG%"
where curl.exe >nul 2>nul
if errorlevel 1 goto ps
curl.exe -L --fail --retry 2 -sS -o "%~2" "%~1" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK curl >> "%LOG%" & exit /b 0)
echo   retrying without certificate revocation check ...
curl.exe -L --fail --retry 2 -sS --ssl-no-revoke -o "%~2" "%~1" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK curl --ssl-no-revoke >> "%LOG%" & exit /b 0)
:ps
echo   trying PowerShell ...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -UseBasicParsing -Uri '%~1' -OutFile '%~2'; exit 0 } catch { Write-Output $_.Exception.Message; exit 1 }" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK powershell >> "%LOG%" & exit /b 0)
echo   !!! FAILED: %~1
echo FAILED >> "%LOG%"
exit /b 0

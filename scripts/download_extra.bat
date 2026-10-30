@echo off
rem ---------------------------------------------------------------
rem  Downloads the data for the "armed conflicts" mode and the
rem  state names for the diplomatic relations block into raw\
rem    UCDP/PRIO Armed Conflict Dataset 26.1 (1946-2025), CC BY 4.0
rem    Correlates of War: Inter-, Intra-, Extra-State War Data, State list 2024
rem    Wikidata: state names RU/EN, CC0 (P530 is not used, see build_diplomacy.py)
rem  A log is written to scripts\download_extra_log.txt
rem ---------------------------------------------------------------
setlocal
cd /d "%~dp0.."
set LOG=%~dp0download_extra_log.txt
echo Download log %DATE% %TIME% > "%LOG%"
echo Project folder: %CD% >> "%LOG%"
if not exist raw mkdir raw

set COW=https://correlatesofwar.org/wp-content/uploads

call :get "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip" "raw\ucdp-prio-acd-261-csv.zip"
call :get "%COW%/Inter-StateWarData_v4.0.csv" "raw\Inter-StateWarData_v4.0.csv"
call :get "%COW%/Extra-StateWarData_v4.0.csv" "raw\Extra-StateWarData_v4.0.csv"
call :get "%COW%/Intra-State-Wars-v5.1.zip" "raw\Intra-State-Wars-v5.1.zip"
call :get "%COW%/States2024.zip" "raw\States2024.zip"
call :sparql "scripts\wikidata_states.rq" "raw\wikidata_states.csv"

echo. >> "%LOG%"
dir /-C raw >> "%LOG%" 2>&1
echo.
echo ===== Files in raw\ =====
dir /-C raw
echo.
echo Done. A log was saved to scripts\download_extra_log.txt. You can close this window.
pause
exit /b 0

:get
echo.
echo Downloading %~2 ...
echo. >> "%LOG%"
echo === %~1 >> "%LOG%"
where curl.exe >nul 2>nul
if errorlevel 1 goto ps
curl.exe -L --fail --retry 2 -sS -A "disputes-map/1.0 (non-commercial research)" -o "%~2" "%~1" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK curl >> "%LOG%" & exit /b 0)
echo   retrying without certificate revocation check ...
curl.exe -L --fail --retry 2 -sS --ssl-no-revoke -A "disputes-map/1.0 (non-commercial research)" -o "%~2" "%~1" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK curl --ssl-no-revoke >> "%LOG%" & exit /b 0)
:ps
echo   trying PowerShell ...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -UseBasicParsing -UserAgent 'disputes-map/1.0' -Uri '%~1' -OutFile '%~2'; exit 0 } catch { Write-Output $_.Exception.Message; exit 1 }" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK powershell >> "%LOG%" & exit /b 0)
echo   !!! FAILED: %~1
echo FAILED >> "%LOG%"
exit /b 0

:sparql
echo.
echo Querying Wikidata: %~1 ...
echo. >> "%LOG%"
echo === SPARQL %~1 >> "%LOG%"
where curl.exe >nul 2>nul
if errorlevel 1 goto sparqlps
curl.exe -G --fail --retry 2 -sS -A "disputes-map/1.0 (non-commercial research)" -H "Accept: text/csv" --data-urlencode "query@%~1" -o "%~2" "https://query.wikidata.org/sparql" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK curl >> "%LOG%" & exit /b 0)
curl.exe -G --fail --retry 2 -sS --ssl-no-revoke -A "disputes-map/1.0 (non-commercial research)" -H "Accept: text/csv" --data-urlencode "query@%~1" -o "%~2" "https://query.wikidata.org/sparql" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK curl --ssl-no-revoke >> "%LOG%" & exit /b 0)
:sparqlps
echo   trying PowerShell ...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { $q = Get-Content -Raw -Encoding UTF8 '%~1'; Invoke-WebRequest -UseBasicParsing -UserAgent 'disputes-map/1.0' -Headers @{Accept='text/csv'} -Uri ('https://query.wikidata.org/sparql?query=' + [uri]::EscapeDataString($q)) -OutFile '%~2'; exit 0 } catch { Write-Output $_.Exception.Message; exit 1 }" >> "%LOG%" 2>&1
if not errorlevel 1 (echo   OK & echo OK powershell >> "%LOG%" & exit /b 0)
echo   !!! FAILED: %~1
echo FAILED >> "%LOG%"
exit /b 0

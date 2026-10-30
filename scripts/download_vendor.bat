@echo off
rem Runs download_vendor.ps1 (MapLibre GL JS + glyphs). Execution policy is bypassed for this one process only.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0download_vendor.ps1"
pause

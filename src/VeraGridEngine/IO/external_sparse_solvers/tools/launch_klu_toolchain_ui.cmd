@echo off
setlocal
set BOOTSTRAPPER=%~dp0benchmark_results\vs_BuildTools_klu.exe
if not exist "%BOOTSTRAPPER%" (
  powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_BuildTools.exe' -OutFile '%BOOTSTRAPPER%'"
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%BOOTSTRAPPER%' -ArgumentList '--installPath C:\Users\andre\ExternalBuildTools --config "%~dp0install_klu_toolchain_ui.vsconfig" --includeRecommended --nocache' -Verb RunAs -Wait"

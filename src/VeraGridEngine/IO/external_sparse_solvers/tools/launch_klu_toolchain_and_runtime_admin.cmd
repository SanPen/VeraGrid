@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "%~dp0install_klu_toolchain_and_runtime_admin.ps1"' -Wait"

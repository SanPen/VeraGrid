@echo off
call "C:\Users\andre\ExternalBuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64
set PLUGIN_DIR=%~dp0
set BUILD_DIR=%PLUGIN_DIR%native_build
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
python setup.py build_ext --build-lib "%BUILD_DIR%"

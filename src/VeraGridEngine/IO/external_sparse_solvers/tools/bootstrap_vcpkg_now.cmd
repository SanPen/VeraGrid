@echo off
call "C:\Users\andre\ExternalBuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64
cd /d C:\Users\andre\.VeraGrid\external_native\vcpkg
bootstrap-vcpkg.bat -disableMetrics

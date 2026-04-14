@echo off
call "C:\Users\andre\ExternalBuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64
where cl
python -m pip install --upgrade --target "C:\Users\andre\.VeraGrid\external_python_packages\klu_cvxoptklu" "C:\Users\andre\PycharmProjects\VeraGrid\trunk\dynamics_emt\benchmark_results\cvxoptklu_src\unpacked\cvxoptklu-1.2.4"

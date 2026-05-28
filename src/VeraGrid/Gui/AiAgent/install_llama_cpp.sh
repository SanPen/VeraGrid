sudo apt-get install nvidia-cuda-toolkit
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m pip uninstall -y llama-cpp-python
set CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_FORCE_CUBLAS=on -DLLAVA_BUILD=off -DCMAKE_CUDA_ARCHITECTURES=native"
set FORCE_CMAKE=1
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m pip install "llama-cpp-python==0.3.23" --no-cache-dir

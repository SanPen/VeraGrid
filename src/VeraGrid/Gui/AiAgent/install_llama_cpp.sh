sudo apt-get install nvidia-cuda-toolkit
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m pip uninstall -y llama-cpp-python
set CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_FORCE_CUBLAS=on -DLLAVA_BUILD=off -DCMAKE_CUDA_ARCHITECTURES=native"
set FORCE_CMAKE=1
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m pip install --require-hashes --no-cache-dir \
  "llama-cpp-python==0.3.23" \
  --hash=sha256:85493cd887b543588941e8704640fef6a54c057443292e527559c30728375ffd

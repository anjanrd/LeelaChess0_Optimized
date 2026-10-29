# Python preparation environment

Root `requirements.txt` is the imported dependency specification. `windows-prep.lock.txt` records `python -m pip freeze` from the existing Python 3.11.9 preparation environment during consolidation; use it for a comparable Windows preparation environment. It is not a portable GPU-runtime lock or proof of a fresh installation.

The Python ONNX Runtime 1.31.1 package is used for CPU model preparation/selection. lc0's Windows GPU executable carries a separate ONNX Runtime 1.22.1 plus TensorRT 10.12 installation under `.runtime/tools/lc0/`. Keep those distinctions explicit.

Use `.venv/Scripts/python.exe -m pip ...` on Windows. Create a fresh `.venv` on another machine rather than copying this one. Historical A-side WSL dependency locks remain under `archive/person-a-week1/requirements/`.

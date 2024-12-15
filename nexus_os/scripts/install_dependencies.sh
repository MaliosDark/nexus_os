#!/bin/bash

# Exit script on any error
set -e

echo "Updating system and installing Python..."
sudo pacman -Syu --noconfirm python python-pip

echo "Creating a virtual environment..."
# Create a virtual environment in the "venv" directory
python -m venv venv

echo "Activating the virtual environment..."
# Activate the virtual environment
source venv/bin/activate

echo "Installing Python packages in the virtual environment..."
# Create a temporary requirements file
cat <<EOL > requirements.txt
aiohappyeyeballs
aiohttp
aiosignal
aiosqlite
annotated-types
anyio
async-timeout
attrs
certifi
charset-normalizer
dataclasses-json
exceptiongroup
faiss-gpu
filelock
frozenlist
fsspec
greenlet
h11
httpcore
httpx
huggingface-hub
idna
Jinja2
joblib
jsonpatch
jsonpointer
langchain
langchain-community
langchain-core
langchain-ollama
langchain-text-splitters
langsmith
MarkupSafe
marshmallow
MouseInfo
mpmath
multidict
mypy-extensions
networkx
numpy
nvidia-cublas-cu12
nvidia-cuda-cupti-cu12
nvidia-cuda-nvrtc-cu12
nvidia-cuda-runtime-cu12
nvidia-cudnn-cu12
nvidia-cufft-cu12
nvidia-curand-cu12
nvidia-cusolver-cu12
nvidia-cusparse-cu12
nvidia-nccl-cu12
nvidia-nvjitlink-cu12
nvidia-nvtx-cu12
ollama
opencv-python
orjson
packaging
pillow
pkg_resources
propcache
psutil
PyAutoGUI
pydantic
pydantic_core
PyGetWindow
PyMsgBox
pyperclip
PyRect
PyScreeze
PySide6
PySide6_Addons
PySide6_Essentials
python3-xlib
pytweening
PyYAML
regex
requests
requests-toolbelt
safetensors
schedule
scikit-learn
scipy
sentence-transformers
shiboken6
sniffio
SQLAlchemy
sympy
tenacity
threadpoolctl
tokenizers
torch
tqdm
transformers
triton
typing-inspect
typing_extensions
urllib3
yarl
EOL

# Install the dependencies in the virtual environment
pip install --upgrade pip
pip install -r requirements.txt

# Clean up the temporary requirements file
rm requirements.txt

echo "All dependencies have been installed in the virtual environment."

# Provide instructions for activating the virtual environment
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To deactivate the virtual environment, simply run: deactivate"

# Deactivate the virtual environment to ensure it's not left active after the script ends
deactivate

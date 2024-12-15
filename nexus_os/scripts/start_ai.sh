#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Error handling function
handle_error() {
    echo "An error occurred during startup. Check the logs above for details."
    exit 1
}

# Trap errors and call handle_error
trap 'handle_error' ERR

echo "Starting Nexus OS initialization..."

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate
export PYTHONPATH=$(pwd)/nexus_os

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "All dependencies installed successfully."

echo "------------------------------------------"
echo "Before starting Nexus OS, ensure Ollama servers are running:"
echo "    ollama serve --model-path /path/to/llama3.2 --port 11434"
echo "    ollama serve --model-path /path/to/bakllava --port 11434"
echo "------------------------------------------"

# Start Nexus OS
echo "Starting Nexus OS..."
#python nexus_os/core/main.py
python3 gui_app.py

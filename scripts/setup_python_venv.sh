#!/bin/bash

cd "$(dirname "$0")"
cd ..
cd $1

# Define your virtual environment directory name
VENV_DIR="venv"

# Check if the virtual environment directory exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists. Activating it."
else
    echo "Creating virtual environment."
    # Create the virtual environment
    python3 -m venv $VENV_DIR
fi

# Activate the virtual environment
# For Bash shell
source $VENV_DIR/bin/activate

# For Fish shell, use: source $VENV_DIR/bin/activate.fish
# For Csh or Tcsh shell, use: source $VENV_DIR/bin/activate.csh
# For PowerShell, use: $VENV_DIR\Scripts\Activate.ps1

# Check if requirements.txt exists and install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt."
    pip install -r requirements.txt
else
    echo "requirements.txt not found."
fi
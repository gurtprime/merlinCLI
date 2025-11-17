#!/bin/bash
# Quick activation script for merlinCLI virtual environment

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating it..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -e .
    echo "Setup complete!"
else
    source venv/bin/activate
    echo "Virtual environment activated!"
    echo "Run 'deactivate' to exit when done."
fi


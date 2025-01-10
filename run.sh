#!/bin/bash

LOCKFILE="dependencies.lock"
REQUIREMENTS="requirements.txt"

echo "Checking if Python is installed..."
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python."
    read -n 1 -s -r -p "Press any key to continue . . ." 
    exit 1
fi

if ! python3 -m venv --help &> /dev/null
then
    echo "venv module is not available."
    read -n 1 -s -r -p "Press any key to continue . . ." 
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

if ! python -m pip --version &> /dev/null
then
    echo "Installing pip..."
    python -m ensurepip > /dev/null 2>&1
    python -m pip install --upgrade pip --disable-pip-version-check > /dev/null 2>&1
fi

if [ ! -f "$LOCKFILE" ]; then
    echo "Lock file not found. Installing dependencies..."
    python -m pip install --disable-pip-version-check -r "$REQUIREMENTS"
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies."
        read -n 1 -s -r -p "Press any key to continue . . ." 
        exit 1
    fi
    cp "$REQUIREMENTS" "$LOCKFILE"
else
    if ! cmp -s "$REQUIREMENTS" "$LOCKFILE"; then
        echo "Requirements have changed. Updating dependencies..."
        python -m pip install --disable-pip-version-check -r "$REQUIREMENTS"
        if [ $? -ne 0 ]; then
            echo "Failed to update dependencies."
            read -n 1 -s -r -p "Press any key to continue . . ." 
            exit 1
        fi
        cp "$REQUIREMENTS" "$LOCKFILE"
    else
        echo "Python dependencies are up to date."
    fi
fi

python src/main.py
read -n 1 -s -r -p "Press any key to continue . . ." 

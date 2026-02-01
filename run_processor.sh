#!/bin/bash

# --- Configuration ---
# Set the location where your Python files are saved.
# Using '.' means the current directory where this script is run.
PYTHON_SCRIPT_DIR="./" 
# If your scripts are in a specific folder, use the full path: 
# e.g., PYTHON_SCRIPT_DIR="/home/user/my_scripts"
# ---------------------


echo "Starting Pulse Vector Pipeline..."
echo "------------------------------------------------"


PYTHON_SCRIPT="process_data.py"

if [ -f "$PYTHON_SCRIPT" ]; then
    echo "-> Executing: $PYTHON_SCRIPT"
    python3 "$PYTHON_SCRIPT"

    
    if [ $? -eq 0 ]; then
        echo "✅ Pipeline completed successfully."
    else
        echo "❌ Pipeline failed."
        exit 1
    fi
else
    echo "⚠️ Error: $PYTHON_SCRIPT not found."
    exit 1
fi

echo "------------------------------------------------"
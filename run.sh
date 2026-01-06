#!/bin/bash
# run.sh
# Wrapper script to run Caveat Umbrella with correct library paths

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add the current directory to LD_LIBRARY_PATH so linux can find libonnxruntime.so
export LD_LIBRARY_PATH="$DIR:$LD_LIBRARY_PATH"

echo "🌂 Starting Caveat Umbrella..."
echo "Libraries path: $LD_LIBRARY_PATH"

# Run the python script using the venv
if [ -f "$DIR/.venv/bin/activate" ]; then
    "$DIR/.venv/bin/python3" "$DIR/main.py" "$@"
else
    # Fallback if no venv found (global install)
    python3 "$DIR/main.py" "$@"
fi

#!/bin/bash
# Start script for Laundriuno

# Load environment variables if config.env exists
if [ -f config.env ]; then
    export $(cat config.env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Flask application
python app.py

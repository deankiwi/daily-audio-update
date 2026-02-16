#!/bin/bash

# Ensure we are in the directory of the script
cd "$(dirname "$0")"

# Go up one level to the project root
cd ..

# Pull the latest changes from the repository
echo "Pulling latest changes..."
git pull origin main

# Sync dependencies using uv
echo "Syncing dependencies..."
uv sync

# Run the main application
echo "Running daily audio update..."
uv run main.py

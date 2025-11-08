#!/bin/bash

# Script to update Ableton Remote Script
# Run this after making changes to the Python files

SOURCE_DIR="/Users/juandavidguerrerocastro/Documents/PROJECTS/MUSIC_DEVICES/ableton_midi_api_integration"
DEST_DIR="/Users/juandavidguerrerocastro/Library/Preferences/Ableton/Live 12.2.6/User Remote Scripts/PushClone"

echo "🔄 Updating Ableton Remote Script..."
echo "Source: $SOURCE_DIR"
echo "Dest:   $DEST_DIR"
echo ""

# Copy all Python files
echo "📦 Copying Python files..."
cp -v "$SOURCE_DIR"/*.py "$DEST_DIR/"

# Touch __init__.py to force Ableton to reload
echo ""
echo "⏰ Updating __init__.py timestamp..."
touch "$DEST_DIR/__init__.py"

echo ""
echo "✅ Files updated successfully!"
echo ""
echo "📋 Next steps:"
echo "1. In Ableton: Preferences → Link, Tempo & MIDI"
echo "2. Control Surface → None"
echo "3. Control Surface → PushClone"
echo "4. Look for '✅ Script loaded' in logs"
echo ""
echo "🔍 Monitor logs:"
echo "tail -f ~/Library/Preferences/Ableton/Live\\ 12.2.6/Log.txt"

#!/bin/bash

# Script para monitorear logs de colores en tiempo real
# Uso: ./watch_color_logs.sh

LOG_FILE="$HOME/Library/Preferences/Ableton/Live 12.2.6/Log.txt"

echo "=================================="
echo "Monitoreando logs de colores RGB"
echo "=================================="
echo "Archivo: $LOG_FILE"
echo ""
echo "Presiona Ctrl+C para salir"
echo ""
echo "Esperando actualizaciones de grilla..."
echo "=================================="
echo ""

# Monitorear el archivo en tiempo real
# Filtrar solo las líneas relevantes de colores
tail -f "$LOG_FILE" | grep --line-buffered -E "GRID_ENCODE|PAD\[|Total payload|====="

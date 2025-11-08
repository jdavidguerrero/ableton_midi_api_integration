#!/bin/bash

# Script para monitorear TODOS los logs en tiempo real
# Uso: ./watch_all_logs.sh

LOG_FILE="$HOME/Library/Preferences/Ableton/Live 12.2.6/Log.txt"

echo "=================================="
echo "Monitoreando TODOS los logs"
echo "=================================="
echo "Archivo: $LOG_FILE"
echo ""
echo "Presiona Ctrl+C para salir"
echo "=================================="
echo ""

# Monitorear el archivo en tiempo real sin filtros
tail -f "$LOG_FILE"

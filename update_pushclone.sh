#!/bin/bash
# 🟢 Ableton PushClone Script Updater (User Library)
# Copia los archivos Python desde el repositorio del proyecto a la carpeta
# real donde Ableton Live busca los Remote Scripts del usuario.

# === CONFIGURACIÓN ===
SOURCE_DIR="/Users/juandavidguerrerocastro/Documents/PROJECTS/MUSIC_DEVICES/ableton_midi_api_integration"
DEST_DIR="/Users/juandavidguerrerocastro/Music/Ableton/User Library/Remote Scripts/PushClone"

echo ""
echo "🎛  Ableton PushClone Script Updater"
echo "📦 Origen:  $SOURCE_DIR"
echo "📂 Destino: $DEST_DIR"
echo ""

# === Crear carpeta destino si no existe ===
mkdir -p "$DEST_DIR"

# === Copiar archivos Python del repositorio ===
echo "🚚 Copiando archivos .py..."
cp -v "$SOURCE_DIR"/*.py "$DEST_DIR/" || {
    echo "❌ Error: no se pudieron copiar los archivos desde $SOURCE_DIR"
    exit 1
}

# === Forzar recarga (actualizar timestamp de __init__.py) ===
if [ -f "$DEST_DIR/__init__.py" ]; then
    echo "⏰ Actualizando timestamp de __init__.py..."
    touch "$DEST_DIR/__init__.py"
fi

# === Limpiar cachés de Python dentro del User Library ===
echo ""
echo "🧹 Limpiando cachés..."
find "/Users/juandavidguerrerocastro/Music/Ableton/User Library/Remote Scripts" \
    -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "/Users/juandavidguerrerocastro/Music/Ableton/User Library/Remote Scripts" \
    -type f -name "*.pyc" -delete 2>/dev/null
echo "✅ Caché limpia."

# === Mostrar pasos finales ===
echo ""
echo "✅ Archivos actualizados correctamente."
echo ""
echo "📋 Pasos siguientes:"
echo "1️⃣  En Ableton → Preferencias → Link, Tempo & MIDI"
echo "2️⃣  Control Surface → None"
echo "3️⃣  Control Surface → PushClone"
echo "   (Esto fuerza a Live a recargar el script.)"
echo ""
echo "🧾 Para verificar en el log:"
echo "   tail -f ~/Library/Preferences/Ableton/Live*/Log.txt | grep PushClone"
echo ""
echo "🚀 Listo."

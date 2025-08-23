#!/usr/bin/env python3
"""
MIDI Debug Test Script
Diagnóstica problemas MIDI con PushClone

Para usar:
1. Abre Ableton Live
2. Carga PushClone como Control Surface  
3. Ejecuta este script en terminal: python midi_debug_test.py
"""

import time
import sys
import os

def print_midi_diagnosis():
    print("🔍 MIDI DIAGNOSIS - PushClone Debug")
    print("=" * 50)
    
    print("\n📋 CHECKLISTS:")
    print("✓ Ableton Live está corriendo?")
    print("✓ PushClone está cargado en Preferences → MIDI?")
    print("✓ Puerto MIDI Input/Output configurado?")
    print("✓ IAC Driver habilitado (macOS)?")
    
    print("\n🔧 PASOS PARA DEBUGGING:")
    print("1. Abrir Ableton Live Logs:")
    print("   macOS: ~/Library/Logs/Ableton Live Logs/Base.log")
    print("   Windows: %USERPROFILE%\\AppData\\Roaming\\Ableton\\Live [version]\\Logs\\")
    
    print("\n2. Filtrar logs de PushClone:")
    print("   # Ubicación correcta de logs en macOS:")
    print("   ls -t \"/Users/$(whoami)/Library/Application Support/Ableton/Live Reports/Usage/\"*.log | head -1")
    print("   # Para monitorear:")
    print("   tail -f [archivo_log_mas_reciente] | grep -i pushclone")
    
    print("\n3. Agregar un device en Live y observar logs")
    
    print("\n🚨 ERRORES MIDI COMUNES:")
    print("• 'Error while sending midi message' = Puerto MIDI cerrado/hardware desconectado")
    print("• SysEx messages son UNIDIRECCIONALES - no requieren ACK")
    print("• Errores normales cuando no hay hardware físico conectado")
    
    print("\n💡 DEBUGGING TIPS:")
    print("• Usar MIDI Monitor app para ver mensajes salientes")
    print("• Verificar que el puerto virtual esté activo")
    print("• Los errores MIDI NO afectan la funcionalidad del script")
    
    print("\n🧪 TESTS MANUALES:")
    print("1. Agregar device → Ver logs: '🎛️ Track X devices changed'")
    print("2. Cambiar volumen → Ver logs: '🔊 Track X volume'")
    print("3. Trigger clip → Ver logs: '📋 Clip triggered'")
    
    print("\n🎛️ COMANDOS SYSEX ENVIADOS:")
    print("• 0x20: Track state")
    print("• 0x10: Clip state") 
    print("• 0x40: Device state")
    print("• 0x4B: NeoTrellis drum grid")
    print("• 0x50: Transport state")
    
    print("\n✅ SCRIPT FUNCIONANDO SI VES:")
    print("• Logs de eventos cuando cambias cosas en Live")
    print("• SysEx messages en MIDI Monitor")
    print("• No crashes del script")

if __name__ == "__main__":
    print_midi_diagnosis()

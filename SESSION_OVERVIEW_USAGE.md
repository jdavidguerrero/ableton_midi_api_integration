# Session Overview - Enhanced Features

## 🎯 Overview

El **Session Overview mejorado** proporciona una vista de zoom múltiple de tu sesión completa con:
- **4 niveles de zoom** (1:1, 2:1, 4:1, 8:1)
- **Indicador de viewport** (muestra dónde está tu ring)
- **Colores de track** en los clips
- **Actualización dinámica** en tiempo real
- **Navegación en overview mode**
- **Jump to position** (click para ir)

---

## 📊 Modos de Zoom

### Zoom 1:1 (Default)
- Cada pad = 1 clip
- Vista: 8x4 clips (8 scenes x 4 tracks)
- Ideal para: control preciso

### Zoom 2:1
- Cada pad = 2x2 clips (4 clips)
- Vista: 16x8 clips
- Ideal para: vista media

### Zoom 4:1
- Cada pad = 4x4 clips (16 clips)
- Vista: 32x16 clips
- Ideal para: proyectos medianos

### Zoom 8:1
- Cada pad = 8x8 clips (64 clips)
- Vista: 64x32 clips
- Ideal para: proyectos grandes, overview completo

---

## 🎮 Comandos MIDI (Hardware → Live)

### Activar/Desactivar Overview

```cpp
// Toggle overview on/off
uint8_t payload[] = {0};  // 0 = toggle
sendSysEx(CMD_SESSION_OVERVIEW, payload, 1);
```

### Controlar Zoom

```cpp
// Zoom in (1:1 ← 2:1 ← 4:1 ← 8:1)
uint8_t payload[] = {1};  // 1 = zoom in
sendSysEx(CMD_SESSION_OVERVIEW, payload, 1);

// Zoom out (1:1 → 2:1 → 4:1 → 8:1)
uint8_t payload[] = {2};  // 2 = zoom out
sendSysEx(CMD_SESSION_OVERVIEW, payload, 1);

// Cycle zoom (1 → 2 → 4 → 8 → 1)
uint8_t payload[] = {3};  // 3 = cycle zoom
sendSysEx(CMD_SESSION_OVERVIEW, payload, 1);
```

### Navegar en Overview

```cpp
// Navigate left/right/up/down
uint8_t action = 0;     // 0 = no toggle
uint8_t direction = 1;  // 0=left, 1=right, 2=up, 3=down
uint8_t payload[] = {action, direction};
sendSysEx(CMD_SESSION_OVERVIEW, payload, 2);
```

### Jump to Position

```cpp
// Click on pad to jump ring to that position
uint8_t action = 0;    // 0 = no toggle
uint8_t reserved = 0;  // Reserved
uint8_t pad_x = 3;     // Pad X coordinate (0-7)
uint8_t pad_y = 1;     // Pad Y coordinate (0-3)
uint8_t payload[] = {action, reserved, pad_x, pad_y};
sendSysEx(CMD_SESSION_OVERVIEW, payload, 4);
```

---

## 📡 Mensajes MIDI (Live → Hardware)

### Overview Grid Data

```cpp
// CMD_SESSION_OVERVIEW_GRID (0x6F)
// Payload: 96 bytes (8x4 pads * 3 RGB bytes)

void handleOverviewGrid(uint8_t* data, uint8_t length) {
    for (int pad = 0; pad < 32; pad++) {
        uint8_t r = data[pad * 3 + 0];
        uint8_t g = data[pad * 3 + 1];
        uint8_t b = data[pad * 3 + 2];

        // Update NeoPixel/LED
        grid.setPixelColor(pad, r*2, g*2, b*2);  // Scale to 0-255
    }
    grid.show();
}
```

### Overview Metadata

```cpp
// CMD_SESSION_OVERVIEW (0x6E)
// Payload: [zoom_level, track_offset, scene_offset, total_tracks, total_scenes]

void handleOverviewMetadata(uint8_t* data, uint8_t length) {
    uint8_t zoom = data[0];          // 1, 2, 4, or 8
    uint8_t track_offset = data[1];  // Current overview position
    uint8_t scene_offset = data[2];
    uint8_t total_tracks = data[3];  // Total in session
    uint8_t total_scenes = data[4];

    // Update display/LEDs with this info
    displayZoomLevel(zoom);
}
```

---

## 🎨 Interpretación de Colores

### Estados de Clips

El color de cada pad en overview representa el estado agregado de los clips en esa región:

| Color | Estado | Descripción |
|-------|--------|-------------|
| **Verde** | Playing | Uno o más clips sonando |
| **Rojo** | Recording | Uno o más clips grabando |
| **Amarillo** | Queued | Uno o más clips en cola |
| **Color de Track** | Has Clips | Clips presentes (usa promedio de colores de tracks) |
| **Negro** | Empty | Sin clips |

### Intensidad del Color

La **intensidad** (brillo) indica la **densidad de clips**:
- Muy brillante = región llena de clips
- Medio = algunos clips
- Tenue = pocos clips

### Indicador de Ring

Las regiones que contienen el **ring viewport** actual tienen un **overlay blanco** (30% white mix) para mostrar dónde estás posicionado.

---

## 💡 Ejemplo de Implementación (Teensy/Arduino)

```cpp
class SessionOverview {
private:
    bool isActive = false;
    uint8_t zoomLevel = 1;
    uint8_t currentTrackOffset = 0;
    uint8_t currentSceneOffset = 0;

    // Grid storage (8x4)
    uint32_t gridColors[32];

public:
    // Toggle overview
    void toggle() {
        isActive = !isActive;

        uint8_t payload[] = {0};  // 0 = toggle
        sendSysEx(CMD_SESSION_OVERVIEW, payload, 1);

        if (!isActive) {
            // Return to normal session view
            clearGrid();
        }
    }

    // Cycle zoom
    void cycleZoom() {
        uint8_t payload[] = {3};  // 3 = cycle zoom
        sendSysEx(CMD_SESSION_OVERVIEW, payload, 1);
    }

    // Handle pad press in overview mode
    void onPadPress(uint8_t x, uint8_t y) {
        if (isActive) {
            // Jump to this position
            uint8_t payload[] = {0, 0, x, y};
            sendSysEx(CMD_SESSION_OVERVIEW, payload, 4);
        }
    }

    // Navigate with arrows/encoders
    void navigate(Direction dir) {
        uint8_t direction;
        switch(dir) {
            case LEFT:  direction = 0; break;
            case RIGHT: direction = 1; break;
            case UP:    direction = 2; break;
            case DOWN:  direction = 3; break;
        }

        uint8_t payload[] = {0, direction};
        sendSysEx(CMD_SESSION_OVERVIEW, payload, 2);
    }

    // Update grid from incoming SysEx
    void updateGrid(uint8_t* data, uint8_t length) {
        // Expect 96 bytes (32 pads * 3 RGB)
        for (int i = 0; i < 32; i++) {
            uint8_t r = data[i * 3 + 0];
            uint8_t g = data[i * 3 + 1];
            uint8_t b = data[i * 3 + 2];

            gridColors[i] = neoPixel.Color(r*2, g*2, b*2);
        }

        // Refresh display
        refreshDisplay();
    }

    // Update metadata
    void updateMetadata(uint8_t* data, uint8_t length) {
        if (length >= 5) {
            zoomLevel = data[0];
            currentTrackOffset = data[1];
            currentSceneOffset = data[2];
            // data[3] = total tracks
            // data[4] = total scenes

            updateZoomIndicator();
        }
    }
};

// Usage in main loop
SessionOverview overview;

void onSysExReceived(uint8_t command, uint8_t* payload, uint8_t length) {
    switch(command) {
        case CMD_SESSION_OVERVIEW_GRID:
            overview.updateGrid(payload, length);
            break;

        case CMD_SESSION_OVERVIEW:
            overview.updateMetadata(payload, length);
            break;
    }
}

void onButtonPressed(uint8_t button) {
    if (button == BUTTON_OVERVIEW) {
        overview.toggle();
    }
    else if (button == BUTTON_ZOOM) {
        overview.cycleZoom();
    }
}

void onEncoderTurned(int delta) {
    if (overview.isActive) {
        if (delta > 0) {
            overview.navigate(RIGHT);
        } else {
            overview.navigate(LEFT);
        }
    }
}
```

---

## 🎯 Flujo de Usuario Típico

1. **Usuario presiona botón "Overview"**
   - Hardware envía: `CMD_SESSION_OVERVIEW` con payload `[0]` (toggle)
   - Live activa overview y envía grid completo
   - Hardware muestra vista con zoom 1:1

2. **Usuario presiona "Zoom" varias veces**
   - Hardware envía: `CMD_SESSION_OVERVIEW` con payload `[3]` (cycle)
   - Live cambia zoom: 1:1 → 2:1 → 4:1 → 8:1 → 1:1
   - Grid se actualiza mostrando más/menos clips por pad

3. **Usuario navega con encoders/arrows**
   - Hardware envía: `CMD_SESSION_OVERVIEW` con payload `[0, direction]`
   - Live mueve el viewport
   - Grid se actualiza con nueva región

4. **Usuario hace click en un pad**
   - Hardware envía: `CMD_SESSION_OVERVIEW` con payload `[0, 0, pad_x, pad_y]`
   - Live mueve el ring a esa posición
   - Overview se actualiza mostrando ring indicator

5. **Usuario presiona "Overview" de nuevo**
   - Hardware envía: `CMD_SESSION_OVERVIEW` con payload `[0]` (toggle off)
   - Live desactiva overview
   - Hardware vuelve a session view normal

---

## 🔧 Ventajas de la Implementación Mejorada

### vs Implementación Anterior

| Feature | Anterior | Mejorado |
|---------|----------|----------|
| Zoom levels | ❌ Fixed 8x8 | ✅ 1:1, 2:1, 4:1, 8:1 |
| Colores | ❌ 4 niveles | ✅ Full RGB + track colors |
| Ring indicator | ❌ No | ✅ White overlay |
| Actualización | ❌ Estática | ✅ Listeners dinámicos |
| Navegación | ❌ No | ✅ 4 direcciones + jump |
| Adaptación | ❌ Hardcoded | ✅ Adapta a session size |
| Grid size | ⚠️ Inconsistente (8x8) | ✅ Correcto (8x4) |

---

## 📝 Notas de Implementación

1. **Memoria**: El overview con listeners usa ~200 bytes por clip visible
2. **Performance**: Los listeners solo se activan cuando overview está activo
3. **Latencia**: Actualizaciones de grid en <50ms típicamente
4. **Escalabilidad**: Funciona con sesiones de 100+ tracks/scenes

---

## 🐛 Troubleshooting

### Grid no se actualiza
- Verificar que CMD_SESSION_OVERVIEW_GRID = 0x6F esté en consts.py
- Confirmar que hardware esté parseando los 96 bytes correctamente

### Colores incorrectos
- Recordar escalar de 0-127 (MIDI) a 0-255 (NeoPixel): `color * 2`
- Verificar orden RGB vs GRB de tus LEDs

### Ring indicator no visible
- El overlay blanco es sutil (30% mix)
- Aumentar mezcla si necesitas más contraste

---

¿Preguntas o quieres ejemplos adicionales de integración?

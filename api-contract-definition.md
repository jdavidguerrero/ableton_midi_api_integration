# 📖 API Contract Definition: PushClone

Este documento es la guía de referencia completa para la comunicación entre el script `PushClone` de Ableton Live y el firmware del controlador de hardware (Teensy).

---

## Sección 1: Proceso de Conexión (Handshake)

Para que la comunicación se inicie correctamente, el script y el hardware deben realizar un "saludo" (handshake) de 3 pasos.

### Paso 1: Live Inicia el Contacto

Apenas cargas el script en Ableton, este enviará un mensaje para ver si hay un controlador compatible escuchando.

-   **Dirección**: `Live -> Hardware`
-   **Comando**: `CMD_HANDSHAKE (0x60)`
-   **Mensaje SysEx de Ejemplo**:
    ```
    F0 7F 00 7F 60 02 50 43 31 F7
    ```
-   **Desglose del Payload**:
    -   `[0x50, 0x43]`: Son los caracteres ASCII para "PC" (PushClone).

### Paso 2: El Hardware Responde

Tu firmware debe estar escuchando este mensaje. Al recibirlo, debe responder inmediatamente para confirmar que es un controlador compatible.

-   **Dirección**: `Hardware -> Live`
-   **Comando**: `CMD_HANDSHAKE (0x60)`
-   **Mensaje SysEx de Ejemplo que debe enviar tu Teensy**:
    ```
    F0 7F 00 7F 60 02 54 53 27 F7
    ```
-   **Desglose del Payload**:
    -   `[0x54, 0x53]`: Se sugiere usar los caracteres ASCII para "TS" (Teensy). El script de Live no valida este payload, pero es una buena práctica para la depuración.

### Paso 3: Live Confirma y Envía el Estado Completo

Al recibir la respuesta del hardware, el script de Live sabe que la conexión es exitosa.

1.  **Confirmación Final**: El script enviará una última confirmación.
    -   **Dirección**: `Live -> Hardware`
    -   **Comando**: `CMD_HANDSHAKE_REPLY (0x61)`
    -   **Mensaje SysEx de Ejemplo**:
        ```
        F0 7F 00 7F 61 02 4C 56 3F F7
        ```
    -   **Desglose del Payload**:
        -   `[0x4C, 0x56]`: Caracteres ASCII para "LV" (Live).

2.  **Volcado de Estado (State Dump)**: Inmediatamente después, el script comenzará a enviar una ráfaga de mensajes SysEx para sincronizar el estado de tu controlador con el estado actual de la sesión de Ableton. Este proceso se detalla en la siguiente sección.

---

## Sección 1.5: Formato general de los mensajes SysEx

Todos los mensajes PushClone usan la misma envoltura:

```
F0 7F 00 7F [CMD] [SEQ] [LEN_MSB] [LEN_LSB] [PAYLOAD …] [CHECKSUM] F7
```

| Campo | Bytes | Descripción |
| --- | --- | --- |
| `F0 7F 00 7F` | 4 | Encabezado Universal Non-Commercial (identifica al script). |
| `[CMD]` | 1 | Comando (7 bits). |
| `[SEQ]` | 1 | Número de secuencia (0‑127) para debug/orden. |
| `[LEN_MSB] [LEN_LSB]` | 2 | Longitud del payload en 14 bits (`(MSB<<7) | LSB`). Desde ahora es **obligatorio** para permitir mensajes de hasta 256 bytes. |
| `[PAYLOAD …]` | N | Datos del comando, todos en el rango 0‑127. |
| `[CHECKSUM]` | 1 | XOR de `CMD`, `SEQ` y todos los bytes del payload, enmascarado con `0x7F`. |
| `F7` | 1 | Fin del mensaje SysEx. |

> **Nota importante:** El firmware del Push clone debe leer SIEMPRE ambos bytes de longitud. Si solo se toma el primer byte (comportamiento de 7 bits), mensajes como `CMD_NEOTRELLIS_CLIP_GRID (192 bytes)` o `CMD_TRANSPORT_STATE` quedarán corruptos.

---

## Sección 2: Volcado de Estado Inicial (State Dump)

Después del handshake, tu controlador recibirá una serie de mensajes para ponerse al día. No es un solo mensaje, sino muchos. Tu firmware debe estar preparado para procesarlos. Los más importantes que recibirás al inicio son:

-   **Estado del Transporte**:
    -   `CMD_TRANSPORT_PLAY (0x40)`: `[is_playing]` (1 o 0).
    -   `CMD_TRANSPORT_LOOP (0x42)`: `[is_loop_on]` (1 o 0).
    -   `CMD_TRANSPORT_METRONOME (0x46)`: `[is_on]` (1 o 0).
    -   `CMD_TRANSPORT_TEMPO (0x43)`: `[tempo_int, tempo_frac]`.
    -   `CMD_TRANSPORT_SIGNATURE (0x44)`: `[numerador, denominador]`.

-   **Estado del Mezclador (por cada track visible)**:
    -   `CMD_TRACK_NAME (0x27)`: `[track_idx, len, ...name]`
    -   `CMD_TRACK_COLOR (0x28)`: `[track_idx, r, g, b]` (en 7-bit)
    -   `CMD_MIXER_VOLUME (0x21)`: `[track_idx, volume]` (0-127)
    -   `CMD_MIXER_PAN (0x22)`: `[track_idx, pan]` (0-127, 64 es centro)
    -   `CMD_MIXER_MUTE (0x23)`: `[track_idx, is_muted]`
    -   `CMD_MIXER_SOLO (0x24)`: `[track_idx, is_soloed]`
    -   `CMD_MIXER_ARM (0x25)`: `[track_idx, is_armed]`

-   **Estado del Grid (¡El más importante para ti!)**:
    -   `CMD_NEOTRELLIS_CLIP_GRID (0x02)`: Este es el mensaje grande de 192 bytes que contiene el estado de color de toda la matriz. Su estructura se detalla en la siguiente sección.

-   **Estado de la Navegación**:
    -   `CMD_RING_POSITION (0x6A)`: `[track_offset, scene_offset, width, height]`. Te dice en qué parte de la sesión está la "caja roja".
    -   `CMD_SELECTED_TRACK (0x64)`: `[track_idx]`.
    -   `CMD_SELECTED_SCENE (0x65)`: `[scene_idx]`.

Tu controlador debe procesar estos mensajes para configurar su estado inicial (colores de LEDs, posiciones de faders motorizados si los tuvieras, pantallas, etc.).

---

## Sección 3: Protocolo del Grid (Matriz 8x4)

Este documento define el "contrato" para la transmisión de datos de la matriz de clips (grid) desde el script de Ableton Live (`PushClone`) hacia el controlador de hardware (Teensy/NeoTrellis). El objetivo es enviar el estado completo de la matriz de 8x4 en un solo mensaje, para que el hardware solo se encargue de "pintar" los LEDs.

---

### 3.1. Resumen del Proceso

-   **Disparador**: El script de Live envía el estado completo del grid cuando ocurren cambios significativos (ej: cambio de `SessionRing`, clips que empiezan/paran de sonar, cambio de vista).
-   **Comando SysEx**: Se utiliza un único comando SysEx para toda la matriz: `CMD_NEOTRELLIS_CLIP_GRID (0x02)`.
-   **Formato de Color**: Cada pad se envía con su color en formato **RGB de 24-bit**, codificado para ser seguro para SysEx.
-   **Lógica del Hardware**: El controlador recibe este mensaje, decodifica los colores para los 32 pads, y actualiza todos los LEDs de una vez. No necesita lógica de estado, solo renderizar lo que recibe.

---

### 3.2. Estructura del Mensaje SysEx

El mensaje completo sigue el formato estándar del proyecto:

```
F0 7F 00 7F [CMD] [SEQ] [LEN_MSB] [LEN_LSB] [PAYLOAD] [CHECKSUM] F7
```

-   **`[CMD]`**: `0x02` (correspondiente a `CMD_NEOTRELLIS_CLIP_GRID`).
-   **`[SEQ]`**: Número de secuencia (0-127) para ordenamiento.
-   **`[LEN_MSB] [LEN_LSB]`**: Longitud del payload. Como el payload es de 192 bytes, se usan 2 bytes para la longitud (codificación de 14-bit).
    -   `LEN_MSB = (192 >> 7) & 0x7F`  -> `1`
    -   `LEN_LSB = 192 & 0x7F` -> `64`
-   **`[PAYLOAD]`**: Los datos de color de los 32 pads (192 bytes en total).
-   **`[CHECKSUM]`**: Suma XOR de `CMD`, `SEQ` y todos los bytes del `PAYLOAD`.

---

### 3.3. Estructura del Payload (El Contrato)

Esta es la parte más importante. El payload contiene los datos de color para los 32 pads de la matriz de 8x4.

-   **Tamaño Total del Payload**: **192 bytes**.
-   **Datos por Pad**: Cada pad se representa con **6 bytes**.
-   **Codificación de Color**: Se usa una codificación de 14-bit para cada canal de color (R, G, B) para poder enviar valores de 0-255 a través de MIDI SysEx (que solo permite bytes de 7-bit).
    -   `R (0-255)` se convierte en `[R_msb, R_lsb]`
    -   `G (0-255)` se convierte en `[G_msb, G_lsb]`
    -   `B (0-255)` se convierte en `[B_msb, B_lsb]`

#### Orden de los Datos en el Payload

El payload es una secuencia lineal de los datos de los 32 pads. El orden de los pads es de **izquierda a derecha, y de arriba hacia abajo**.

```
Pad 0, Pad 1, Pad 2, ..., Pad 7   (Fila 0)
Pad 8, Pad 9, ..., Pad 15         (Fila 1)
...
Pad 24, Pad 25, ..., Pad 31       (Fila 3)
```

#### Formato de Datos para un Solo Pad (6 bytes)

```
[ R_msb, R_lsb, G_msb, G_lsb, B_msb, B_lsb ]
```

-   `R_msb = (valor_R >> 7) & 0x7F;`
-   `R_lsb = valor_R & 0x7F;`
-   ... y así sucesivamente para G y B.

#### Estructura Completa del Payload (192 bytes)

```
[Pad 0: 6 bytes], [Pad 1: 6 bytes], ..., [Pad 31: 6 bytes]
```

---

### 3.4. Ejemplo de Implementación en C++ (Teensy / Arduino)

Este código de ejemplo muestra cómo el firmware del controlador debería parsear el mensaje SysEx y actualizar una matriz de NeoPixels.

```cpp
#include <Adafruit_NeoPixel.h>

// Asume que tienes una matriz de 8x4 NeoTrellis o similar
#define NUM_PIXELS 32
Adafruit_NeoPixel grid = Adafruit_NeoPixel(NUM_PIXELS, PIN, NEO_GRB + NEO_KHZ800);

// Función que se llama cuando se recibe el SysEx CMD_NEOTRELLIS_CLIP_GRID (0x02)
void handleGridUpdate(const uint8_t* payload, unsigned int length) {
    // 1. Verificar la longitud del payload. Debería ser 192 bytes.
    if (length != 192) {
        Serial.println("Error: Payload del grid con longitud incorrecta.");
        return;
    }

    // 2. Iterar a través de los 32 pads
    for (int i = 0; i < NUM_PIXELS; i++) {
        // Calcular el índice de inicio para los datos de este pad
        int offset = i * 6;

        // 3. Decodificar el color de 24-bit desde los 6 bytes de 14-bit
        uint8_t r_msb = payload[offset + 0];
        uint8_t r_lsb = payload[offset + 1];
        uint8_t g_msb = payload[offset + 2];
        uint8_t g_lsb = payload[offset + 3];
        uint8_t b_msb = payload[offset + 4];
        uint8_t b_lsb = payload[offset + 5];

        // Reconstruir los valores de 8-bit (0-255)
        uint8_t red   = (r_msb << 7) | r_lsb;
        uint8_t green = (g_msb << 7) | g_lsb;
        uint8_t blue  = (b_msb << 7) | b_lsb;

        // 4. Asignar el color al LED correspondiente
        // El orden de los pads en el payload coincide con el índice del LED (0-31)
        grid.setPixelColor(i, grid.Color(red, green, blue));
    }

    // 5. Actualizar toda la matriz de LEDs de una vez
    grid.show();
}

// En tu parser principal de SysEx:
void onSysExMessage(const uint8_t* data, unsigned int length) {
    // ... validación de header y checksum ...
    
    uint8_t command = data[4];
    const uint8_t* payload = &data[7]; // O donde empiece tu payload
    unsigned int payload_len = ...; // Extraer longitud

    if (command == 0x02) { // CMD_NEOTRELLIS_CLIP_GRID
        handleGridUpdate(payload, payload_len);
    }
    // ... otros comandos ...
}
```

---

## Sección 4: Referencia completa del API Contract

Las siguientes tablas cubren **todos los comandos declarados en `consts.py`**. “Dirección” indica el flujo recomendado (`Live → HW`, `HW → Live` o `Bidireccional`). El tamaño del payload se expresa en bytes de 7 bits antes de la codificación SysEx.

### 4.1 Vista/Miscelánea (0x01‑0x05)

| Comando | Hex | Dirección | Payload | Descripción |
| --- | --- | --- | --- | --- |
| `CMD_SWITCH_VIEW` | `0x01` | HW → Live | `[view_id]` (1) | Solicita cambiar entre vistas (`0=clip`, `1=mixer`, `2=device`, `3=note`). |
| `CMD_NEOTRELLIS_CLIP_GRID` | `0x02` | Live → HW | `192` | Frame completo del grid 8×4 (32 pads × 6 bytes RGB). |
| `CMD_TRANSPORT_QUANTIZE` | `0x03` | Bidireccional | `[quant]` (1) | Define/lee cuantización de grabación MIDI. |
| `CMD_DRUM_RACK_STATE` | `0x04` | Live → HW | Variable | Estado extendido de Drum Rack: `[track, device, pad_states…]`. |
| `CMD_NEOTRELLIS_GRID` | `0x05` | Live → HW | Variable (≤192) | Actualización parcial del grid NeoTrellis. |

### 4.2 Clips y Escenas (0x10‑0x1F)

| Comando | Hex | Dir | Payload | Descripción |
| --- | --- | --- | --- | --- |
| `CMD_CLIP_STATE` | `0x10` | Live → HW | `[track, scene, state, Rmsb, Rlsb, Gmsb, Glsb, Bmsb, Blsb]` | Estado + color completo por clip. |
| `CMD_CLIP_TRIGGER` | `0x11` | HW → Live | `[track, scene]` | Lanza clip. |
| `CMD_SCENE_FIRE` | `0x12` | HW → Live | `[scene]` | Dispara escena. |
| `CMD_CLIP_STOP` | `0x13` | HW → Live | `[track, scene]` | Detiene clip. |
| `CMD_CLIP_NAME` | `0x14` | Live → HW | `[track, scene, len, texto…]` | Nombre UTF‑8. |
| `CMD_CLIP_LOOP` | `0x15` | Live → HW | `[track, scene, flag]` |
| `CMD_CLIP_MUTED` | `0x16` | Live → HW | `[track, scene, flag]` |
| `CMD_CLIP_WARP` | `0x17` | Live → HW | `[track, scene, flag]` |
| `CMD_CLIP_START` | `0x18` | Live → HW | `[track, scene, start_hi, start_lo]` |
| `CMD_CLIP_END` | `0x19` | Live → HW | `[track, scene, end_hi, end_lo]` |
| `CMD_SCENE_STATE` | `0x1A` | Live → HW | `[scene, flags…]` | Incluye disparo y armado. |
| `CMD_SCENE_NAME` | `0x1B` | Live → HW | `[scene, len, texto…]` |
| `CMD_SCENE_COLOR` | `0x1C` | Live → HW | `[scene, r, g, b]` (compacto) |
| `CMD_SCENE_IS_TRIGGERED` | `0x1D` | Live → HW | `[scene, flag]` |
| `CMD_MIDI_CLIP_QUANTIZE` | `0x1E` | HW → Live | `[track, scene, quant]` |
| `CMD_QUANTIZE_CLIP` | `0x1F` | HW → Live | `[optional_quant]` |

### 4.3 Mixer/Tracks (0x20‑0x2F)

| Comando | Hex | Dir | Payload (resumen) |
| --- | --- | --- | --- |
| `CMD_MIXER_STATE (0x20)` | Live → HW | Snapshot completo: `[track, volume, pan, mute, solo, arm, sends…]`. |
| `CMD_MIXER_VOLUME (0x21)` | Bidireccional | `[track, value]` |
| `CMD_MIXER_PAN (0x22)` | Bidireccional | `[track, value]` |
| `CMD_MIXER_MUTE (0x23)` | Bidireccional | `[track, flag]` |
| `CMD_MIXER_SOLO (0x24)` | Bidireccional | `[track, flag]` |
| `CMD_MIXER_ARM (0x25)` | Bidireccional | `[track, flag]` |
| `CMD_MIXER_SEND (0x26)` | Bidireccional | `[track, send_idx, value]` |
| `CMD_TRACK_NAME (0x27)` | Live → HW | `[track, len, texto…]` |
| `CMD_TRACK_COLOR (0x28)` | Live → HW | `[track, r, g, b]` |
| `CMD_TRACK_PLAYING_SLOT (0x29)` | Live → HW | `[track, slot_idx]` |
| `CMD_TRACK_FIRED_SLOT (0x2A)` | Live → HW | `[track, slot_idx]` |
| `CMD_TRACK_FOLD_STATE (0x2B)` | Live → HW | `[track, flag]` |
| `CMD_GROOVE_AMOUNT (0x2C)` | Bidireccional | `[track, value]` |
| `CMD_GROOVE_TEMPLATE (0x2D)` | Bidireccional | `[track, template_id]` |
| `CMD_GROOVE_POOL (0x2E)` | Live → HW | `[count, template_ids…]` |
| `CMD_TRACK_CROSSFADE (0x2F)` | Bidireccional | `[track, assign (0=A,1=Off,2=B)]` |

### 4.4 Devices y Racks (0x30‑0x3F)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_DEVICE_LIST` | `0x30` | Live → HW | `[track, device_count, ids…]` |
| `CMD_DEVICE_SELECT` | `0x31` | HW → Live | `[track, device_idx]` |
| `CMD_DEVICE_PARAMS` | `0x32` | Live → HW | `[track, device, param_count, values…]` |
| `CMD_PARAM_CHANGE` | `0x33` | Bidireccional | `[track, device, param, value]` |
| `CMD_PARAM_VALUE` | `0x34` | Live → HW | `[track, device, param, value, len, label…]` |
| `CMD_DEVICE_ENABLE` | `0x35` | Bidireccional | `[track, device, flag]` |
| `CMD_DEVICE_PREV_NEXT` | `0x36` | HW → Live | `[direction]` |
| `CMD_PARAM_PAGE` | `0x37` | HW → Live | `[page_idx]` |
| `CMD_CHAIN_SELECT` | `0x38` | HW → Live | `[track, device, chain_idx]` |
| `CMD_CHAIN_MUTE` | `0x39` | Bidireccional | `[track, device, chain, flag]` |
| `CMD_CHAIN_SOLO` | `0x3A` | Bidireccional | `[track, device, chain, flag]` |
| `CMD_CHAIN_VOLUME` | `0x3B` | Bidireccional | `[track, device, chain, value]` |
| `CMD_CHAIN_PAN` | `0x3C` | Bidireccional | `[track, device, chain, value]` |
| `CMD_CHAIN_SEND` | `0x3D` | Bidireccional | `[track, device, chain, send_idx, value]` |
| `CMD_CHAIN_CROSSFADE` | `0x3E` | Bidireccional | `[track, device, chain, assign]` |
| `CMD_RACK_MACRO` | `0x3F` | Bidireccional | `[track, device, macro_idx, value]` |

### 4.5 Transporte/Automatización (0x40‑0x4F)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_TRANSPORT_PLAY` | `0x40` | HW → Live | `[flag]` |
| `CMD_TRANSPORT_RECORD` | `0x41` | Bidireccional | `[flag]` |
| `CMD_TRANSPORT_LOOP` | `0x42` | Bidireccional | `[flag]` |
| `CMD_TRANSPORT_TEMPO` | `0x43` | Live → HW | `[tempo_int, tempo_frac]` |
| `CMD_TRANSPORT_SIGNATURE` | `0x44` | Live → HW | `[numerador, denominador]` |
| `CMD_TRANSPORT_POSITION` | `0x45` | Live → HW | `[bar, beat, sixteenth]` |
| `CMD_TRANSPORT_METRONOME` | `0x46` | Bidireccional | `[flag]` |
| `CMD_TRANSPORT_OVERDUB` | `0x47` | Bidireccional | `[flag]` |
| `CMD_TRANSPORT_PUNCH` | `0x48` | Bidireccional | `[tipo (1=in/2=out), flag]` |
| `CMD_RECORD_QUANTIZATION` | `0x49` | Bidireccional | `[quant]` |
| `CMD_SESSION_RECORD` | `0x4A` | Bidireccional | `[flag]` |
| `CMD_AUTOMATION_RECORD / CMD_ARRANGEMENT_RECORD` | `0x4B` | Bidireccional | `[flag]` |
| `CMD_RE_ENABLE_AUTOMATION` | `0x4C` | HW → Live | Sin payload |
| `CMD_BACK_TO_ARRANGER` | `0x4D` | HW → Live | Sin payload |
| `CMD_UNDO / CMD_REDO` | `0x4E / 0x4F` | HW → Live | Sin payload |

### 4.6 Notas, Escalas y Secuenciador (0x50‑0x5F)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_NOTE_ON / OFF` | `0x50 / 0x51` | HW → Live | `[note, velocity]` |
| `CMD_SCALE_CHANGE` | `0x52` | HW → Live | `[scale_id, root]` |
| `CMD_SCALE_INFO` | `0x53` | Live → HW | `[scale_id, notes…]` |
| `CMD_OCTAVE_CHANGE / INFO` | `0x54 / 0x55` | Bidireccional | `[offset]` |
| `CMD_STEP_SEQUENCER_STATE` | `0x56` | Live → HW | `[page, len, steps…]` |
| `CMD_STEP_SEQUENCER_NOTE` | `0x57` | HW → Live | `[page, step, pitch, velocity]` |
| `CMD_STEP_SEQUENCER_RESOLUTION` | `0x58` | HW → Live | `[resolution]` |
| `CMD_STEP_SEQUENCER_PAGE` | `0x59` | HW → Live | `[page_idx]` |
| `CMD_STEP_SEQUENCER_HOLD` | `0x5A` | Bidireccional | `[step, flag]` |
| `CMD_STEP_EDIT_PARAMS` | `0x5B` | Bidireccional | `[step, param_id, value]` |
| `CMD_STEP_SEQUENCER_INFO` | `0x5C` | Live → HW | `[pages, steps_por_page, scale_id…]` |
| `CMD_STEP_CLEAR_ALL` | `0x5D` | HW → Live | Sin payload |
| `CMD_STEP_COPY_PAGE` | `0x5E` | HW → Live | `[src_page, dst_page]` |
| `CMD_LOOP_MARKERS` | `0x5F` | Bidireccional | `[start_bar, start_beat, end_bar, end_beat]` |

### 4.7 Sistema/Navegación (0x60‑0x6F)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_HANDSHAKE` | `0x60` | Bidireccional | `[2 bytes ID]` |
| `CMD_HANDSHAKE_REPLY` | `0x61` | Live → HW | `[0x4C, 0x56]` |
| `CMD_VIEW_STATE` | `0x62` | Live → HW | Snapshot de vista principal. |
| `CMD_PING_TEST` | `0x63` | Bidireccional | `[“PING”]` |
| `CMD_SELECTED_TRACK` | `0x64` | Live → HW | `[track_idx]` |
| `CMD_SELECTED_SCENE` | `0x65` | Live → HW | `[scene_idx]` |
| `CMD_DETAIL_CLIP` | `0x66` | Live → HW | `[track, scene]` |
| `CMD_BROWSER_MODE` | `0x67` | Live → HW | `[mode_id]` |
| `CMD_RING_NAVIGATE / SELECT / POSITION` | `0x68‑0x6A` | Bidireccional | `[track_offset, scene_offset, width, height]` (POSITION). |
| `CMD_TRACK_SELECT / SCENE_SELECT` | `0x6B / 0x6C` | Bidireccional | `[index]` |
| `CMD_SESSION_MODE` | `0x6D` | Live → HW | `[mode]` |
| `CMD_SESSION_OVERVIEW` | `0x6E` | Bidireccional | `[flag]` |
| `CMD_SESSION_OVERVIEW_GRID` | `0x6F` | Live → HW | Grid resumido para overview. |

### 4.8 Acciones de Canción y Clip (0x70‑0x7F)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_CREATE_AUDIO_TRACK` | `0x70` | HW → Live | Sin payload |
| `CMD_CREATE_MIDI_TRACK` | `0x71` | HW → Live | Sin payload |
| `CMD_CREATE_RETURN_TRACK` | `0x72` | HW → Live | Sin payload |
| `CMD_CREATE_SCENE` | `0x73` | HW → Live | Sin payload |
| `CMD_DUPLICATE_TRACK` | `0x74` | HW → Live | `[track_idx]` opcional |
| `CMD_DUPLICATE_CLIP` | `0x75` | HW → Live | `[track, scene]` |
| `CMD_CLIP_DUPLICATE/DELETE/COPY/PASTE` | `0x76‑0x79` | HW → Live | `[track, scene]` |
| `CMD_CLIP_*_RESULT` | `0x7A‑0x7D` | Live → HW | `[status_code]` |
| `CMD_CAPTURE_MIDI` | `0x7E` | HW → Live | Sin payload |
| `CMD_QUANTIZE_NOTES` | `0x7F` | HW → Live | `[strength]` opcional |

### 4.9 Grid/LED extendido (0x80‑0x83)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_GRID_UPDATE` | `0x80` | Live → HW | `[32 pads × 3 bytes compact RGB]` |
| `CMD_GRID_SINGLE_PAD` | `0x81` | Live → HW | `[pad_idx, r, g, b]` |
| `CMD_GRID_PAD_PRESS` | `0x82` | HW → Live | `[pad_idx, state]` |
| `CMD_DEVICE_CHAIN` | `0x83` | Live → HW | `[track, device, chain_info…]` |

### 4.10 Streaming/Tempo/Notas (0x90‑0x9C)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_TRACK_METER` | `0x90` | Live → HW | `[track, level]` (20 Hz) |
| `CMD_TRACK_CUE_VOLUME` | `0x91` | Bidireccional | `[value]` |
| `CMD_CLIP_PLAYING_POSITION` | `0x92` | Live → HW | `[track, scene, pos_hi, pos_lo]` |
| `CMD_CLIP_LOOP_START / END` | `0x93 / 0x94` | Bidireccional | `[track, scene, value_hi, value_lo]` |
| `CMD_CLIP_LENGTH` | `0x95` | Live → HW | `[track, scene, len_hi, len_lo]` |
| `CMD_CLIP_IS_RECORDING` | `0x96` | Live → HW | `[track, scene, flag]` |
| `CMD_DRUM_PAD_STATE` | `0x97` | Live → HW | `[track, device, pad_idx, state, r, g, b]` |
| `CMD_NUDGE` | `0x98` | HW → Live | `[direction] (1=up,0=down)` |
| `CMD_TRANSPORT_STATE` | `0x99` | Live → HW | `[is_playing, beat, bar]` |
| `CMD_MIDI_NOTES` | `0x9A` | Live → HW | `[track, scene, count, (pitch,start_hi,start_lo,dur_hi,dur_lo,vel)…]` |
| `CMD_MIDI_NOTE_ADD` | `0x9B` | HW → Live | `[track, scene, pitch, vel, start_hi, start_lo, dur_hi, dur_lo]` |
| `CMD_MIDI_NOTE_REMOVE` | `0x9C` | HW → Live | `[track, scene, start_hi, start_lo, end_hi, end_lo, (pitch_lo, pitch_hi opcional)]` |

### 4.11 Plugins/Sistema (0xA0‑0xA5)

| Comando | Hex | Dir | Payload |
| --- | --- | --- | --- |
| `CMD_PLUGIN_PRESET` | `0xA0` | Live → HW | `[track, device, program, len, nombre…]` |
| `CMD_PLUGIN_PROGRAM` | `0xA1` | Bidireccional | `[track, device, program]` |
| `CMD_PLUGIN_UI` | `0xA2` | Bidireccional | `[track, device, flag]` |
| `CMD_PLUGIN_LATENCY` | `0xA3` | Live → HW | `[track, device, latency_hi, latency_lo]` |
| `CMD_CPU_USAGE` | `0xA4` | Live → HW | `[avg_pct, peak_pct]` |
| `CMD_CUE_POINT` | `0xA5` | Live → HW | `[cue_idx, time_hi, time_lo, len, nombre…]` |

---

## Sección 5: Recordatorio del layout 8×4 y alineación con el firmware

- `consts.py` fija `GRID_WIDTH = 8`, `GRID_HEIGHT = 4` y `TOTAL_PADS = 32`; `PushClone` establece `ring_width = 4` y `ring_height = 8`, mientras que `ClipManager` limita listeners y actualizaciones al mismo rango.  
- El firmware debe mapear exactamente **4 filas físicas (tracks)** por **8 columnas (escenas)** cuando procese `CMD_NEOTRELLIS_CLIP_GRID`, `CMD_GRID_UPDATE`, `CMD_GRID_SINGLE_PAD` y cualquier comando que hable del Session Ring.  
- Todos los mensajes usan longitud de payload en 14 bits: actualiza la Teensy/NeoTrellis para leer `[LEN_MSB, LEN_LSB]` y reconstruir `payload_len = (MSB << 7) | LSB` antes de consumir el contenido.  
- Si envías comandos al script (p.ej. `CMD_CLIP_TRIGGER`, `CMD_NUDGE`, `CMD_MIDI_NOTE_ADD`), respeta los tamaños de payload indicados en las tablas anteriores; Live validará cada byte y descartará mensajes que no coincidan con el contrato.

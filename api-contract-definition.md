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

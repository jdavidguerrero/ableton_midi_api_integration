# 🎹 Ableton Push Clone - MIDI Protocol Reference

**Version:** 2.0 (Updated November 2024)
**Hardware:** Teensy 4.1 + Adafruit NeoTrellis M4 (8×4 Grid)
**Communication:** USB MIDI (bidirectional)

---

## 📡 SysEx Message Format

All custom commands use MIDI System Exclusive messages with the following structure:

```
[F0] [7F] [00] [7F] [CMD] [SEQ] [LEN] [PAYLOAD...] [CHECKSUM] [F7]
│    │    │    │    │     │     │     │             │          │
│    │    │    │    │     │     │     │             │          └─ End SysEx
│    │    │    │    │     │     │     │             └─ XOR checksum
│    │    │    │    │     │     │     └─ Data bytes (variable length)
│    │    │    │    │     │     └─ Payload length
│    │    │    │    │     └─ Sequence number (0-127)
│    │    │    │    └─ Command byte (see tables below)
│    │    │    └─ Device ID (0x7F = all devices)
│    │    └─ Sub-ID #1 (0x00 = non-commercial)
│    └─ Manufacturer ID (0x7F = development/educational)
└─ System Exclusive start
```

### Message Components

| Field | Size | Range | Description |
|-------|------|-------|-------------|
| **Header** | 4 bytes | `F0 7F 00 7F` | Fixed SysEx header |
| **CMD** | 1 byte | `0x00-0xFF` | Command identifier |
| **SEQ** | 1 byte | `0x00-0x7F` | Sequence number (7-bit) |
| **LEN** | 1 byte | `0x00-0x7F` | Payload length (7-bit, max 127 bytes) |
| **PAYLOAD** | 0-127 bytes | `0x00-0x7F` each | Command-specific data (all 7-bit) |
| **CHECKSUM** | 1 byte | `0x00-0x7F` | XOR of all payload bytes |
| **Footer** | 1 byte | `0xF7` | End of SysEx |

### Checksum Calculation

```cpp
uint8_t calculate_checksum(uint8_t* payload, uint8_t length) {
    uint8_t checksum = 0;
    for (int i = 0; i < length; i++) {
        checksum ^= payload[i];
    }
    return checksum & 0x7F;
}
```

---

## 🎨 14-bit Encoding (MSB/LSB)

For values >127, we use 14-bit encoding with two 7-bit bytes:

```
Value Range: 0 - 16,383 (2^14)
MSB (Most Significant Byte): bits 13-7
LSB (Least Significant Byte): bits 6-0
```

### Encoding (Python/Live)
```python
msb = (value >> 7) & 0x7F  # Upper 7 bits
lsb = value & 0x7F          # Lower 7 bits
```

### Decoding (C++/Teensy)
```cpp
uint16_t value = (msb << 7) | lsb;
```

### Examples
```
Value 0:     MSB=0x00, LSB=0x00
Value 127:   MSB=0x00, LSB=0x7F
Value 128:   MSB=0x01, LSB=0x00
Value 255:   MSB=0x01, LSB=0x7F
Value 1000:  MSB=0x07, LSB=0x68  (1000 = 7×128 + 104)
Value 16383: MSB=0x7F, LSB=0x7F
```

---

## 📋 Command Categories

| Range | Category | Description |
|-------|----------|-------------|
| `0x00-0x0F` | System | Handshake, ping, view state |
| `0x10-0x1F` | Clip/Scene | Clip launch, scene launch, clip properties |
| `0x20-0x2F` | Track/Mixer | Track properties, mixer controls |
| `0x30-0x3F` | Device/Plugin | Device selection, parameters, racks |
| `0x40-0x4F` | Transport/Automation | Play, record, loop, tempo, automation |
| `0x50-0x5F` | Note/Scale/Sequencer | MIDI notes, scales, step sequencer |
| `0x60-0x6F` | System/Navigation | Selected track/scene, ring navigation |
| `0x70-0x7F` | Song/Clip Actions | Create, delete, duplicate operations |
| `0x80-0x8F` | Grid Commands | Full grid updates, pad colors |
| `0x90-0x9F` | Streaming Data | High-frequency data (metering, position) |
| `0xA0-0xAF` | Plugin-Specific | VST/AU preset, program, UI |

---

## 🔧 Command Reference

### System Commands (0x00-0x0F)

#### 0x00 - CMD_HANDSHAKE
**Direction:** Hardware → Live
**Purpose:** Initial connection handshake
**Payload:** `[hardware_version_major, hardware_version_minor, grid_width, grid_height]`
```
Example: [0x01, 0x00, 0x08, 0x04]  // v1.0, 8×4 grid
```

#### 0x01 - CMD_HANDSHAKE_REPLY
**Direction:** Live → Hardware
**Purpose:** Handshake acknowledgment
**Payload:** `[status, firmware_version_major, firmware_version_minor]`
```
Status codes:
  0x00 = Connection failed
  0x01 = Connection successful
  0x02 = Version mismatch warning
```

#### 0x02 - CMD_VIEW_STATE
**Direction:** Live → Hardware
**Purpose:** Complete view state dump (on connection)
**Payload:** `[view_mode, track_count, scene_count, tempo_msb, tempo_lsb, ...]`

#### 0x03 - CMD_PING_TEST
**Direction:** Bidirectional
**Purpose:** Connection test / keep-alive
**Payload:** `[timestamp_msb, timestamp_lsb]` (optional)

#### 0x04 - CMD_DRUM_RACK_STATE
**Direction:** Live → Hardware
**Purpose:** Drum rack full state
**Payload:** `[track_idx, device_idx, pad_count, pad_states...]`

#### 0x05 - CMD_NEOTRELLIS_GRID
**Direction:** Live → Hardware
**Purpose:** Complete 8×4 RGB grid update
**Payload:** `[R0, G0, B0, R1, G1, B1, ..., R31, G31, B31]` (96 bytes)
```
32 pads × 3 bytes (RGB) = 96 bytes total
Pad order: row-major (left-to-right, top-to-bottom)
```

---

### Clip/Scene Commands (0x10-0x1F)

#### 0x10 - CMD_CLIP_LAUNCH
**Direction:** Hardware → Live
**Purpose:** Launch clip in session
**Payload:** `[track_idx, scene_idx]`

#### 0x11 - CMD_CLIP_STOP
**Direction:** Hardware → Live
**Purpose:** Stop clip/track
**Payload:** `[track_idx]`

#### 0x12 - CMD_CLIP_STATE
**Direction:** Live → Hardware
**Purpose:** Clip state update
**Payload:** `[track_idx, scene_idx, state, color_r, color_g, color_b]`
```
State codes:
  0x00 = Empty
  0x01 = Playing
  0x02 = Queued
  0x03 = Recording
```

#### 0x13 - CMD_CLIP_COLOR
**Direction:** Bidirectional
**Purpose:** Clip color (14-bit RGB encoding)
**Payload:** `[track_idx, scene_idx, r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]`

#### 0x14 - CMD_CLIP_NAME
**Direction:** Live → Hardware
**Purpose:** Clip name (ASCII encoded)
**Payload:** `[track_idx, scene_idx, char0, char1, ..., charN]` (max 20 chars)

#### 0x1A - CMD_SCENE_LAUNCH
**Direction:** Hardware → Live
**Purpose:** Launch scene
**Payload:** `[scene_idx]`

#### 0x1B - CMD_SCENE_STATE
**Direction:** Live → Hardware
**Purpose:** Scene state
**Payload:** `[scene_idx, clip_count, color_r, color_g, color_b]`

#### 0x1C - CMD_SCENE_COLOR
**Direction:** Bidirectional
**Purpose:** Scene color (14-bit RGB)
**Payload:** `[scene_idx, r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]`

#### 0x1D - CMD_SCENE_NAME
**Direction:** Live → Hardware
**Purpose:** Scene name
**Payload:** `[scene_idx, char0, char1, ..., charN]`

#### 0x1F - CMD_QUANTIZE_CLIP
**Direction:** Hardware → Live
**Purpose:** Quantize clip notes
**Payload:** `[quantization_value]` (0=None, 4=1/4, 6=1/8, 8=1/16)

---

### Track/Mixer Commands (0x20-0x2F)

#### 0x20 - CMD_TRACK_VOLUME
**Direction:** Bidirectional
**Purpose:** Track volume (0.0 - 1.0 normalized)
**Payload:** `[track_idx, volume_7bit]` (0-127 = 0.0-1.0)

#### 0x21 - CMD_TRACK_PAN
**Direction:** Bidirectional
**Purpose:** Track pan (-1.0 to +1.0)
**Payload:** `[track_idx, pan_7bit]` (0=hard left, 64=center, 127=hard right)

#### 0x22 - CMD_TRACK_SEND
**Direction:** Bidirectional
**Purpose:** Track send level
**Payload:** `[track_idx, send_idx, level_7bit]`

#### 0x23 - CMD_TRACK_ARM
**Direction:** Bidirectional
**Purpose:** Track arm for recording
**Payload:** `[track_idx, armed]` (0=disarmed, 1=armed)

#### 0x24 - CMD_TRACK_MUTE
**Direction:** Bidirectional
**Purpose:** Track mute
**Payload:** `[track_idx, muted]` (0=unmuted, 1=muted)

#### 0x25 - CMD_TRACK_SOLO
**Direction:** Bidirectional
**Purpose:** Track solo
**Payload:** `[track_idx, soloed]` (0=unsoloed, 1=soloed)

#### 0x26 - CMD_TRACK_NAME
**Direction:** Live → Hardware
**Purpose:** Track name
**Payload:** `[track_idx, char0, char1, ..., charN]`

#### 0x27 - CMD_TRACK_COLOR
**Direction:** Live → Hardware
**Purpose:** Track color (14-bit RGB)
**Payload:** `[track_idx, r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]`

#### 0x2F - CMD_TRACK_CROSSFADE
**Direction:** Bidirectional
**Purpose:** Track crossfade assignment
**Payload:** `[track_idx, assign]` (0=A, 1=None, 2=B)

---

### Streaming Data Commands (0x90-0x9F)

#### 0x90 - CMD_TRACK_METER
**Direction:** Live → Hardware (throttled 20Hz)
**Purpose:** Track output meter level
**Payload:** `[track_idx, level_7bit]` (0-127 = 0.0-1.0)

#### 0x92 - CMD_CLIP_PLAYING_POSITION
**Direction:** Live → Hardware (throttled 20Hz)
**Purpose:** Clip playback position
**Payload:** `[track_idx, scene_idx, beats_7bit, fraction_7bit]`

#### 0x93 - CMD_CLIP_LOOP_START
**Direction:** Bidirectional
**Purpose:** Clip loop start position
**Payload:** `[track_idx, scene_idx, beats_7bit, fraction_7bit]`

#### 0x94 - CMD_CLIP_LOOP_END
**Direction:** Bidirectional
**Purpose:** Clip loop end position
**Payload:** `[track_idx, scene_idx, beats_7bit, fraction_7bit]`

#### 0x95 - CMD_CLIP_LENGTH
**Direction:** Live → Hardware
**Purpose:** Clip length in beats
**Payload:** `[track_idx, scene_idx, length_beats, length_fraction]`

#### 0x96 - CMD_CLIP_IS_RECORDING
**Direction:** Live → Hardware
**Purpose:** ClipSlot recording state
**Payload:** `[track_idx, scene_idx, is_recording]`

#### 0x97 - CMD_DRUM_PAD_STATE
**Direction:** Live → Hardware
**Purpose:** Individual drum pad state
**Payload:** `[track_idx, device_idx, pad_idx, mute, solo, has_chain]`

#### 0x98 - CMD_NUDGE
**Direction:** Hardware → Live
**Purpose:** Tempo nudge up/down
**Payload:** `[direction]` (0=down, 1=up)

---

### Transport/Automation Commands (0x40-0x4F)

#### 0x40 - CMD_TRANSPORT_PLAY
**Direction:** Bidirectional
**Purpose:** Play/stop toggle
**Payload:** `[is_playing]` (0=stopped, 1=playing)

#### 0x41 - CMD_TRANSPORT_RECORD
**Direction:** Bidirectional
**Purpose:** Record mode toggle
**Payload:** `[is_recording]`

#### 0x42 - CMD_TRANSPORT_LOOP
**Direction:** Bidirectional
**Purpose:** Loop mode toggle
**Payload:** `[loop_enabled]`

#### 0x43 - CMD_TRANSPORT_TEMPO
**Direction:** Live → Hardware
**Purpose:** Song tempo
**Payload:** `[tempo_msb, tempo_lsb]` (BPM × 10, e.g., 1200 = 120.0 BPM)

#### 0x44 - CMD_TRANSPORT_SIGNATURE
**Direction:** Live → Hardware
**Purpose:** Time signature
**Payload:** `[numerator, denominator]` (e.g., [4, 4] = 4/4 time)

#### 0x45 - CMD_TRANSPORT_POSITION
**Direction:** Live → Hardware
**Purpose:** Song position
**Payload:** `[bar, beat, sixteenth]`

#### 0x46 - CMD_TRANSPORT_METRONOME (alias: CMD_METRONOME)
**Direction:** Bidirectional
**Purpose:** Metronome on/off
**Payload:** `[enabled]`

#### 0x49 - CMD_RECORD_QUANTIZATION
**Direction:** Bidirectional
**Purpose:** Record quantization setting
**Payload:** `[quantization_value]` (0-10, see quantization table)

#### 0x4B - CMD_ARRANGEMENT_RECORD (alias: CMD_AUTOMATION_RECORD)
**Direction:** Bidirectional
**Purpose:** Arrangement overdub
**Payload:** `[is_recording]`

#### 0x4D - CMD_BACK_TO_ARRANGER
**Direction:** Hardware → Live
**Purpose:** Return to arrangement view
**Payload:** (empty)

#### 0x5F - CMD_LOOP_MARKERS
**Direction:** Live → Hardware
**Purpose:** Loop start/end markers
**Payload:** `[start_bar, start_beat, end_bar, end_beat]`

---

### Device/Plugin Commands (0x30-0x3F)

#### 0x30 - CMD_DEVICE_LIST
**Direction:** Live → Hardware
**Purpose:** List of devices in track
**Payload:** `[track_idx, device_count, device0_type, device1_type, ...]`

#### 0x31 - CMD_DEVICE_SELECT
**Direction:** Hardware → Live
**Purpose:** Select device
**Payload:** `[track_idx, device_idx]`

#### 0x34 - CMD_PARAM_VALUE
**Direction:** Live → Hardware
**Purpose:** Device parameter value
**Payload:** `[track_idx, device_idx, param_idx, value_7bit, name_len, name...]`

#### 0x35 - CMD_DEVICE_ENABLE
**Direction:** Bidirectional
**Purpose:** Device on/off
**Payload:** `[track_idx, device_idx, is_enabled]`

#### 0x38 - CMD_CHAIN_SELECT
**Direction:** Hardware → Live
**Purpose:** Select chain in rack
**Payload:** `[track_idx, device_idx, chain_idx]`

#### 0x3F - CMD_RACK_MACRO
**Direction:** Bidirectional
**Purpose:** Rack macro parameter
**Payload:** `[track_idx, device_idx, macro_idx, value_7bit]`

#### 0x83 - CMD_DEVICE_CHAIN
**Direction:** Live → Hardware
**Purpose:** Chain information
**Payload:** `[track_idx, device_idx, chain_idx, data...]`

---

### Session Ring/Navigation Commands (0x60-0x6F)

#### 0x68 - CMD_RING_NAVIGATE
**Direction:** Hardware → Live
**Purpose:** Navigate session ring
**Payload:** `[direction]` (0=left, 1=right, 2=up, 3=down)

#### 0x69 - CMD_RING_SELECT
**Direction:** Hardware → Live
**Purpose:** Select position in ring
**Payload:** `[ring_track, ring_scene]`

#### 0x6A - CMD_RING_POSITION
**Direction:** Live → Hardware (14-bit encoding)
**Purpose:** Ring offset position
**Payload:** `[track_msb, track_lsb, scene_msb, scene_lsb, width, height, overview_mode]`
```
Example: Offset track=150, scene=200, width=4, height=8, normal mode
  track_msb = 150 >> 7 = 1
  track_lsb = 150 & 0x7F = 22
  scene_msb = 200 >> 7 = 1
  scene_lsb = 200 & 0x7F = 72
  Payload: [0x01, 0x16, 0x01, 0x48, 0x04, 0x08, 0x00]
```

#### 0x6B - CMD_TRACK_SELECT
**Direction:** Live → Hardware (14-bit encoding)
**Purpose:** Track selection update
**Payload:** `[track_msb, track_lsb, is_in_ring]`

#### 0x6C - CMD_SCENE_SELECT
**Direction:** Live → Hardware (14-bit encoding)
**Purpose:** Scene selection update
**Payload:** `[scene_msb, scene_lsb, is_in_ring]`

#### 0x6E - CMD_SESSION_OVERVIEW
**Direction:** Hardware → Live
**Purpose:** Toggle session overview mode
**Payload:** (empty)

#### 0x6F - CMD_SESSION_OVERVIEW_GRID
**Direction:** Live → Hardware
**Purpose:** Overview mode grid (density map)
**Payload:** `[R0, G0, B0, ..., R31, G31, B31]` (96 bytes)
```
Color coding:
  (20, 20, 20)    = No clips (dark gray)
  (60, 60, 60)    = Few clips (medium gray)
  (100, 100, 100) = Many clips (light gray)
  (127, 127, 127) = Full region (white)
  (50, 100, 255)  = Selected region (blue)
```

---

## 📊 Data Tables

### Quantization Values
```
Value | Name    | Description
------|---------|-------------
0     | None    | No quantization
1     | 1 Bar   | One bar
2     | 1/2     | Half note
3     | 1/2T    | Half note triplet
4     | 1/4     | Quarter note
5     | 1/4T    | Quarter note triplet
6     | 1/8     | Eighth note
7     | 1/8T    | Eighth note triplet
8     | 1/16    | Sixteenth note
9     | 1/16T   | Sixteenth note triplet
10    | 1/32    | Thirty-second note
```

### Clip States
```
Value | State      | LED Color
------|------------|------------
0x00  | Empty      | Off (0,0,0)
0x01  | Playing    | Green (76,255,76)
0x02  | Queued     | Yellow (255,255,76)
0x03  | Recording  | Red (255,76,76)
```

### Crossfade Assignments
```
Value | Assignment
------|------------
0     | A (left)
1     | None (center)
2     | B (right)
```

---

## 🔄 Typical Message Flows

### Hardware Boot Sequence
```
1. Hardware → Live:  CMD_HANDSHAKE [0x01, 0x00, 0x08, 0x04]
2. Live → Hardware:  CMD_HANDSHAKE_REPLY [0x01, 0x02, 0x00]
3. Live → Hardware:  CMD_RING_POSITION [...]
4. Live → Hardware:  CMD_NEOTRELLIS_GRID [96 bytes RGB data]
5. Live → Hardware:  CMD_TRANSPORT_PLAY [is_playing]
6. Live → Hardware:  CMD_TRANSPORT_TEMPO [tempo_msb, tempo_lsb]
... (complete state dump)
```

### Clip Launch
```
1. Hardware → Live:  CMD_CLIP_LAUNCH [track_idx, scene_idx]
2. Live → Hardware:  CMD_CLIP_STATE [track_idx, scene_idx, 0x02, ...] (queued)
3. Live → Hardware:  CMD_CLIP_STATE [track_idx, scene_idx, 0x01, ...] (playing)
4. Live → Hardware:  CMD_NEOTRELLIS_GRID [updated grid colors]
```

### Ring Navigation
```
1. Hardware → Live:  CMD_RING_NAVIGATE [0x01] (right)
2. Live → Hardware:  CMD_RING_POSITION [new offset with 14-bit encoding]
3. Live → Hardware:  CMD_NEOTRELLIS_GRID [new clips in view]
```

### Session Overview Toggle
```
1. Hardware → Live:  CMD_SESSION_OVERVIEW
2. Live → Hardware:  CMD_RING_POSITION [..., 0x01] (overview_mode=1)
3. Live → Hardware:  CMD_SESSION_OVERVIEW_GRID [density map 96 bytes]

--- User presses pad in overview ---

4. Hardware → Live:  CMD_RING_SELECT [ring_track, ring_scene]
5. Live → Hardware:  CMD_RING_POSITION [..., 0x00] (overview_mode=0, new offset)
6. Live → Hardware:  CMD_NEOTRELLIS_GRID [normal view]
```

---

## 🚨 Error Handling

### Invalid Command
When receiving an unknown command, respond with:
```
CMD_PING_TEST [0x00, 0x00]  // Acknowledge but signal error
```

### Checksum Mismatch
Discard message and do NOT respond. Live will retry if needed.

### Overflow Protection
All payload bytes MUST be 7-bit (0x00-0x7F). If a byte > 0x7F is received, mask it:
```cpp
payload_byte &= 0x7F;
```

---

## 💾 Teensy Implementation Example

```cpp
// Decode 14-bit value
uint16_t decode_14bit(uint8_t msb, uint8_t lsb) {
    return ((uint16_t)msb << 7) | (uint16_t)lsb;
}

// Handle CMD_RING_POSITION
void handle_ring_position(uint8_t* payload, uint8_t length) {
    if (length < 7) return;  // Invalid payload

    uint16_t track_offset = decode_14bit(payload[0], payload[1]);
    uint16_t scene_offset = decode_14bit(payload[2], payload[3]);
    uint8_t width = payload[4];
    uint8_t height = payload[5];
    bool overview_mode = payload[6] > 0;

    // Update internal state
    session_ring.track_offset = track_offset;
    session_ring.scene_offset = scene_offset;
    session_ring.overview_mode = overview_mode;
}

// Handle CMD_NEOTRELLIS_GRID
void handle_grid_update(uint8_t* payload, uint8_t length) {
    if (length != 96) return;  // Must be exactly 32 pads × 3 RGB

    for (int pad = 0; pad < 32; pad++) {
        uint8_t r = payload[pad * 3];
        uint8_t g = payload[pad * 3 + 1];
        uint8_t b = payload[pad * 3 + 2];

        neotrellis.setPixelColor(pad, r, g, b);
    }
    neotrellis.show();
}
```

---

## 📈 Performance Considerations

### Throttling
High-frequency commands are throttled to prevent MIDI bandwidth saturation:

| Command | Max Rate | Notes |
|---------|----------|-------|
| CMD_TRACK_METER | 20 Hz | Peak-hold strategy |
| CMD_CLIP_PLAYING_POSITION | 20 Hz | Latest value |
| CMD_TRANSPORT_POSITION | ~1 Hz | Only on beat change |

### Grid Updates
- **Full grid:** Max 60 Hz (96 bytes + overhead ≈ 100 bytes @ 31,250 bps MIDI = ~3ms)
- **Single pad:** Can be sent individually for efficiency (use CMD_GRID_SINGLE_PAD if needed)

### Sequence Numbers
Use SEQ field to detect dropped/out-of-order messages. Increment on each send:
```cpp
static uint8_t seq_num = 0;
payload[0] = seq_num++;
seq_num &= 0x7F;  // Wrap at 127
```

---

## 🔗 See Also

- [Live Object Model Documentation](https://docs.cycling74.com/max8/vignettes/live_object_model)
- [Push 3 Manual](https://www.ableton.com/en/manual/push-3/)
- [MIDI 1.0 Specification](https://www.midi.org/specifications)

---

**Last Updated:** November 8, 2024
**Maintained by:** Ableton Push Clone Project

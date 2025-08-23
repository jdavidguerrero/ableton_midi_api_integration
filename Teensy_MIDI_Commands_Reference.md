# 🎛️ **Ableton Push Clone - Comando MIDI Reference para Teensy**

## 📡 **SysEx Protocol**
- **Header**: `F0 7F 00 7F`
- **Format**: `F0 7F 00 7F [CMD] [LEN] [PAYLOAD...] [CHECKSUM] F7`
- **Checksum**: XOR de todos los bytes desde CMD hasta el final del payload

---

## 🎵 **TRANSPORT COMMANDS (0x50-0x5F)**

### `0x50` - Transport State
```cpp
// [is_playing, is_recording, is_overdubbing, tempo_bpm, time_sig_num, time_sig_den]
// Ejemplo: F0 7F 00 7F 50 06 01 00 00 78 04 04 F7 (playing, 120 BPM, 4/4)
void handleTransportState(uint8_t playing, uint8_t recording, uint8_t overdub, 
                         uint8_t tempo, uint8_t sig_num, uint8_t sig_den);
```

### `0x51` - Loop State  
```cpp
// [is_loop_enabled]
void handleLoopState(uint8_t enabled);
```

### `0x52` - Record State
```cpp
// [is_recording]  
void handleRecordState(uint8_t recording);
```

### `0x53` - Metronome State
```cpp
// [is_enabled]
void handleMetronomeState(uint8_t enabled);
```

### `0x54` - Punch In/Out State
```cpp
// [punch_in_enabled, punch_out_enabled]
void handlePunchState(uint8_t punch_in, uint8_t punch_out);
```

### `0x55` - Quantization Setting
```cpp
// [quantization_index] (0=None, 1=1/4, 2=1/8, 3=1/16, etc.)
void handleQuantizationState(uint8_t quant_index);
```

### `0x56` - Session Record State
```cpp
// [is_session_recording]
void handleSessionRecordState(uint8_t recording);
```

---

## 🎚️ **TRACK COMMANDS (0x20-0x2F)**

### `0x20` - Track State
```cpp
// [track_idx, volume, pan, is_muted, is_soloed, is_armed, has_audio_in, has_audio_out]
void handleTrackState(uint8_t track, uint8_t volume, uint8_t pan, 
                      uint8_t muted, uint8_t soloed, uint8_t armed,
                      uint8_t has_in, uint8_t has_out);
```

### `0x21` - Track Name
```cpp
// [track_idx, name_length, ...name_bytes]
void handleTrackName(uint8_t track, const char* name);
```

### `0x22` - Track Color
```cpp
// [track_idx, r, g, b]
void handleTrackColor(uint8_t track, uint8_t r, uint8_t g, uint8_t b);
```

### `0x23` - Track Volume
```cpp
// [track_idx, volume_0_127]
void handleTrackVolume(uint8_t track, uint8_t volume);
```

### `0x24` - Track Pan
```cpp
// [track_idx, pan_0_127] (64 = center)
void handleTrackPan(uint8_t track, uint8_t pan);
```

### `0x25` - Track Send
```cpp
// [track_idx, send_idx, send_value_0_127]
void handleTrackSend(uint8_t track, uint8_t send, uint8_t value);
```

### `0x26` - Track Crossfader
```cpp
// [track_idx, crossfader_assign] (0=none, 1=A, 2=B)
void handleTrackCrossfader(uint8_t track, uint8_t assign);
```

### `0x27` - Track Playing Slot
```cpp
// [track_idx, slot_idx_or_127_if_none]
void handleTrackPlayingSlot(uint8_t track, uint8_t slot);
```

### `0x28` - Track Fired Slot  
```cpp
// [track_idx, slot_idx_or_127_if_none]
void handleTrackFiredSlot(uint8_t track, uint8_t slot);
```

### `0x29` - Track Fold State
```cpp
// [track_idx, is_folded]
void handleTrackFoldState(uint8_t track, uint8_t folded);
```

---

## 🎬 **CLIP COMMANDS (0x30-0x3F)**

### `0x30` - Clip State
```cpp
// [track_idx, scene_idx, has_clip, is_playing, is_triggered, is_recording, length_bars]
void handleClipState(uint8_t track, uint8_t scene, uint8_t has_clip,
                     uint8_t playing, uint8_t triggered, uint8_t recording, uint8_t length);
```

### `0x31` - Clip Name
```cpp
// [track_idx, scene_idx, name_length, ...name_bytes]
void handleClipName(uint8_t track, uint8_t scene, const char* name);
```

### `0x32` - Clip Color
```cpp
// [track_idx, scene_idx, r, g, b]
void handleClipColor(uint8_t track, uint8_t scene, uint8_t r, uint8_t g, uint8_t b);
```

### `0x33` - Scene State
```cpp
// [scene_idx, is_triggered]
void handleSceneState(uint8_t scene, uint8_t triggered);
```

### `0x34` - Scene Name
```cpp
// [scene_idx, name_length, ...name_bytes]
void handleSceneName(uint8_t scene, const char* name);
```

### `0x35` - Scene Color
```cpp
// [scene_idx, r, g, b]
void handleSceneColor(uint8_t scene, uint8_t r, uint8_t g, uint8_t b);
```

---

## 🎛️ **DEVICE COMMANDS (0x40-0x4F)**

### `0x40` - Device State
```cpp
// [track_idx, device_idx, is_enabled, device_type, num_parameters]
void handleDeviceState(uint8_t track, uint8_t device, uint8_t enabled, 
                       uint8_t type, uint8_t num_params);
```

### `0x41` - Device Name
```cpp
// [track_idx, device_idx, name_length, ...name_bytes]
void handleDeviceName(uint8_t track, uint8_t device, const char* name);
```

### `0x42` - Device Parameter
```cpp
// [track_idx, device_idx, param_idx, value_0_127, param_name_length, ...param_name]
void handleDeviceParameter(uint8_t track, uint8_t device, uint8_t param, 
                          uint8_t value, const char* param_name);
```

### `0x48` - Drum Rack State
```cpp
// [track_idx, device_idx, selected_pad_idx_or_127]
void handleDrumRackState(uint8_t track, uint8_t device, uint8_t selected_pad);
```

### `0x49` - Drum Pad State
```cpp
// [track_idx, device_idx, pad_idx, has_sample]
void handleDrumPadState(uint8_t track, uint8_t device, uint8_t pad, uint8_t has_sample);
```

### `0x4B` - **🎯 NeoTrellis Grid** (¡NUEVO!)
```cpp
// [track_idx, device_idx, pad0_state, pad1_state, ..., pad31_state]
// Estados: 0=empty, 1=loaded, 2=active, 3=selected
void handleNeoTrellisGrid(uint8_t track, uint8_t device, uint8_t grid_data[32]) {
    for (int i = 0; i < 32; i++) {
        int row = i / 8;
        int col = i % 8;
        uint8_t color = grid_data[i];
        
        // Mapear a colores NeoTrellis
        switch(color) {
            case 0: setPixel(row, col, 0x100010); break;   // Dim purple (empty)
            case 1: setPixel(row, col, 0x404010); break;   // Dim yellow (loaded)  
            case 2: setPixel(row, col, 0x808020); break;   // Bright yellow (active)
            case 3: setPixel(row, col, 0x801080); break;   // Bright magenta (selected)
        }
    }
    neotrellis.show();
}
```

---

## 🧭 **NAVIGATION COMMANDS (0xB0-0xBF)**

### `0xB0` - Selected Track
```cpp
// [track_idx]
void handleSelectedTrack(uint8_t track);
```

### `0xB1` - Selected Scene  
```cpp
// [scene_idx]
void handleSelectedScene(uint8_t scene);
```

### `0xB2` - Detail Clip
```cpp
// [track_idx, scene_idx] 
void handleDetailClip(uint8_t track, uint8_t scene);
```

### `0xB3` - Highlighted Clip Slot
```cpp
// [track_idx, scene_idx]
void handleHighlightedClipSlot(uint8_t track, uint8_t scene);
```

---

## 🎨 **VIEW COMMANDS (0x70-0x7F)**

### `0x70` - View Switch
```cpp
// [view_id] (0=Session, 1=Arrangement, 2=Detail_Clip, 3=Detail_Device)
void handleViewSwitch(uint8_t view_id);
```

---

## 🔄 **AUTOMATION COMMANDS (0xC0-0xCF)**

### `0xC0` - Automation Record
```cpp
// [is_enabled]
void handleAutomationRecord(uint8_t enabled);
```

### `0xC1` - Re-enable Automation
```cpp
// [can_re_enable]
void handleReEnableAutomation(uint8_t can_enable);
```

### `0xC2` - Back to Arrangement
```cpp
// [back_to_arrangement_state]
void handleBackToArrangement(uint8_t state);
```

---

## 💡 **Teensy Implementation Tips**

### 1. **SysEx Parser Principal**
```cpp
void handleSysEx(uint8_t* data, uint8_t length) {
    if (length < 7) return; // Mínimo: F0 7F 00 7F CMD LEN F7
    
    if (data[0] == 0xF0 && data[1] == 0x7F && data[2] == 0x00 && data[3] == 0x7F) {
        uint8_t command = data[4];
        uint8_t payload_len = data[5];
        uint8_t* payload = &data[6];
        
        // Verificar checksum
        uint8_t checksum = 0;
        for (int i = 4; i < 6 + payload_len; i++) {
            checksum ^= data[i];
        }
        if (checksum != data[6 + payload_len]) return; // Bad checksum
        
        // Procesar comando
        switch(command) {
            case 0x4B: handleNeoTrellisGrid(payload[0], payload[1], &payload[2]); break;
            case 0x50: handleTransportState(payload); break;
            case 0x20: handleTrackState(payload); break;
            // ... más comandos
        }
    }
}
```

### 2. **NeoTrellis Color Mapping**
```cpp
const uint32_t DRUM_COLORS[] = {
    0x100010,  // 0: Empty (very dim purple)
    0x404010,  // 1: Loaded (dim yellow) 
    0x808020,  // 2: Active (bright yellow)
    0x801080   // 3: Selected (bright magenta)
};

void updateDrumPad(int pad_idx, uint8_t state) {
    int row = pad_idx / 8;
    int col = pad_idx % 8;
    neotrellis.setPixelColor(row * 8 + col, DRUM_COLORS[state & 0x03]);
}
```

¡Ahora tienes **todos los comandos disponibles** para implementar un controlador completo! 🎛️✨

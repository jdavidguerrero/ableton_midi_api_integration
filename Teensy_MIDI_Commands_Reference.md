# 🎛️ **Ableton Push Clone - Comando MIDI Reference para Teensy**

## 📡 **SysEx Protocol**
- **Header**: `F0 7F 00 7F`
- **Format**: `F0 7F 00 7F [CMD] [SEQ] [LEN] [PAYLOAD...] [CHECKSUM] F7`
- **Checksum**: XOR de todos los bytes desde CMD hasta el final del payload

---

## 🎵 **VIEW SWITCHING COMMANDS (0x01)**

### `0x01` - Switch View
```cpp
// [view_id]
void handleViewSwitch(uint8_t view_id);
```

---

## 🎵 **MISC COMMANDS (0x02-0x05)**

### `0x02` - NeoTrellis Clip Grid
```cpp
// [r1, g1, b1, r2, g2, b2, ...]
void handleNeoTrellisClipGrid(uint8_t* grid_data);
```

### `0x03` - Transport Quantize
```cpp
// [quantization_index]
void handleTransportQuantize(uint8_t quant_index);
```

### `0x04` - Drum Rack State
```cpp
// [track_idx, device_idx, selected_pad_idx_or_127]
void handleDrumRackState(uint8_t track, uint8_t device, uint8_t selected_pad);
```

### `0x05` - NeoTrellis Grid
```cpp
// [track_idx, device_idx, pad0_state, pad1_state, ..., pad31_state]
void handleNeoTrellisGrid(uint8_t track, uint8_t device, uint8_t grid_data[32]);
```

---

## 🎬 **CLIP/SCENE COMMANDS (0x10-0x1F)**

### `0x10` - Clip State
```cpp
// [track_idx, scene_idx, has_clip, is_playing, is_triggered, is_recording, length_bars]
void handleClipState(uint8_t track, uint8_t scene, uint8_t has_clip,
                     uint8_t playing, uint8_t triggered, uint8_t recording, uint8_t length);
```

### `0x11` - Clip Trigger
```cpp
// [track_idx, scene_idx]
void sendClipTrigger(uint8_t track, uint8_t scene);
```

### `0x12` - Scene Fire
```cpp
// [scene_idx]
void sendSceneFire(uint8_t scene);
```

### `0x13` - Clip Stop
```cpp
// [track_idx, scene_idx]
void sendClipStop(uint8_t track, uint8_t scene);
```

### `0x14` - Clip Name
```cpp
// [track_idx, scene_idx, name_length, ...name_bytes]
void handleClipName(uint8_t track, uint8_t scene, const char* name);
```

### `0x15` - Clip Loop
```cpp
// [track_idx, scene_idx, is_looping]
void handleClipLoop(uint8_t track, uint8_t scene, uint8_t is_looping);
```

### `0x16` - Clip Muted
```cpp
// [track_idx, scene_idx, is_muted]
void handleClipMuted(uint8_t track, uint8_t scene, uint8_t is_muted);
```

### `0x17` - Clip Warp
```cpp
// [track_idx, scene_idx, is_warping]
void handleClipWarp(uint8_t track, uint8_t scene, uint8_t is_warping);
```

### `0x18` - Clip Start
```cpp
// [track_idx, scene_idx, start_marker_beats, start_marker_fraction]
void handleClipStart(uint8_t track, uint8_t scene, uint8_t start_beats, uint8_t start_fraction);
```

### `0x19` - Clip End
```cpp
// [track_idx, scene_idx, end_marker_beats, end_marker_fraction]
void handleClipEnd(uint8_t track, uint8_t scene, uint8_t end_beats, uint8_t end_fraction);
```

### `0x1A` - Scene State
```cpp
// [scene_idx, is_triggered]
void handleSceneState(uint8_t scene, uint8_t triggered);
```

### `0x1B` - Scene Name
```cpp
// [scene_idx, name_length, ...name_bytes]
void handleSceneName(uint8_t scene, const char* name);
```

### `0x1C` - Scene Color
```cpp
// [scene_idx, r, g, b]
void handleSceneColor(uint8_t scene, uint8_t r, uint8_t g, uint8_t b);
```

### `0x1D` - Scene Is Triggered
```cpp
// [scene_idx, is_triggered]
void handleSceneIsTriggered(uint8_t scene, uint8_t is_triggered);
```

### `0x1E` - MIDI Clip Quantize
```cpp
// [track_idx, scene_idx, quantization_index]
void sendMidiClipQuantize(uint8_t track, uint8_t scene, uint8_t quant_index);
```

### `0x1F` - Quantize Clip
```cpp
// [track_idx, scene_idx, quantization_index]
void sendQuantizeClip(uint8_t track, uint8_t scene, uint8_t quant_index);
```

---

## 🎚️ **MIXER/TRACK COMMANDS (0x20-0x2F)**

### `0x20` - Mixer State
```cpp
// [track_idx, volume, pan, is_muted, is_soloed, is_armed, has_audio_in, has_audio_out]
void handleMixerState(uint8_t track, uint8_t volume, uint8_t pan, 
                      uint8_t muted, uint8_t soloed, uint8_t armed,
                      uint8_t has_in, uint8_t has_out);
```

### `0x21` - Mixer Volume
```cpp
// [track_idx, volume_0_127]
void handleMixerVolume(uint8_t track, uint8_t volume);
```

### `0x22` - Mixer Pan
```cpp
// [track_idx, pan_0_127] (64 = center)
void handleMixerPan(uint8_t track, uint8_t pan);
```

### `0x23` - Mixer Mute
```cpp
// [track_idx, is_muted]
void handleMixerMute(uint8_t track, uint8_t is_muted);
```

### `0x24` - Mixer Solo
```cpp
// [track_idx, is_soloed]
void handleMixerSolo(uint8_t track, uint8_t is_soloed);
```

### `0x25` - Mixer Arm
```cpp
// [track_idx, is_armed]
void handleMixerArm(uint8_t track, uint8_t is_armed);
```

### `0x26` - Mixer Send
```cpp
// [track_idx, send_idx, send_value_0_127]
void handleMixerSend(uint8_t track, uint8_t send, uint8_t value);
```

### `0x27` - Track Name
```cpp
// [track_idx, name_length, ...name_bytes]
void handleTrackName(uint8_t track, const char* name);
```

### `0x28` - Track Color
```cpp
// [track_idx, r, g, b]
void handleTrackColor(uint8_t track, uint8_t r, uint8_t g, uint8_t b);
```

### `0x29` - Track Playing Slot
```cpp
// [track_idx, slot_idx_or_127_if_none]
void handleTrackPlayingSlot(uint8_t track, uint8_t slot);
```

### `0x2A` - Track Fired Slot
```cpp
// [track_idx, slot_idx_or_127_if_none]
void handleTrackFiredSlot(uint8_t track, uint8_t slot);
```

### `0x2B` - Track Fold State
```cpp
// [track_idx, is_folded]
void handleTrackFoldState(uint8_t track, uint8_t folded);
```

### `0x2C` - Groove Amount
```cpp
// [track_idx, groove_amount_0_127]
void handleGrooveAmount(uint8_t track, uint8_t amount);
```

### `0x2D` - Groove Template
```cpp
// [track_idx, template_idx_or_127_if_none]
void handleGrooveTemplate(uint8_t track, uint8_t template_idx);
```

### `0x2E` - Groove Pool
```cpp
// [num_templates, template_0_idx, template_0_name_len, ...name, ...]
void handleGroovePool(uint8_t num_templates, uint8_t* data);
```

---

## 🎛️ **DEVICE/PLUGIN COMMANDS (0x30-0x3F)**

### `0x30` - Device List
```cpp
// [track_idx, num_devices, dev_0_idx, dev_0_name_len, ...name, ...]
void handleDeviceList(uint8_t track, uint8_t num_devices, uint8_t* data);
```

### `0x31` - Device Select
```cpp
// [track_idx, device_idx]
void sendDeviceSelect(uint8_t track, uint8_t device);
```

### `0x32` - Device Params
```cpp
// [track_idx, device_idx, page, total_pages, param_0_idx, param_0_val, ...]
void handleDeviceParams(uint8_t track, uint8_t device, uint8_t page, uint8_t total_pages, uint8_t* data);
```

### `0x33` - Param Change
```cpp
// [track_idx, device_idx, param_idx, value_0_127]
void sendParamChange(uint8_t track, uint8_t device, uint8_t param, uint8_t value);
```

### `0x34` - Param Value
```cpp
// [track_idx, device_idx, param_idx, value_0_127, name_len, ...name]
void handleParamValue(uint8_t track, uint8_t device, uint8_t param, uint8_t value, const char* name);
```

### `0x35` - Device Enable
```cpp
// [track_idx, device_idx, is_enabled]
void sendDeviceEnable(uint8_t track, uint8_t device, uint8_t is_enabled);
```

### `0x36` - Device Prev/Next
```cpp
// [direction] (0=prev, 1=next)
void sendDevicePrevNext(uint8_t direction);
```

### `0x37` - Param Page
```cpp
// [direction] (0=prev, 1=next)
void sendParamPage(uint8_t direction);
```

### `0x38` - Chain Select
```cpp
// [track_idx, device_idx, chain_idx]
void sendChainSelect(uint8_t track, uint8_t device, uint8_t chain);
```

### `0x39` - Chain Mute
```cpp
// [track_idx, device_idx, chain_idx, is_muted]
void sendChainMute(uint8_t track, uint8_t device, uint8_t chain, uint8_t is_muted);
```

### `0x3A` - Chain Solo
```cpp
// [track_idx, device_idx, chain_idx, is_soloed]
void sendChainSolo(uint8_t track, uint8_t device, uint8_t chain, uint8_t is_soloed);
```

### `0x3B` - Chain Volume
```cpp
// [track_idx, device_idx, chain_idx, volume_0_127]
void sendChainVolume(uint8_t track, uint8_t device, uint8_t chain, uint8_t volume);
```

### `0x3C` - Chain Pan
```cpp
// [track_idx, device_idx, chain_idx, pan_0_127]
void sendChainPan(uint8_t track, uint8_t device, uint8_t chain, uint8_t pan);
```

### `0x3D` - Chain Send
```cpp
// [track_idx, device_idx, chain_idx, send_idx, value_0_127]
void sendChainSend(uint8_t track, uint8_t device, uint8_t chain, uint8_t send, uint8_t value);
```

### `0x3E` - Chain Crossfade
```cpp
// [track_idx, device_idx, chain_idx, assign]
void sendChainCrossfade(uint8_t track, uint8_t device, uint8_t chain, uint8_t assign);
```

### `0x3F` - Rack Macro
```cpp
// [track_idx, device_idx, macro_idx, value_0_127]
void sendRackMacro(uint8_t track, uint8_t device, uint8_t macro, uint8_t value);
```

---

##  TRANSPORT/AUTOMATION COMMANDS (0x40-0x4F)

### `0x40` - Transport Play
```cpp
// [is_playing]
void handleTransportPlay(uint8_t is_playing);
```

### `0x41` - Transport Record
```cpp
// [is_recording]
void handleTransportRecord(uint8_t is_recording);
```

### `0x42` - Transport Loop
```cpp
// [is_loop_enabled]
void handleTransportLoop(uint8_t is_loop_enabled);
```

### `0x43` - Transport Tempo
```cpp
// [tempo_int, tempo_fraction]
void handleTransportTempo(uint8_t tempo_int, uint8_t tempo_fraction);
```

### `0x44` - Transport Signature
```cpp
// [numerator, denominator]
void handleTransportSignature(uint8_t numerator, uint8_t denominator);
```

### `0x45` - Transport Position
```cpp
// [bar, beat, sixteenth]
void handleTransportPosition(uint8_t bar, uint8_t beat, uint8_t sixteenth);
```

### `0x46` - Transport Metronome
```cpp
// [is_enabled]
void handleTransportMetronome(uint8_t is_enabled);
```

### `0x47` - Transport Overdub
```cpp
// [is_overdub_enabled]
void handleTransportOverdub(uint8_t is_overdub_enabled);
```

### `0x48` - Transport Punch
```cpp
// [punch_type, is_enabled]
void handleTransportPunch(uint8_t punch_type, uint8_t is_enabled);
```

### `0x49` - Record Quantization
```cpp
// [quantization_index]
void handleRecordQuantization(uint8_t quant_index);
```

### `0x4A` - Session Record
```cpp
// [is_session_recording]
void handleSessionRecord(uint8_t is_session_recording);
```

### `0x4B` - Automation Record
```cpp
// [is_automation_recording]
void handleAutomationRecord(uint8_t is_automation_recording);
```

### `0x4C` - Re-enable Automation
```cpp
// [can_re_enable]
void handleReEnableAutomation(uint8_t can_re_enable);
```

### `0x4D` - Back to Arranger
```cpp
// [is_back_to_arranger]
void handleBackToArranger(uint8_t is_back_to_arranger);
```

### `0x4E` - Undo
```cpp
void sendUndo();
```

### `0x4F` - Redo
```cpp
void sendRedo();
```

---

## 🎹 **NOTE/SCALE/SEQUENCER COMMANDS (0x50-0x5F)**

### `0x50` - Note On
```cpp
// [note, velocity]
void sendNoteOn(uint8_t note, uint8_t velocity);
```

### `0x51` - Note Off
```cpp
// [note]
void sendNoteOff(uint8_t note);
```

### `0x52` - Scale Change
```cpp
// [root_note, scale_id]
void sendScaleChange(uint8_t root_note, uint8_t scale_id);
```

### `0x53` - Scale Info
```cpp
// [root_note, scale_id]
void handleScaleInfo(uint8_t root_note, uint8_t scale_id);
```

### `0x54` - Octave Change
```cpp
// [octave]
void sendOctaveChange(uint8_t octave);
```

### `0x55` - Octave Info
```cpp
// [octave]
void handleOctaveInfo(uint8_t octave);
```

### `0x56` - Step Sequencer State
```cpp
// [step_0_state, step_1_state, ..., step_31_state]
void handleStepSequencerState(uint8_t grid_data[32]);
```

### `0x57` - Step Sequencer Note
```cpp
// [track_idx, note, velocity]
void sendStepSequencerNote(uint8_t track, uint8_t note, uint8_t velocity);
```

### `0x58` - Step Sequencer Resolution
```cpp
// [resolution_index]
void sendStepSequencerResolution(uint8_t resolution);
```

### `0x59` - Step Sequencer Page
```cpp
// [page_index]
void sendStepSequencerPage(uint8_t page);
```

### `0x5A` - Step Sequencer Hold
```cpp
// [step_index]
void sendStepSequencerHold(uint8_t step_index);
```

### `0x5B` - Step Edit Params
```cpp
// [velocity, length, microtiming]
void sendStepEditParams(uint8_t velocity, uint8_t length, uint8_t microtiming);
```

### `0x5C` - Step Sequencer Info
```cpp
// [page, resolution, total_steps]
void handleStepSequencerInfo(uint8_t page, uint8_t resolution, uint8_t total_steps);
```

### `0x5D` - Step Clear All
```cpp
void sendStepClearAll();
```

### `0x5E` - Step Copy Page
```cpp
void sendStepCopyPage();
```

---

## 🧭 **SYSTEM/NAVIGATION COMMANDS (0x60-0x6F)**

### `0x60` - Handshake
```cpp
void sendHandshake();
```

### `0x61` - Handshake Reply
```cpp
void handleHandshakeReply();
```

### `0x62` - View State
```cpp
// [view_id]
void handleViewState(uint8_t view_id);
```

### `0x63` - Ping Test
```cpp
void sendPingTest();
```

### `0x64` - Selected Track
```cpp
// [track_idx]
void handleSelectedTrack(uint8_t track);
```

### `0x65` - Selected Scene
```cpp
// [scene_idx]
void handleSelectedScene(uint8_t scene);
```

### `0x66` - Detail Clip
```cpp
// [track_idx, scene_idx]
void handleDetailClip(uint8_t track, uint8_t scene);
```

### `0x67` - Browser Mode
```cpp
// [is_browse_mode]
void handleBrowserMode(uint8_t is_browse_mode);
```

### `0x68` - Ring Navigate
```cpp
// [direction]
void sendRingNavigate(uint8_t direction);
```

### `0x69` - Ring Select
```cpp
// [ring_track, ring_scene]
void sendRingSelect(uint8_t track, uint8_t scene);
```

### `0x6A` - Ring Position
```cpp
// [track_offset, scene_offset, ring_width, ring_height]
void handleRingPosition(uint8_t track_offset, uint8_t scene_offset, uint8_t width, uint8_t height);
```

### `0x6B` - Track Select
```cpp
// [track_idx, is_selected]
void handleTrackSelect(uint8_t track, uint8_t is_selected);
```

### `0x6C` - Scene Select
```cpp
// [scene_idx, is_selected]
void handleSceneSelect(uint8_t scene, uint8_t is_selected);
```

### `0x6D` - Session Mode
```cpp
// [mode_id]
void handleSessionMode(uint8_t mode_id);
```

### `0x6E` - Session Overview
```cpp
// [is_overview_mode]
void handleSessionOverview(uint8_t is_overview_mode);
```

### `0x6F` - Session Overview Grid
```cpp
// [grid_data...]
void handleSessionOverviewGrid(uint8_t* grid_data);
```

---

## 💡 **SONG/CLIP ACTIONS (0x70-0x7F)**

### `0x70` - Create Audio Track
```cpp
void sendCreateAudioTrack();
```

### `0x71` - Create MIDI Track
```cpp
void sendCreateMidiTrack();
```

### `0x72` - Create Return Track
```cpp
void sendCreateReturnTrack();
```

### `0x73` - Create Scene
```cpp
void sendCreateScene();
```

### `0x74` - Duplicate Track
```cpp
// [track_idx]
void sendDuplicateTrack(uint8_t track_idx);
```

### `0x75` - Duplicate Clip
```cpp
// [src_track, src_scene, dst_track, dst_scene]
void sendDuplicateClip(uint8_t src_track, uint8_t src_scene, uint8_t dst_track, uint8_t dst_scene);
```

### `0x76` - Clip Duplicate
```cpp
// [src_track, src_scene, dst_track, dst_scene]
void sendClipDuplicate(uint8_t src_track, uint8_t src_scene, uint8_t dst_track, uint8_t dst_scene);
```

### `0x77` - Clip Delete
```cpp
// [track_idx, scene_idx]
void sendClipDelete(uint8_t track_idx, uint8_t scene_idx);
```

### `0x78` - Clip Copy
```cpp
// [track_idx, scene_idx]
void sendClipCopy(uint8_t track_idx, uint8_t scene_idx);
```

### `0x79` - Clip Paste
```cpp
// [track_idx, scene_idx]
void sendClipPaste(uint8_t track_idx, uint8_t scene_idx);
```

### `0x7A` - Clip Duplicate Result
```cpp
// [success]
void handleClipDuplicateResult(uint8_t success);
```

### `0x7B` - Clip Delete Result
```cpp
// [success]
void handleClipDeleteResult(uint8_t success);
```

### `0x7C` - Clip Copy Result
```cpp
// [success]
void handleClipCopyResult(uint8_t success);
```

### `0x7D` - Clip Paste Result
```cpp
// [success]
void handleClipPasteResult(uint8_t success);
```

### `0x7E` - Capture MIDI
```cpp
void sendCaptureMidi();
```

### `0x7F` - Quantize Notes
```cpp
// [track_idx, scene_idx, quantization_index]
void sendQuantizeNotes(uint8_t track_idx, uint8_t scene_idx, uint8_t quant_idx);
```

---

## 💡 **Teensy Implementation Tips**

### 1. **SysEx Parser Principal**
```cpp
void handleSysEx(uint8_t* data, uint8_t length) {
    if (length < 9) return; // Mínimo: F0 7F 00 7F CMD SEQ LEN ... CHK F7
    
    if (data[0] == 0xF0 && data[1] == 0x7F && data[2] == 0x00 && data[3] == 0x7F) {
        uint8_t command = data[4];
        uint8_t sequence = data[5];
        uint8_t payload_len = data[6];
        uint8_t* payload = &data[7];
        
        // Verificar checksum
        uint8_t checksum = command ^ sequence;
        for (int i = 0; i < payload_len; i++) {
            checksum ^= payload[i];
        }
        checksum &= 0x7F;
        if (checksum != data[7 + payload_len]) return; // Bad checksum
        
        // Procesar comando
        switch(command) {
            case 0x05: handleNeoTrellisGrid(payload[0], payload[1], &payload[2]); break;
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
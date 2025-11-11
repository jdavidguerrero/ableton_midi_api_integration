# PushClone - Changelog

## [1.0.6] - 2025-11-11

### Fixed
- **MIDIUtils.py / StepSequencerManager.py**: Restored `SysExEncoder.encode_view_switch()` and `encode_step_sequencer_state()` helpers and updated the sequencer manager to use them, eliminating the missing-attribute errors when sending navigation and sequencer snapshots.
- **ClipManager.py / SessionRing.py**: Session grid updates now follow the current session ring window. Newly visited regions automatically register listeners so creating clips in any scrolled area refreshes the hardware grid immediately.
- **Color fidelity**: `ColorUtils.live_color_to_rgb()` now decodes Live's `clip.color`/`track.color` values as `0xRRGGBB`, and grid logs show the raw Live color for each pad to verify the values coming from the API.
- **SysEx encoder**: Commands are no longer forced into 7-bit values, so `CMD_DISCONNECT = 0xB0` (and any other >0x7F command) is transmitted as-is.
- **Palette tuning**: Added NeoTrellis-friendly overrides for Live's indexed palette and a uniform “dim white” color for empty pads so the hardware grid stays legible even when Live chooses muddy hues.
- **Connection flow**: The script now marks itself connected right after sending the handshake (and whenever hardware sends a handshake) so the complete state/grid is pushed immediately, even if the hardware doesn't reply. Validation was also relaxed so extended command IDs (> `0x7F`) are allowed while payload bytes remain 7-bit clean.
- **CPU telemetry opt-out**: `CMD_CPU_USAGE (0xA4)` is now gated behind `ENABLE_CPU_USAGE_STREAM` (default `False`) to avoid repeated MIDI send failures on hardware that doesn’t implement the command.
- **Session ring refresh**: When Live moves the session ring (e.g., selecting tracks/scenes with the mouse), `_send_ring_clips()` now runs automatically so the hardware grid reflects clips created outside the current window as soon as you return.
- **Handshake resilience**: PushClone now retries the handshake every second until the hardware answers, which fixes the case where the controller is already plugged in before Live launches. Logs also include the script version (`SCRIPT_VERSION`) on startup for easier debugging.

## [1.0.5] - 2025-11-11

### Added
- **Disconnect Notification**: Script now sends `CMD_DISCONNECT (0xB0)` to hardware when closing/disconnecting
  - **consts.py**: Added `CMD_DISCONNECT = 0xB0` constant
  - **PushClone.py**: Modified `disconnect()` to send notification before cleanup
  - **Purpose**: Allows hardware to detect when Live closes and update connection state (e.g., change LED indicators)
  - **Format**: `F0 7F 00 7F B0 [SEQ] 00 00 [CHECKSUM] F7` (empty payload)

### Documentation
- Hardware should handle `CMD_DISCONNECT (0xB0)` to:
  - Update connection status LEDs (turn red/off)
  - Clear grid/display
  - Reset to disconnected state
  - Stop sending commands until new handshake

## [1.0.4] - 2025-11-11

### Fixed
- **🐛 CRITICAL BUG**: STOPPED clips (created but not playing) were showing as PLAYING (green)
  - **consts.py**: Added `CLIP_STOPPED = 4` constant for clips that exist but aren't playing
  - **ClipManager.py**: Fixed state detection in 2 locations (lines 1066, 700) to use `CLIP_STOPPED` instead of wrong values
  - **MIDIUtils.py**: Updated state_names dictionary to match constant values
  - **Result**: STOPPED clips now show their original Ableton color, PLAYING clips show green

### Behavior Changes
- **Clip Colors**:
  - STOPPED (exists but not playing) → Shows **original clip color** from Ableton
  - PLAYING → Shows **green** (G=255)
  - QUEUED → Shows **yellow** tint
  - RECORDING → Shows **red** tint
  - EMPTY (no clip) → Shows **dim track color** (÷ 8)

## [1.0.3] - 2025-11-11

### Fixed
- **SessionRing.py**: Fixed missing method `_update_ring_to_include` → `_update_ring_from_selection` (2 locations)
  - Resolves errors when selecting tracks/scenes in Live
- **MIDIUtils.py**: Fixed track/scene label calculation in grid encoding logs (cosmetic fix)

## [1.0.2] - 2025-11-11

### Fixed
- **ClipManager.py**: Grid iteration order corrected to scene-by-scene (rows), tracks as columns
  - Now sends: T0S0, T1S0, T2S0... (8 tracks × 4 scenes)
- **ClipManager.py**: Fixed method calls `_send_grid_update()` → `_send_neotrellis_clip_grid()` (4 locations)
- **ClipManager.py**: Added bounds checking for track color access
- **PushClone.py**: Auto-connection on valid command receipt (hardware doesn't send handshake reply)

## [1.0.1] - 2025-11-08

### Fixed
- **MIDIUtils.py**: Color conversion for packed RGB integers (0xRRGGBB format)
- **BrowserManager.py**: Ring command filtering to prevent "Unknown command" errors
- **consts.py**: Grid configuration updated to 8 tracks × 4 scenes

### Added
- Debug logging for grid colors and navigation

## [1.0.0] - Initial Release

### Features
- Complete Live API coverage (9 managers)
- SessionRing for grid navigation
- Full RGB (14-bit) encoding for NeoTrellis M4
- SysEx protocol with checksums
- Listener system for all Live objects

---

## Usage

**Script location:** `/Users/juandavidguerrerocastro/Music/Ableton/User Library/Remote Scripts/PushClone`

**To update:**
```bash
cd /Users/juandavidguerrerocastro/Documents/PROJECTS/MUSIC_DEVICES/ableton_midi_api_integration
./update_pushclone.sh
```

**To reload in Ableton:**
1. Preferences → Link, Tempo & MIDI
2. Control Surface → None
3. Control Surface → PushClone

**Check version in logs:**
```bash
tail -f ~/Library/Preferences/Ableton/Live*/Log.txt | grep "PushClone Script"
```
Should show: `--- PushClone Script v1.0.5 (2025-11-11) Loading ---`

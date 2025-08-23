# 🎛️ Ableton Push Clone - MIDI API Integration

A complete Ableton Live remote script for creating a custom Push-style controller with bidirectional MIDI communication.

## 🚀 Features

- **🎵 Session View**: Complete clip launching, stopping, and scene management
- **🎚️ Mixer View**: Track volume, pan, mute, solo, sends, and crossfader control
- **🎛️ Device View**: Device parameters, rack chains, and drum pad support
- **🥁 Drum Rack**: Full NeoTrellis 4x8 grid support with visual feedback
- **🎼 Note View**: Scale selection, octave control, and instrument management
- **🚀 Transport**: Play, record, loop, metronome, and quantization
- **🔍 Navigation**: Track/scene selection and detail view switching
- **🤖 Automation**: Recording, re-enabling, and undo/redo operations

## 📁 Project Structure

### Core Files
- **`PushClone.py`** - Main orchestrator and control surface
- **`MIDIUtils.py`** - SysEx encoding/decoding utilities
- **`consts.py`** - All MIDI command constants

### Manager Modules
- **`SongManager.py`** - Session and application management
- **`TrackManager.py`** - Track and mixer management
- **`ClipManager.py`** - Clip and scene management  
- **`DeviceManager.py`** - Device and drum rack management
- **`TransportManager.py`** - Transport controls
- **`BrowserManager.py`** - Navigation and view switching
- **`AutomationManager.py`** - Automation features

### Documentation
- **`PushClone_API_Documentation.md`** - Complete API documentation
- **`Teensy_MIDI_Commands_Reference.md`** - Hardware implementation guide

## 🎛️ Hardware Support

### NeoTrellis Drum Grid
- **4x8 grid** (32 pads) with color-coded feedback
- **Real-time updates** when samples are loaded/unloaded
- **Visual selection** highlighting
- **State mapping**: Empty, Loaded, Active, Selected

### MIDI Protocol
- **SysEx-based** bidirectional communication
- **Checksum validation** for data integrity
- **Command categorization** by Live Object Model
- **Hardware handshake** protocol

## 🛠️ Installation

1. Copy all Python files to your Ableton Live Remote Scripts folder:
   ```
   ~/Music/Ableton/User Library/Remote Scripts/PushClone/
   ```

2. Add your script in Ableton Live preferences:
   - Live → Preferences → Link MIDI
   - Control Surface: PushClone
   - Input/Output: Your MIDI device

3. Configure your hardware MIDI device to use the SysEx protocol

## 🎯 MIDI Commands

The script implements **80+ MIDI commands** covering:

- **Transport** (0x50-0x5F): Play, record, loop, metronome
- **Tracks** (0x20-0x2F): Volume, pan, mute, solo, sends
- **Clips** (0x10-0x1F): States, names, colors, loop points
- **Devices** (0x40-0x4F): Parameters, drum racks, chains
- **Navigation** (0xB0-0xBF): Track/scene selection
- **Views** (0x70-0x7F): Session, arrangement, detail
- **Automation** (0xC0-0xCF): Recording, undo/redo

## 🔧 Development

### Requirements
- **Ableton Live** 10+ (tested with Live 11/12)
- **Python** (built into Live)
- **Hardware**: Teensy 4.0+ or similar microcontroller

### Key Features
- **Modular architecture** based on Live Object Model
- **Comprehensive error handling** and logging
- **Live API compatibility** checks for different versions
- **Clip type detection** (audio vs MIDI)
- **CPU usage monitoring** with throttling

## 🎵 Usage Examples

### Basic Session Control
```python
# Trigger clip at track 0, scene 1
send_sysex(CMD_CLIP_TRIGGER, [0, 1])

# Set track 2 volume to 50%
send_sysex(CMD_MIXER_VOLUME, [2, 64])

# Fire scene 3
send_sysex(CMD_SCENE_FIRE, [3])
```

### Drum Rack Integration
```python
# Receives NeoTrellis grid updates automatically
# Command 0x4B: [track, device, pad0...pad31]
# Pad states: 0=empty, 1=loaded, 2=active, 3=selected
```

## 📊 Statistics

- **5,678** total lines of code
- **80+** MIDI commands implemented
- **7** specialized manager modules
- **200+** API methods covered
- **32-pad** drum grid support

## 🤝 Contributing

This project is designed for educational and development purposes. Feel free to:

- Extend hardware support
- Add new MIDI commands
- Improve error handling
- Optimize performance

## 📄 License

Open source project for Ableton Live controller development.

## 🔗 Links

- **Repository**: [GitHub - ableton_midi_api_integration](https://github.com/jdavidguerrero/ableton_midi_api_integration)
- **Ableton Live Object Model**: [Cycling74 Documentation](https://docs.cycling74.com/legacy/max8/vignettes/live_object_model)

---

**Built with ❤️ for the music production community**

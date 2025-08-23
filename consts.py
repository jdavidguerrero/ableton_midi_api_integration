# consts.py - Complete Protocol Constants
"""
PushClone Complete Protocol Constants
Supports all views: Clip, Mixer, Device, Note
"""

# SysEx Header (Universal Non-Commercial) 
SYSEX_HEADER = (0xF0, 0x7F, 0x00, 0x7F)
SYSEX_END = 0xF7

# ========================================
# VIEW SWITCHING COMMANDS
# ========================================
CMD_SWITCH_VIEW = 0x01          # Switch active view

# ========================================
# CONNECTION COMMANDS (0x60-0x6F)
# ========================================
CMD_HANDSHAKE = 0x60            # Initial handshake
CMD_HANDSHAKE_REPLY = 0x61      # Handshake response
CMD_VIEW_STATE = 0x62           # Complete view state dump
CMD_PING_TEST = 0x63            # MIDI connection test

# ========================================
# CLIP VIEW COMMANDS (0x10-0x1F)
# ========================================
CMD_CLIP_STATE = 0x10           # Clip state change (Live → Teensy)
CMD_CLIP_TRIGGER = 0x11         # Trigger clip (Teensy → Live)
CMD_SCENE_FIRE = 0x12           # Fire scene (Teensy → Live)
CMD_CLIP_STOP = 0x13            # Stop clip (Teensy → Live)
CMD_CLIP_NAME = 0x14            # Clip name (Live → Teensy)
CMD_CLIP_LOOP = 0x15            # Clip loop state (Live → Teensy)
CMD_CLIP_MUTED = 0x16           # Clip muted state (Live → Teensy)
CMD_CLIP_WARP = 0x17            # Clip warp state (Live → Teensy)
CMD_CLIP_START = 0x18           # Clip start marker (Live → Teensy)
CMD_CLIP_END = 0x19             # Clip end marker (Live → Teensy)
CMD_SCENE_STATE = 0x1A          # Scene state info (Live → Teensy)
CMD_SCENE_NAME = 0x1B           # Scene name change (Live → Teensy)
CMD_SCENE_COLOR = 0x1C          # Scene color change (Live → Teensy)
CMD_SCENE_IS_TRIGGERED = 0x1D   # Scene triggered state (Live → Teensy)

# ========================================
# MIXER VIEW COMMANDS (0x20-0x2F)
# ========================================
CMD_MIXER_STATE = 0x20          # Complete mixer channel state (Live → Teensy)
CMD_MIXER_VOLUME = 0x21         # Volume change (bidirectional)
CMD_MIXER_PAN = 0x22            # Pan change (bidirectional)
CMD_MIXER_MUTE = 0x23           # Mute toggle (bidirectional)
CMD_MIXER_SOLO = 0x24           # Solo toggle (bidirectional)
CMD_MIXER_ARM = 0x25            # Arm toggle (bidirectional)
CMD_MIXER_SEND = 0x26           # Send level change (bidirectional)
CMD_TRACK_NAME = 0x27           # Track name change (Live → Teensy)
CMD_TRACK_COLOR = 0x2B          # Track color change (Live → Teensy)
CMD_TRACK_PLAYING_SLOT = 0x28   # Track playing slot index (Live → Teensy)
CMD_TRACK_FIRED_SLOT = 0x29     # Track fired slot index (Live → Teensy)
CMD_TRACK_FOLD_STATE = 0x2A     # Track fold state (Live → Teensy)

# ========================================
# DEVICE VIEW COMMANDS (0x30-0x3F)
# ========================================
CMD_DEVICE_LIST = 0x30          # Device list in track (Live → Teensy)
CMD_DEVICE_SELECT = 0x31        # Select device (Teensy → Live)
CMD_DEVICE_PARAMS = 0x32        # Device parameters (Live → Teensy)
CMD_PARAM_CHANGE = 0x33         # Parameter value change (bidirectional)
CMD_PARAM_VALUE = 0x34          # Individual parameter value (Live → Teensy)
CMD_DEVICE_ENABLE = 0x35        # Device enable/disable (bidirectional)
CMD_DEVICE_PREV_NEXT = 0x36     # Navigate devices (Teensy → Live)
CMD_PARAM_PAGE = 0x37           # Parameter page change (Teensy → Live)

# ========================================
# NOTE VIEW COMMANDS (0x40-0x4F)
# ========================================
CMD_NOTE_ON = 0x40              # MIDI note on (Teensy → Live)
CMD_NOTE_OFF = 0x41             # MIDI note off (Teensy → Live)
CMD_SCALE_CHANGE = 0x42         # Scale change (Teensy → Live)
CMD_SCALE_INFO = 0x43           # Scale info (Live → Teensy)
CMD_OCTAVE_CHANGE = 0x44        # Octave change (Teensy → Live)
CMD_OCTAVE_INFO = 0x45          # Octave info (Live → Teensy)
CMD_TRACK_INSTRUMENT = 0x46     # Track instrument info (Live → Teensy)
CMD_DRUM_PAD_MAP = 0x47         # Drum pad mapping (Live → Teensy)
CMD_DRUM_RACK_STATE = 0x48      # Drum rack state (Live → Teensy)
CMD_DRUM_PAD_STATE = 0x49       # Drum pad state (Live → Teensy)
CMD_DEVICE_CHAIN = 0x4A         # Device chain state (Live → Teensy)
CMD_NEOTRELLIS_GRID = 0x4B      # NeoTrellis 4x8 grid state (Live → Teensy)
CMD_DRUM_PAD_COLOR = 0x4C       # Drum pad color/state (Live → Teensy)

# ========================================
# TRANSPORT COMMANDS (0x50-0x5F)
# ========================================
CMD_TRANSPORT = 0x50            # Transport state (Live → Teensy)
CMD_TRANSPORT_PLAY = 0x51       # Play/stop toggle (Teensy → Live)
CMD_TRANSPORT_RECORD = 0x52     # Record toggle (bidirectional)
CMD_TRANSPORT_LOOP = 0x53       # Loop toggle (bidirectional)
CMD_TRANSPORT_TEMPO = 0x54      # Tempo change (Live → Teensy)
CMD_TRANSPORT_SIGNATURE = 0x55  # Time signature (Live → Teensy)
CMD_TRANSPORT_POSITION = 0x56   # Song position (Live → Teensy)
CMD_TRANSPORT_METRONOME = 0x57  # Metronome state (bidirectional)
CMD_TRANSPORT_OVERDUB = 0x58    # Overdub state (bidirectional)
CMD_TRANSPORT_PUNCH = 0x59      # Punch in/out state (bidirectional)
CMD_TRANSPORT_QUANTIZE = 0x5A   # MIDI quantization (bidirectional)
CMD_SESSION_RECORD = 0x5B       # Session record state (bidirectional)

# ========================================
# BROWSER/NAVIGATION COMMANDS (0xB0-0xBF)
# ========================================
CMD_SELECTED_TRACK = 0xB0         # Selected track change (Live → Teensy)
CMD_SELECTED_SCENE = 0xB1         # Selected scene change (Live → Teensy)
CMD_DETAIL_CLIP = 0xB2            # Detail clip change (Live → Teensy)
CMD_BROWSER_MODE = 0xB3           # Browser mode state (Live → Teensy)

# ========================================
# AUTOMATION COMMANDS (0xC0-0xCF)
# ========================================
CMD_AUTOMATION_RECORD = 0xC0      # Automation record state (bidirectional)
CMD_RE_ENABLE_AUTOMATION = 0xC1   # Re-enable automation (Teensy → Live)
CMD_BACK_TO_ARRANGER = 0xC2       # Back to arranger (Teensy → Live)
CMD_UNDO = 0xC3                   # Undo action (Teensy → Live)
CMD_REDO = 0xC4                   # Redo action (Teensy → Live)
CMD_CAPTURE_MIDI = 0xC5           # Capture MIDI (Teensy → Live)
CMD_QUANTIZE_CLIP = 0xC6          # Quantize clip (Teensy → Live)
CMD_QUANTIZE_NOTES = 0xC7         # Quantize notes (Teensy → Live)

# ========================================
# CLIP STATES
# ========================================
CLIP_EMPTY = 0
CLIP_PLAYING = 1
CLIP_QUEUED = 2
CLIP_RECORDING = 3

# ========================================
# GRID DIMENSIONS
# ========================================
GRID_WIDTH = 8                  # Scenes (horizontal)
GRID_HEIGHT = 4                 # Tracks (vertical)
TOTAL_PADS = GRID_WIDTH * GRID_HEIGHT  # 32 pads total

# ========================================
# LIVE COLOR MAPPING
# ========================================
LIVE_COLORS = {
    0: (255, 76, 76),    # Red
    1: (255, 165, 76),   # Orange  
    2: (255, 255, 76),   # Yellow
    3: (165, 255, 76),   # Lime
    4: (76, 255, 76),    # Green
    5: (76, 255, 165),   # Mint
    6: (76, 255, 255),   # Cyan
    7: (76, 165, 255),   # Light Blue
    8: (76, 76, 255),    # Blue
    9: (165, 76, 255),   # Purple
    10: (255, 76, 255),  # Magenta
    11: (255, 76, 165),  # Pink
    12: (127, 127, 127), # Gray
    13: (255, 255, 255), # White
    14: (50, 50, 50),    # Dark Gray
    15: (0, 0, 0),       # Black
}

# ========================================
# DEFAULT TRACK COLORS
# ========================================
DEFAULT_TRACK_COLORS = [
    (255, 76, 76),   # Red
    (255, 165, 76),  # Orange
    (255, 255, 76),  # Yellow
    (76, 255, 76),   # Green
    (76, 165, 255),  # Light Blue
    (165, 76, 255),  # Purple
    (255, 76, 255),  # Magenta
    (127, 127, 127), # Gray
]

# ========================================
# SCALE DEFINITIONS
# ========================================
SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Blues": [0, 3, 5, 6, 7, 10],
    "Pentatonic": [0, 2, 4, 7, 9]
}

# ========================================
# DEBUG SETTINGS
# ========================================
DEBUG_ENABLED = True
LOG_MIDI_MESSAGES = True   # Enable for Teensy development
LOG_LISTENER_EVENTS = True # Enable for debugging  
LOG_VIEW_SWITCHES = True
LOG_PARAMETER_CHANGES = False

# ========================================
# HARDWARE CONFIGURATION
# ========================================
NEOTRELLIS_ROWS = 4
NEOTRELLIS_COLS = 8
NUM_ENCODERS = 8
NUM_FADERS = 4
NUM_BUTTONS = 16

# ========================================
# TIMING CONFIGURATION
# ========================================
DEBOUNCE_TIME_MS = 50           # Button debounce time
ENCODER_SENSITIVITY = 1         # Encoder steps per value change
FADER_SMOOTHING = 0.1          # Fader value smoothing
LED_BRIGHTNESS = 0.8           # Default LED brightness
LED_UPDATE_RATE_MS = 50        # LED update frequency
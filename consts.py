# consts.py - Complete Protocol Constants
"""
PushClone Complete Protocol Constants
Supports all views: Clip, Mixer, Device, Note
"""

# SysEx Header (Universal Non-Commercial) 
SYSEX_HEADER = (0xF0, 0x7F, 0x00, 0x7F)
SYSEX_END = 0xF7
SCRIPT_VERSION = "1.0.9"

# ========================================
# SYSTEM & NAVIGATION COMMANDS (0x00-0x0F)
# ========================================
CMD_HANDSHAKE = 0x00            # Initial handshake (Hardware → Live)
CMD_HANDSHAKE_REPLY = 0x01      # Handshake response (Live → Hardware)
CMD_DISCONNECT = 0x02           # Disconnect notification (Live → Hardware when script closes)
CMD_PING_TEST = 0x03            # MIDI connection test
CMD_SWITCH_VIEW = 0x04          # Switch active view
CMD_VIEW_STATE = 0x05           # Complete view state dump
CMD_SELECTED_TRACK = 0x06       # Selected track change (Live → Teensy)
CMD_SELECTED_SCENE = 0x07       # Selected scene change (Live → Teensy)
CMD_DETAIL_CLIP = 0x08          # Detail clip change (Live → Teensy)
CMD_BROWSER_MODE = 0x09         # Browser mode state (Live → Teensy)
CMD_RING_NAVIGATE = 0x0A        # Navigate session ring
CMD_RING_SELECT = 0x0B          # Select in session ring
CMD_RING_POSITION = 0x0C        # Ring position update
CMD_TRACK_SELECT = 0x0D         # Track selection (from hardware)
CMD_SCENE_SELECT = 0x0E         # Scene selection (from hardware)
CMD_SESSION_MODE = 0x0F         # Session screen/pad mode switch

# ========================================
# CLIP & SCENE COMMANDS (0x10-0x1F)
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
CMD_CLIP_PLAYING_POSITION = 0x1E # Clip playing position (Live → Hardware, throttled)
CMD_CLIP_LENGTH = 0x1F          # Clip length in beats (Live → Hardware)

# ========================================
# MIXER & TRACK COMMANDS (0x20-0x2F)
# ========================================
CMD_MIXER_STATE = 0x20          # Complete mixer channel state (Live → Teensy)
CMD_MIXER_VOLUME = 0x21         # Volume change (bidirectional)
CMD_MIXER_PAN = 0x22            # Pan change (bidirectional)
CMD_MIXER_MUTE = 0x23           # Mute toggle (bidirectional)
CMD_MIXER_SOLO = 0x24           # Solo toggle (bidirectional)
CMD_MIXER_ARM = 0x25            # Arm toggle (bidirectional)
CMD_MIXER_SEND = 0x26           # Send level change (bidirectional)
CMD_TRACK_NAME = 0x27           # Track name change (Live → Teensy)
CMD_TRACK_COLOR = 0x28          # Track color change (Live → Teensy)
CMD_TRACK_PLAYING_SLOT = 0x29   # Track playing slot index (Live → Teensy)
CMD_TRACK_FIRED_SLOT = 0x2A     # Track fired slot index (Live → Teensy)
CMD_TRACK_FOLD_STATE = 0x2B     # Track fold state (Live → Teensy)
CMD_TRACK_CROSSFADE = 0x2C     # Track crossfade assign (bidirectional)
CMD_TRACK_CUE_VOLUME = 0x2D     # Track cue/pre-listen volume (bidirectional)
CMD_TRACK_METER = 0x2E          # Track output meter level (Live → Hardware, throttled)
CMD_CPU_USAGE = 0x2F            # CPU usage (avg, peak) (Live → Hardware)

# ========================================
# DEVICE & PLUGIN COMMANDS (0x30-0x3F)
# ========================================
CMD_DEVICE_LIST = 0x30          # Device list in track (Live → Teensy)
CMD_DEVICE_SELECT = 0x31        # Select device (Teensy → Live)
CMD_DEVICE_PARAMS = 0x32        # Device parameters (Live → Teensy)
CMD_PARAM_CHANGE = 0x33         # Parameter value change (bidirectional)
CMD_PARAM_VALUE = 0x34          # Individual parameter value (Live → Teensy)
CMD_DEVICE_ENABLE = 0x35        # Device enable/disable (bidirectional)
CMD_DEVICE_PREV_NEXT = 0x36     # Navigate devices (Teensy → Live)
CMD_PARAM_PAGE = 0x37           # Parameter page change (Teensy → Live)
CMD_RACK_MACRO = 0x38           # Rack macro parameter (bidirectional)
CMD_DEVICE_CHAIN = 0x39         # Chain info/update (Live → Hardware)
CMD_CHAIN_SELECT = 0x3A         # Select chain in rack device (Teensy → Live)
CMD_CHAIN_MUTE = 0x3B           # Chain mute toggle (bidirectional)
CMD_CHAIN_SOLO = 0x3C           # Chain solo toggle (bidirectional)
CMD_CHAIN_VOLUME = 0x3D         # Chain volume change (bidirectional)
CMD_CHAIN_PAN = 0x3E            # Chain pan change (bidirectional)
CMD_CHAIN_SEND = 0x3F           # Chain send level (bidirectional)

# ========================================
# TRANSPORT & AUTOMATION (0x40-0x4F)
# ========================================
CMD_TRANSPORT_PLAY = 0x40       # Play/stop toggle (Teensy → Live)
CMD_TRANSPORT_RECORD = 0x41     # Record toggle (bidirectional)
CMD_TRANSPORT_LOOP = 0x42       # Loop toggle (bidirectional)
CMD_TRANSPORT_TEMPO = 0x43      # Tempo change (Live → Teensy)
CMD_TRANSPORT_SIGNATURE = 0x44  # Time signature (Live → Teensy)
CMD_TRANSPORT_POSITION = 0x45   # Song position (Live → Teensy)
CMD_TRANSPORT_METRONOME = 0x46  # Metronome state (bidirectional)
CMD_TRANSPORT_OVERDUB = 0x47    # Overdub state (bidirectional)
CMD_TRANSPORT_PUNCH = 0x48      # Punch in/out state (bidirectional)
CMD_TRANSPORT_STATE = 0x49      # Consolidated transport state (Live → Hardware)
CMD_NUDGE = 0x4A                # Tempo nudge up/down (Hardware → Live)
CMD_RE_ENABLE_AUTOMATION = 0x4B # Re-enable automation (Teensy → Live)
CMD_BACK_TO_ARRANGER = 0x4C     # Back to arranger (Teensy → Live)
CMD_UNDO = 0x4D                 # Undo action (Teensy → Live)
CMD_REDO = 0x4E                 # Redo action (Teensy → Live)
CMD_CAPTURE_MIDI = 0x4F         # Capture MIDI (Hardware → Live)

# ========================================
# NOTE, SCALE & SEQUENCER (0x50-0x5F)
# ========================================
CMD_NOTE_ON = 0x50              # MIDI note on (Teensy → Live)
CMD_NOTE_OFF = 0x51             # MIDI note off (Teensy → Live)
CMD_SCALE_CHANGE = 0x52         # Scale change (Teensy → Live)
CMD_SCALE_INFO = 0x53           # Scale info (Live → Teensy)
CMD_OCTAVE_CHANGE = 0x54        # Octave change (Teensy → Live)
CMD_OCTAVE_INFO = 0x55          # Octave info (Live → Teensy)
CMD_STEP_SEQUENCER_STATE = 0x56 # Sequencer grid state (Live → Teensy)
CMD_STEP_SEQUENCER_NOTE = 0x57  # Add/remove note (Teensy → Live)
CMD_STEP_SEQUENCER_RESOLUTION = 0x58 # Change resolution (Teensy → Live)
CMD_STEP_SEQUENCER_PAGE = 0x59  # Change page (Teensy → Live)
CMD_STEP_SEQUENCER_HOLD = 0x5A  # Hold step for editing (Teensy → Live)
CMD_STEP_EDIT_PARAMS = 0x5B     # Step edit parameters (bidirectional)
CMD_STEP_SEQUENCER_INFO = 0x5C  # Sequencer info (Live → Teensy)
CMD_STEP_CLEAR_ALL = 0x5D       # Clear all notes in page (Teensy → Live)
CMD_STEP_COPY_PAGE = 0x5E       # Copy page (Teensy → Live)
CMD_LOOP_MARKERS = 0x5F         # Loop markers (start/end) (bidirectional)

# ========================================
# GRID, GROOVE & QUANTIZATION (0x60-0x6F)
# ========================================
CMD_GRID_UPDATE = 0x60          # Full 8x4 grid color update (Live → Hardware)
CMD_GRID_SINGLE_PAD = 0x61      # Single pad color (Live → Hardware)
CMD_GRID_PAD_PRESS = 0x62       # Pad press/release (Hardware → Live)
CMD_SESSION_OVERVIEW = 0x63     # Session overview toggle/navigate
CMD_SESSION_OVERVIEW_GRID = 0x64 # Session overview grid data
CMD_DRUM_RACK_STATE = 0x65      # Drum rack state (Live → Teensy)
CMD_DRUM_PAD_STATE = 0x66       # Drum pad state (Live → Hardware)
CMD_GROOVE_AMOUNT = 0x67        # Track groove amount (bidirectional)
CMD_GROOVE_TEMPLATE = 0x68      # Track groove template (bidirectional)
CMD_GROOVE_POOL = 0x69          # Groove pool templates (Live → Teensy)
CMD_RECORD_QUANTIZATION = 0x6A  # Record quantization setting (bidirectional)
CMD_TRANSPORT_QUANTIZE = 0x6B   # MIDI quantization (bidirectional)
CMD_MIDI_CLIP_QUANTIZE = 0x6C   # Quantize MIDI clip (Teensy → Live)
CMD_QUANTIZE_CLIP = 0x6D        # Quantize selected clip (Teensy → Live)
CMD_QUANTIZE_NOTES = 0x6E       # Quantize notes (Hardware → Live)
CMD_CUE_POINT = 0x6F            # Cue point info (Live → Hardware)

# ========================================
# SONG & CLIP ACTIONS (0x70-0x7F)
# ========================================
CMD_CREATE_AUDIO_TRACK = 0x70   # Create audio track (Teensy → Live)
CMD_CREATE_MIDI_TRACK = 0x71    # Create MIDI track (Teensy → Live)
CMD_CREATE_RETURN_TRACK = 0x72  # Create return track (Teensy → Live)
CMD_CREATE_SCENE = 0x73         # Create scene (Teensy → Live)
CMD_DUPLICATE_TRACK = 0x74      # Duplicate track (Teensy → Live)
CMD_DUPLICATE_CLIP = 0x75       # Duplicate clip (Teensy → Live)
CMD_CLIP_DELETE = 0x76          # Delete clip
CMD_CLIP_COPY = 0x77            # Copy clip
CMD_CLIP_PASTE = 0x78           # Paste clip
CMD_CLIP_DUPLICATE_RESULT = 0x79 # Duplicate result
CMD_CLIP_DELETE_RESULT = 0x7A   # Delete result
CMD_CLIP_COPY_RESULT = 0x7B     # Copy result
CMD_CLIP_PASTE_RESULT = 0x7C    # Paste result
CMD_MIDI_NOTES = 0x7D           # Batched MIDI notes dump (Live → Hardware)
CMD_MIDI_NOTE_ADD = 0x7E        # Insert MIDI note into clip (Hardware → Live)
CMD_MIDI_NOTE_REMOVE = 0x7F     # Remove MIDI note(s) from clip (Hardware → Live)

# Aliases for backward compatibility or clarity
CMD_METRONOME = CMD_TRANSPORT_METRONOME
CMD_AUTOMATION_RECORD = CMD_TRANSPORT_OVERDUB # Overdub is the modern term
CMD_ARRANGEMENT_RECORD = CMD_TRANSPORT_OVERDUB
CMD_TRANSPORT = CMD_TRANSPORT_STATE
CMD_CLIP_DUPLICATE = CMD_DUPLICATE_CLIP

# PLUGIN-SPECIFIC COMMANDS (Now integrated into other sections)
CMD_PLUGIN_PRESET = CMD_RACK_MACRO
CMD_PLUGIN_PROGRAM = CMD_DEVICE_SELECT
CMD_PLUGIN_UI = CMD_DEVICE_ENABLE
CMD_PLUGIN_LATENCY = CMD_CPU_USAGE

# ========================================
# CLIP STATES
# ========================================
CLIP_EMPTY = 0
CLIP_PLAYING = 1
CLIP_QUEUED = 2
CLIP_RECORDING = 3
CLIP_STOPPED = 4  # Clip exists but not playing (shows original clip color)

# ========================================
# PUSH CLONE GRID CONFIGURATION
# ========================================
# NeoTrellis M4 Layout:
#   - 8 columnas (horizontal) = 8 TRACKS (incluyendo master)
#   - 4 filas (vertical) = 4 SCENES
GRID_WIDTH = 8                  # 8 tracks (horizontal)
GRID_HEIGHT = 4                 # 4 scenes (vertical)
TOTAL_PADS = 32                 # 8x4 = 32 pads

# ========================================
# LIVE COLOR MAPPING (for hardware)
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

# NeoTrellis-specific palette adjustments for Live's indexed colors
NEOTRELLIS_COLOR_MAP = {
    0: (255, 80, 72),    # Red - slightly brighter
    1: (255, 180, 90),   # Orange - reduce brown feel
    2: (255, 255, 110),  # Yellow - extra brightness
    3: (190, 255, 110),  # Lime
    4: (90, 255, 140),   # Green - avoid muddy green
    5: (90, 255, 210),   # Mint - more cyan
    6: (100, 240, 255),  # Cyan - softer blue
    7: (120, 190, 255),  # Light Blue
    8: (110, 140, 255),  # Blue - brighter
    9: (200, 100, 255),  # Purple - less dark
    10: (255, 100, 235), # Magenta
    11: (255, 130, 190), # Pink
    12: (190, 190, 190), # Gray - brighter
    13: (255, 255, 255), # White
    14: (80, 80, 80),    # Dark Gray - avoid full black
    15: (10, 10, 10),    # Black - leave a faint glow
}

# Default LED color for empty pads (no clip present)
NEOTRELLIS_EMPTY_PAD_COLOR = (40, 40, 40)

# Clip state colors (for reference - actual colors calculated in MIDIUtils.py)
CLIP_STATE_COLORS = {
    CLIP_EMPTY: (0, 0, 0),           # Off
    CLIP_STOPPED: None,              # Uses original clip color (calculated)
    CLIP_PLAYING: (76, 255, 76),     # Green (calculated from base color)
    CLIP_QUEUED: (255, 255, 76),     # Yellow (calculated from base color)
    CLIP_RECORDING: (255, 76, 76),   # Red (calculated from base color)
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
ENABLE_CPU_USAGE_STREAM = False  # Disable CPU usage SysEx until firmware supports it reliably

# ========================================
# PROTOCOL SETTINGS
# ========================================
MAX_SYSEX_SIZE = 256            # Maximum SysEx message size (supports full-grid payloads)
GRID_UPDATE_RATE_MS = 16        # ~60fps grid updates

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
CMD_CHAIN_SELECT = 0x38         # Select chain in rack device (Teensy → Live)
CMD_CHAIN_MUTE = 0x39           # Chain mute toggle (bidirectional)
CMD_CHAIN_SOLO = 0x3A           # Chain solo toggle (bidirectional)
CMD_CHAIN_VOLUME = 0x3B         # Chain volume change (bidirectional)
CMD_CHAIN_PAN = 0x3C            # Chain pan change (bidirectional)
CMD_CHAIN_SEND = 0x3D           # Chain send level (bidirectional)
CMD_CHAIN_CROSSFADE = 0x3E      # Chain crossfade assign (bidirectional)
CMD_RACK_MACRO = 0x3F           # Rack macro parameter (bidirectional)

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
CMD_NEOTRELLIS_CLIP_GRID = 0x4D # NeoTrellis 8x4 clip grid colors (Live → Teensy)
CMD_NOTE_VIEW_MODE = 0x4E       # Note view mode (drum/melodic) (bidirectional)
CMD_NOTE_AUTO_DETECT = 0x4F      # Auto-detect note view mode (bidirectional)
CMD_NOTE_DRUM_GRID = 0x41        # Drum grid colors (Live → Teensy) 
CMD_NOTE_MELODIC_GRID = 0x42     # Melodic grid colors (Live → Teensy)
CMD_NOTE_SCALE_CONFIG = 0x43     # Scale configuration (Live → Teensy)
CMD_NOTE_DRUM_CONFIG = 0x44      # Drum configuration (Live → Teensy)
CMD_NOTE_DRUM_PAD_INFO = 0x45    # Drum pad info (Live → Teensy)
CMD_NOTE_OCTAVE = 0x46           # Octave change (bidirectional)
CMD_NOTE_VELOCITY_LEVEL = 0x47   # Drum velocity level (bidirectional)
CMD_NOTE_KEY_LAYOUT = 0x48       # Melodic key layout (bidirectional)

# ========================================
# STEP SEQUENCER COMMANDS (0x80-0x8F)
# ========================================
CMD_STEP_SEQUENCER_STATE = 0x80      # Sequencer grid state (Live → Teensy)
CMD_STEP_SEQUENCER_NOTE = 0x81       # Add/remove note (Teensy → Live)
CMD_STEP_SEQUENCER_RESOLUTION = 0x82 # Change resolution (Teensy → Live)
CMD_STEP_SEQUENCER_PAGE = 0x83       # Change page (Teensy → Live)
CMD_STEP_SEQUENCER_HOLD = 0x84       # Hold step for editing (Teensy → Live)
CMD_STEP_EDIT_PARAMS = 0x85          # Step edit parameters (bidirectional)
CMD_STEP_SEQUENCER_INFO = 0x86       # Sequencer info (Live → Teensy)
CMD_STEP_CLEAR_ALL = 0x87            # Clear all notes in page (Teensy → Live)
CMD_STEP_COPY_PAGE = 0x88            # Copy page (Teensy → Live)

# ========================================
# PLUGIN DEVICE COMMANDS (0x70-0x7F)
# ========================================
CMD_PLUGIN_PRESET = 0x71          # Plugin preset info (Live → Teensy)
CMD_PLUGIN_PROGRAM = 0x72         # Plugin program info (Live → Teensy)
CMD_PLUGIN_LATENCY = 0x73         # Plugin latency info (Live → Teensy)
CMD_PLUGIN_UI = 0x74              # Plugin UI visibility (Live → Teensy)
CMD_PLUGIN_BANK = 0x75            # Plugin bank info (Live → Teensy)
CMD_PLUGIN_TYPE = 0x76            # Plugin type info (VST/AU/VST3)
CMD_PLUGIN_VENDOR = 0x77          # Plugin vendor info

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
CMD_METRONOME = 0x5C            # Metronome toggle (bidirectional)
CMD_RECORD_QUANTIZATION = 0x5D  # Record quantization setting (bidirectional)
CMD_QUANTIZE_CLIP = 0x5E        # Quantize selected clip (Teensy → Live)
CMD_BACK_TO_ARRANGER = 0x5F     # Back to arrangement (Teensy → Live)

# ========================================
# SESSION RING COMMANDS (0xB0-0xBF)
# ========================================
CMD_RING_NAVIGATE = 0xB0        # Navigate session ring
CMD_RING_SELECT = 0xB1          # Select in session ring
CMD_RING_POSITION = 0xB2        # Ring position update
CMD_TRACK_SELECT = 0xB3         # Track selection
CMD_SCENE_SELECT = 0xB4         # Scene selection
CMD_SESSION_MODE = 0xB5         # Session screen/pad mode
CMD_SESSION_OVERVIEW = 0xB6     # Session overview toggle
CMD_SESSION_OVERVIEW_GRID = 0xB7 # Session overview grid data
CMD_CLIP_DUPLICATE = 0xB8       # Duplicate clip
CMD_CLIP_DELETE = 0xB9          # Delete clip
CMD_CLIP_COPY = 0xBA            # Copy clip
CMD_CLIP_PASTE = 0xBB           # Paste clip
CMD_CLIP_DUPLICATE_RESULT = 0xBC # Duplicate result
CMD_CLIP_DELETE_RESULT = 0xBD   # Delete result
CMD_CLIP_COPY_RESULT = 0xBE     # Copy result
CMD_CLIP_PASTE_RESULT = 0xBF    # Paste result

# ========================================
# BROWSER/NAVIGATION COMMANDS (0x60-0x6F) - RELOCATED
# ========================================
CMD_SELECTED_TRACK = 0x64         # Selected track change (Live → Teensy) - was 0xB0
CMD_SELECTED_SCENE = 0x65         # Selected scene change (Live → Teensy) - was 0xB1  
CMD_DETAIL_CLIP = 0x66            # Detail clip change (Live → Teensy) - was 0xB2
CMD_BROWSER_MODE = 0x67           # Browser mode state (Live → Teensy) - was 0xB3

# ========================================
# AUTOMATION COMMANDS (0x68-0x6F) - RELOCATED 
# ========================================
CMD_AUTOMATION_RECORD = 0x68      # Automation record state (bidirectional) - was 0xC0
CMD_RE_ENABLE_AUTOMATION = 0x69   # Re-enable automation (Teensy → Live) - was 0xC1
CMD_BACK_TO_ARRANGER = 0x6A       # Back to arranger (Teensy → Live) - was 0xC2
CMD_UNDO = 0x6B                   # Undo action (Teensy → Live) - was 0xC3
CMD_REDO = 0x6C                   # Redo action (Teensy → Live) - was 0xC4
CMD_CAPTURE_MIDI = 0x6D           # Capture MIDI (Teensy → Live) - was 0xC5
CMD_QUANTIZE_CLIP = 0x6E          # Quantize clip (Teensy → Live) - was 0xC6
CMD_QUANTIZE_NOTES = 0x6F         # Quantize notes (Teensy → Live) - was 0xC7

# ========================================
# GROOVE POOL COMMANDS (0x78-0x7F) - RELOCATED
# ========================================
CMD_GROOVE_POOL = 0x78            # Groove pool templates (Live → Teensy) - was 0xD0
CMD_GROOVE_AMOUNT = 0x79          # Track groove amount (bidirectional) - was 0xD1
CMD_GROOVE_TEMPLATE = 0x7A        # Track groove template (bidirectional) - was 0xD2

# ========================================
# MIDI CLIP COMMANDS (0x7B-0x7F) - RELOCATED  
# ========================================
CMD_MIDI_NOTES = 0x7B             # MIDI notes data (Live → Teensy) - was 0xE0
CMD_MIDI_NOTE_ADD = 0x7C          # Add MIDI note (Teensy → Live) - was 0xE1
CMD_MIDI_NOTE_REMOVE = 0x7D       # Remove MIDI note (Teensy → Live) - was 0xE2
CMD_MIDI_NOTE_MODIFY = 0x7E       # Modify MIDI note (Teensy → Live) - was 0xE3
CMD_MIDI_CLIP_QUANTIZE = 0x7F     # Quantize MIDI clip (Teensy → Live) - was 0xE4

# ========================================
# SONG CREATION COMMANDS (0xF0-0xFF)
# ========================================
CMD_CREATE_AUDIO_TRACK = 0xF0     # Create audio track (Teensy → Live)
CMD_CREATE_MIDI_TRACK = 0xF1      # Create MIDI track (Teensy → Live)
CMD_CREATE_RETURN_TRACK = 0xF2    # Create return track (Teensy → Live)
CMD_CREATE_SCENE = 0xF3           # Create scene (Teensy → Live)
CMD_DUPLICATE_TRACK = 0xF4        # Duplicate track (Teensy → Live)
CMD_DUPLICATE_CLIP = 0xF5         # Duplicate clip (Teensy → Live)

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
# MIDIUtils.py - Unified MIDI Encoding Utilities
"""
Handles encoding of binary data into MIDI SysEx messages, with a focus on
full 24-bit (14-bit encoded) color support for modern controllers like NeoTrellis.
"""

from .consts import *

# ========================================
# Color Encoding Utilities
# ========================================

class ColorEncoder:
    """
    Advanced color encoding for controllers supporting full RGB.
    Supports full 0-255 RGB values through 14-bit MIDI encoding.
    """

    @staticmethod
    def encode_rgb_14bit(r, g, b):
        """
        Encodes a 24-bit RGB color into a 6-byte, 14-bit representation suitable for SysEx.
        Each color channel (0-255) is split into two 7-bit bytes (MSB and LSB).
        """
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        # Encode each channel
        r_msb = (r >> 7) & 0x7F
        r_lsb = r & 0x7F
        g_msb = (g >> 7) & 0x7F
        g_lsb = g & 0x7F
        b_msb = (b >> 7) & 0x7F
        b_lsb = b & 0x7F

        # Return encoded bytes in RGB order: [R_MSB, R_LSB, G_MSB, G_LSB, B_MSB, B_LSB]
        return [r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]

    @staticmethod
    def decode_rgb_14bit(data, offset=0):
        """
        Decodes a 6-byte, 14-bit representation back into a 24-bit RGB tuple.
        """
        if len(data) < offset + 6:
            return (0, 0, 0)

        r = (data[offset + 0] << 7) | data[offset + 1]
        g = (data[offset + 2] << 7) | data[offset + 3]
        b = (data[offset + 4] << 7) | data[offset + 5]

        return (r, g, b)

# ========================================
# Main SysEx Encoder
# ========================================

class SysExEncoder:
    """
    Handles the creation of MIDI SysEx messages for the PushClone protocol.
    """
    _sequence_number = 0
    _max_sequence = 127

    @classmethod
    def _get_next_sequence(cls):
        """Gets the next sequence number for message ordering and reliability."""
        cls._sequence_number = (cls._sequence_number + 1) % cls._max_sequence
        return cls._sequence_number

    @staticmethod
    def create_sysex(command, payload):
        """
        Creates a complete, valid SysEx message with header, command, sequence,
        length, payload, and checksum.
        """
        try:
            message = list(SYSEX_HEADER)
            message.append(command & 0x7F)
            
            sequence = SysExEncoder._get_next_sequence()
            message.append(sequence)
            
            payload_len = len(payload) if payload else 0
            # Always encode payload length as 14-bit (MSB, LSB)
            len_msb = (payload_len >> 7) & 0x7F
            len_lsb = payload_len & 0x7F
            message.extend([len_msb, len_lsb])

            if payload:
                for byte in payload:
                    if not (0 <= byte <= 127):
                        print(f"❌ Invalid 8-bit value in SysEx payload: {byte}. Command: 0x{command:02X}")
                        return None
                    message.append(byte)
            
            checksum = command ^ sequence
            if payload:
                for byte in payload:
                    checksum ^= byte
            message.append(checksum & 0x7F)
            
            message.append(SYSEX_END)
            return message
        except Exception as e:
            print(f"❌ Error creating SysEx message: {e}")
            return None

    # --- Grid and Color Commands ---

    @staticmethod
    def encode_grid_update_full_rgb(grid_data, logger=None):
        """
        Encodes the entire 8x4 grid state with full 24-bit RGB colors.
        """
        while len(grid_data) < 32:
            grid_data.append((0, 0, 0))
        grid_data = grid_data[:32]

        if logger:
            logger("=" * 80)
            logger(f"GRID_ENCODE: Encoding {len(grid_data)} pads with full RGB (14-bit)")
            logger("=" * 80)

        payload = []
        for pad_idx, (r, g, b) in enumerate(grid_data):
            # Calculate row/col for display
            track = pad_idx // 8  # 0-3 (4 tracks)
            scene = pad_idx % 8   # 0-7 (8 scenes)

            encoded = ColorEncoder.encode_rgb_14bit(r, g, b)
            payload.extend(encoded)

            # Log ALL pads to see what's being sent
            if logger:
                logger(f"PAD[{pad_idx:02d}] T{track}S{scene}: RGB({r:3d},{g:3d},{b:3d}) -> [{encoded[0]:02X} {encoded[1]:02X}] [{encoded[2]:02X} {encoded[3]:02X}] [{encoded[4]:02X} {encoded[5]:02X}]")

        if logger:
            logger(f"GRID_ENCODE: Total payload size: {len(payload)} bytes (expected: 192)")
            logger("=" * 80)

        return SysExEncoder.create_sysex(CMD_NEOTRELLIS_CLIP_GRID, payload)

    @staticmethod
    def encode_clip_state_full_rgb(track, scene, state, color):
        """
        Encodes the state and full 24-bit RGB color of a single clip.
        """
        r, g, b = color if isinstance(color, (list, tuple)) else (0,0,0)

        payload = [track & 0x7F, scene & 0x7F, state & 0x7F]
        encoded_color = ColorEncoder.encode_rgb_14bit(r, g, b)
        payload.extend(encoded_color)

        return SysExEncoder.create_sysex(CMD_CLIP_STATE, payload)

    @staticmethod
    def encode_clip_state_compact(track, scene, state, color):
        """
        Encodes clip state with compact 7-bit RGB. For legacy or low-bandwidth use.
        """
        r, g, b = color if isinstance(color, (list, tuple)) else (128, 128, 128)
        payload = [
            track & 0x7F,
            scene & 0x7F,
            state & 0x7F,
            (int(r) >> 1) & 0x7F,
            (int(g) >> 1) & 0x7F,
            (int(b) >> 1) & 0x7F,
        ]
        return SysExEncoder.create_sysex(CMD_CLIP_STATE, payload)

    # --- Other Encoders ---

    @staticmethod
    def encode_param_value(track, device, param, value, display_str):
        """Encodes an individual parameter value with its display string."""
        display_bytes = display_str.encode('utf-8')[:10]
        
        payload = [
            track & 0x7F,
            device & 0x7F,
            param & 0x7F,
            value & 0x7F,
            len(display_bytes)
        ]
        payload.extend(list(display_bytes))
        
        return SysExEncoder.create_sysex(CMD_PARAM_VALUE, payload)

    @staticmethod
    def encode_transport(playing, beat, bar):
        """Encodes the main transport state."""
        payload = [
            1 if playing else 0,
            int(beat) & 0x7F,
            int(bar) & 0x7F
        ]
        return SysExEncoder.create_sysex(CMD_TRANSPORT_STATE, payload)

    @staticmethod
    def log_sysex(message, direction="OUT"):
        """Logs a SysEx message for debugging purposes."""
        if not message:
            print(f"--- {direction}: Empty SysEx message ---")
            return
        hex_string = " ".join([f"{b:02X}" for b in message])
        command = message[4] if len(message) > 4 else 0x00
        print(f"MIDI {direction} | CMD: {command:02X} | LEN: {len(message)} | DATA: [{hex_string}]")

# ========================================
# Color Transformation Utilities
# ========================================

class ColorUtils:
    """
    Utility class for handling Ableton Live's color system and converting
    it into usable RGB values for the hardware controller.
    """
    
    @staticmethod
    def live_color_to_rgb(live_color):
        """
        Converts a Live color value into a 24-bit RGB tuple.

        Live's color property returns an integer representing RGB:
        - If value is small (0-69), it's a Live color index
        - If value is large, it's a packed RGB integer: 0xRRGGBB

        Example: 16249980 = 0xF8EB0C = RGB(248, 235, 12) = Yellow
        """
        from .consts import LIVE_COLORS

        # If it's a known color index (0-69), use the LIVE_COLORS lookup
        if live_color in LIVE_COLORS:
            return LIVE_COLORS[live_color]

        # Otherwise, decode as packed RGB integer
        # Live color format is likely BBGGRR, not RRGGBB
        try:
            b = (live_color >> 16) & 0xFF
            g = (live_color >> 8) & 0xFF
            r = live_color & 0xFF

            # Debug log to verify conversion (comment out after testing)
            # print(f"COLOR_DECODE: Live_color={live_color} (0x{live_color:06X}) -> RGB({r},{g},{b})")

            return (r, g, b)
        except:
            # Fallback to gray if something goes wrong
            return (128, 128, 128)

    @staticmethod
    def get_track_default_color(track_index):
        """
        Gets a default color for a track based on its index, cycling through
        a predefined list of colors.
        """
        from .consts import DEFAULT_TRACK_COLORS
        return DEFAULT_TRACK_COLORS[track_index % len(DEFAULT_TRACK_COLORS)]

    @staticmethod
    def get_clip_state_color(state, base_rgb_color):
        """
        Calculates the final display color for a clip based on its state
        (e.g., playing, stopped, recording) and its base color.
        """
        r, g, b = base_rgb_color

        state_names = {
            0: 'EMPTY',
            1: 'STOPPED',
            2: 'PLAYING',
            3: 'QUEUED',
            4: 'RECORDING'
        }

        if state == CLIP_PLAYING:
            final_color = (r // 2, min(255, g + 150), b // 2)
        elif state == CLIP_RECORDING:
            final_color = (min(255, r + 150), g // 2, b // 2)
        elif state == CLIP_QUEUED:
            final_color = (min(255, r + 100), min(255, g + 100), b // 2)
        elif state == CLIP_EMPTY:
            final_color = (0, 0, 0)
        else: # Clip exists but is stopped
            final_color = (r, g, b)

        # Log disabled to reduce verbosity - see GRID_ENCODE for full details
        # state_name = state_names.get(state, f'UNKNOWN({state})')
        # print(f"COLOR_STATE: State={state_name} BaseRGB({r},{g},{b}) -> FinalRGB({final_color[0]},{final_color[1]},{final_color[2]})")

        return final_color

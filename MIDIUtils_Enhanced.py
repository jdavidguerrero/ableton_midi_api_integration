# MIDIUtils_Enhanced.py - Full RGB Color Support for NeoTrellis M4
"""
Enhanced MIDI utilities with 14-bit RGB color encoding
Allows full 0-255 RGB values through SysEx (not limited to 0-127)
"""

from .consts import *

class ColorEncoder:
    """
    Advanced color encoding for NeoTrellis M4
    Supports full RGB (0-255) through 14-bit MIDI encoding
    """

    @staticmethod
    def encode_rgb_14bit(r, g, b):
        """
        Encode RGB color as 14-bit values (MSB/LSB pairs)

        Args:
            r, g, b (int): RGB values 0-255

        Returns:
            list: [r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb] (6 bytes)

        Example:
            RGB(220, 180, 100) →
            [1, 92, 1, 52, 0, 100] (14-bit encoding)
        """
        # Clamp to 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # Encode each channel as 14-bit (MSB/LSB)
        r_msb = (r >> 7) & 0x7F  # High 7 bits
        r_lsb = r & 0x7F         # Low 7 bits

        g_msb = (g >> 7) & 0x7F
        g_lsb = g & 0x7F

        b_msb = (b >> 7) & 0x7F
        b_lsb = b & 0x7F

        return [r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]

    @staticmethod
    def decode_rgb_14bit(data, offset=0):
        """
        Decode 14-bit RGB color from SysEx data

        Args:
            data (list): SysEx payload
            offset (int): Starting position in data

        Returns:
            tuple: (r, g, b) values 0-255
        """
        if len(data) < offset + 6:
            return (0, 0, 0)

        r = (data[offset + 0] << 7) | data[offset + 1]
        g = (data[offset + 2] << 7) | data[offset + 3]
        b = (data[offset + 4] << 7) | data[offset + 5]

        return (r, g, b)

    @staticmethod
    def encode_rgb_compact(r, g, b):
        """
        Encode RGB as compact 3-byte format (7-bit per channel)
        Use when full precision not needed (saves bandwidth)

        Args:
            r, g, b (int): RGB values 0-255

        Returns:
            list: [r7, g7, b7] (3 bytes, 7-bit range)
        """
        r7 = (r >> 1) & 0x7F  # Divide by 2
        g7 = (g >> 1) & 0x7F
        b7 = (b >> 1) & 0x7F

        return [r7, g7, b7]

    @staticmethod
    def encode_rgb_palette(r, g, b):
        """
        Encode RGB using closest match from Live color palette
        Most efficient for known colors

        Args:
            r, g, b (int): RGB values 0-255

        Returns:
            int: Color index from LIVE_COLORS palette (0-15)
        """
        from .consts import LIVE_COLORS

        # Find closest palette color (simple distance)
        min_distance = float('inf')
        closest_idx = 0

        for idx, (pr, pg, pb) in LIVE_COLORS.items():
            distance = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
            if distance < min_distance:
                min_distance = distance
                closest_idx = idx

        return closest_idx


class SysExEncoderEnhanced:
    """
    Enhanced SysEx encoder with full RGB support
    Drop-in replacement for existing SysExEncoder
    """

    _sequence_number = 0
    _max_sequence = 127

    @classmethod
    def _get_next_sequence(cls):
        cls._sequence_number = (cls._sequence_number + 1) % cls._max_sequence
        return cls._sequence_number

    @staticmethod
    def create_sysex(command, payload):
        """Create SysEx message (same as original)"""
        try:
            message = list(SYSEX_HEADER)
            message.append(command)

            sequence = SysExEncoderEnhanced._get_next_sequence()
            message.append(sequence)

            payload_len = len(payload) if payload else 0
            message.append(payload_len)

            if payload:
                for byte in payload:
                    if byte > 127:
                        print(f"❌ Invalid MIDI byte in SysEx: {byte}")
                        return None
                    message.append(byte & 0x7F)

            checksum = command ^ sequence
            if payload:
                for byte in payload:
                    checksum ^= byte
            message.append(checksum & 0x7F)

            message.append(SYSEX_END)

            return message

        except Exception as e:
            print(f"❌ Error creating SysEx: {e}")
            return None

    # ========================================
    # ENHANCED COLOR COMMANDS
    # ========================================

    @staticmethod
    def encode_clip_state_full_rgb(track, scene, state, color):
        """
        Encode clip state with FULL RGB color (14-bit)

        Args:
            track (int): Track index
            scene (int): Scene index
            state (int): Clip state (CLIP_EMPTY, CLIP_PLAYING, etc.)
            color (tuple): RGB tuple (0-255, 0-255, 0-255)

        Returns:
            list: SysEx message

        Payload format:
            [track, scene, state, r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]
            Total: 9 bytes
        """
        try:
            r, g, b = color if isinstance(color, (list, tuple)) and len(color) >= 3 else (127, 127, 127)

            # Use 14-bit encoding for full RGB
            rgb_encoded = ColorEncoder.encode_rgb_14bit(r, g, b)

            payload = [track, scene, state] + rgb_encoded
            return SysExEncoderEnhanced.create_sysex(CMD_CLIP_STATE, payload)

        except Exception as e:
            print(f"❌ Error encoding clip state: {e}")
            return None

    @staticmethod
    def encode_track_color_full_rgb(track, color):
        """
        Encode track color with FULL RGB (14-bit)

        Args:
            track (int): Track index
            color (tuple): RGB tuple (0-255, 0-255, 0-255)

        Returns:
            list: SysEx message

        Payload format:
            [track, r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]
            Total: 7 bytes
        """
        try:
            r, g, b = color if isinstance(color, (list, tuple)) and len(color) >= 3 else (127, 127, 127)

            rgb_encoded = ColorEncoder.encode_rgb_14bit(r, g, b)

            payload = [track] + rgb_encoded
            return SysExEncoderEnhanced.create_sysex(CMD_TRACK_COLOR, payload)

        except Exception as e:
            print(f"❌ Error encoding track color: {e}")
            return None

    @staticmethod
    def encode_neotrellis_clip_grid_full_rgb(grid_data):
        """
        Encode NeoTrellis 8x4 clip grid with FULL RGB colors

        Args:
            grid_data (list): 32 RGB color tuples (r, g, b)

        Returns:
            list: SysEx message

        Payload format:
            32 clips × 6 bytes (14-bit RGB) = 192 bytes

        WARNING: Large message! Consider splitting if needed.
        """
        try:
            # Ensure we have exactly 32 values
            while len(grid_data) < 32:
                grid_data.append((0, 0, 0))
            grid_data = grid_data[:32]

            payload = []
            for r, g, b in grid_data:
                payload.extend(ColorEncoder.encode_rgb_14bit(r, g, b))

            # Total payload: 192 bytes (32 clips × 6 bytes)
            return SysExEncoderEnhanced.create_sysex(CMD_NEOTRELLIS_CLIP_GRID, payload)

        except Exception as e:
            print(f"❌ Error encoding NeoTrellis grid: {e}")
            return None

    @staticmethod
    def encode_grid_update_full_rgb(grid_data):
        """
        Encode full 8x4 grid update with FULL RGB (CMD_GRID_UPDATE)
        Optimized version for bulk updates

        Args:
            grid_data (list): 32 RGB tuples [(r, g, b), ...]

        Returns:
            list: SysEx message
        """
        try:
            while len(grid_data) < 32:
                grid_data.append((0, 0, 0))
            grid_data = grid_data[:32]

            payload = []
            for r, g, b in grid_data:
                payload.extend(ColorEncoder.encode_rgb_14bit(r, g, b))

            return SysExEncoderEnhanced.create_sysex(CMD_GRID_UPDATE, payload)

        except Exception as e:
            print(f"❌ Error encoding grid update: {e}")
            return None

    @staticmethod
    def encode_single_pad_full_rgb(pad_index, r, g, b):
        """
        Encode single pad color update with FULL RGB (CMD_GRID_SINGLE_PAD)
        Most efficient for individual pad updates

        Args:
            pad_index (int): Pad index 0-31
            r, g, b (int): RGB values 0-255

        Returns:
            list: SysEx message

        Payload format:
            [pad_index, r_msb, r_lsb, g_msb, g_lsb, b_msb, b_lsb]
            Total: 7 bytes (very efficient!)
        """
        try:
            rgb_encoded = ColorEncoder.encode_rgb_14bit(r, g, b)
            payload = [pad_index] + rgb_encoded

            return SysExEncoderEnhanced.create_sysex(CMD_GRID_SINGLE_PAD, payload)

        except Exception as e:
            print(f"❌ Error encoding single pad: {e}")
            return None

    # ========================================
    # BACKWARD COMPATIBILITY
    # ========================================

    @staticmethod
    def encode_clip_state_compact(track, scene, state, color):
        """
        Encode clip state with compact RGB (7-bit, backward compatible)
        Use when bandwidth is critical
        """
        try:
            r, g, b = color if isinstance(color, (list, tuple)) and len(color) >= 3 else (127, 127, 127)

            # Use compact encoding (7-bit)
            rgb_encoded = ColorEncoder.encode_rgb_compact(r, g, b)

            payload = [track, scene, state] + rgb_encoded
            return SysExEncoderEnhanced.create_sysex(CMD_CLIP_STATE, payload)

        except Exception as e:
            print(f"❌ Error encoding clip state (compact): {e}")
            return None


# ========================================
# USAGE EXAMPLES
# ========================================

"""
EXAMPLE 1: Full RGB Clip State
-------------------------------
# Live side:
color = (220, 180, 145)  # Full RGB from Live
message = SysExEncoderEnhanced.encode_clip_state_full_rgb(0, 0, CLIP_PLAYING, color)
send_midi(message)

# Hardware side (Teensy):
void handleClipState(uint8_t* data, uint8_t len) {
    uint8_t track = data[0];
    uint8_t scene = data[1];
    uint8_t state = data[2];

    // Decode 14-bit RGB
    uint8_t r = (data[3] << 7) | data[4];  // 0-255
    uint8_t g = (data[5] << 7) | data[6];
    uint8_t b = (data[7] << 7) | data[8];

    // Set NeoPixel with FULL color!
    int padIndex = scene * 4 + track;
    neoPixels.setPixelColor(padIndex, r, g, b);
    neoPixels.show();
}


EXAMPLE 2: Single Pad Update
-----------------------------
# Live side:
message = SysExEncoderEnhanced.encode_single_pad_full_rgb(15, 255, 128, 64)
send_midi(message)

# Hardware side:
void handleSinglePad(uint8_t* data, uint8_t len) {
    uint8_t pad = data[0];
    uint8_t r = (data[1] << 7) | data[2];
    uint8_t g = (data[3] << 7) | data[4];
    uint8_t b = (data[5] << 7) | data[6];

    neoPixels.setPixelColor(pad, r, g, b);
    neoPixels.show();
}


EXAMPLE 3: Full Grid Update
----------------------------
# Live side:
grid = []
for track_idx in range(4):
    for scene_idx in range(8):
        clip_color = get_clip_color(track_idx, scene_idx)
        grid.append(clip_color)  # (r, g, b) tuples

message = SysExEncoderEnhanced.encode_grid_update_full_rgb(grid)
send_midi(message)

# Hardware side:
void handleGridUpdate(uint8_t* data, uint8_t len) {
    // Expect 192 bytes (32 pads × 6 bytes each)
    for (int pad = 0; pad < 32; pad++) {
        int offset = pad * 6;
        uint8_t r = (data[offset + 0] << 7) | data[offset + 1];
        uint8_t g = (data[offset + 2] << 7) | data[offset + 3];
        uint8_t b = (data[offset + 4] << 7) | data[offset + 5];

        neoPixels.setPixelColor(pad, r, g, b);
    }
    neoPixels.show();
}
"""

# MIDIUtils.py - EXTENDED VERSION (agregar estos métodos)
from .consts import *

class SysExEncoder:
    """Handles encoding of binary data into MIDI SysEx messages"""
    
    # ========================================
    # TUS MÉTODOS EXISTENTES (mantener como están)
    # ========================================
    
    @staticmethod
    def create_sysex(command, payload):
        """Create a complete SysEx message with header, command, payload and checksum"""
        try:
            # Start with SysEx header
            message = list(SYSEX_HEADER)
            
            # Add command byte
            message.append(command)
            
            # Add payload length
            payload_len = len(payload) if payload else 0
            message.append(payload_len)
            
            # Add payload data
            if payload:
                message.extend(payload)
            
            # Add simple checksum (XOR of command and payload)
            checksum = command
            if payload:
                for byte in payload:
                    checksum ^= byte
            message.append(checksum & 0x7F)  # Keep in 7-bit MIDI range
            
            # Add SysEx end byte
            message.append(SYSEX_END)
            
            return message
            
        except Exception as e:
            print(f"❌ Error creating SysEx: {e}")
            return None

    @staticmethod
    def encode_clip_state(track, scene, state, color):
        """Encode clip state message"""
        try:
            r, g, b = color if isinstance(color, (list, tuple)) and len(color) >= 3 else (127, 127, 127)
            
            # Ensure RGB values are in MIDI range (0-127)
            r = min(127, max(0, int(r // 2)))  # Convert from 0-255 to 0-127
            g = min(127, max(0, int(g // 2)))
            b = min(127, max(0, int(b // 2)))
            
            payload = [track, scene, state, r, g, b]
            return SysExEncoder.create_sysex(CMD_CLIP_STATE, payload)
            
        except Exception as e:
            print(f"❌ Error encoding clip state: {e}")
            return None

    @staticmethod
    def encode_track_color(track, color):
        """Encode track color message"""
        try:
            r, g, b = color if isinstance(color, (list, tuple)) and len(color) >= 3 else (127, 127, 127)
            
            # Ensure RGB values are in MIDI range (0-127)
            r = min(127, max(0, int(r // 2)))  # Convert from 0-255 to 0-127
            g = min(127, max(0, int(g // 2)))
            b = min(127, max(0, int(b // 2)))
            
            payload = [track, r, g, b]
            return SysExEncoder.create_sysex(CMD_TRACK_COLOR, payload)
            
        except Exception as e:
            print(f"❌ Error encoding track color: {e}")
            return None

    @staticmethod
    def encode_transport(playing, beat, bar):
        """Encode transport state message"""
        try:
            playing_byte = 1 if playing else 0
            beat_byte = int(beat) & 0x7F  # Keep in 7-bit range
            bar_byte = int(bar) & 0x7F
            
            payload = [playing_byte, beat_byte, bar_byte]
            return SysExEncoder.create_sysex(CMD_TRANSPORT, payload)
            
        except Exception as e:
            print(f"❌ Error encoding transport: {e}")
            return None

    @staticmethod
    def log_sysex(message, direction="OUT"):
        """Log SysEx message for debugging"""
        try:
            if not message:
                print(f"❌ {direction}: Empty SysEx message")
                return
                
            hex_string = " ".join([f"{b:02X}" for b in message])
            command = message[4] if len(message) > 4 else 0x00
            length = len(message)
            
            print(f"🔌 {direction}: CMD:{command:02X} LEN:{length} DATA:[{hex_string}]")
            
        except Exception as e:
            print(f"❌ Error logging SysEx: {e}")
    
    # ========================================
    # NUEVOS MÉTODOS PARA AGREGAR
    # ========================================
    
    @staticmethod
    def encode_mixer_channel(track, volume, pan, sends, flags):
        """
        Encode mixer channel state
        Args:
            track (int): Track index (0-7)
            volume (int): Volume 0-127
            pan (int): Pan 0-127 (64=center)
            sends (list): Send levels [A, B, C] 0-127 each
            flags (int): Packed flags (mute=0x01, solo=0x02, arm=0x04)
        Returns:
            list: SysEx message
        """
        # Ensure sends has exactly 3 values
        while len(sends) < 3:
            sends.append(0)
        sends = sends[:3]  # Take only first 3
        
        payload = [track, volume, pan] + sends + [flags]
        return SysExEncoder.create_sysex(CMD_MIXER_STATE, payload)
    
    @staticmethod
    def encode_device_list(track, devices_info):
        """
        Encode device list for track
        Args:
            track (int): Track index (0-7)
            devices_info (list): List of device info dicts
                Each dict: {'name': str, 'enabled': bool, 'index': int}
        Returns:
            list: SysEx message
        """
        payload = [track, len(devices_info)]
        
        for device in devices_info[:8]:  # Max 8 devices
            name_bytes = device['name'].encode('utf-8')[:10]  # Max 10 chars
            
            payload.extend([
                device['index'],
                len(name_bytes),
                1 if device['enabled'] else 0
            ])
            payload.extend(list(name_bytes))
        
        return SysExEncoder.create_sysex(CMD_DEVICE_LIST, payload)
    
    @staticmethod
    def encode_device_params(track, device, page, total_pages, params_info):
        """
        Encode device parameters for specific page
        Args:
            track (int): Track index
            device (int): Device index
            page (int): Current page (0-based)
            total_pages (int): Total number of pages
            params_info (list): List of 8 parameter dicts
                Each dict: {'index': int, 'value': int 0-127, 'name': str}
                Use {'index': 0xFF} for empty slots
        Returns:
            list: SysEx message
        """
        payload = [track, device, page, total_pages]
        
        # Always send exactly 8 parameters
        for i in range(8):
            if i < len(params_info):
                param = params_info[i]
                if param['index'] != 0xFF:  # Valid parameter
                    name_bytes = param['name'].encode('utf-8')[:8]
                    payload.extend([
                        param['index'],
                        param['value'],
                        len(name_bytes)
                    ])
                    payload.extend(list(name_bytes))
                else:  # Empty parameter
                    payload.extend([0xFF, 0, 0])
            else:  # No parameter data
                payload.extend([0xFF, 0, 0])
        
        return SysExEncoder.create_sysex(CMD_DEVICE_PARAMS, payload)
    
    @staticmethod
    def encode_param_value(track, device, param, value, display_str):
        """
        Encode individual parameter value with display string
        Args:
            track (int): Track index
            device (int): Device index  
            param (int): Parameter index
            value (int): Parameter value 0-127
            display_str (str): Display string (e.g., "120 Hz", "50%")
        Returns:
            list: SysEx message
        """
        display_bytes = display_str.encode('utf-8')[:10]  # Max 10 chars
        
        payload = [track, device, param, value, len(display_bytes)]
        payload.extend(list(display_bytes))
        
        return SysExEncoder.create_sysex(CMD_PARAM_VALUE, payload)
    
    @staticmethod
    def encode_scale_info(root_note, scale_id):
        """
        Encode scale and root note information
        Args:
            root_note (int): Root note 0-11 (C=0)
            scale_id (int): Scale ID (Major=0, Minor=1, etc.)
        Returns:
            list: SysEx message
        """
        payload = [root_note, scale_id]
        return SysExEncoder.create_sysex(CMD_SCALE_INFO, payload)
    
    @staticmethod
    def encode_octave_info(octave):
        """
        Encode octave information
        Args:
            octave (int): Current octave (0-8)
        Returns:
            list: SysEx message
        """
        payload = [octave]
        return SysExEncoder.create_sysex(CMD_OCTAVE_INFO, payload)
    
    @staticmethod
    def encode_track_instrument(track, has_instrument, is_drum_rack, instrument_name):
        """
        Encode track instrument information for note view
        Args:
            track (int): Track index
            has_instrument (bool): Track has instrument device
            is_drum_rack (bool): Instrument is drum rack
            instrument_name (str): Instrument device name
        Returns:
            list: SysEx message
        """
        name_bytes = instrument_name.encode('utf-8')[:10] if instrument_name else []
        
        payload = [
            track,
            1 if has_instrument else 0,
            1 if is_drum_rack else 0,
            len(name_bytes)
        ]
        payload.extend(list(name_bytes))
        
        return SysExEncoder.create_sysex(CMD_TRACK_INSTRUMENT, payload)
    
    @staticmethod
    def encode_view_switch(view_id):
        """
        Encode view switch command
        Args:
            view_id (int): View ID (0=clip, 1=mixer, 2=device, 3=note)
        Returns:
            list: SysEx message
        """
        payload = [view_id]
        return SysExEncoder.create_sysex(CMD_SWITCH_VIEW, payload)
    
    @staticmethod
    def encode_scene_state(scene, is_triggered):
        """
        Encode scene state
        Args:
            scene (int): Scene index
            is_triggered (bool): Scene is triggered/queued
        Returns:
            list: SysEx message
        """
        payload = [scene, 1 if is_triggered else 0]
        return SysExEncoder.create_sysex(CMD_SCENE_STATE, payload)
    
    @staticmethod
    def encode_neotrellis_grid(track, device, grid_data):
        """
        Encode NeoTrellis 4x8 drum grid
        Args:
            track (int): Track index
            device (int): Device index
            grid_data (list): 32 color values (0=empty, 1=loaded, 2=active, 3=selected)
        Returns:
            list: SysEx message
        """
        # Ensure we have exactly 32 values
        while len(grid_data) < 32:
            grid_data.append(0)
        grid_data = grid_data[:32]
        
        payload = [track, device] + grid_data
        return SysExEncoder.create_sysex(CMD_NEOTRELLIS_GRID, payload)

# ========================================
# ColorUtils CLASS (tu clase existente es perfecta)
# ========================================

class ColorUtils:
    """Color conversion utilities"""
    
    @staticmethod
    def live_color_to_rgb(live_color):
        """
        Convert Live color value to RGB tuple
        Args:
            live_color: Live color index or value
        Returns:
            tuple: (r, g, b) values 0-255
        """
        try:
            # Live color mapping (from consts.py)
            from .consts import LIVE_COLORS, DEFAULT_TRACK_COLORS
            
            # If it's an integer, use it as index into LIVE_COLORS
            if isinstance(live_color, int):
                if live_color in LIVE_COLORS:
                    return LIVE_COLORS[live_color]
                else:
                    # Use modulo to wrap around available colors
                    color_idx = live_color % len(DEFAULT_TRACK_COLORS)
                    return DEFAULT_TRACK_COLORS[color_idx]
            
            # If it's already a tuple/list, return as is
            elif isinstance(live_color, (tuple, list)) and len(live_color) >= 3:
                return (int(live_color[0]), int(live_color[1]), int(live_color[2]))
            
            # Default fallback color (white)
            else:
                return (255, 255, 255)
                
        except Exception as e:
            print(f"❌ Error converting Live color: {e}")
            return (127, 127, 127)  # Gray fallback
    
    @staticmethod
    def get_track_default_color(track_index):
        """
        Get default color for track by index
        Args:
            track_index (int): Track index
        Returns:
            tuple: (r, g, b) values 0-255
        """
        try:
            from .consts import DEFAULT_TRACK_COLORS
            color_idx = track_index % len(DEFAULT_TRACK_COLORS)
            return DEFAULT_TRACK_COLORS[color_idx]
        except:
            return (127, 127, 127)
    
    @staticmethod
    def get_clip_state_color(state, track_color):
        """
        Calculate clip LED color based on state and track color
        Args:
            state (int): Clip state (CLIP_EMPTY, CLIP_PLAYING, etc.)
            track_color (tuple): Base track RGB color
        Returns:
            tuple: Final RGB color for clip LED
        """
        try:
            from .consts import CLIP_EMPTY, CLIP_PLAYING, CLIP_QUEUED, CLIP_RECORDING
            
            r, g, b = track_color
            
            if state == CLIP_EMPTY:
                # Empty = very dim
                return (r // 8, g // 8, b // 8)
            elif state == CLIP_PLAYING:
                # Playing = full brightness
                return (r, g, b)
            elif state == CLIP_QUEUED:
                # Queued = pulsing bright
                return (min(255, r + 50), min(255, g + 50), min(255, b + 50))
            elif state == CLIP_RECORDING:
                # Recording = red overlay
                return (min(255, r + 100), g // 2, b // 2)
            else:
                # Unknown state = half brightness
                return (r // 2, g // 2, b // 2)
                
        except Exception as e:
            print(f"❌ Error calculating clip state color: {e}")
            return (127, 127, 127)
    
    # ========================================
    # NUEVOS MÉTODOS (los que ya tienes implementados)
    # ========================================
    
    @staticmethod
    def get_mixer_led_color(track_color, is_mute, is_solo, is_arm):
        """
        Calculate LED color for mixer channel based on state
        Args:
            track_color (tuple): Base track RGB color
            is_mute (bool): Track is muted
            is_solo (bool): Track is solo
            is_arm (bool): Track is armed for recording
        Returns:
            tuple: Final RGB color for LED
        """
        r, g, b = track_color
        
        if is_mute:
            # Muted = very dim
            return (r // 8, g // 8, b // 8)
        elif is_solo:
            # Solo = bright yellow overlay
            return (min(255, r + 100), min(255, g + 100), 0)
        elif is_arm:
            # Armed = red overlay
            return (min(255, r + 100), g // 2, b // 2)
        else:
            # Normal = full track color
            return (r, g, b)
    
    @staticmethod
    def get_device_led_color(is_enabled, is_selected):
        """
        Calculate LED color for device state
        Args:
            is_enabled (bool): Device is enabled
            is_selected (bool): Device is currently selected
        Returns:
            tuple: RGB color for device LED
        """
        if is_selected and is_enabled:
            return (0, 255, 100)  # Bright green = selected & enabled
        elif is_selected:
            return (255, 100, 0)  # Orange = selected but disabled
        elif is_enabled:
            return (100, 100, 255)  # Blue = enabled but not selected
        else:
            return (50, 50, 50)   # Dim gray = disabled
    
    @staticmethod
    def get_note_pad_color(note, current_scale, root_note, is_playing):
        """
        Calculate LED color for note pad based on scale and state
        Args:
            note (int): MIDI note number
            current_scale (list): Scale intervals [0, 2, 4, 5, 7, 9, 11]
            root_note (int): Root note (0-11, C=0)
            is_playing (bool): Note is currently playing
        Returns:
            tuple: RGB color for note pad
        """
        # Check if note is in current scale
        note_in_scale = (note - root_note) % 12 in current_scale
        
        if is_playing:
            return (255, 255, 255)  # White = playing
        elif note_in_scale:
            return (100, 255, 100)  # Green = in scale
        else:
            return (50, 50, 100)    # Dim blue = out of scale
    
    @staticmethod
    def get_transport_led_color(is_playing, is_recording, is_loop):
        """
        Calculate LED color for transport buttons
        Args:
            is_playing (bool): Transport is playing
            is_recording (bool): Recording is enabled
            is_loop (bool): Loop is enabled
        Returns:
            dict: Colors for each transport button
        """
        return {
            'play': (0, 255, 0) if is_playing else (50, 50, 50),      # Green/dim
            'record': (255, 0, 0) if is_recording else (50, 50, 50),  # Red/dim
            'loop': (255, 255, 0) if is_loop else (50, 50, 50)        # Yellow/dim
        }
    
    @staticmethod
    def get_drum_pad_color(pad_state):
        """
        Calculate LED color for drum pad state
        Args:
            pad_state (int): 0=empty, 1=loaded, 2=active, 3=selected
        Returns:
            tuple: RGB color for drum pad LED
        """
        colors = {
            0: (10, 10, 10),      # Empty - very dim
            1: (100, 100, 50),    # Loaded - yellow dim
            2: (255, 255, 100),   # Active - yellow bright  
            3: (255, 100, 255)    # Selected - magenta bright
        }
        return colors.get(pad_state, (50, 50, 50))
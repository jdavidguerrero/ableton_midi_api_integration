# NoteViewManager.py - Enhanced Note View with Drum/Melodic modes
"""
Manages Note View functionality with differentiated drum and melodic modes
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class NoteViewManager:
    """
    Manages Note View with drum and melodic mode support
    - Drum mode: 4x4 drum pads with samples
    - Melodic mode: Scale-based note layout
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        
        # Note view modes
        self._current_mode = "melodic"  # "drum" or "melodic"
        self._auto_detect = True  # Auto-detect mode based on selected track
        
        # Melodic mode settings
        self._current_scale = "Minor"
        self._current_root = 0  # C = 0
        self._current_octave = 4
        self._key_layout = "chromatic"  # "chromatic", "in_key", "circle_fifths"
        
        # Drum mode settings
        self._drum_note_offset = 36  # C2 (standard drum mapping)
        self._selected_drum_pad = 0
        self._drum_velocity_levels = [32, 64, 96, 127]  # 4 velocity levels
        self._current_velocity_level = 2  # Index into velocity levels
        
        # Grid layout (4x8 = 32 pads)
        self._grid_width = 8
        self._grid_height = 4
        self._total_pads = 32
        
        # Note state tracking
        self._playing_notes = set()  # Currently playing notes
        self._note_colors = {}  # Note -> color mapping
        
        # Listeners
        self._is_active = False
        self._listeners = []
        
    def setup_listeners(self):
        """Setup note view listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("🎹 Setting up Note View listeners...")
            
            # Track selection changes (for auto mode detection)
            track_listener = lambda: self._on_selected_track_changed()
            self.song.view.add_selected_track_listener(track_listener)
            self._listeners.append(('selected_track', track_listener))
            
            # Device selection changes (for drum rack detection)
            device_listener = lambda: self._on_selected_device_changed()
            self.song.view.add_selected_device_listener(device_listener)
            self._listeners.append(('selected_device', device_listener))
            
            # Initialize mode based on current selection
            self._detect_and_set_mode()
            
            self._is_active = True
            self.c_surface.log_message("✅ Note View listeners setup")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up note view listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all note view listeners"""
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 'selected_track':
                        self.song.view.remove_selected_track_listener(listener_func)
                    elif listener_type == 'selected_device':
                        self.song.view.remove_selected_device_listener(listener_func)
                except:
                    pass
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Note View listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning note view listeners: {e}")
    
    # ========================================
    # MODE DETECTION AND SWITCHING
    # ========================================
    
    def _on_selected_track_changed(self):
        """Handle track selection changes"""
        if self._auto_detect and self.c_surface._is_connected:
            self._detect_and_set_mode()
    
    def _on_selected_device_changed(self):
        """Handle device selection changes"""
        if self._auto_detect and self.c_surface._is_connected:
            self._detect_and_set_mode()
    
    def _detect_and_set_mode(self):
        """Auto-detect and set appropriate note view mode"""
        try:
            selected_track = self.song.view.selected_track
            
            if not selected_track:
                return
                
            # Check if track has a drum rack
            has_drum_rack = False
            selected_device = None
            
            try:
                selected_device = self.song.view.selected_device
                if selected_device:
                    has_drum_rack = (hasattr(selected_device, 'can_have_drum_pads') and 
                                   selected_device.can_have_drum_pads)
            except:
                pass
            
            # Also check for instruments that suggest drum mode
            if not has_drum_rack and selected_device:
                device_name = getattr(selected_device, 'name', '').lower()
                drum_keywords = ['drum', 'kit', 'percussion', 'beat', 'rhythm']
                has_drum_rack = any(keyword in device_name for keyword in drum_keywords)
            
            # Set mode based on detection
            new_mode = "drum" if has_drum_rack else "melodic"
            
            if new_mode != self._current_mode:
                self.c_surface.log_message(
                    f"🎯 Auto-detected mode change: {self._current_mode} → {new_mode}"
                )
                self._set_mode(new_mode, auto_detected=True)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error detecting note view mode: {e}")
    
    def set_mode(self, mode):
        """Manually set note view mode"""
        self._auto_detect = False  # Disable auto-detection
        self._set_mode(mode, auto_detected=False)
    
    def _set_mode(self, mode, auto_detected=False):
        """Internal mode setting"""
        try:
            if mode not in ["drum", "melodic"]:
                return False
                
            old_mode = self._current_mode
            self._current_mode = mode
            
            detection_str = "(auto)" if auto_detected else "(manual)"
            self.c_surface.log_message(f"🎼 Note View mode: {old_mode} → {mode} {detection_str}")
            
            # Send mode change to hardware
            mode_id = 1 if mode == "drum" else 0
            self.c_surface._send_sysex_command(CMD_NOTE_VIEW_MODE, [mode_id])
            
            # Update grid layout
            self._send_complete_note_grid()
            
            # Send mode-specific configuration
            if mode == "drum":
                self._send_drum_config()
            else:
                self._send_scale_config()
            
            return True
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting note view mode: {e}")
            return False
    
    def toggle_auto_detect(self):
        """Toggle auto-detection of note view mode"""
        self._auto_detect = not self._auto_detect
        
        self.c_surface.log_message(
            f"🔍 Note View auto-detect: {'ON' if self._auto_detect else 'OFF'}"
        )
        
        if self._auto_detect:
            self._detect_and_set_mode()
        
        # Send auto-detect state to hardware
        self.c_surface._send_sysex_command(CMD_NOTE_AUTO_DETECT, [1 if self._auto_detect else 0])
    
    # ========================================
    # GRID LAYOUT AND COLORS
    # ========================================
    
    def _send_complete_note_grid(self):
        """Send complete note grid based on current mode"""
        try:
            if not self.c_surface._is_connected:
                return
                
            if self._current_mode == "drum":
                self._send_drum_grid()
            else:
                self._send_melodic_grid()
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending note grid: {e}")
    
    def _send_drum_grid(self):
        """Send drum mode grid (4x8 = 32 pads)"""
        try:
            selected_device = self.song.view.selected_device
            grid_colors = []
            
            for pad_idx in range(self._total_pads):
                color = self._get_drum_pad_color(pad_idx, selected_device)
                # Convert to RGB for hardware
                r, g, b = color
                grid_colors.extend([r >> 1, g >> 1, b >> 1])  # Convert to 7-bit
            
            # Send drum grid
            self.c_surface._send_sysex_command(CMD_NOTE_DRUM_GRID, grid_colors)\n            \n            # Also send drum pad info\n            self._send_drum_pad_info(selected_device)\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error sending drum grid: {e}\")\n    \n    def _send_melodic_grid(self):\n        \"\"\"Send melodic mode grid based on scale\"\"\"\n        try:\n            grid_colors = []\n            scale_notes = self._get_scale_notes()\n            \n            for pad_idx in range(self._total_pads):\n                note = self._get_melodic_note_for_pad(pad_idx)\n                color = self._get_melodic_pad_color(note, scale_notes)\n                \n                # Convert to RGB for hardware\n                r, g, b = color\n                grid_colors.extend([r >> 1, g >> 1, b >> 1])  # Convert to 7-bit\n            \n            # Send melodic grid\n            self.c_surface._send_sysex_command(CMD_NOTE_MELODIC_GRID, grid_colors)\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error sending melodic grid: {e}\")\n    \n    def _get_drum_pad_color(self, pad_idx, device):\n        \"\"\"Get color for drum pad based on state\"\"\"\n        try:\n            if not device or not hasattr(device, 'drum_pads'):\n                return (30, 30, 30)  # Dim gray for no device\n                \n            drum_note = self._drum_note_offset + pad_idx\n            \n            # Check if pad has content\n            if (drum_note < len(device.drum_pads) and \n                device.drum_pads[drum_note] is not None):\n                \n                drum_pad = device.drum_pads[drum_note]\n                \n                # Check if pad is selected\n                if (hasattr(device, 'view') and \n                    hasattr(device.view, 'selected_drum_pad') and\n                    device.view.selected_drum_pad == drum_pad):\n                    return (255, 100, 255)  # Magenta for selected\n                \n                # Check if pad is playing\n                if drum_note in self._playing_notes:\n                    return (255, 255, 255)  # White for playing\n                \n                # Check pad properties\n                if hasattr(drum_pad, 'chains') and drum_pad.chains:\n                    # Has sample/chains - use velocity-based color\n                    velocity_color = self._get_velocity_color(self._current_velocity_level)\n                    return velocity_color\n                else:\n                    return (100, 100, 50)  # Yellow dim for empty pad\n            else:\n                return (20, 20, 20)  # Very dim for no pad\n                \n        except Exception as e:\n            return (50, 50, 50)  # Gray fallback\n    \n    def _get_melodic_pad_color(self, note, scale_notes):\n        \"\"\"Get color for melodic pad based on scale and state\"\"\"\n        try:\n            # Check if note is playing\n            if note in self._playing_notes:\n                return (255, 255, 255)  # White for playing\n            \n            # Check if note is in current scale\n            note_in_scale = (note % 12) in [n % 12 for n in scale_notes]\n            \n            if note_in_scale:\n                # In scale - use root/chord colors\n                interval = (note - self._current_root) % 12\n                if interval == 0:  # Root note\n                    return (255, 100, 100)  # Red for root\n                elif interval in [2, 4, 7, 9, 11]:  # Chord tones (approximate)\n                    return (100, 255, 100)  # Green for chord tones\n                else:\n                    return (100, 200, 255)  # Blue for scale notes\n            else:\n                # Out of scale - dim\n                return (50, 50, 100)  # Dim blue for chromatic\n                \n        except Exception as e:\n            return (75, 75, 75)  # Gray fallback\n    \n    def _get_velocity_color(self, level_idx):\n        \"\"\"Get color based on velocity level\"\"\"\n        velocity = self._drum_velocity_levels[level_idx]\n        \n        if velocity >= 127:\n            return (255, 100, 100)  # Red for max\n        elif velocity >= 96:\n            return (255, 200, 100)  # Orange for high\n        elif velocity >= 64:\n            return (255, 255, 100)  # Yellow for medium\n        else:\n            return (100, 255, 100)  # Green for low\n    \n    # ========================================\n    # SCALE AND NOTE CALCULATIONS\n    # ========================================\n    \n    def _get_scale_notes(self):\n        \"\"\"Get notes in current scale\"\"\"\n        try:\n            from .consts import SCALES\n            scale_intervals = SCALES.get(self._current_scale, [0, 2, 4, 5, 7, 9, 11])\n            \n            # Generate scale notes for current octave range\n            scale_notes = []\n            for octave in range(self._current_octave - 1, self._current_octave + 3):\n                for interval in scale_intervals:\n                    note = self._current_root + interval + (octave * 12)\n                    if 0 <= note <= 127:  # Valid MIDI range\n                        scale_notes.append(note)\n            \n            return sorted(scale_notes)\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error getting scale notes: {e}\")\n            return [60, 62, 64, 65, 67, 69, 71, 72]  # C major fallback\n    \n    def _get_melodic_note_for_pad(self, pad_idx):\n        \"\"\"Get MIDI note for melodic pad based on layout\"\"\"\n        try:\n            if self._key_layout == \"chromatic\":\n                # Chromatic layout: each pad is next semitone\n                base_note = self._current_root + (self._current_octave * 12)\n                return base_note + pad_idx\n                \n            elif self._key_layout == \"in_key\":\n                # In-key layout: only scale notes\n                scale_notes = self._get_scale_notes()\n                if pad_idx < len(scale_notes):\n                    return scale_notes[pad_idx]\n                else:\n                    return scale_notes[-1] + (pad_idx - len(scale_notes) + 1)\n                    \n            elif self._key_layout == \"circle_fifths\":\n                # Circle of fifths layout (advanced)\n                base_note = self._current_root + (self._current_octave * 12)\n                # This is a simplified circle of fifths - could be enhanced\n                fifth_interval = 7\n                return base_note + ((pad_idx * fifth_interval) % 12) + ((pad_idx // 12) * 12)\n                \n            else:\n                # Default to chromatic\n                base_note = self._current_root + (self._current_octave * 12)\n                return base_note + pad_idx\n                \n        except Exception as e:\n            return 60 + pad_idx  # Fallback starting from C4\n    \n    # ========================================\n    # NOTE HANDLING\n    # ========================================\n    \n    def handle_note_on(self, pad_idx, velocity=None):\n        \"\"\"Handle note on from hardware\"\"\"\n        try:\n            if self._current_mode == \"drum\":\n                note = self._drum_note_offset + pad_idx\n                note_velocity = velocity or self._drum_velocity_levels[self._current_velocity_level]\n            else:\n                note = self._get_melodic_note_for_pad(pad_idx)\n                note_velocity = velocity or 100\n            \n            # Clamp to valid MIDI range\n            if 0 <= note <= 127:\n                self._playing_notes.add(note)\n                \n                # Send MIDI note to Live\n                self.c_surface._send_midi((0x90, note, note_velocity))\n                \n                self.c_surface.log_message(\n                    f\"🎹 Note ON: pad={pad_idx}, note={note}, vel={note_velocity} ({self._current_mode})\"\n                )\n                \n                # Update grid to show playing note\n                self._send_complete_note_grid()\n                \n                return True\n            \n            return False\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error handling note on: {e}\")\n            return False\n    \n    def handle_note_off(self, pad_idx):\n        \"\"\"Handle note off from hardware\"\"\"\n        try:\n            if self._current_mode == \"drum\":\n                note = self._drum_note_offset + pad_idx\n            else:\n                note = self._get_melodic_note_for_pad(pad_idx)\n            \n            # Clamp to valid MIDI range\n            if 0 <= note <= 127:\n                self._playing_notes.discard(note)\n                \n                # Send MIDI note off to Live\n                self.c_surface._send_midi((0x80, note, 0))\n                \n                self.c_surface.log_message(\n                    f\"🎹 Note OFF: pad={pad_idx}, note={note} ({self._current_mode})\"\n                )\n                \n                # Update grid to remove playing indication\n                self._send_complete_note_grid()\n                \n                return True\n            \n            return False\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error handling note off: {e}\")\n            return False\n    \n    # ========================================\n    # CONFIGURATION METHODS\n    # ========================================\n    \n    def set_scale(self, root_note, scale_name):\n        \"\"\"Set scale for melodic mode\"\"\"\n        try:\n            from .consts import SCALES\n            \n            if scale_name in SCALES:\n                self._current_root = root_note % 12\n                self._current_scale = scale_name\n                \n                note_names = [\"C\", \"C#\", \"D\", \"D#\", \"E\", \"F\", \"F#\", \"G\", \"G#\", \"A\", \"A#\", \"B\"]\n                root_name = note_names[self._current_root]\n                \n                self.c_surface.log_message(f\"🎵 Scale: {root_name} {scale_name}\")\n                \n                # Send scale info to hardware\n                self._send_scale_config()\n                \n                # Update grid if in melodic mode\n                if self._current_mode == \"melodic\":\n                    self._send_complete_note_grid()\n                \n                return True\n            \n            return False\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error setting scale: {e}\")\n            return False\n    \n    def set_octave(self, octave):\n        \"\"\"Set octave for melodic mode\"\"\"\n        try:\n            self._current_octave = max(0, min(9, octave))\n            \n            self.c_surface.log_message(f\"🎵 Octave: {self._current_octave}\")\n            \n            # Send octave info to hardware\n            self.c_surface._send_sysex_command(CMD_NOTE_OCTAVE, [self._current_octave])\n            \n            # Update grid if in melodic mode\n            if self._current_mode == \"melodic\":\n                self._send_complete_note_grid()\n            \n            return True\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error setting octave: {e}\")\n            return False\n    \n    def set_velocity_level(self, level_idx):\n        \"\"\"Set velocity level for drum mode\"\"\"\n        try:\n            if 0 <= level_idx < len(self._drum_velocity_levels):\n                self._current_velocity_level = level_idx\n                velocity = self._drum_velocity_levels[level_idx]\n                \n                self.c_surface.log_message(f\"🥁 Drum velocity level: {level_idx} (vel={velocity})\")\n                \n                # Send velocity level to hardware\n                self.c_surface._send_sysex_command(CMD_NOTE_VELOCITY_LEVEL, [level_idx, velocity])\n                \n                # Update grid colors if in drum mode\n                if self._current_mode == \"drum\":\n                    self._send_complete_note_grid()\n                \n                return True\n            \n            return False\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error setting velocity level: {e}\")\n            return False\n    \n    def set_key_layout(self, layout):\n        \"\"\"Set key layout for melodic mode\"\"\"\n        try:\n            if layout in [\"chromatic\", \"in_key\", \"circle_fifths\"]:\n                self._key_layout = layout\n                \n                self.c_surface.log_message(f\"🎹 Key layout: {layout}\")\n                \n                # Send layout info to hardware\n                layout_id = [\"chromatic\", \"in_key\", \"circle_fifths\"].index(layout)\n                self.c_surface._send_sysex_command(CMD_NOTE_KEY_LAYOUT, [layout_id])\n                \n                # Update grid if in melodic mode\n                if self._current_mode == \"melodic\":\n                    self._send_complete_note_grid()\n                \n                return True\n            \n            return False\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error setting key layout: {e}\")\n            return False\n    \n    # ========================================\n    # SEND CONFIGURATION METHODS\n    # ========================================\n    \n    def _send_scale_config(self):\n        \"\"\"Send scale configuration to hardware\"\"\"\n        try:\n            from .consts import SCALES\n            scale_names = list(SCALES.keys())\n            scale_id = scale_names.index(self._current_scale) if self._current_scale in scale_names else 0\n            \n            payload = [\n                self._current_root,\n                scale_id,\n                self._current_octave,\n                [\"chromatic\", \"in_key\", \"circle_fifths\"].index(self._key_layout)\n            ]\n            \n            self.c_surface._send_sysex_command(CMD_NOTE_SCALE_CONFIG, payload)\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error sending scale config: {e}\")\n    \n    def _send_drum_config(self):\n        \"\"\"Send drum configuration to hardware\"\"\"\n        try:\n            payload = [\n                self._drum_note_offset,\n                self._current_velocity_level,\n                self._drum_velocity_levels[self._current_velocity_level],\n                self._selected_drum_pad\n            ]\n            \n            self.c_surface._send_sysex_command(CMD_NOTE_DRUM_CONFIG, payload)\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error sending drum config: {e}\")\n    \n    def _send_drum_pad_info(self, device):\n        \"\"\"Send drum pad information to hardware\"\"\"\n        try:\n            if not device or not hasattr(device, 'drum_pads'):\n                return\n                \n            # Send info for first 16 pads (4x4 grid on hardware)\n            for pad_idx in range(min(16, self._total_pads)):\n                drum_note = self._drum_note_offset + pad_idx\n                \n                if (drum_note < len(device.drum_pads) and \n                    device.drum_pads[drum_note] is not None):\n                    \n                    drum_pad = device.drum_pads[drum_note]\n                    \n                    # Pack pad info\n                    name_bytes = getattr(drum_pad, 'name', f'Pad {pad_idx}').encode('utf-8')[:8]\n                    \n                    payload = [\n                        pad_idx,\n                        drum_note,\n                        len(name_bytes)\n                    ]\n                    payload.extend(list(name_bytes))\n                    \n                    # Pad flags\n                    flags = 0\n                    if hasattr(drum_pad, 'chains') and drum_pad.chains:\n                        flags |= 0x01  # Has sample\n                    if hasattr(drum_pad, 'mute') and drum_pad.mute:\n                        flags |= 0x02  # Muted\n                    if hasattr(drum_pad, 'solo') and drum_pad.solo:\n                        flags |= 0x04  # Solo\n                    \n                    payload.append(flags)\n                    \n                    self.c_surface._send_sysex_command(CMD_NOTE_DRUM_PAD_INFO, payload)\n                    \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error sending drum pad info: {e}\")\n    \n    # ========================================\n    # COMMAND HANDLING\n    # ========================================\n    \n    def handle_note_command(self, command, payload):\n        \"\"\"Handle note view commands from hardware\"\"\"\n        try:\n            if command == CMD_NOTE_ON and len(payload) >= 2:\n                pad_idx, velocity = payload[0], payload[1]\n                self.handle_note_on(pad_idx, velocity)\n                \n            elif command == CMD_NOTE_OFF and len(payload) >= 1:\n                pad_idx = payload[0]\n                self.handle_note_off(pad_idx)\n                \n            elif command == CMD_NOTE_VIEW_MODE and len(payload) >= 1:\n                mode = \"drum\" if payload[0] == 1 else \"melodic\"\n                self.set_mode(mode)\n                \n            elif command == CMD_NOTE_AUTO_DETECT:\n                self.toggle_auto_detect()\n                \n            elif command == CMD_SCALE_CHANGE and len(payload) >= 2:\n                root_note, scale_id = payload[0], payload[1]\n                from .consts import SCALES\n                scale_names = list(SCALES.keys())\n                if scale_id < len(scale_names):\n                    self.set_scale(root_note, scale_names[scale_id])\n                    \n            elif command == CMD_OCTAVE_CHANGE and len(payload) >= 1:\n                octave = payload[0]\n                self.set_octave(octave)\n                \n            elif command == CMD_NOTE_VELOCITY_LEVEL and len(payload) >= 1:\n                level = payload[0]\n                self.set_velocity_level(level)\n                \n            elif command == CMD_NOTE_KEY_LAYOUT and len(payload) >= 1:\n                layout_id = payload[0]\n                layouts = [\"chromatic\", \"in_key\", \"circle_fifths\"]\n                if layout_id < len(layouts):\n                    self.set_key_layout(layouts[layout_id])\n                    \n            else:\n                self.c_surface.log_message(f\"❓ Unknown note command: 0x{command:02X}\")\n                \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error handling note command 0x{command:02X}: {e}\")\n    \n    # ========================================\n    # PUBLIC INTERFACE\n    # ========================================\n    \n    def get_note_view_info(self):\n        \"\"\"Get current note view information\"\"\"\n        return {\n            'current_mode': self._current_mode,\n            'auto_detect': self._auto_detect,\n            'melodic': {\n                'scale': self._current_scale,\n                'root_note': self._current_root,\n                'octave': self._current_octave,\n                'key_layout': self._key_layout\n            },\n            'drum': {\n                'note_offset': self._drum_note_offset,\n                'velocity_level': self._current_velocity_level,\n                'velocity': self._drum_velocity_levels[self._current_velocity_level],\n                'selected_pad': self._selected_drum_pad\n            },\n            'playing_notes': list(self._playing_notes)\n        }\n    \n    def send_complete_state(self):\n        \"\"\"Send complete note view state\"\"\"\n        try:\n            if not self.c_surface._is_connected:\n                return\n                \n            self.c_surface.log_message(\"📡 Sending complete note view state...\")\n            \n            # Send mode and config\n            mode_id = 1 if self._current_mode == \"drum\" else 0\n            self.c_surface._send_sysex_command(CMD_NOTE_VIEW_MODE, [mode_id])\n            \n            if self._current_mode == \"drum\":\n                self._send_drum_config()\n            else:\n                self._send_scale_config()\n            \n            # Send complete grid\n            self._send_complete_note_grid()\n            \n            # Send auto-detect state\n            self.c_surface._send_sysex_command(CMD_NOTE_AUTO_DETECT, [1 if self._auto_detect else 0])\n            \n        except Exception as e:\n            self.c_surface.log_message(f\"❌ Error sending note view state: {e}\")
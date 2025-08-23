# PushClone.py - Complete Control Surface Orchestrator
from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

# Import all managers
from .SongManager import SongManager
from .TrackManager import TrackManager
from .ClipManager import ClipManager
from .DeviceManager import DeviceManager
from .TransportManager import TransportManager
from .BrowserManager import BrowserManager
from .AutomationManager import AutomationManager

class PushClone(ControlSurface):
    """
    Complete PushClone Control Surface Orchestrator
    
    Integrates all specialized managers for comprehensive Live API coverage:
    - SongManager: Tempo, signature, metronome, cue points
    - TrackManager: Tracks, mixer, routing
    - ClipManager: Clips, scenes, session matrix
    - DeviceManager: Devices, parameters, racks, drum pads
    - TransportManager: Transport, record, loop
    - BrowserManager: Navigation, selection, views
    - AutomationManager: Automation, quantization, undo/redo
    
    Provides bidirectional MIDI SysEx communication with hardware controller.
    """

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        
        # Connection state
        self._is_connected = False
        self._message_count = 0
        self._current_view = "clip"  # clip, mixer, device, note
        
        # Initialize all managers
        self._managers = {}
        self._initialize_managers()
        
        # Current selections and state
        self._current_track = 0
        self._current_device = 0
        self._current_param_page = 0
        self._current_scale = "Minor"
        self._current_root = 0  # C = 0
        self._current_octave = 4
        
        with self.component_guard():
            self.log_message("🚀 PushClone Orchestrator Loading...")
            self.show_message("PushClone: Initializing Complete API Coverage...")
            
            # Setup all managers
            self._setup_all_managers()
            
            # Send handshake
            self._send_handshake()
            
            self.log_message("✅ PushClone Orchestrator Ready - Full Live API Coverage Active")

    def disconnect(self):
        """Cleanup and disconnect"""
        self.log_message("👋 PushClone Orchestrator Disconnecting...")
        self._cleanup_all_managers()
        ControlSurface.disconnect(self)

    # ========================================
    # MANAGER INITIALIZATION
    # ========================================
    
    def _initialize_managers(self):
        """Initialize all specialized managers"""
        try:
            self.log_message("🔧 Initializing managers...")
            
            # Create all managers
            self._managers['song'] = SongManager(self)
            self._managers['track'] = TrackManager(self)
            self._managers['clip'] = ClipManager(self)
            self._managers['device'] = DeviceManager(self)
            self._managers['transport'] = TransportManager(self)
            self._managers['browser'] = BrowserManager(self)
            self._managers['automation'] = AutomationManager(self)
            
            self.log_message(f"✅ Initialized {len(self._managers)} managers")
            
        except Exception as e:
            self.log_message(f"❌ Error initializing managers: {e}")
    
    def _setup_all_managers(self):
        """Setup listeners for all managers"""
        try:
            self.log_message("🎛️ Setting up all manager listeners...")
            
            # Setup each manager with appropriate parameters
            self._managers['song'].setup_listeners()
            self._managers['track'].setup_listeners(max_tracks=8)
            self._managers['clip'].setup_listeners(max_tracks=8, max_scenes=8)
            self._managers['device'].setup_listeners(max_tracks=8, max_devices_per_track=8)
            self._managers['transport'].setup_listeners()
            self._managers['browser'].setup_listeners()
            self._managers['automation'].setup_listeners()
            
            self.log_message("✅ All managers setup complete")
            
        except Exception as e:
            self.log_message(f"❌ Error setting up managers: {e}")
    
    def _cleanup_all_managers(self):
        """Cleanup all managers"""
        try:
            self.log_message("🧹 Cleaning up all managers...")
            
            for manager_name, manager in self._managers.items():
                try:
                    manager.cleanup_listeners()
                    self.log_message(f"✅ Cleaned up {manager_name} manager")
                except Exception as e:
                    self.log_message(f"❌ Error cleaning {manager_name} manager: {e}")
            
            self.log_message("✅ All managers cleaned up")
            
        except Exception as e:
            self.log_message(f"❌ Error during manager cleanup: {e}")

    # ========================================
    # MIDI COMMUNICATION
    # ========================================
    
    def _send_handshake(self):
        """Send initial handshake to hardware"""
        try:
            # Create handshake SysEx message
            payload = [0x50, 0x43]  # "PC" for PushClone
            message = SysExEncoder.create_sysex(CMD_HANDSHAKE, payload)
            
            if message:
                self._send_midi(tuple(message))
                self.log_message("🤝 Handshake sent to hardware")
            else:
                self.log_message("❌ Failed to create handshake message")
                
        except Exception as e:
            self.log_message(f"❌ Error sending handshake: {e}")
    
    def _send_sysex_command(self, command, payload, silent=False):
        """Send SysEx command to hardware"""
        try:
            message = SysExEncoder.create_sysex(command, payload)
            if message:
                self._send_midi(tuple(message))
                # Log SysEx for debugging (only if not silent)
                if not silent and DEBUG_ENABLED:
                    SysExEncoder.log_sysex(message, "OUT")
            else:
                if not silent:
                    self.log_message(f"❌ Error creating SysEx command 0x{command:02X}")
                
        except Exception as e:
            # Log all errors for Teensy development
            if not silent:
                self.log_message(f"❌ Error sending SysEx command 0x{command:02X}: {e}")
    
    def _send_sysex_command_silent(self, command, payload):
        """Send SysEx command silently (no logging)"""
        self._send_sysex_command(command, payload, silent=True)
    
    def handle_sysex(self, midi_bytes):
        """Handle incoming SysEx messages from hardware"""
        try:
            if len(midi_bytes) < 6:  # Minimum valid message length
                self.log_message(f"⚠️ SysEx too short: {len(midi_bytes)} bytes")
                return
            
            # Log incoming SysEx for debugging
            SysExEncoder.log_sysex(list(midi_bytes), "IN")
            
            # Verify header
            if midi_bytes[:4] != SYSEX_HEADER:
                self.log_message(f"⚠️ Invalid SysEx header: {[hex(b) for b in midi_bytes[:4]]}")
                return
            
            command = midi_bytes[4]
            payload_length = midi_bytes[5]
            
            if len(midi_bytes) < 6 + payload_length + 2:  # +2 for checksum and end byte
                self.log_message(f"⚠️ SysEx payload incomplete: expected {payload_length}, got {len(midi_bytes) - 8}")
                return
            
            payload = list(midi_bytes[6:6+payload_length])
            received_checksum = midi_bytes[6+payload_length]
            
            # Verify checksum
            calculated_checksum = command
            for byte in payload:
                calculated_checksum ^= byte
            calculated_checksum &= 0x7F
            
            if received_checksum != calculated_checksum:
                self.log_message(f"⚠️ SysEx checksum error: got {received_checksum:02X}, expected {calculated_checksum:02X}")
                return
            
            # Route command to appropriate manager
            self._route_command(command, payload)
            
        except Exception as e:
            self.log_message(f"❌ Error handling SysEx: {e}")
    
    def _route_command(self, command, payload):
        """Route SysEx command to appropriate manager"""
        try:
            # Connection commands
            if command == CMD_HANDSHAKE:
                self._handle_handshake(payload)
            elif command == CMD_HANDSHAKE_REPLY:
                self._handle_handshake_reply(payload)
            
            # Transport commands (0x50-0x5F)
            elif 0x50 <= command <= 0x5F:
                self._managers['transport'].handle_transport_command(command, payload)
            
            # Clip view commands (0x10-0x1F)
            elif 0x10 <= command <= 0x1F:
                self._handle_clip_command(command, payload)
            
            # Mixer view commands (0x20-0x2F)
            elif 0x20 <= command <= 0x2F:
                self._handle_mixer_command(command, payload)
            
            # Device view commands (0x30-0x3F)
            elif 0x30 <= command <= 0x3F:
                self._handle_device_command(command, payload)
            
            # Note view commands (0x40-0x4F)
            elif 0x40 <= command <= 0x4F:
                self._handle_note_command(command, payload)
            
            # Browser/Navigation commands (0xB0-0xBF)
            elif 0xB0 <= command <= 0xBF:
                self._managers['browser'].handle_navigation_command(command, payload)
            
            # Automation commands (0xC0-0xCF)
            elif 0xC0 <= command <= 0xCF:
                self._managers['automation'].handle_automation_command(command, payload)
            
            # View switching
            elif command == CMD_SWITCH_VIEW:
                self._handle_view_switch(payload)
            
            else:
                self.log_message(f"❓ Unknown command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error routing command 0x{command:02X}: {e}")
    
    def _handle_handshake(self, payload):
        """Handle handshake from hardware"""
        try:
            self.log_message("🤝 Handshake received from hardware")
            
            # Send handshake reply
            reply_payload = [0x4C, 0x56]  # "LV" for Live
            self._send_sysex_command(CMD_HANDSHAKE_REPLY, reply_payload)
            
            # Mark as connected and send complete state
            self._is_connected = True
            self.log_message("✅ Connection established")
            
            # Send complete state from all managers
            self._send_complete_state()
            
        except Exception as e:
            self.log_message(f"❌ Error handling handshake: {e}")
    
    def _handle_handshake_reply(self, payload):
        """Handle handshake reply from hardware"""
        try:
            self.log_message("🤝 Handshake reply received")
            self._is_connected = True
            
        except Exception as e:
            self.log_message(f"❌ Error handling handshake reply: {e}")
    
    def _send_complete_state(self):
        """Send complete state from all managers"""
        try:
            self.log_message("📡 Sending complete state from all managers...")
            
            # Send state from each manager
            self._managers['song'].send_complete_state()
            self._managers['transport'].send_complete_state()
            self._managers['track'].send_complete_state()
            self._managers['clip'].send_complete_state()
            self._managers['device'].send_complete_state()
            self._managers['browser'].send_complete_state()
            self._managers['automation'].send_complete_state()
            
            self.log_message("✅ Complete state sent from all managers")
            
        except Exception as e:
            self.log_message(f"❌ Error sending complete state: {e}")

    # ========================================
    # COMMAND HANDLERS
    # ========================================
    
    def _handle_clip_command(self, command, payload):
        """Handle clip view commands"""
        try:
            if command == CMD_CLIP_TRIGGER and len(payload) >= 2:
                track_idx, scene_idx = payload[0], payload[1]
                self._managers['clip'].fire_clip(track_idx, scene_idx)
                
            elif command == CMD_CLIP_STOP and len(payload) >= 2:
                track_idx, scene_idx = payload[0], payload[1]
                self._managers['clip'].stop_clip(track_idx, scene_idx)
                
            elif command == CMD_SCENE_FIRE and len(payload) >= 1:
                scene_idx = payload[0]
                self._managers['clip'].fire_scene(scene_idx)
                
            else:
                self.log_message(f"❓ Unknown clip command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling clip command 0x{command:02X}: {e}")
    
    def _handle_mixer_command(self, command, payload):
        """Handle mixer view commands"""
        try:
            if command == CMD_MIXER_VOLUME and len(payload) >= 2:
                track_idx, volume = payload[0], payload[1]
                self._set_track_volume(track_idx, volume / 127.0)
                
            elif command == CMD_MIXER_PAN and len(payload) >= 2:
                track_idx, pan = payload[0], payload[1]
                pan_value = (pan - 64) / 63.0  # Convert 0-127 to -1.0/1.0
                self._set_track_pan(track_idx, pan_value)
                
            elif command == CMD_MIXER_MUTE and len(payload) >= 1:
                track_idx = payload[0]
                self._toggle_track_mute(track_idx)
                
            elif command == CMD_MIXER_SOLO and len(payload) >= 1:
                track_idx = payload[0]
                self._toggle_track_solo(track_idx)
                
            elif command == CMD_MIXER_ARM and len(payload) >= 1:
                track_idx = payload[0]
                self._toggle_track_arm(track_idx)
                
            elif command == CMD_MIXER_SEND and len(payload) >= 3:
                track_idx, send_idx, send_value = payload[0], payload[1], payload[2]
                self._set_track_send(track_idx, send_idx, send_value / 127.0)
                
            else:
                self.log_message(f"❓ Unknown mixer command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling mixer command 0x{command:02X}: {e}")
    
    def _handle_device_command(self, command, payload):
        """Handle device view commands"""
        try:
            if command == CMD_DEVICE_SELECT and len(payload) >= 2:
                track_idx, device_idx = payload[0], payload[1]
                self._managers['device'].select_device(track_idx, device_idx)
                
            elif command == CMD_PARAM_CHANGE and len(payload) >= 4:
                track_idx, device_idx, param_idx, value = payload[0], payload[1], payload[2], payload[3]
                self._set_device_parameter(track_idx, device_idx, param_idx, value / 127.0)
                
            elif command == CMD_DEVICE_ENABLE and len(payload) >= 2:
                track_idx, device_idx = payload[0], payload[1]
                self._toggle_device_enable(track_idx, device_idx)
                
            elif command == CMD_DEVICE_PREV_NEXT and len(payload) >= 1:
                direction = payload[0]  # 0 = previous, 1 = next
                self._managers['device'].navigate_device(1 if direction else -1)
                
            elif command == CMD_PARAM_PAGE and len(payload) >= 1:
                direction = payload[0]  # 0 = previous, 1 = next
                self._managers['device'].change_parameter_page(1 if direction else -1)
                
            else:
                self.log_message(f"❓ Unknown device command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling device command 0x{command:02X}: {e}")
    
    def _handle_note_command(self, command, payload):
        """Handle note view commands"""
        try:
            if command == CMD_NOTE_ON and len(payload) >= 2:
                note, velocity = payload[0], payload[1]
                self._send_midi_note(note, velocity, True)
                
            elif command == CMD_NOTE_OFF and len(payload) >= 1:
                note = payload[0]
                self._send_midi_note(note, 0, False)
                
            elif command == CMD_SCALE_CHANGE and len(payload) >= 2:
                root_note, scale_id = payload[0], payload[1]
                self._set_scale(root_note, scale_id)
                
            elif command == CMD_OCTAVE_CHANGE and len(payload) >= 1:
                octave = payload[0]
                self._set_octave(octave)
                
            else:
                self.log_message(f"❓ Unknown note command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling note command 0x{command:02X}: {e}")
    
    def _handle_view_switch(self, payload):
        """Handle view switching"""
        try:
            if len(payload) >= 1:
                view_id = payload[0]
                view_names = ["clip", "mixer", "device", "note"]
                
                if view_id < len(view_names):
                    self._current_view = view_names[view_id]
                    self.log_message(f"👁️ Switched to {self._current_view} view")
                    
                    # Send view-specific state
                    self._send_view_state(view_id)
                
        except Exception as e:
            self.log_message(f"❌ Error handling view switch: {e}")

    # ========================================
    # ACTION METHODS
    # ========================================
    
    def _set_track_volume(self, track_idx, volume):
        """Set track volume"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                track.mixer_device.volume.value = max(0.0, min(1.0, volume))
                self.log_message(f"🔊 Track {track_idx} volume: {volume:.2f}")
        except Exception as e:
            self.log_message(f"❌ Error setting track {track_idx} volume: {e}")
    
    def _set_track_pan(self, track_idx, pan):
        """Set track pan"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                track.mixer_device.panning.value = max(-1.0, min(1.0, pan))
                self.log_message(f"◀️▶️ Track {track_idx} pan: {pan:.2f}")
        except Exception as e:
            self.log_message(f"❌ Error setting track {track_idx} pan: {e}")
    
    def _toggle_track_mute(self, track_idx):
        """Toggle track mute"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                track.mute = not track.mute
                self.log_message(f"🔇 Track {track_idx} mute: {track.mute}")
        except Exception as e:
            self.log_message(f"❌ Error toggling track {track_idx} mute: {e}")
    
    def _toggle_track_solo(self, track_idx):
        """Toggle track solo"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                track.solo = not track.solo
                self.log_message(f"🔊 Track {track_idx} solo: {track.solo}")
        except Exception as e:
            self.log_message(f"❌ Error toggling track {track_idx} solo: {e}")
    
    def _toggle_track_arm(self, track_idx):
        """Toggle track arm"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                if hasattr(track, 'can_be_armed') and track.can_be_armed:
                    track.arm = not track.arm
                    self.log_message(f"🔴 Track {track_idx} arm: {track.arm}")
        except Exception as e:
            self.log_message(f"❌ Error toggling track {track_idx} arm: {e}")
    
    def _set_track_send(self, track_idx, send_idx, send_value):
        """Set track send level"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                if send_idx < len(track.mixer_device.sends):
                    send = track.mixer_device.sends[send_idx]
                    send.value = max(0.0, min(1.0, send_value))
                    self.log_message(f"📤 Track {track_idx} send {send_idx}: {send_value:.2f}")
        except Exception as e:
            self.log_message(f"❌ Error setting track {track_idx} send {send_idx}: {e}")
    
    def _set_device_parameter(self, track_idx, device_idx, param_idx, value):
        """Set device parameter value"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                devices = list(track.devices)
                
                if device_idx < len(devices):
                    device = devices[device_idx]
                    
                    if param_idx < len(device.parameters):
                        param = device.parameters[param_idx]
                        # Scale value to parameter range
                        param_range = param.max - param.min
                        param_value = param.min + (value * param_range)
                        param.value = param_value
                        
                        self.log_message(f"🎚️ T{track_idx}D{device_idx}P{param_idx}: {param_value:.2f}")
        except Exception as e:
            self.log_message(f"❌ Error setting parameter T{track_idx}D{device_idx}P{param_idx}: {e}")
    
    def _toggle_device_enable(self, track_idx, device_idx):
        """Toggle device enabled state"""
        try:
            if track_idx < len(self.song().tracks):
                track = self.song().tracks[track_idx]
                devices = list(track.devices)
                
                if device_idx < len(devices):
                    device = devices[device_idx]
                    device.is_enabled = not device.is_enabled
                    self.log_message(f"🔘 T{track_idx}D{device_idx} enabled: {device.is_enabled}")
        except Exception as e:
            self.log_message(f"❌ Error toggling device T{track_idx}D{device_idx}: {e}")
    
    def _send_midi_note(self, note, velocity, is_note_on):
        """Send MIDI note to selected track"""
        try:
            selected_track = self.song().view.selected_track
            
            if selected_track and hasattr(selected_track, 'can_be_armed') and selected_track.can_be_armed:
                # Create MIDI note message
                status = 0x90 if is_note_on else 0x80  # Note on/off
                midi_message = (status, note, velocity)
                
                self._send_midi(midi_message)
                
                action = "ON" if is_note_on else "OFF"
                self.log_message(f"🎹 MIDI Note {action}: {note} vel:{velocity}")
        except Exception as e:
            self.log_message(f"❌ Error sending MIDI note {note}: {e}")
    
    def _set_scale(self, root_note, scale_id):
        """Set scale for note view"""
        try:
            scale_names = list(SCALES.keys())
            
            if scale_id < len(scale_names):
                self._current_root = root_note
                self._current_scale = scale_names[scale_id]
                
                note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                root_name = note_names[root_note % 12]
                
                self.log_message(f"🎵 Scale: {root_name} {self._current_scale}")
                
                # Send scale info to hardware
                message = SysExEncoder.encode_scale_info(root_note, scale_id)
                if message:
                    self._send_midi(tuple(message))
        except Exception as e:
            self.log_message(f"❌ Error setting scale: {e}")
    
    def _set_octave(self, octave):
        """Set octave for note view"""
        try:
            self._current_octave = max(0, min(8, octave))
            self.log_message(f"🎵 Octave: {self._current_octave}")
            
            # Send octave info to hardware
            message = SysExEncoder.encode_octave_info(self._current_octave)
            if message:
                self._send_midi(tuple(message))
        except Exception as e:
            self.log_message(f"❌ Error setting octave: {e}")
    
    def _send_view_state(self, view_id):
        """Send view-specific state"""
        try:
            if view_id == 0:  # Clip view
                self._managers['clip'].send_complete_state()
            elif view_id == 1:  # Mixer view
                self._managers['track'].send_complete_state()
            elif view_id == 2:  # Device view
                self._managers['device'].send_complete_state()
            elif view_id == 3:  # Note view
                # Send current scale and octave info
                scale_names = list(SCALES.keys())
                scale_id = scale_names.index(self._current_scale) if self._current_scale in scale_names else 0
                
                scale_message = SysExEncoder.encode_scale_info(self._current_root, scale_id)
                octave_message = SysExEncoder.encode_octave_info(self._current_octave)
                
                if scale_message:
                    self._send_midi(tuple(scale_message))
                if octave_message:
                    self._send_midi(tuple(octave_message))
        except Exception as e:
            self.log_message(f"❌ Error sending view {view_id} state: {e}")

    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_manager(self, manager_name):
        """Get specific manager instance"""
        return self._managers.get(manager_name)
    
    def get_connection_state(self):
        """Get current connection state"""
        return {
            'is_connected': self._is_connected,
            'current_view': self._current_view,
            'message_count': self._message_count,
            'managers_active': len([m for m in self._managers.values() if hasattr(m, '_is_active') and m._is_active])
        }
    
    def get_complete_state(self):
        """Get complete state from all managers"""
        try:
            state = {
                'connection': self.get_connection_state(),
                'current_selections': {
                    'track': self._current_track,
                    'device': self._current_device,
                    'param_page': self._current_param_page,
                    'scale': self._current_scale,
                    'root_note': self._current_root,
                    'octave': self._current_octave
                }
            }
            
            # Get state from managers if they have the methods
            for manager_name, manager in self._managers.items():
                try:
                    if hasattr(manager, 'get_song_info') and manager_name == 'song':
                        state['song'] = manager.get_song_info()
                    elif hasattr(manager, 'get_transport_info') and manager_name == 'transport':
                        state['transport'] = manager.get_transport_info()
                    elif hasattr(manager, 'get_navigation_info') and manager_name == 'browser':
                        state['navigation'] = manager.get_navigation_info()
                    elif hasattr(manager, 'get_automation_info') and manager_name == 'automation':
                        state['automation'] = manager.get_automation_info()
                except:
                    pass  # Skip if method doesn't exist or fails
            
            return state
            
        except Exception as e:
            self.log_message(f"❌ Error getting complete state: {e}")
            return {}

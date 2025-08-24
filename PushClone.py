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
from .GroovePoolManager import GroovePoolManager
from .StepSequencerManager import StepSequencerManager
from .SessionRing import SessionRing
from .MessageCoalescer import MessageCoalescer

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
        self._session_ring = None
        self._message_coalescer = None
        self._initialize_managers()
        
        # Current selections and state
        self._current_track = 0
        self._current_device = 0
        self._current_param_page = 0
        self._current_scale = "Minor"
        self._current_root = 0  # C = 0
        self._current_octave = 4
        
        # Session navigation modes
        self._session_mode = "session_screen"  # "session_screen" or "session_pad"
        self._overview_mode = False  # Session overview on/off
        self._clip_actions = {  # Available clip actions
            'duplicate': True,
            'delete': True,
            'copy': True,
            'paste': False  # Will be True when clipboard has content
        }
        self._clipboard = None  # For clip copy/paste
        
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
            self._managers['groove_pool'] = GroovePoolManager(self)
            self._managers['step_sequencer'] = StepSequencerManager(self)
            
            # Initialize Session Ring
            self._session_ring = SessionRing(self)
            
            # Initialize Message Coalescer for performance
            self._message_coalescer = MessageCoalescer(self)
            
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
            self._managers['step_sequencer'].setup_listeners()
            self._session_ring.setup_listeners()
            
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
            
            self._managers['step_sequencer'].cleanup_listeners()
            
            # Cleanup session ring and message coalescer
            if self._session_ring:
                self._session_ring.cleanup_listeners()
            if self._message_coalescer:
                self._message_coalescer.cleanup()
            
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
    
    def _send_sysex_command(self, command, payload, silent=False, priority=None):
        """Send SysEx command to hardware"""
        try:
            message = SysExEncoder.create_sysex(command, payload)
            if message:
                # Validate message before sending
                if len(message) > 64:  # Increased limit for larger SysEx messages
                    if not silent:
                        self.log_message(f"⚠️ SysEx too long ({len(message)} bytes) for command 0x{command:02X}")
                    return
                    
                # Check for invalid SysEx format
                if message[0] != 0xF0 or message[-1] != 0xF7:
                    if not silent:
                        self.log_message(f"⚠️ Invalid SysEx format for command 0x{command:02X}")
                    return
                
                # Check payload length vs declared length
                if len(message) >= 9:  # Header(4) + Command(1) + Seq(1) + Length(1) + Checksum(1) + End(1) = 9 minimum
                    declared_length = message[6]  # Length byte position (now at index 6)
                    # Message structure: Header(4) + Command(1) + Seq(1) + Length(1) + Payload(N) + Checksum(1) + End(1) = 9 + N
                    actual_payload_length = len(message) - 9  # Total - overhead (9 bytes)
                    if declared_length != actual_payload_length:
                        if not silent:
                            self.log_message(f"⚠️ SysEx length mismatch for 0x{command:02X}: declared={declared_length}, actual={actual_payload_length}, message_len={len(message)}")
                        # Don't return - this is often a false positive due to encoding issues
                        # Instead, log it but continue sending
                
                # Validate all MIDI bytes are in valid range (0-127), ignoring header and footer
                invalid_bytes = [b for b in message[4:-1] if b < 0 or b > 127]
                if invalid_bytes:
                    if not silent:
                        self.log_message(f"❌ Invalid MIDI bytes in SysEx payload 0x{command:02X}: {invalid_bytes}")
                    return
                
                try:
                    # Use message coalescer for performance optimization
                    if self._message_coalescer and not priority:
                        # Queue message for coalescing (except high priority)
                        self._message_coalescer.queue_message(command, payload)
                    else:
                        # Send immediately for high priority or when coalescer unavailable
                        self._send_midi(tuple(message))
                    
                    # Log successful sends for debugging
                    if not silent and DEBUG_ENABLED:
                        SysExEncoder.log_sysex(message, "OUT")
                        self.log_message(f"✅ Sent SysEx 0x{command:02X} ({len(message)} bytes)")
                except Exception as midi_error:
                    if not silent:
                        error_msg = str(midi_error)
                        if "Error while sending midi message" in error_msg:
                            self.log_message(f"🔌 MIDI port issue for command 0x{command:02X}: Hardware may be disconnected")
                        else:
                            self.log_message(f"❌ MIDI send failed 0x{command:02X}: {error_msg}")
            else:
                if not silent:
                    self.log_message(f"❌ Error creating SysEx command 0x{command:02X}")
                
        except Exception as e:
            # Log all errors for Teensy development
            if not silent:
                self.log_message(f"❌ Error in SysEx command 0x{command:02X}: {e}")
    
    def _send_sysex_command_silent(self, command, payload):
        """Send SysEx command silently (no logging)"""
        self._send_sysex_command(command, payload, silent=True)
    
    def test_midi_connection(self):
        """Test MIDI connection by sending a simple ping"""
        try:
            self.log_message("🔍 Testing MIDI connection...")
            
            # Send a minimal ping test
            test_payload = [0x50, 0x49, 0x4E, 0x47]  # "PING" in ASCII
            self._send_sysex_command(CMD_PING_TEST, test_payload)
            
            # Also test with raw MIDI note
            try:
                self._send_midi((0x90, 60, 64))  # Note On C4
                self._send_midi((0x80, 60, 64))  # Note Off C4
                self.log_message("✅ Raw MIDI test successful")
            except Exception as e:
                self.log_message(f"❌ Raw MIDI test failed: {e}")
                
        except Exception as e:
            self.log_message(f"❌ MIDI connection test failed: {e}")
    
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
            sequence = midi_bytes[5]
            payload_length = midi_bytes[6]
            
            if len(midi_bytes) < 7 + payload_length + 2:  # +2 for checksum and end byte
                self.log_message(f"⚠️ SysEx payload incomplete: expected {payload_length}, got {len(midi_bytes) - 9}")
                return
            
            payload = list(midi_bytes[7:7+payload_length])
            received_checksum = midi_bytes[7+payload_length]
            
            # Verify enhanced checksum
            calculated_checksum = command ^ sequence
            for byte in payload:
                calculated_checksum ^= byte
            calculated_checksum &= 0x7F
            
            if received_checksum != calculated_checksum:
                self.log_message(f"⚠️ SysEx checksum error: got {received_checksum:02X}, expected {calculated_checksum:02X}")
                return
            
            # Log sequence number for debugging
            if DEBUG_ENABLED:
                self.log_message(f"📨 SysEx CMD:{command:02X} SEQ:{sequence} LEN:{payload_length}")
            
            # Route command to appropriate manager
            self._route_command(command, payload)
            
        except Exception as e:
            self.log_message(f"❌ Error handling SysEx: {e}")
    
    def _route_command(self, command, payload):
        """Route SysEx command to appropriate manager"""
        try:
            # View switching
            if command == CMD_SWITCH_VIEW:
                self._handle_view_switch(payload)

            # Clip/Scene commands (0x10-0x1F)
            elif 0x10 <= command <= 0x1F:
                self._handle_clip_command(command, payload)

            # Mixer/Track commands (0x20-0x2F)
            elif 0x20 <= command <= 0x2F:
                self._handle_mixer_command(command, payload)

            # Device/Plugin commands (0x30-0x3F)
            elif 0x30 <= command <= 0x3F:
                self._handle_device_command(command, payload)

            # Transport/Automation commands (0x40-0x4F)
            elif 0x40 <= command <= 0x4F:
                self._managers['transport'].handle_transport_command(command, payload)
                self._managers['automation'].handle_automation_command(command, payload)

            # Note/Scale/Sequencer commands (0x50-0x5F)
            elif 0x50 <= command <= 0x5F:
                self._handle_note_command(command, payload)
                self._managers['step_sequencer'].handle_step_sequencer_command(command, payload)

            # System/Navigation commands (0x60-0x6F)
            elif 0x60 <= command <= 0x6F:
                if command in [CMD_HANDSHAKE, CMD_HANDSHAKE_REPLY, CMD_PING_TEST]:
                    self._handle_handshake_command(command, payload)
                elif command in [CMD_RING_NAVIGATE, CMD_RING_SELECT, CMD_RING_POSITION]:
                    self._session_ring.handle_navigation_command(command, payload)
                else:
                    self._managers['browser'].handle_navigation_command(command, payload)

            # Song/Clip actions (0x70-0x7F)
            elif 0x70 <= command <= 0x7F:
                self._handle_song_creation_command(command, payload)
                self.handle_session_navigation_command(command, payload)

            else:
                self.log_message(f"❓ Unknown command: 0x{command:02X}")

        except Exception as e:
            self.log_message(f"❌ Error routing command 0x{command:02X}: {e}")
    
    def _handle_handshake_command(self, command, payload):
        """Handle handshake commands"""
        try:
            if command == CMD_HANDSHAKE:
                self.log_message("🤝 Handshake received from hardware")
                # payload contains hardware identification info
                
                # Send handshake reply
                reply_payload = [0x4C, 0x56]  # "LV" for Live
                self._send_sysex_command(CMD_HANDSHAKE_REPLY, reply_payload)
                
                # Mark as connected and send complete state
                self._is_connected = True
                self.log_message("✅ Connection established")
                
                # Send complete state from all managers
                self._send_complete_state()
            elif command == CMD_HANDSHAKE_REPLY:
                self.log_message("🤝 Handshake reply received")
                # payload contains hardware confirmation
                self._is_connected = True
        except Exception as e:
            self.log_message(f"❌ Error handling handshake command 0x{command:02X}: {e}")
    
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
            self._managers['step_sequencer'].send_complete_state()
            if self._session_ring:
                self._session_ring.send_complete_state()
            
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
            track = self._get_track_safe(track_idx)
            if track:
                track.mute = not track.mute
                self.log_message(f"🔇 Track {track_idx} mute: {track.mute}")
            else:
                self.log_message(f"❌ Invalid track index: {track_idx}")
        except Exception as e:
            self.log_message(f"❌ Error toggling track {track_idx} mute: {e}")
    
    def _toggle_track_solo(self, track_idx):
        """Toggle track solo"""
        try:
            track = self._get_track_safe(track_idx)
            if track:
                track.solo = not track.solo
                self.log_message(f"🔊 Track {track_idx} solo: {track.solo}")
            else:
                self.log_message(f"❌ Invalid track index: {track_idx}")
        except Exception as e:
            self.log_message(f"❌ Error toggling track {track_idx} solo: {e}")
    
    def _toggle_track_arm(self, track_idx):
        """Toggle track arm"""
        try:
            track = self._get_track_safe(track_idx)
            if track and hasattr(track, 'can_be_armed') and track.can_be_armed:
                track.arm = not track.arm
                self.log_message(f"🔴 Track {track_idx} arm: {track.arm}")
            elif track:
                self.log_message(f"⚠️ Track {track_idx} cannot be armed")
            else:
                self.log_message(f"❌ Invalid track index: {track_idx}")
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
                    device.is_active = not device.is_active
                    self.log_message(f"🔘 T{track_idx}D{device_idx} enabled: {device.is_active}")
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
    # LIVE API SAFE ACCESS METHODS
    # ========================================
    
    def _get_track_safe(self, track_idx):
        """Safely get track by index with bounds checking"""
        try:
            tracks = self.song().tracks
            if 0 <= track_idx < len(tracks):
                return tracks[track_idx]
            elif track_idx < len(tracks) + len(self.song().return_tracks):
                return_idx = track_idx - len(tracks)
                if 0 <= return_idx < len(self.song().return_tracks):
                    return self.song().return_tracks[return_idx]
            elif track_idx == len(tracks) + len(self.song().return_tracks):
                return self.song().master_track
            return None
        except Exception as e:
            self.log_message(f"❌ Error accessing track {track_idx}: {e}")
            return None
    
    def _get_scene_safe(self, scene_idx):
        """Safely get scene by index with bounds checking"""
        try:
            scenes = self.song().scenes
            if 0 <= scene_idx < len(scenes):
                return scenes[scene_idx]
            return None
        except Exception as e:
            self.log_message(f"❌ Error accessing scene {scene_idx}: {e}")
            return None
    
    def _get_device_safe(self, track_idx, device_idx):
        """Safely get device by track and device index"""
        try:
            track = self._get_track_safe(track_idx)
            if track and 0 <= device_idx < len(track.devices):
                return track.devices[device_idx]
            return None
        except Exception as e:
            self.log_message(f"❌ Error accessing device T{track_idx}D{device_idx}: {e}")
            return None
    
    def _get_clip_slot_safe(self, track_idx, scene_idx):
        """Safely get clip slot with bounds checking"""
        try:
            track = self._get_track_safe(track_idx)
            if track and 0 <= scene_idx < len(track.clip_slots):
                return track.clip_slots[scene_idx]
            return None
        except Exception as e:
            self.log_message(f"❌ Error accessing clip slot T{track_idx}S{scene_idx}: {e}")
            return None
    
    def _get_live_version(self):
        """Get Live version for compatibility checks"""
        try:
            if hasattr(self.application(), 'get_major_version'):
                major = self.application().get_major_version()
                minor = getattr(self.application(), 'get_minor_version', lambda: 0)()
                return (major, minor)
            return (11, 0)  # Default fallback
        except Exception:
            return (11, 0)  # Safe fallback
    
    def _has_feature(self, feature_name, min_version=(11, 0)):
        """Check if Live version supports a feature"""
        try:
            current_version = self._get_live_version()
            # feature_name parameter for future feature-specific checks
            return current_version >= min_version
        except Exception:
            return False  # Conservative fallback
    
    def _safe_hasattr_and_call(self, obj, attr_name, default_value=None):
        """Safely check attribute existence and get value with fallback"""
        try:
            if hasattr(obj, attr_name):
                attr = getattr(obj, attr_name)
                return attr() if callable(attr) else attr
            return default_value
        except Exception:
            return default_value
    
    def _handle_song_creation_command(self, command, payload):
        """Handle Song creation and manipulation commands"""
        try:
            if command == CMD_CREATE_AUDIO_TRACK:
                self._create_audio_track()
                
            elif command == CMD_CREATE_MIDI_TRACK:
                self._create_midi_track()
                
            elif command == CMD_CREATE_RETURN_TRACK:
                self._create_return_track()
                
            elif command == CMD_CREATE_SCENE:
                self._create_scene()
                
            elif command == CMD_DUPLICATE_TRACK and len(payload) >= 1:
                track_idx = payload[0]
                self._duplicate_track(track_idx)
                
            elif command == CMD_DUPLICATE_CLIP and len(payload) >= 4:
                src_track, src_scene, dst_track, dst_scene = payload[0], payload[1], payload[2], payload[3]
                self._duplicate_clip(src_track, src_scene, dst_track, dst_scene)
                
            else:
                self.log_message(f"❓ Unknown song creation command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling song creation command 0x{command:02X}: {e}")
    
    def _create_audio_track(self):
        """Create a new audio track using Live API"""
        try:
            if hasattr(self.song(), 'create_audio_track'):
                new_track_idx = len(self.song().tracks)
                self.song().create_audio_track(new_track_idx)
                self.log_message(f"🎤 Created audio track at index {new_track_idx}")
                return True
            else:
                self.log_message("⚠️ create_audio_track not available in this Live version")
                return False
        except Exception as e:
            self.log_message(f"❌ Error creating audio track: {e}")
            return False
    
    def _create_midi_track(self):
        """Create a new MIDI track using Live API"""
        try:
            if hasattr(self.song(), 'create_midi_track'):
                new_track_idx = len(self.song().tracks)
                self.song().create_midi_track(new_track_idx)
                self.log_message(f"🎹 Created MIDI track at index {new_track_idx}")
                return True
            else:
                self.log_message("⚠️ create_midi_track not available in this Live version")
                return False
        except Exception as e:
            self.log_message(f"❌ Error creating MIDI track: {e}")
            return False
    
    def _create_return_track(self):
        """Create a new return track using Live API"""
        try:
            if hasattr(self.song(), 'create_return_track'):
                new_return_idx = len(self.song().return_tracks)
                self.song().create_return_track()
                self.log_message(f"🔄 Created return track at index {new_return_idx}")
                return True
            else:
                self.log_message("⚠️ create_return_track not available in this Live version")
                return False
        except Exception as e:
            self.log_message(f"❌ Error creating return track: {e}")
            return False
    
    def _create_scene(self):
        """Create a new scene using Live API"""
        try:
            if hasattr(self.song(), 'create_scene'):
                new_scene_idx = len(self.song().scenes)
                self.song().create_scene(new_scene_idx)
                self.log_message(f"🎬 Created scene at index {new_scene_idx}")
                return True
            else:
                self.log_message("⚠️ create_scene not available in this Live version")
                return False
        except Exception as e:
            self.log_message(f"❌ Error creating scene: {e}")
            return False
    
    def _duplicate_track(self, track_idx):
        """Duplicate a track using Live API"""
        try:
            track = self._get_track_safe(track_idx)
            if track:
                if hasattr(track, 'duplicate_clip_slot'):
                    # Method varies by Live version - try different approaches
                    if hasattr(self.song(), 'duplicate_track'):
                        self.song().duplicate_track(track_idx)
                        self.log_message(f"📋 Duplicated track {track_idx}")
                        return True
                    else:
                        self.log_message(f"⚠️ Track duplication not available in this Live version")
                        return False
                else:
                    self.log_message(f"⚠️ Track {track_idx} doesn't support duplication")
                    return False
            else:
                self.log_message(f"❌ Invalid track index: {track_idx}")
                return False
        except Exception as e:
            self.log_message(f"❌ Error duplicating track {track_idx}: {e}")
            return False
    
    def _duplicate_clip(self, src_track_idx, src_scene_idx, dst_track_idx, dst_scene_idx):
        """Duplicate a clip using Live API"""
        try:
            src_clip_slot = self._get_clip_slot_safe(src_track_idx, src_scene_idx)
            dst_clip_slot = self._get_clip_slot_safe(dst_track_idx, dst_scene_idx)
            
            if src_clip_slot and dst_clip_slot:
                if src_clip_slot.has_clip:
                    if hasattr(src_clip_slot, 'duplicate_clip_to'):
                        src_clip_slot.duplicate_clip_to(dst_clip_slot)
                        self.log_message(
                            f"📋 Duplicated clip: T{src_track_idx}S{src_scene_idx} → T{dst_track_idx}S{dst_scene_idx}"
                        )
                        return True
                    elif hasattr(dst_clip_slot, 'duplicate_clip_slot'):
                        dst_clip_slot.duplicate_clip_slot(src_clip_slot)
                        self.log_message(
                            f"📋 Duplicated clip: T{src_track_idx}S{src_scene_idx} → T{dst_track_idx}S{dst_scene_idx}"
                        )
                        return True
                    else:
                        # Fallback: manual duplication for MIDI clips
                        if hasattr(self._managers['clip'], 'duplicate_midi_clip_notes'):
                            return self._managers['clip'].duplicate_midi_clip_notes(
                                src_track_idx, src_scene_idx, dst_track_idx, dst_scene_idx
                            )
                        else:
                            self.log_message("⚠️ Clip duplication not available in this Live version")
                            return False
                else:
                    self.log_message(f"⚠️ Source clip slot T{src_track_idx}S{src_scene_idx} is empty")
                    return False
            else:
                self.log_message(f"❌ Invalid clip slot indices")
                return False
        except Exception as e:
            self.log_message(f"❌ Error duplicating clip: {e}")
            return False
    
    # ========================================
    # SESSION NAVIGATION AND MODES
    # ========================================
    
    def switch_session_mode(self, mode):
        """Switch between session screen and session pad mode"""
        try:
            if mode in ["session_screen", "session_pad"]:
                old_mode = self._session_mode
                self._session_mode = mode
                
                self.log_message(f"🔄 Session mode: {old_mode} → {mode}")
                
                # Send mode change to hardware
                mode_id = 0 if mode == "session_screen" else 1
                self._send_sysex_command(CMD_SESSION_MODE, [mode_id])
                
                # Update display based on mode
                if mode == "session_screen":
                    # Show full session view with ring
                    if self._session_ring:
                        self._session_ring.send_complete_state()
                else:
                    # Show pad-focused session view
                    self._send_session_overview()
                
                return True
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error switching session mode: {e}")
            return False
    
    def toggle_session_overview(self):
        """Toggle session overview mode"""
        try:
            self._overview_mode = not self._overview_mode
            
            self.log_message(f"🔍 Session overview: {'ON' if self._overview_mode else 'OFF'}")
            
            # Send overview state to hardware
            self._send_sysex_command(CMD_SESSION_OVERVIEW, [1 if self._overview_mode else 0])
            
            if self._overview_mode:
                self._send_session_overview()
            else:
                # Return to normal session view
                if self._session_ring:
                    self._session_ring.send_complete_state()
            
        except Exception as e:
            self.log_message(f"❌ Error toggling overview: {e}")
    
    def _send_session_overview(self):
        """Send session overview grid data"""
        try:
            if not self._is_connected:
                return
            
            # Create overview grid (8x8 representing larger session area)
            overview_grid = []
            tracks = self.song().tracks
            scenes = self.song().scenes
            
            for scene_idx in range(8):
                for track_idx in range(8):
                    if (track_idx < len(tracks) and scene_idx < len(scenes)):
                        clip_slot = tracks[track_idx].clip_slots[scene_idx]
                        
                        # Overview colors: simplified clip states
                        if clip_slot.has_clip:
                            if clip_slot.is_playing:
                                color = 3  # Playing - bright
                            elif clip_slot.is_triggered:
                                color = 2  # Queued - medium
                            else:
                                color = 1  # Has clip - dim
                        else:
                            color = 0  # Empty
                    else:
                        color = 0  # Outside session bounds
                    
                    overview_grid.append(color)
            
            # Send overview grid
            self._send_sysex_command(CMD_SESSION_OVERVIEW_GRID, overview_grid)
            
        except Exception as e:
            self.log_message(f"❌ Error sending session overview: {e}")
    
    def handle_session_navigation_command(self, command, payload):
        """Handle session navigation commands"""
        try:
            if command == CMD_SESSION_MODE and len(payload) >= 1:
                mode = "session_screen" if payload[0] == 0 else "session_pad"
                self.switch_session_mode(mode)
                
            elif command == CMD_SESSION_OVERVIEW:
                self.toggle_session_overview()
                
            elif command == CMD_CLIP_DUPLICATE and len(payload) >= 4:
                src_track, src_scene, dst_track, dst_scene = payload[0], payload[1], payload[2], payload[3]
                self.duplicate_clip(src_track, src_scene, dst_track, dst_scene)
                
            elif command == CMD_CLIP_DELETE and len(payload) >= 2:
                track_idx, scene_idx = payload[0], payload[1]
                self.delete_clip(track_idx, scene_idx)
                
            elif command == CMD_CLIP_COPY and len(payload) >= 2:
                track_idx, scene_idx = payload[0], payload[1]
                self.copy_clip(track_idx, scene_idx)
                
            elif command == CMD_CLIP_PASTE and len(payload) >= 2:
                track_idx, scene_idx = payload[0], payload[1]
                self.paste_clip(track_idx, scene_idx)
                
            else:
                self.log_message(f"❓ Unknown session navigation command: 0x{command:02X}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling session navigation command 0x{command:02X}: {e}")
    
    def duplicate_clip(self, source_track, source_scene, target_track, target_scene):
        """Duplicate clip from source to target position"""
        try:
            if self._managers['clip']:
                success = self._managers['clip'].duplicate_midi_clip_notes(
                    source_track, source_scene, target_track, target_scene
                )
                
                if success:
                    self.log_message(
                        f"📋 Duplicated clip: T{source_track}S{source_scene} → T{target_track}S{target_scene}"
                    )
                    # Send confirmation to hardware
                    self._send_sysex_command(CMD_CLIP_DUPLICATE_RESULT, [1])  # Success
                else:
                    self._send_sysex_command(CMD_CLIP_DUPLICATE_RESULT, [0])  # Failed
                
                return success
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error duplicating clip: {e}")
            self._send_sysex_command(CMD_CLIP_DUPLICATE_RESULT, [0])
            return False
    
    def delete_clip(self, track_idx, scene_idx):
        """Delete clip at specified position"""
        try:
            if (track_idx < len(self.song().tracks) and 
                scene_idx < len(self.song().scenes)):
                
                track = self.song().tracks[track_idx]
                clip_slot = track.clip_slots[scene_idx]
                
                if clip_slot.has_clip:
                    clip_slot.delete_clip()
                    self.log_message(f"🗑️ Deleted clip T{track_idx}S{scene_idx}")
                    
                    # Send confirmation to hardware
                    self._send_sysex_command(CMD_CLIP_DELETE_RESULT, [1])
                    return True
                else:
                    self.log_message(f"⚠️ No clip to delete at T{track_idx}S{scene_idx}")
                    self._send_sysex_command(CMD_CLIP_DELETE_RESULT, [0])
                    return False
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error deleting clip T{track_idx}S{scene_idx}: {e}")
            self._send_sysex_command(CMD_CLIP_DELETE_RESULT, [0])
            return False
    
    def copy_clip(self, track_idx, scene_idx):
        """Copy clip to clipboard"""
        try:
            if (track_idx < len(self.song().tracks) and 
                scene_idx < len(self.song().scenes)):
                
                track = self.song().tracks[track_idx]
                clip_slot = track.clip_slots[scene_idx]
                
                if clip_slot.has_clip:
                    # Store clip data in clipboard
                    if self._managers['clip']:
                        notes = self._managers['clip'].get_midi_clip_notes(track_idx, scene_idx)
                        if notes:
                            self._clipboard = {
                                'type': 'midi_clip',
                                'notes': notes,
                                'source_track': track_idx,
                                'source_scene': scene_idx,
                                'clip_name': clip_slot.clip.name,
                                'clip_color': clip_slot.clip.color
                            }
                            
                            self.log_message(f"📋 Copied clip T{track_idx}S{scene_idx} to clipboard")
                            self._clip_actions['paste'] = True
                            
                            # Send confirmation to hardware
                            self._send_sysex_command(CMD_CLIP_COPY_RESULT, [1])
                            return True
                
                self.log_message(f"⚠️ No clip data to copy at T{track_idx}S{scene_idx}")
                self._send_sysex_command(CMD_CLIP_COPY_RESULT, [0])
                return False
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error copying clip T{track_idx}S{scene_idx}: {e}")
            self._send_sysex_command(CMD_CLIP_COPY_RESULT, [0])
            return False
    
    def paste_clip(self, target_track, target_scene):
        """Paste clip from clipboard"""
        try:
            if not self._clipboard:
                self.log_message("⚠️ No clip in clipboard to paste")
                self._send_sysex_command(CMD_CLIP_PASTE_RESULT, [0])
                return False
            
            if (target_track < len(self.song().tracks) and 
                target_scene < len(self.song().scenes)):
                
                if self._clipboard['type'] == 'midi_clip':
                    # Create new clip at target position
                    target_clip_slot = self.song().tracks[target_track].clip_slots[target_scene]
                    
                    # Clear existing clip if any
                    if target_clip_slot.has_clip:
                        target_clip_slot.delete_clip()
                    
                    # Create new clip
                    target_clip_slot.create_clip(4.0)  # 4 bars
                    
                    if target_clip_slot.has_clip and self._managers['clip']:
                        target_clip = target_clip_slot.clip
                        
                        # Copy properties
                        target_clip.name = self._clipboard['clip_name']
                        target_clip.color = self._clipboard['clip_color']
                        
                        # Add notes
                        notes = self._clipboard['notes']
                        if notes:
                            note_tuples = []
                            for note in notes:
                                note_tuples.append((
                                    note['pitch'],
                                    note['start_time'],
                                    note['duration'],
                                    note['velocity'],
                                    False  # not muted
                                ))
                            
                            target_clip.set_notes_extended(note_tuples)
                            
                            self.log_message(
                                f"📎 Pasted {len(notes)} notes to T{target_track}S{target_scene}"
                            )
                            
                            # Send confirmation to hardware
                            self._send_sysex_command(CMD_CLIP_PASTE_RESULT, [1])
                            return True
                
                self._send_sysex_command(CMD_CLIP_PASTE_RESULT, [0])
                return False
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error pasting clip to T{target_track}S{target_scene}: {e}")
            self._send_sysex_command(CMD_CLIP_PASTE_RESULT, [0])
            return False
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_manager(self, manager_name):
        """Get specific manager instance"""
        if manager_name == 'session_ring':
            return self._session_ring
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
            
            # Session navigation state
            state['session_navigation'] = {
                'session_mode': self._session_mode,
                'overview_mode': self._overview_mode,
                'clip_actions': self._clip_actions.copy(),
                'has_clipboard': self._clipboard is not None
            }
            
            return state
            
        except Exception as e:
            self.log_message(f"❌ Error getting complete state: {e}")
            return {}

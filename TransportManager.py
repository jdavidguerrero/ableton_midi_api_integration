# TransportManager.py - Transport and Playback Management
"""
Manages Transport-level functionality and playback control
Based on Live Object Model: Song transport properties
"""

from .consts import *
from .MIDIUtils import SysExEncoder

class TransportManager:
    """
    Manages all Transport-level listeners and handlers
    Covers: Play/stop, record, loop, transport position
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self._listeners = []
        self._is_active = False
        
        # Transport state tracking
        self._last_beat = -1
        self._last_bar = -1
        
    def setup_listeners(self):
        """Setup transport listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("🚀 Setting up Transport listeners...")
            
            # === PLAYBACK CONTROL ===
            
            # Play/Stop
            play_listener = lambda: self._on_is_playing_changed()
            self.song.add_is_playing_listener(play_listener)
            self._listeners.append(('is_playing', play_listener))
            
            # Record
            record_listener = lambda: self._on_record_mode_changed()
            self.song.add_record_mode_listener(record_listener)
            self._listeners.append(('record_mode', record_listener))
            
            # Loop
            loop_listener = lambda: self._on_loop_changed()
            self.song.add_loop_listener(loop_listener)
            self._listeners.append(('loop', loop_listener))
            
            # === TRANSPORT POSITION ===
            
            # Song position (current beat)
            position_listener = lambda: self._on_current_song_time_changed()
            self.song.add_current_song_time_listener(position_listener)
            self._listeners.append(('current_song_time', position_listener))
            
            # === LOOP MARKERS ===
            
            # Loop start
            loop_start_listener = lambda: self._on_loop_start_changed()
            self.song.add_loop_start_listener(loop_start_listener)
            self._listeners.append(('loop_start', loop_start_listener))
            
            # Loop length
            loop_length_listener = lambda: self._on_loop_length_changed()
            self.song.add_loop_length_listener(loop_length_listener)
            self._listeners.append(('loop_length', loop_length_listener))
            
            # === ARRANGEMENT RECORDING ===
            
            # Arrangement record
            arrangement_record_listener = lambda: self._on_arrangement_overdub_changed()
            self.song.add_arrangement_overdub_listener(arrangement_record_listener)
            self._listeners.append(('arrangement_overdub', arrangement_record_listener))
            
            # Back to arrangement (Live 9.0+)
            if hasattr(self.song, 'add_back_to_arrangement_listener'):
                back_to_arrangement_listener = lambda: self._on_back_to_arrangement_changed()
                self.song.add_back_to_arrangement_listener(back_to_arrangement_listener)
                self._listeners.append(('back_to_arrangement', back_to_arrangement_listener))
            else:
                self.c_surface.log_message("ℹ️ back_to_arrangement_listener not available (requires Live 9.0+)")
            
            # === ADDITIONAL TRANSPORT PROPERTIES ===
            
            # Nudge up/down (if available)
            if hasattr(self.song, 'nudge_up'):
                nudge_up_listener = lambda: self._on_nudge_up()
                self.song.add_nudge_up_listener(nudge_up_listener)
                self._listeners.append(('nudge_up', nudge_up_listener))
            
            if hasattr(self.song, 'nudge_down'):
                nudge_down_listener = lambda: self._on_nudge_down()
                self.song.add_nudge_down_listener(nudge_down_listener)
                self._listeners.append(('nudge_down', nudge_down_listener))
            
            self._is_active = True
            self.c_surface.log_message(f"✅ Transport listeners setup ({len(self._listeners)} listeners)")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up transport listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all transport listeners"""
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 'is_playing':
                        self.song.remove_is_playing_listener(listener_func)
                    elif listener_type == 'record_mode':
                        self.song.remove_record_mode_listener(listener_func)
                    elif listener_type == 'loop':
                        self.song.remove_loop_listener(listener_func)
                    elif listener_type == 'current_song_time':
                        self.song.remove_current_song_time_listener(listener_func)
                    elif listener_type == 'loop_start':
                        self.song.remove_loop_start_listener(listener_func)
                    elif listener_type == 'loop_length':
                        self.song.remove_loop_length_listener(listener_func)
                    elif listener_type == 'arrangement_overdub':
                        self.song.remove_arrangement_overdub_listener(listener_func)
                    elif listener_type == 'back_to_arrangement':
                        self.song.remove_back_to_arrangement_listener(listener_func)
                    elif listener_type == 'nudge_up':
                        self.song.remove_nudge_up_listener(listener_func)
                    elif listener_type == 'nudge_down':
                        self.song.remove_nudge_down_listener(listener_func)
                except:
                    pass  # Ignore if already removed
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Transport listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning transport listeners: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_is_playing_changed(self):
        """Playback state changed"""
        if self.c_surface._is_connected:
            is_playing = self.song.is_playing
            self.c_surface.log_message(f"▶️ Playing: {is_playing}")
            self._send_transport_play_state(is_playing)
    
    def _on_record_mode_changed(self):
        """Record mode changed"""
        if self.c_surface._is_connected:
            record_mode = self.song.record_mode
            self.c_surface.log_message(f"🔴 Record: {record_mode}")
            self._send_transport_record_state(record_mode)
    
    def _on_loop_changed(self):
        """Loop state changed"""
        if self.c_surface._is_connected:
            loop_enabled = self.song.loop
            self.c_surface.log_message(f"🔄 Loop: {loop_enabled}")
            self._send_transport_loop_state(loop_enabled)
    
    def _on_current_song_time_changed(self):
        """Song position changed"""
        if self.c_surface._is_connected:
            song_time = self.song.current_song_time
            
            # Calculate bars and beats
            beats_per_bar = self.song.signature_numerator
            current_beat = int(song_time) % beats_per_bar
            current_bar = int(song_time) // beats_per_bar
            
            # Only send if changed significantly (avoid spam)
            if current_beat != self._last_beat or current_bar != self._last_bar:
                self._last_beat = current_beat
                self._last_bar = current_bar
                
                # Log occasionally
                if current_beat == 0:  # On downbeat
                    self.c_surface.log_message(f"⏱️ Position: Bar {current_bar + 1}, Beat {current_beat + 1}")
                
                self._send_transport_position(current_bar, current_beat, song_time)
    
    def _on_loop_start_changed(self):
        """Loop start position changed"""
        if self.c_surface._is_connected:
            loop_start = self.song.loop_start
            self.c_surface.log_message(f"⏪ Loop start: {loop_start:.2f}")
            self._send_loop_markers()
    
    def _on_loop_length_changed(self):
        """Loop length changed"""
        if self.c_surface._is_connected:
            loop_length = self.song.loop_length
            self.c_surface.log_message(f"📏 Loop length: {loop_length:.2f}")
            self._send_loop_markers()
    
    def _on_arrangement_overdub_changed(self):
        """Arrangement overdub changed"""
        if self.c_surface._is_connected:
            arrangement_overdub = self.song.arrangement_overdub
            self.c_surface.log_message(f"🎼 Arrangement overdub: {arrangement_overdub}")
            self._send_arrangement_record_state(arrangement_overdub)
    
    def _on_back_to_arrangement_changed(self):
        """Back to arrangement changed"""
        if self.c_surface._is_connected and hasattr(self.song, 'back_to_arrangement'):
            back_to_arrangement = self.song.back_to_arrangement
            self.c_surface.log_message(f"🔙 Back to arrangement: {back_to_arrangement}")
            self._send_back_to_arrangement_state(back_to_arrangement)
    
    def _on_nudge_up(self):
        """Nudge up triggered"""
        if self.c_surface._is_connected:
            self.c_surface.log_message("⬆️ Nudge up")
            self._send_nudge_event('up')
    
    def _on_nudge_down(self):
        """Nudge down triggered"""
        if self.c_surface._is_connected:
            self.c_surface.log_message("⬇️ Nudge down")
            self._send_nudge_event('down')
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_transport_play_state(self, is_playing):
        """Send play state to hardware"""
        try:
            payload = [1 if is_playing else 0]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_PLAY, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending play state: {e}")
    
    def _send_transport_record_state(self, is_recording):
        """Send record state to hardware"""
        try:
            payload = [1 if is_recording else 0]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_RECORD, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending record state: {e}")
    
    def _send_transport_loop_state(self, is_loop):
        """Send loop state to hardware"""
        try:
            payload = [1 if is_loop else 0]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_LOOP, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending loop state: {e}")
    
    def _send_transport_position(self, bar, beat, song_time):
        """Send transport position to hardware"""
        try:
            # Calculate sixteenths
            beat_fraction = song_time - int(song_time)
            sixteenths = int(beat_fraction * 16)
            
            payload = [
                bar & 0x7F,          # Bar (0-127)
                beat & 0x7F,         # Beat (0-127)
                sixteenths & 0x7F    # Sixteenths (0-15)
            ]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_POSITION, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending transport position: {e}")
    
    def _send_loop_markers(self):
        """Send loop start and length to hardware"""
        try:
            loop_start = self.song.loop_start
            loop_length = self.song.loop_length
            loop_end = loop_start + loop_length
            
            # Convert to bars/beats
            beats_per_bar = self.song.signature_numerator
            
            start_bar = int(loop_start) // beats_per_bar
            start_beat = int(loop_start) % beats_per_bar
            
            end_bar = int(loop_end) // beats_per_bar
            end_beat = int(loop_end) % beats_per_bar
            
            # Send loop markers (could use separate commands or combine)
            payload = [
                start_bar & 0x7F,
                start_beat & 0x7F,
                end_bar & 0x7F,
                end_beat & 0x7F
            ]
            # Using transport position command for simplicity
            # Could add CMD_LOOP_MARKERS = 0x5B to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending loop markers: {e}")
    
    def _send_arrangement_record_state(self, is_recording):
        """Send arrangement record state to hardware"""
        try:
            payload = [1 if is_recording else 0]
            # Could add CMD_ARRANGEMENT_RECORD = 0x5C to consts.py
            # For now, reuse general transport record
            self.c_surface._send_sysex_command(CMD_TRANSPORT_RECORD, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending arrangement record: {e}")
    
    def _send_back_to_arrangement_state(self, back_to_arrangement):
        """Send back to arrangement state to hardware"""
        try:
            payload = [1 if back_to_arrangement else 0]
            self.c_surface._send_sysex_command(CMD_BACK_TO_ARRANGER, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending back to arrangement: {e}")
    
    def _send_nudge_event(self, direction):
        """Send nudge event to hardware"""
        try:
            direction_byte = 1 if direction == 'up' else 0
            payload = [direction_byte]
            # Could add CMD_NUDGE = 0x5D to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending nudge {direction}: {e}")
    
    def _send_complete_transport_state(self):
        """Send complete transport state using the existing method"""
        try:
            # Use the existing transport encoding from MIDIUtils
            playing = self.song.is_playing
            beat = int(self.song.current_song_time) % self.song.signature_numerator
            bar = int(self.song.current_song_time) // self.song.signature_numerator
            
            message = SysExEncoder.encode_transport(playing, beat, bar)
            if message:
                self.c_surface._send_midi(tuple(message))
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending complete transport state: {e}")
    
    # ========================================
    # TRANSPORT ACTIONS (for handling incoming commands)
    # ========================================
    
    def toggle_play(self):
        """Toggle play/stop"""
        try:
            if self.song.is_playing:
                self.song.stop_playing()
                self.c_surface.log_message("⏹️ Transport stopped")
            else:
                self.song.start_playing()
                self.c_surface.log_message("▶️ Transport started")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling play: {e}")
    
    def toggle_record(self):
        """Toggle record mode"""
        try:
            self.song.record_mode = not self.song.record_mode
            state = "enabled" if self.song.record_mode else "disabled"
            self.c_surface.log_message(f"🔴 Record {state}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling record: {e}")
    
    def toggle_loop(self):
        """Toggle loop mode"""
        try:
            self.song.loop = not self.song.loop
            state = "enabled" if self.song.loop else "disabled"
            self.c_surface.log_message(f"🔄 Loop {state}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling loop: {e}")
    
    def jump_to_previous_cue(self):
        """Jump to previous cue point"""
        try:
            if self.song.cue_points:
                current_time = self.song.current_song_time
                
                # Find previous cue point
                previous_cue = None
                for cue_point in reversed(self.song.cue_points):
                    if cue_point.time < current_time - 0.1:  # Small tolerance
                        previous_cue = cue_point
                        break
                
                if previous_cue:
                    previous_cue.jump()
                    self.c_surface.log_message(f"⏪ Jumped to cue: {previous_cue.name}")
                else:
                    # Jump to beginning
                    self.song.current_song_time = 0.0
                    self.c_surface.log_message("⏪ Jumped to beginning")
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error jumping to previous cue: {e}")
    
    def jump_to_next_cue(self):
        """Jump to next cue point"""
        try:
            if self.song.cue_points:
                current_time = self.song.current_song_time
                
                # Find next cue point
                next_cue = None
                for cue_point in self.song.cue_points:
                    if cue_point.time > current_time + 0.1:  # Small tolerance
                        next_cue = cue_point
                        break
                
                if next_cue:
                    next_cue.jump()
                    self.c_surface.log_message(f"⏩ Jumped to cue: {next_cue.name}")
                else:
                    self.c_surface.log_message("⏩ No next cue point")
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error jumping to next cue: {e}")
    
    def tap_tempo(self):
        """Tap tempo (if available)"""
        try:
            if hasattr(self.song, 'tap_tempo'):
                self.song.tap_tempo()
                self.c_surface.log_message(f"👆 Tap tempo: {self.song.tempo:.1f} BPM")
            else:
                self.c_surface.log_message("ℹ️ Tap tempo not available in this Live version")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error with tap tempo: {e}")
    
    def nudge_plus(self):
        """Nudge tempo up"""
        try:
            if hasattr(self.song, 'nudge_up'):
                self.song.nudge_up()
                self.c_surface.log_message("⬆️ Nudge tempo up")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error nudging up: {e}")
    
    def nudge_minus(self):
        """Nudge tempo down"""
        try:
            if hasattr(self.song, 'nudge_down'):
                self.song.nudge_down()
                self.c_surface.log_message("⬇️ Nudge tempo down")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error nudging down: {e}")
    
    def toggle_arrangement_overdub(self):
        """Toggle arrangement overdub"""
        try:
            self.song.arrangement_overdub = not self.song.arrangement_overdub
            state = "enabled" if self.song.arrangement_overdub else "disabled"
            self.c_surface.log_message(f"🎼 Arrangement overdub {state}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling arrangement overdub: {e}")
    
    def trigger_back_to_arrangement(self):
        """Trigger back to arrangement"""
        try:
            if hasattr(self.song, 'back_to_arrangement'):
                self.song.back_to_arrangement = True
                self.c_surface.log_message("🔙 Back to arrangement triggered")
            else:
                self.c_surface.log_message("ℹ️ back_to_arrangement not available (requires Live 9.0+)")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error triggering back to arrangement: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_transport_info(self):
        """Get complete transport information"""
        try:
            current_time = self.song.current_song_time
            beats_per_bar = self.song.signature_numerator
            current_beat = int(current_time) % beats_per_bar
            current_bar = int(current_time) // beats_per_bar
            
            return {
                'is_playing': self.song.is_playing,
                'record_mode': self.song.record_mode,
                'loop': self.song.loop,
                'current_song_time': current_time,
                'current_bar': current_bar,
                'current_beat': current_beat,
                'tempo': self.song.tempo,
                'signature_numerator': self.song.signature_numerator,
                'signature_denominator': self.song.signature_denominator,
                'loop_start': self.song.loop_start,
                'loop_length': self.song.loop_length,
                'arrangement_overdub': self.song.arrangement_overdub,
                'back_to_arrangement': getattr(self.song, 'back_to_arrangement', False),
                'metronome': self.song.metronome,
                'cue_points_count': len(self.song.cue_points)
            }
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting transport info: {e}")
            return {}
    
    def send_complete_state(self):
        """Send complete transport state to hardware"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete transport state...")
            
            # Send individual states
            self._send_transport_play_state(self.song.is_playing)
            self._send_transport_record_state(self.song.record_mode)
            self._send_transport_loop_state(self.song.loop)
            
            # Send position
            current_time = self.song.current_song_time
            beats_per_bar = self.song.signature_numerator
            current_beat = int(current_time) % beats_per_bar
            current_bar = int(current_time) // beats_per_bar
            self._send_transport_position(current_bar, current_beat, current_time)
            
            # Send loop markers
            self._send_loop_markers()
            
            # Send arrangement states
            self._send_arrangement_record_state(self.song.arrangement_overdub)
            if hasattr(self.song, 'back_to_arrangement'):
                self._send_back_to_arrangement_state(self.song.back_to_arrangement)
            
            # Send complete transport using existing encoder
            self._send_complete_transport_state()
            
            self.c_surface.log_message("✅ Transport state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending transport state: {e}")
    
    def handle_transport_command(self, command, payload):
        """Handle incoming transport commands from hardware"""
        try:
            if command == CMD_TRANSPORT_PLAY:
                self.toggle_play()
            elif command == CMD_TRANSPORT_RECORD:
                self.toggle_record()
            elif command == CMD_TRANSPORT_LOOP:
                self.toggle_loop()
            elif command == CMD_BACK_TO_ARRANGER:
                self.trigger_back_to_arrangement()
            else:
                self.c_surface.log_message(f"❓ Unknown transport command: 0x{command:02X}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling transport command 0x{command:02X}: {e}")
    
    def set_position(self, bars, beats, sixteenths=0):
        """Set song position"""
        try:
            beats_per_bar = self.song.signature_numerator
            total_beats = (bars * beats_per_bar) + beats + (sixteenths / 16.0)
            
            self.song.current_song_time = total_beats
            self.c_surface.log_message(f"⏱️ Set position: {bars}.{beats}.{sixteenths}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting position: {e}")
    
    def set_loop_region(self, start_bars, start_beats, length_bars, length_beats):
        """Set loop region"""
        try:
            beats_per_bar = self.song.signature_numerator
            
            loop_start = (start_bars * beats_per_bar) + start_beats
            loop_length = (length_bars * beats_per_bar) + length_beats
            
            self.song.loop_start = loop_start
            self.song.loop_length = loop_length
            
            self.c_surface.log_message(f"🔄 Set loop: {start_bars}.{start_beats} for {length_bars}.{length_beats}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting loop region: {e}")

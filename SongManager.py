# SongManager.py - Song, Application and Global Settings Management
"""
Manages Song-level properties and global application settings
Based on Live Object Model: Song, Application, TuningSystem, CuePoints
"""

from .consts import *
from .MIDIUtils import SysExEncoder

class SongManager:
    """
    Manages all Song-level listeners and handlers
    Covers: Song properties, tempo, signature, metronome, cue points, global settings
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self.app = control_surface.application()
        self._listeners = []
        self._is_active = False
        
        self.c_surface.log_message("🔧 Initializing SongManager...")
        
        # CPU monitoring throttling
        self._cpu_monitor_enabled = ENABLE_CPU_USAGE_STREAM
        self._last_cpu_log_time = 0
        self._cpu_log_interval = 5.0  # Log CPU only every 5 seconds
        self._last_cpu_values = (0, 0)  # (avg, peak)
        self._cpu_alert_threshold = 70.0  # Alert only when > 70%
        
    def setup_listeners(self):
        """Setup all song-level listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("🎵 Setting up Song listeners...")
            
            # === SONG LISTENERS ===
            self._add_song_listeners()
            
            # === APPLICATION LISTENERS ===
            self._add_application_listeners()
            
            # === CUE POINTS LISTENERS ===
            self._add_cue_point_listeners()
            
            self._is_active = True
            self.c_surface.log_message("✅ Song listeners setup complete")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up song listeners: {e}")
    
    def _add_song_listeners(self):
        """Add Song object listeners"""
        # Tempo
        tempo_listener = lambda: self._on_tempo_changed()
        self.song.add_tempo_listener(tempo_listener)
        self._listeners.append(('tempo', tempo_listener))
        
        # Time Signature
        sig_num_listener = lambda: self._on_signature_changed()
        sig_den_listener = lambda: self._on_signature_changed()
        self.song.add_signature_numerator_listener(sig_num_listener)
        self.song.add_signature_denominator_listener(sig_den_listener)
        self._listeners.extend([
            ('signature_numerator', sig_num_listener),
            ('signature_denominator', sig_den_listener)
        ])
        
        # Song Time (Current Position)
        song_time_listener = lambda: self._on_song_time_changed()
        self.song.add_current_song_time_listener(song_time_listener)
        self._listeners.append(('current_song_time', song_time_listener))
        
        # Metronome
        metronome_listener = lambda: self._on_metronome_changed()
        self.song.add_metronome_listener(metronome_listener)
        self._listeners.append(('metronome', metronome_listener))
        
        # Overdub
        overdub_listener = lambda: self._on_overdub_changed()
        self.song.add_overdub_listener(overdub_listener)
        self._listeners.append(('overdub', overdub_listener))
        
        # Tracks list changes (when tracks are added/removed)
        tracks_listener = lambda: self._on_tracks_changed()
        self.song.add_tracks_listener(tracks_listener)
        self._listeners.append(('tracks', tracks_listener))
        
        # Punch In/Out
        punch_in_listener = lambda: self._on_punch_in_changed()
        punch_out_listener = lambda: self._on_punch_out_changed()
        self.song.add_punch_in_listener(punch_in_listener)
        self.song.add_punch_out_listener(punch_out_listener)
        self._listeners.extend([
            ('punch_in', punch_in_listener),
            ('punch_out', punch_out_listener)
        ])
        
        # MIDI Recording Quantization
        midi_quant_listener = lambda: self._on_midi_recording_quantization_changed()
        self.song.add_midi_recording_quantization_listener(midi_quant_listener)
        self._listeners.append(('midi_recording_quantization', midi_quant_listener))
        
        # Session Record
        if hasattr(self.song, 'session_record'):
            session_record_listener = lambda: self._on_session_record_changed()
            self.song.add_session_record_listener(session_record_listener)
            self._listeners.append(('session_record', session_record_listener))
    
    def _add_application_listeners(self):
        """Add Application object listeners"""
        # CPU Usage (optional)
        if self._cpu_monitor_enabled:
            cpu_listener = lambda: self._on_cpu_usage_changed()
            self.app.add_average_process_usage_listener(cpu_listener)
            self.app.add_peak_process_usage_listener(cpu_listener)
            self._listeners.extend([
                ('average_cpu', cpu_listener),
                ('peak_cpu', cpu_listener)
            ])
        
        # Control Surfaces
        control_surfaces_listener = lambda: self._on_control_surfaces_changed()
        self.app.add_control_surfaces_listener(control_surfaces_listener)
        self._listeners.append(('control_surfaces', control_surfaces_listener))
    
    def _add_cue_point_listeners(self):
        """Add CuePoint listeners"""
        # Main cue points list
        cue_points_listener = lambda: self._on_cue_points_changed()
        self.song.add_cue_points_listener(cue_points_listener)
        self._listeners.append(('cue_points', cue_points_listener))
        
        # Individual cue point listeners
        for i, cue_point in enumerate(self.song.cue_points):
            name_listener = lambda idx=i: self._on_cue_point_name_changed(idx)
            time_listener = lambda idx=i: self._on_cue_point_time_changed(idx)
            
            cue_point.add_name_listener(name_listener)
            cue_point.add_time_listener(time_listener)
            
            self._listeners.extend([
                (f'cue_point_{i}_name', name_listener),
                (f'cue_point_{i}_time', time_listener)
            ])
    
    def cleanup_listeners(self):
        """Remove all song listeners"""
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 'tempo':
                        self.song.remove_tempo_listener(listener_func)
                    elif listener_type == 'signature_numerator':
                        self.song.remove_signature_numerator_listener(listener_func)
                    elif listener_type == 'signature_denominator':
                        self.song.remove_signature_denominator_listener(listener_func)
                    elif listener_type == 'current_song_time':
                        self.song.remove_current_song_time_listener(listener_func)
                    elif listener_type == 'metronome':
                        self.song.remove_metronome_listener(listener_func)
                    elif listener_type == 'overdub':
                        self.song.remove_overdub_listener(listener_func)
                    elif listener_type == 'tracks':
                        self.song.remove_tracks_listener(listener_func)
                    elif listener_type == 'punch_in':
                        self.song.remove_punch_in_listener(listener_func)
                    elif listener_type == 'punch_out':
                        self.song.remove_punch_out_listener(listener_func)
                    elif listener_type == 'midi_recording_quantization':
                        self.song.remove_midi_recording_quantization_listener(listener_func)
                    elif listener_type == 'session_record':
                        self.song.remove_session_record_listener(listener_func)
                    elif listener_type == 'average_cpu':
                        self.app.remove_average_process_usage_listener(listener_func)
                    elif listener_type == 'peak_cpu':
                        self.app.remove_peak_process_usage_listener(listener_func)
                    elif listener_type == 'control_surfaces':
                        self.app.remove_control_surfaces_listener(listener_func)
                    elif listener_type == 'cue_points':
                        self.song.remove_cue_points_listener(listener_func)
                    elif 'cue_point_' in listener_type:
                        # Handle individual cue point listeners
                        parts = listener_type.split('_')
                        cue_idx = int(parts[2])
                        if cue_idx < len(self.song.cue_points):
                            cue_point = self.song.cue_points[cue_idx]
                            if 'name' in listener_type:
                                cue_point.remove_name_listener(listener_func)
                            elif 'time' in listener_type:
                                cue_point.remove_time_listener(listener_func)
                except:
                    pass  # Ignore if already removed
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Song listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning song listeners: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_tempo_changed(self):
        """Tempo changed"""
        if self.c_surface._is_connected:
            tempo = self.song.tempo
            self.c_surface.log_message(f"🎵 Tempo: {tempo:.2f} BPM")
            self._send_tempo_state(tempo)
    
    def _on_signature_changed(self):
        """Time signature changed"""
        if self.c_surface._is_connected:
            numerator = self.song.signature_numerator
            denominator = self.song.signature_denominator
            self.c_surface.log_message(f"🎼 Signature: {numerator}/{denominator}")
            self._send_signature_state(numerator, denominator)
    
    def _on_song_time_changed(self):
        """Song position changed"""
        if self.c_surface._is_connected:
            song_time = self.song.current_song_time
            # Only log occasionally to avoid spam
            if int(song_time) % 4 == 0:  # Every 4 beats
                self.c_surface.log_message(f"⏱️ Position: {song_time:.2f} beats")
            self._send_song_position_state(song_time)
    
    def _on_metronome_changed(self):
        """Metronome state changed"""
        if self.c_surface._is_connected:
            metronome = self.song.metronome
            self.c_surface.log_message(f"🔔 Metronome: {metronome}")
            self._send_metronome_state(metronome)
    
    def _on_overdub_changed(self):
        """Overdub state changed"""
        if self.c_surface._is_connected:
            overdub = self.song.overdub
            self.c_surface.log_message(f"🔄 Overdub: {overdub}")
            self._send_overdub_state(overdub)
    
    def _on_tracks_changed(self):
        """Tracks list changed (track added/removed)"""
        if self.c_surface._is_connected:
            track_count = len(self.song.tracks)
            self.c_surface.log_message(f"🎚️ Tracks changed: {track_count} tracks total")
            
            # Notify all managers to refresh their listeners
            if hasattr(self.c_surface, '_managers'):
                if 'track' in self.c_surface._managers:
                    self.c_surface._managers['track'].refresh_all_tracks()
                if 'device' in self.c_surface._managers:
                    self.c_surface._managers['device'].refresh_all_tracks()
                if 'clip' in self.c_surface._managers:
                    self.c_surface._managers['clip'].refresh_all_tracks()
    
    def _on_punch_in_changed(self):
        """Punch in changed"""
        if self.c_surface._is_connected:
            punch_in = self.song.punch_in
            self.c_surface.log_message(f"⏯️ Punch In: {punch_in}")
            self._send_punch_state('in', punch_in)
    
    def _on_punch_out_changed(self):
        """Punch out changed"""
        if self.c_surface._is_connected:
            punch_out = self.song.punch_out
            self.c_surface.log_message(f"⏹️ Punch Out: {punch_out}")
            self._send_punch_state('out', punch_out)
    
    def _on_midi_recording_quantization_changed(self):
        """MIDI quantization changed"""
        if self.c_surface._is_connected:
            quantization = self.song.midi_recording_quantization
            self.c_surface.log_message(f"📏 MIDI Quantization: {quantization}")
            self._send_quantization_state(quantization)
    
    def _on_session_record_changed(self):
        """Session record changed"""
        if self.c_surface._is_connected:
            session_record = self.song.session_record
            self.c_surface.log_message(f"🎙️ Session Record: {session_record}")
            self._send_session_record_state(session_record)
    
    def _on_cpu_usage_changed(self):
        """CPU usage changed - optional stream to hardware"""
        if not (self.c_surface._is_connected and self._cpu_monitor_enabled):
            return
            
        try:
            avg_cpu = getattr(self.app, 'average_process_usage', 0.0)
            peak_cpu = getattr(self.app, 'peak_process_usage', 0.0)
            
            # Only log when CPU is REALLY high (above 80%)
            if peak_cpu > 80.0:
                self.c_surface.log_message(f"⚠️ VERY HIGH CPU: Avg:{avg_cpu:.1f}% Peak:{peak_cpu:.1f}%")
            
            # Send to hardware throttled (once per second max)
            import time
            now = time.time()
            last_sent = getattr(self, '_last_cpu_send', 0)
            if now - last_sent >= self._cpu_log_interval:
                self._last_cpu_send = now
                self._send_cpu_usage_state(avg_cpu, peak_cpu)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error in CPU monitoring: {e}")
    
    def _on_control_surfaces_changed(self):
        """Control surfaces changed"""
        if self.c_surface._is_connected:
            surfaces = self.app.control_surfaces
            self.c_surface.log_message(f"🎛️ Control Surfaces: {len(surfaces)} active")
            self._send_control_surfaces_state(surfaces)
    
    def _on_cue_points_changed(self):
        """Cue points list changed"""
        if self.c_surface._is_connected:
            cue_points = self.song.cue_points
            self.c_surface.log_message(f"📍 Cue Points: {len(cue_points)} markers")
            self._send_cue_points_list(cue_points)
    
    def _on_cue_point_name_changed(self, cue_idx):
        """Individual cue point name changed"""
        if self.c_surface._is_connected and cue_idx < len(self.song.cue_points):
            cue_point = self.song.cue_points[cue_idx]
            self.c_surface.log_message(f"📍 Cue {cue_idx} name: '{cue_point.name}'")
            self._send_cue_point_state(cue_idx, cue_point)
    
    def _on_cue_point_time_changed(self, cue_idx):
        """Individual cue point time changed"""
        if self.c_surface._is_connected and cue_idx < len(self.song.cue_points):
            cue_point = self.song.cue_points[cue_idx]
            self.c_surface.log_message(f"📍 Cue {cue_idx} time: {cue_point.time:.2f}")
            self._send_cue_point_state(cue_idx, cue_point)
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_tempo_state(self, tempo):
        """Send tempo to hardware"""
        try:
            # Convert tempo to int (BPM) and fraction
            tempo_int = int(tempo)
            tempo_fraction = int((tempo - tempo_int) * 100)  # 0-99
            
            payload = [tempo_int, tempo_fraction]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_TEMPO, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending tempo: {e}")
    
    def _send_signature_state(self, numerator, denominator):
        """Send time signature to hardware"""
        try:
            payload = [numerator, denominator]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_SIGNATURE, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending signature: {e}")
    
    def _send_song_position_state(self, song_time):
        """Send song position to hardware"""
        try:
            # Convert to bars.beats.sixteenths using current time signature
            numerator = max(1, int(self.song.signature_numerator))
            denominator = max(1, int(self.song.signature_denominator))
            quarter_per_beat = 4.0 / denominator
            bar_length_quarters = numerator * quarter_per_beat
            if bar_length_quarters <= 0:
                bar_length_quarters = 4.0
            
            bars = int(song_time // bar_length_quarters)
            beat_time = song_time - (bars * bar_length_quarters)
            current_beat = int(beat_time // quarter_per_beat)
            beat_fraction = beat_time - (current_beat * quarter_per_beat)
            sixteenths = int((song_time - int(song_time)) * 16) & 0x7F
            beats = current_beat & 0x7F
            
            payload = [bars & 0x7F, beats, sixteenths]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_POSITION, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending position: {e}")
    
    def _send_metronome_state(self, metronome):
        """Send metronome state to hardware"""
        try:
            payload = [1 if metronome else 0]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_METRONOME, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending metronome: {e}")
    
    def _send_overdub_state(self, overdub):
        """Send overdub state to hardware"""
        try:
            payload = [1 if overdub else 0]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_OVERDUB, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending overdub: {e}")
    
    def _send_punch_state(self, punch_type, state):
        """Send punch in/out state to hardware"""
        try:
            punch_type_byte = 1 if punch_type == 'in' else 2
            payload = [punch_type_byte, 1 if state else 0]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_PUNCH, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending punch {punch_type}: {e}")
    
    def _send_quantization_state(self, quantization):
        """Send MIDI quantization to hardware"""
        try:
            # Map quantization values to hardware-friendly format
            quant_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}  # Can be extended
            quant_value = quant_map.get(quantization, 0)
            
            payload = [quant_value]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_QUANTIZE, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending quantization: {e}")
    
    def _send_session_record_state(self, session_record):
        """Send session record state to hardware"""
        try:
            payload = [1 if session_record else 0]
            self.c_surface._send_sysex_command(CMD_SESSION_RECORD, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending session record: {e}")
    
    def _send_cpu_usage_state(self, avg_cpu, peak_cpu):
        """Send CPU usage to hardware"""
        if not self._cpu_monitor_enabled:
            return
        try:
            # Convert to 0-127 range
            avg_byte = int(avg_cpu * 127)
            peak_byte = int(peak_cpu * 127)
            
            payload = [avg_byte & 0x7F, peak_byte & 0x7F]
            self.c_surface._send_sysex_command(CMD_CPU_USAGE, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending CPU usage: {e}")
    
    def _send_control_surfaces_state(self, surfaces):
        """Send control surfaces info to hardware"""
        try:
            payload = [len(surfaces)]
            # Add surface IDs if needed
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending control surfaces: {e}")
    
    def _send_cue_points_list(self, cue_points):
        """Send cue points list to hardware"""
        try:
            payload = [len(cue_points)]
            # Could send basic info about each cue point
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending cue points list: {e}")
    
    def _send_cue_point_state(self, cue_idx, cue_point):
        """Send individual cue point state to hardware"""
        try:
            name_bytes = cue_point.name.encode('utf-8')[:12]  # Max 12 chars
            time_bars = int(cue_point.time) // 4
            time_beats = int(cue_point.time) % 4
            
            payload = [cue_idx & 0x7F, time_bars & 0x7F, time_beats & 0x7F, len(name_bytes) & 0x7F]
            payload.extend([b & 0x7F for b in name_bytes])  # Ensure 7-bit

            self.c_surface._send_sysex_command(CMD_CUE_POINT, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending cue point {cue_idx}: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_song_info(self):
        """Get complete song information"""
        return {
            'tempo': self.song.tempo,
            'signature': f"{self.song.signature_numerator}/{self.song.signature_denominator}",
            'current_time': self.song.current_song_time,
            'metronome': self.song.metronome,
            'overdub': self.song.overdub,
            'punch_in': self.song.punch_in,
            'punch_out': self.song.punch_out,
            'quantization': self.song.midi_recording_quantization,
            'session_record': getattr(self.song, 'session_record', False),
            'cue_points_count': len(self.song.cue_points)
        }
    
    def send_complete_state(self):
        """Send complete song state to hardware"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete song state...")
            
            # Send all current states
            self._send_tempo_state(self.song.tempo)
            self._send_signature_state(self.song.signature_numerator, self.song.signature_denominator)
            self._send_song_position_state(self.song.current_song_time)
            self._send_metronome_state(self.song.metronome)
            self._send_overdub_state(self.song.overdub)
            self._send_punch_state('in', self.song.punch_in)
            self._send_punch_state('out', self.song.punch_out)
            self._send_quantization_state(self.song.midi_recording_quantization)
            
            if hasattr(self.song, 'session_record'):
                self._send_session_record_state(self.song.session_record)
            
            if self._cpu_monitor_enabled:
                self._send_cpu_usage_state(self.app.average_process_usage, self.app.peak_process_usage)
            self._send_cue_points_list(self.song.cue_points)
            
            self.c_surface.log_message("✅ Song state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending song state: {e}")

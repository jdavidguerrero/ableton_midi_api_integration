# TrackManager.py - Track and Mixer Management
"""
Manages Track-level properties and mixer functionality
Based on Live Object Model: Track, MixerDevice, DeviceIO
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class TrackManager:
    """
    Manages all Track-level listeners and handlers
    Covers: Track properties, mixer, routing, states
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self._track_listeners = {}  # track_idx: [listeners]
        self._is_active = False

        self.c_surface.log_message("🔧 Initializing TrackManager...")

        # Metering throttling (prevent MIDI saturation)
        self._meter_values = {}      # track_idx: current_peak
        self._meter_last_sent = {}   # track_idx: timestamp_ms
        self._meter_interval_ms = 50 # 20Hz update rate (instead of 60Hz raw)
        
    def setup_listeners(self, max_tracks=8):
        """Setup track listeners for specified number of tracks"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message(f"🎛️ Setting up Track listeners for {max_tracks} tracks...")
            
            for track_idx in range(min(max_tracks, len(self.song.tracks))):
                self._setup_single_track_listeners(track_idx)
            
            self._is_active = True
            self.c_surface.log_message(f"✅ Track listeners setup for {len(self._track_listeners)} tracks")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up track listeners: {e}")
    
    def _setup_single_track_listeners(self, track_idx):
        """Setup listeners for a single track"""
        if track_idx in self._track_listeners:
            return  # Already setup
            
        try:
            track = self.song.tracks[track_idx]
            listeners = []
            
            # === BASIC TRACK PROPERTIES ===
            
            # Name
            name_listener = lambda idx=track_idx: self._on_track_name_changed(idx)
            track.add_name_listener(name_listener)
            listeners.append(('name', name_listener))
            
            # Color
            color_listener = lambda idx=track_idx: self._on_track_color_changed(idx)
            track.add_color_listener(color_listener)
            listeners.append(('color', color_listener))
            
            # Mute/Solo
            mute_listener = lambda idx=track_idx: self._on_track_mute_changed(idx)
            solo_listener = lambda idx=track_idx: self._on_track_solo_changed(idx)
            track.add_mute_listener(mute_listener)
            track.add_solo_listener(solo_listener)
            listeners.extend([
                ('mute', mute_listener),
                ('solo', solo_listener)
            ])
            
            # Arm (only for audio/MIDI tracks)
            if hasattr(track, 'can_be_armed') and track.can_be_armed:
                arm_listener = lambda idx=track_idx: self._on_track_arm_changed(idx)
                track.add_arm_listener(arm_listener)
                listeners.append(('arm', arm_listener))
            
            # === TRACK STATES ===
            
            # Playing slot index
            playing_slot_listener = lambda idx=track_idx: self._on_track_playing_slot_changed(idx)
            track.add_playing_slot_index_listener(playing_slot_listener)
            listeners.append(('playing_slot_index', playing_slot_listener))
            
            # Fired slot index
            fired_slot_listener = lambda idx=track_idx: self._on_track_fired_slot_changed(idx)
            track.add_fired_slot_index_listener(fired_slot_listener)
            listeners.append(('fired_slot_index', fired_slot_listener))
            
            # Fold state (for group tracks)
            if hasattr(track, 'is_foldable') and track.is_foldable:
                fold_listener = lambda idx=track_idx: self._on_track_fold_changed(idx)
                track.add_is_folded_listener(fold_listener)
                listeners.append(('is_folded', fold_listener))
            
            # Devices list changes (when devices are added/removed)
            if hasattr(track, 'devices'):
                devices_listener = lambda idx=track_idx: self._on_track_devices_changed(idx)
                track.add_devices_listener(devices_listener)
                listeners.append(('devices', devices_listener))

            # Output metering (VU meter with throttling)
            if hasattr(track, 'output_meter_level'):
                meter_listener = lambda idx=track_idx: self._on_track_meter_changed(idx)
                track.add_output_meter_level_listener(meter_listener)
                listeners.append(('output_meter_level', meter_listener))
                # Initialize throttling variables
                self._meter_values[track_idx] = 0.0
                self._meter_last_sent[track_idx] = 0

            # === MIXER DEVICE ===
            self._setup_mixer_listeners(track_idx, track, listeners)
            
            # Store all listeners for this track
            self._track_listeners[track_idx] = listeners
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up track {track_idx} listeners: {e}")
    
    def _setup_mixer_listeners(self, track_idx, track, listeners):
        """Setup mixer device listeners for a track"""
        try:
            mixer = track.mixer_device
            
            # Volume
            volume_listener = lambda idx=track_idx: self._on_track_volume_changed(idx)
            mixer.volume.add_value_listener(volume_listener)
            listeners.append(('volume', volume_listener))
            
            # Panning
            pan_listener = lambda idx=track_idx: self._on_track_pan_changed(idx)
            mixer.panning.add_value_listener(pan_listener)
            listeners.append(('panning', pan_listener))
            
            # Sends (typically A, B, C)
            for send_idx, send in enumerate(mixer.sends[:3]):  # Limit to 3 sends
                send_listener = lambda t_idx=track_idx, s_idx=send_idx: self._on_track_send_changed(t_idx, s_idx)
                send.add_value_listener(send_listener)
                listeners.append((f'send_{send_idx}', send_listener))

            # Crossfade Assign (A/None/B for DJ-style crossfader)
            if hasattr(mixer, 'crossfade_assign'):
                crossfade_listener = lambda idx=track_idx: self._on_track_crossfade_changed(idx)
                mixer.add_crossfade_assign_listener(crossfade_listener)
                listeners.append(('crossfade_assign', crossfade_listener))

            # Cue Volume (solo/master headphone) - only available on master track
            if track is self.song.master_track:
                cue_control = getattr(mixer, 'cue_volume', None)
                if cue_control:
                    cue_listener = lambda idx=track_idx: self._on_track_cue_volume_changed(idx)
                    cue_control.add_value_listener(cue_listener)
                    listeners.append(('cue_volume', cue_listener))

        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up mixer listeners for track {track_idx}: {e}")
    
    def cleanup_listeners(self):
        """Remove all track listeners"""
        if not self._is_active:
            return
            
        try:
            for track_idx, listeners in self._track_listeners.items():
                if track_idx < len(self.song.tracks):
                    track = self.song.tracks[track_idx]
                    mixer = track.mixer_device
                    
                    for listener_type, listener_func in listeners:
                        try:
                            if listener_type == 'name':
                                track.remove_name_listener(listener_func)
                            elif listener_type == 'color':
                                track.remove_color_listener(listener_func)
                            elif listener_type == 'mute':
                                track.remove_mute_listener(listener_func)
                            elif listener_type == 'solo':
                                track.remove_solo_listener(listener_func)
                            elif listener_type == 'arm':
                                track.remove_arm_listener(listener_func)
                            elif listener_type == 'playing_slot_index':
                                track.remove_playing_slot_index_listener(listener_func)
                            elif listener_type == 'fired_slot_index':
                                track.remove_fired_slot_index_listener(listener_func)
                            elif listener_type == 'is_folded':
                                track.remove_is_folded_listener(listener_func)
                            elif listener_type == 'devices':
                                track.remove_devices_listener(listener_func)
                            elif listener_type == 'volume':
                                mixer.volume.remove_value_listener(listener_func)
                            elif listener_type == 'panning':
                                mixer.panning.remove_value_listener(listener_func)
                            elif listener_type.startswith('send_'):
                                send_idx = int(listener_type.split('_')[1])
                                if send_idx < len(mixer.sends):
                                    mixer.sends[send_idx].remove_value_listener(listener_func)
                            elif listener_type == 'output_meter_level':
                                track.remove_output_meter_level_listener(listener_func)
                            elif listener_type == 'crossfade_assign':
                                mixer.remove_crossfade_assign_listener(listener_func)
                            elif listener_type == 'cue_volume':
                                mixer.cue_volume.remove_value_listener(listener_func)
                        except:
                            pass  # Ignore if already removed
            
            self._track_listeners = {}
            self._is_active = False
            self.c_surface.log_message("✅ Track listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning track listeners: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_track_name_changed(self, track_idx):
        """Track name changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            self.c_surface.log_message(f"📝 Track {track_idx} name: '{track.name}'")
            self._send_track_name(track_idx, track.name)
    
    def _on_track_color_changed(self, track_idx):
        """Track color changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            color_rgb = ColorUtils.live_color_to_rgb(track.color)
            self.c_surface.log_message(f"🎨 Track {track_idx} color: {color_rgb}")
            self._send_track_color(track_idx, color_rgb)
    
    def _on_track_mute_changed(self, track_idx):
        """Track mute changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            self.c_surface.log_message(f"🔇 Track {track_idx} mute: {track.mute}")
            self._send_track_mute_state(track_idx, track.mute)
    
    def _on_track_solo_changed(self, track_idx):
        """Track solo changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            self.c_surface.log_message(f"🔊 Track {track_idx} solo: {track.solo}")
            self._send_track_solo_state(track_idx, track.solo)
    
    def _on_track_arm_changed(self, track_idx):
        """Track arm changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            is_armed = track.arm if hasattr(track, 'can_be_armed') and track.can_be_armed else False
            self.c_surface.log_message(f"🔴 Track {track_idx} arm: {is_armed}")
            self._send_track_arm_state(track_idx, is_armed)
    
    def _on_track_playing_slot_changed(self, track_idx):
        """Track playing slot changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            playing_slot = track.playing_slot_index
            self.c_surface.log_message(f"▶️ Track {track_idx} playing slot: {playing_slot}")
            self._send_track_playing_slot(track_idx, playing_slot)
    
    def _on_track_fired_slot_changed(self, track_idx):
        """Track fired slot changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            fired_slot = track.fired_slot_index
            self.c_surface.log_message(f"🔥 Track {track_idx} fired slot: {fired_slot}")
            self._send_track_fired_slot(track_idx, fired_slot)
    
    def _on_track_fold_changed(self, track_idx):
        """Track fold state changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            is_folded = track.is_folded if hasattr(track, 'is_folded') else False
            self.c_surface.log_message(f"📁 Track {track_idx} folded: {is_folded}")
            self._send_track_fold_state(track_idx, is_folded)
    
    def _on_track_devices_changed(self, track_idx):
        """Track devices list changed (device added/removed)"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            device_count = len(track.devices) if hasattr(track, 'devices') else 0
            self.c_surface.log_message(f"🎛️ Track {track_idx} devices changed: {device_count} devices")
            
            # Notify DeviceManager to refresh device listeners
            if hasattr(self.c_surface, '_managers') and 'device' in self.c_surface._managers:
                self.c_surface._managers['device'].refresh_track_devices(track_idx)
            
            # Send updated track state
            self.send_complete_track_state(track_idx)
    
    def _on_track_volume_changed(self, track_idx):
        """Track volume changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            volume = track.mixer_device.volume.value
            # Only log volume changes if parameter logging is enabled
            from .consts import LOG_PARAMETER_CHANGES
            if LOG_PARAMETER_CHANGES:
                self.c_surface.log_message(f"🔊 Track {track_idx} volume: {volume:.2f}")
            self._send_track_volume_state(track_idx, volume)
    
    def _on_track_pan_changed(self, track_idx):
        """Track pan changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            pan = track.mixer_device.panning.value
            self.c_surface.log_message(f"◀️▶️ Track {track_idx} pan: {pan:.2f}")
            self._send_track_pan_state(track_idx, pan)
    
    def _on_track_send_changed(self, track_idx, send_idx):
        """Track send changed"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            if send_idx < len(track.mixer_device.sends):
                send_value = track.mixer_device.sends[send_idx].value
                self.c_surface.log_message(f"📤 Track {track_idx} send {send_idx}: {send_value:.2f}")
                self._send_track_send_state(track_idx, send_idx, send_value)

    def _on_track_crossfade_changed(self, track_idx):
        """Track crossfade assign changed (A/None/B)"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            mixer = track.mixer_device
            if hasattr(mixer, 'crossfade_assign'):
                # crossfade_assign values: 0=A (left), 1=None (center), 2=B (right)
                crossfade = mixer.crossfade_assign
                crossfade_str = ['A', 'None', 'B'][crossfade]
                self.c_surface.log_message(f"⚡ Track {track_idx} crossfade: {crossfade_str}")
                self._send_track_crossfade(track_idx, crossfade)

    def _on_track_cue_volume_changed(self, track_idx):
        """Track cue volume changed (pre-listen/headphone monitoring)"""
        if self.c_surface._is_connected and track_idx < len(self.song.tracks):
            track = self.song.tracks[track_idx]
            mixer = track.mixer_device
            if hasattr(mixer, 'cue_volume'):
                cue_volume = mixer.cue_volume.value  # 0.0 to 1.0
                self.c_surface.log_message(f"🎧 Track {track_idx} cue volume: {cue_volume:.2f}")
                self._send_track_cue_volume(track_idx, cue_volume)

    def _on_track_meter_changed(self, track_idx):
        """Track output meter level changed (VU meter with throttling)"""
        if not self.c_surface._is_connected or track_idx >= len(self.song.tracks):
            return

        try:
            import time
            track = self.song.tracks[track_idx]
            current_time_ms = int(time.time() * 1000)

            # Get current meter value (0.0 to 1.0)
            meter_level = track.output_meter_level

            # Update peak value (peak hold strategy)
            if track_idx not in self._meter_values:
                self._meter_values[track_idx] = meter_level
                self._meter_last_sent[track_idx] = 0

            # Track the peak value within throttle interval
            self._meter_values[track_idx] = max(self._meter_values[track_idx], meter_level)

            # Check if throttle interval has elapsed
            time_since_last = current_time_ms - self._meter_last_sent[track_idx]
            if time_since_last >= self._meter_interval_ms:
                # Send the peak value accumulated during interval
                peak_value = self._meter_values[track_idx]
                self._send_track_meter(track_idx, peak_value)

                # Reset for next interval
                self._meter_values[track_idx] = 0.0
                self._meter_last_sent[track_idx] = current_time_ms

        except Exception as e:
            self.c_surface.log_message(f"❌ Error in meter handler T{track_idx}: {e}")

    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_track_name(self, track_idx, name):
        """Send track name to hardware"""
        try:
            name_bytes = name.encode('utf-8')[:12]  # Max 12 chars
            payload = [track_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_TRACK_NAME, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track name T{track_idx}: {e}")
    
    def _send_track_color(self, track_idx, color_rgb):
        """Send track color to hardware"""
        try:
            r, g, b = color_rgb
            # Convert to MIDI range
            r = min(127, max(0, r // 2))
            g = min(127, max(0, g // 2))
            b = min(127, max(0, b // 2))
            
            payload = [track_idx, r, g, b]
            self.c_surface._send_sysex_command(CMD_TRACK_COLOR, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track color T{track_idx}: {e}")
    
    def _send_track_mute_state(self, track_idx, is_muted):
        """Send track mute state to hardware"""
        try:
            payload = [track_idx, 1 if is_muted else 0]
            self.c_surface._send_sysex_command(CMD_MIXER_MUTE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track mute T{track_idx}: {e}")
    
    def _send_track_solo_state(self, track_idx, is_solo):
        """Send track solo state to hardware"""
        try:
            payload = [track_idx, 1 if is_solo else 0]
            self.c_surface._send_sysex_command(CMD_MIXER_SOLO, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track solo T{track_idx}: {e}")
    
    def _send_track_arm_state(self, track_idx, is_armed):
        """Send track arm state to hardware"""
        try:
            payload = [track_idx, 1 if is_armed else 0]
            self.c_surface._send_sysex_command(CMD_MIXER_ARM, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track arm T{track_idx}: {e}")
    
    def _send_track_volume_state(self, track_idx, volume):
        """Send track volume state to hardware"""
        try:
            volume_127 = int(volume * 127)
            payload = [track_idx, volume_127]
            self.c_surface._send_sysex_command(CMD_MIXER_VOLUME, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track volume T{track_idx}: {e}")
    
    def _send_track_pan_state(self, track_idx, pan):
        """Send track pan state to hardware"""
        try:
            pan_127 = int((pan + 1.0) * 63.5)  # Convert -1.0/1.0 to 0-127
            payload = [track_idx, pan_127]
            self.c_surface._send_sysex_command(CMD_MIXER_PAN, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track pan T{track_idx}: {e}")
    
    def _send_track_send_state(self, track_idx, send_idx, send_value):
        """Send track send state to hardware"""
        try:
            send_127 = int(send_value * 127)
            payload = [track_idx, send_idx, send_127]
            self.c_surface._send_sysex_command(CMD_MIXER_SEND, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track send T{track_idx}S{send_idx}: {e}")

    def _send_track_crossfade(self, track_idx, crossfade_assign):
        """
        Send track crossfade assign to hardware

        Args:
            track_idx (int): Track index
            crossfade_assign (int): 0=A (left), 1=None (center), 2=B (right)
        """
        try:
            payload = [track_idx, crossfade_assign]
            self.c_surface._send_sysex_command(CMD_TRACK_CROSSFADE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track crossfade T{track_idx}: {e}")

    def _send_track_cue_volume(self, track_idx, cue_volume):
        """
        Send track cue volume (pre-listen/headphone) to hardware

        Args:
            track_idx (int): Track index
            cue_volume (float): Cue volume 0.0 to 1.0
        """
        try:
            cue_127 = int(cue_volume * 127)
            payload = [track_idx, cue_127]
            self.c_surface._send_sysex_command(CMD_TRACK_CUE_VOLUME, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track cue volume T{track_idx}: {e}")

    def _send_track_meter(self, track_idx, meter_level):
        """
        Send track output meter level to hardware (throttled to 20Hz)

        Args:
            track_idx (int): Track index
            meter_level (float): Peak meter level 0.0 to 1.0
        """
        try:
            # Convert to 7-bit MIDI (0-127)
            meter_127 = int(meter_level * 127)
            payload = [track_idx, meter_127]
            self.c_surface._send_sysex_command(CMD_TRACK_METER, payload)
        except Exception as e:
            # Don't log meter errors (too verbose)
            pass

    def _send_track_playing_slot(self, track_idx, playing_slot):
        """Send track playing slot to hardware"""
        try:
            # Validate track_idx is within valid range
            if track_idx < 0 or track_idx > 127:
                track_idx = 127  # Use 127 for invalid values
            
            # Validate slot_idx is within valid range
            if playing_slot < 0 or playing_slot > 127:
                slot_idx = 127  # 127 = no slot playing
            else:
                slot_idx = playing_slot
            
            payload = [track_idx, slot_idx]
            self.c_surface._send_sysex_command(CMD_TRACK_PLAYING_SLOT, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track playing slot T{track_idx}: {e}")
    
    def _send_track_fired_slot(self, track_idx, fired_slot):
        """Send track fired slot to hardware"""
        try:
            # Validate track_idx is within valid range
            if track_idx < 0 or track_idx > 127:
                track_idx = 127  # Use 127 for invalid values
            
            # Validate slot_idx is within valid range
            if fired_slot < 0 or fired_slot > 127:
                slot_idx = 127  # 127 = no slot fired
            else:
                slot_idx = fired_slot
            
            payload = [track_idx, slot_idx]
            self.c_surface._send_sysex_command(CMD_TRACK_FIRED_SLOT, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track fired slot T{track_idx}: {e}")
    
    def _send_track_fold_state(self, track_idx, is_folded):
        """Send track fold state to hardware"""
        try:
            payload = [track_idx, 1 if is_folded else 0]
            self.c_surface._send_sysex_command(CMD_TRACK_FOLD_STATE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track fold state T{track_idx}: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_track_info(self, track_idx):
        """Get complete track information"""
        if track_idx >= len(self.song.tracks):
            return None
            
        track = self.song.tracks[track_idx]
        mixer = track.mixer_device
        
        return {
            'name': track.name,
            'color': ColorUtils.live_color_to_rgb(track.color),
            'mute': track.mute,
            'solo': track.solo,
            'arm': getattr(track, 'arm', False) if hasattr(track, 'can_be_armed') and track.can_be_armed else False,
            'volume': mixer.volume.value,
            'pan': mixer.panning.value,
            'sends': [send.value for send in mixer.sends[:3]],
            'playing_slot': track.playing_slot_index,
            'fired_slot': track.fired_slot_index,
            'is_foldable': hasattr(track, 'is_foldable') and track.is_foldable,
            'is_folded': getattr(track, 'is_folded', False),
            'can_be_armed': hasattr(track, 'can_be_armed') and track.can_be_armed
        }
    
    def send_complete_track_state(self, track_idx):
        """Send complete state for a single track"""
        if not self.c_surface._is_connected or track_idx >= len(self.song.tracks):
            return
            
        try:
            track = self.song.tracks[track_idx]
            mixer = track.mixer_device
            
            # Send all track states
            self._send_track_name(track_idx, track.name)
            self._send_track_color(track_idx, ColorUtils.live_color_to_rgb(track.color))
            self._send_track_mute_state(track_idx, track.mute)
            self._send_track_solo_state(track_idx, track.solo)
            
            if hasattr(track, 'can_be_armed') and track.can_be_armed:
                self._send_track_arm_state(track_idx, track.arm)
            
            self._send_track_volume_state(track_idx, mixer.volume.value)
            self._send_track_pan_state(track_idx, mixer.panning.value)
            
            # Send sends
            for send_idx, send in enumerate(mixer.sends[:3]):
                self._send_track_send_state(track_idx, send_idx, send.value)

            # Send new mixer features
            if hasattr(mixer, 'crossfade_assign'):
                self._send_track_crossfade(track_idx, mixer.crossfade_assign)

            if hasattr(mixer, 'cue_volume'):
                self._send_track_cue_volume(track_idx, mixer.cue_volume.value)

            # Note: Metering is NOT sent in initial state (only real-time updates)
            # because it's high-frequency streaming data

            # Send states
            self._send_track_playing_slot(track_idx, track.playing_slot_index)
            self._send_track_fired_slot(track_idx, track.fired_slot_index)

            if hasattr(track, 'is_foldable') and track.is_foldable:
                self._send_track_fold_state(track_idx, track.is_folded)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track {track_idx} state: {e}")
    
    def refresh_all_tracks(self):
        """Refresh listeners for all tracks (when tracks are added/removed)"""
        try:
            self.c_surface.log_message("🔄 Refreshing all track listeners...")
            
            # Clean up all existing listeners
            self.cleanup_listeners()
            
            # Re-setup listeners for all current tracks
            self.setup_listeners(max_tracks=8)
            
            self.c_surface.log_message("✅ All track listeners refreshed")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error refreshing all tracks: {e}")
    
    def send_complete_state(self):
        """Send complete state for all tracks"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete track state...")
            
            for track_idx in self._track_listeners.keys():
                self.send_complete_track_state(track_idx)
            
            self.c_surface.log_message("✅ Track state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track state: {e}")

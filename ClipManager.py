# ClipManager.py - Clip and Scene Management
"""
Manages ClipSlot, Clip and Scene functionality
Based on Live Object Model: ClipSlot, Clip, Scene
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class ClipManager:
    """
    Manages all Clip and Scene level listeners and handlers
    Covers: ClipSlot states, Clip properties, Scene management
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self._clip_listeners = {}  # (track_idx, scene_idx): [listeners]
        self._scene_listeners = {}  # scene_idx: [listeners]
        self._is_active = False
        
    def setup_listeners(self, max_tracks=8, max_scenes=8):
        """Setup clip and scene listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message(f"🎵 Setting up Clip listeners for {max_tracks}x{max_scenes} grid...")
            
            # Setup clip slot listeners
            for track_idx in range(min(max_tracks, len(self.song.tracks))):
                for scene_idx in range(min(max_scenes, len(self.song.scenes))):
                    self._setup_single_clip_listeners(track_idx, scene_idx)
            
            # Setup scene listeners
            for scene_idx in range(min(max_scenes, len(self.song.scenes))):
                self._setup_single_scene_listeners(scene_idx)
            
            self._is_active = True
            self.c_surface.log_message(f"✅ Clip listeners setup for {len(self._clip_listeners)} clips, {len(self._scene_listeners)} scenes")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up clip listeners: {e}")
    
    def _setup_single_clip_listeners(self, track_idx, scene_idx):
        """Setup listeners for a single clip slot"""
        clip_key = (track_idx, scene_idx)
        if clip_key in self._clip_listeners:
            return  # Already setup
            
        try:
            if (track_idx >= len(self.song.tracks) or 
                scene_idx >= len(self.song.scenes)):
                return
                
            track = self.song.tracks[track_idx]
            clip_slot = track.clip_slots[scene_idx]
            listeners = []
            
            # === CLIP SLOT LISTENERS ===
            
            # Has clip (clip added/removed)
            has_clip_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_has_clip_changed(t_idx, s_idx)
            clip_slot.add_has_clip_listener(has_clip_listener)
            listeners.append(('has_clip', has_clip_listener))
            
            # Playing status
            playing_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_playing_changed(t_idx, s_idx)
            clip_slot.add_playing_status_listener(playing_listener)
            listeners.append(('playing_status', playing_listener))
            
            # === CLIP LISTENERS (if clip exists) ===
            if clip_slot.has_clip:
                self._setup_clip_content_listeners(track_idx, scene_idx, clip_slot.clip, listeners)
            
            # Store all listeners for this clip
            self._clip_listeners[clip_key] = listeners
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up clip T{track_idx}S{scene_idx} listeners: {e}")
    
    def _setup_clip_content_listeners(self, track_idx, scene_idx, clip, listeners):
        """Setup listeners for actual clip content"""
        try:
            # Clip name
            name_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_name_changed(t_idx, s_idx)
            clip.add_name_listener(name_listener)
            listeners.append(('name', name_listener))
            
            # Clip color
            color_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_color_changed(t_idx, s_idx)
            clip.add_color_listener(color_listener)
            listeners.append(('color', color_listener))
            
            # Loop state
            if hasattr(clip, 'looping'):
                loop_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_loop_changed(t_idx, s_idx)
                clip.add_looping_listener(loop_listener)
                listeners.append(('looping', loop_listener))
            
            # Muted state
            if hasattr(clip, 'muted'):
                muted_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_muted_changed(t_idx, s_idx)
                clip.add_muted_listener(muted_listener)
                listeners.append(('muted', muted_listener))
            
            # Warping (for audio clips only)
            if self._is_audio_clip(clip) and hasattr(clip, 'warping'):
                warp_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_warp_changed(t_idx, s_idx)
                try:
                    clip.add_warping_listener(warp_listener)
                    listeners.append(('warping', warp_listener))
                except Exception as e:
                    self.c_surface.log_message(f"⚠️ Cannot add warping listener to T{track_idx}S{scene_idx}: {e}")
            
            # Start marker (for audio clips)
            if hasattr(clip, 'start_marker'):
                start_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_start_marker_changed(t_idx, s_idx)
                try:
                    clip.add_start_marker_listener(start_listener)
                    listeners.append(('start_marker', start_listener))
                except Exception as e:
                    # Some clips may not support start marker listeners
                    pass
            
            # End marker (for audio clips)
            if hasattr(clip, 'end_marker'):
                end_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_end_marker_changed(t_idx, s_idx)
                try:
                    clip.add_end_marker_listener(end_listener)
                    listeners.append(('end_marker', end_listener))
                except Exception as e:
                    # Some clips may not support end marker listeners
                    pass
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up clip content listeners T{track_idx}S{scene_idx}: {e}")
    
    def _setup_single_scene_listeners(self, scene_idx):
        """Setup listeners for a single scene"""
        if scene_idx in self._scene_listeners:
            return  # Already setup
            
        try:
            if scene_idx >= len(self.song.scenes):
                return
                
            scene = self.song.scenes[scene_idx]
            listeners = []
            
            # Scene name
            name_listener = lambda s_idx=scene_idx: self._on_scene_name_changed(s_idx)
            scene.add_name_listener(name_listener)
            listeners.append(('name', name_listener))
            
            # Scene color
            color_listener = lambda s_idx=scene_idx: self._on_scene_color_changed(s_idx)
            scene.add_color_listener(color_listener)
            listeners.append(('color', color_listener))
            
            # Scene triggered state
            triggered_listener = lambda s_idx=scene_idx: self._on_scene_triggered_changed(s_idx)
            scene.add_is_triggered_listener(triggered_listener)
            listeners.append(('is_triggered', triggered_listener))
            
            # Store all listeners for this scene
            self._scene_listeners[scene_idx] = listeners
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up scene S{scene_idx} listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all clip and scene listeners"""
        if not self._is_active:
            return
            
        try:
            # Clean up clip listeners
            for (track_idx, scene_idx), listeners in self._clip_listeners.items():
                if (track_idx < len(self.song.tracks) and 
                    scene_idx < len(self.song.scenes)):
                    
                    track = self.song.tracks[track_idx]
                    clip_slot = track.clip_slots[scene_idx]
                    
                    for listener_type, listener_func in listeners:
                        try:
                            if listener_type == 'has_clip':
                                clip_slot.remove_has_clip_listener(listener_func)
                            elif listener_type == 'playing_status':
                                clip_slot.remove_playing_status_listener(listener_func)
                            elif clip_slot.has_clip:
                                clip = clip_slot.clip
                                if listener_type == 'name':
                                    clip.remove_name_listener(listener_func)
                                elif listener_type == 'color':
                                    clip.remove_color_listener(listener_func)
                                elif listener_type == 'looping':
                                    clip.remove_looping_listener(listener_func)
                                elif listener_type == 'muted':
                                    clip.remove_muted_listener(listener_func)
                                elif listener_type == 'warping':
                                    clip.remove_warping_listener(listener_func)
                                elif listener_type == 'start_marker':
                                    clip.remove_start_marker_listener(listener_func)
                                elif listener_type == 'end_marker':
                                    clip.remove_end_marker_listener(listener_func)
                        except:
                            pass  # Ignore if already removed
            
            # Clean up scene listeners
            for scene_idx, listeners in self._scene_listeners.items():
                if scene_idx < len(self.song.scenes):
                    scene = self.song.scenes[scene_idx]
                    
                    for listener_type, listener_func in listeners:
                        try:
                            if listener_type == 'name':
                                scene.remove_name_listener(listener_func)
                            elif listener_type == 'color':
                                scene.remove_color_listener(listener_func)
                            elif listener_type == 'is_triggered':
                                scene.remove_is_triggered_listener(listener_func)
                        except:
                            pass  # Ignore if already removed
            
            self._clip_listeners = {}
            self._scene_listeners = {}
            self._is_active = False
            self.c_surface.log_message("✅ Clip and scene listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning clip listeners: {e}")
    
    # ========================================
    # CLIP EVENT HANDLERS
    # ========================================
    
    def _on_clip_has_clip_changed(self, track_idx, scene_idx):
        """Clip added or removed from slot"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"🎵 Clip slot T{track_idx}S{scene_idx} has_clip changed")
            
            # Re-setup listeners if clip was added
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                clip_slot = self.song.tracks[track_idx].clip_slots[scene_idx]
                if clip_slot.has_clip:
                    # Add clip content listeners
                    clip_key = (track_idx, scene_idx)
                    if clip_key in self._clip_listeners:
                        listeners = self._clip_listeners[clip_key]
                        self._setup_clip_content_listeners(track_idx, scene_idx, clip_slot.clip, listeners)
            
            self._send_clip_state(track_idx, scene_idx)
    
    def _on_clip_playing_changed(self, track_idx, scene_idx):
        """Clip playing status changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"▶️ Clip T{track_idx}S{scene_idx} playing status changed")
            self._send_clip_state(track_idx, scene_idx)
    
    def _on_clip_name_changed(self, track_idx, scene_idx):
        """Clip name changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            self.c_surface.log_message(f"📝 Clip T{track_idx}S{scene_idx} name: '{clip.name}'")
            self._send_clip_name(track_idx, scene_idx, clip.name)
    
    def _on_clip_color_changed(self, track_idx, scene_idx):
        """Clip color changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            color_rgb = ColorUtils.live_color_to_rgb(clip.color)
            self.c_surface.log_message(f"🎨 Clip T{track_idx}S{scene_idx} color: {color_rgb}")
            self._send_clip_state(track_idx, scene_idx)  # Send full state with new color
    
    def _on_clip_loop_changed(self, track_idx, scene_idx):
        """Clip loop state changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            loop_state = clip.looping if hasattr(clip, 'looping') else False
            self.c_surface.log_message(f"🔄 Clip T{track_idx}S{scene_idx} loop: {loop_state}")
            self._send_clip_loop_state(track_idx, scene_idx, loop_state)
    
    def _on_clip_muted_changed(self, track_idx, scene_idx):
        """Clip muted state changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            muted_state = clip.muted if hasattr(clip, 'muted') else False
            self.c_surface.log_message(f"🔇 Clip T{track_idx}S{scene_idx} muted: {muted_state}")
            self._send_clip_muted_state(track_idx, scene_idx, muted_state)
    
    def _on_clip_warp_changed(self, track_idx, scene_idx):
        """Clip warp state changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            warp_state = clip.warping if hasattr(clip, 'warping') else False
            self.c_surface.log_message(f"🌊 Clip T{track_idx}S{scene_idx} warp: {warp_state}")
            self._send_clip_warp_state(track_idx, scene_idx, warp_state)
    
    def _on_clip_start_marker_changed(self, track_idx, scene_idx):
        """Clip start marker changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            start_marker = clip.start_marker if hasattr(clip, 'start_marker') else 0.0
            self.c_surface.log_message(f"⏪ Clip T{track_idx}S{scene_idx} start: {start_marker:.2f}")
            self._send_clip_start_marker(track_idx, scene_idx, start_marker)
    
    def _on_clip_end_marker_changed(self, track_idx, scene_idx):
        """Clip end marker changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            end_marker = clip.end_marker if hasattr(clip, 'end_marker') else 0.0
            self.c_surface.log_message(f"⏩ Clip T{track_idx}S{scene_idx} end: {end_marker:.2f}")
            self._send_clip_end_marker(track_idx, scene_idx, end_marker)
    
    # ========================================
    # SCENE EVENT HANDLERS
    # ========================================
    
    def _on_scene_name_changed(self, scene_idx):
        """Scene name changed"""
        if self.c_surface._is_connected and scene_idx < len(self.song.scenes):
            scene = self.song.scenes[scene_idx]
            self.c_surface.log_message(f"📝 Scene S{scene_idx} name: '{scene.name}'")
            self._send_scene_name(scene_idx, scene.name)
    
    def _on_scene_color_changed(self, scene_idx):
        """Scene color changed"""
        if self.c_surface._is_connected and scene_idx < len(self.song.scenes):
            scene = self.song.scenes[scene_idx]
            color_rgb = ColorUtils.live_color_to_rgb(scene.color)
            self.c_surface.log_message(f"🎨 Scene S{scene_idx} color: {color_rgb}")
            self._send_scene_color(scene_idx, color_rgb)
    
    def _on_scene_triggered_changed(self, scene_idx):
        """Scene triggered state changed"""
        if self.c_surface._is_connected and scene_idx < len(self.song.scenes):
            scene = self.song.scenes[scene_idx]
            is_triggered = scene.is_triggered
            self.c_surface.log_message(f"🔥 Scene S{scene_idx} triggered: {is_triggered}")
            self._send_scene_triggered_state(scene_idx, is_triggered)
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_clip_state(self, track_idx, scene_idx):
        """Send complete clip state to hardware"""
        try:
            if (track_idx >= len(self.song.tracks) or 
                scene_idx >= len(self.song.scenes)):
                return
            
            track = self.song.tracks[track_idx]
            clip_slot = track.clip_slots[scene_idx]
            
            # Determine clip state
            if not clip_slot.has_clip:
                state = CLIP_EMPTY
            elif clip_slot.is_playing:
                state = CLIP_PLAYING
            elif clip_slot.is_triggered:
                state = CLIP_QUEUED
            elif hasattr(clip_slot, 'is_recording') and clip_slot.is_recording:
                state = CLIP_RECORDING
            else:
                state = CLIP_EMPTY
            
            # Get color (clip color if exists, otherwise track color)
            if clip_slot.has_clip:
                color = ColorUtils.live_color_to_rgb(clip_slot.clip.color)
            else:
                color = ColorUtils.live_color_to_rgb(track.color)
            
            # Calculate final LED color based on state
            final_color = ColorUtils.get_clip_state_color(state, color)
            
            # Send clip state message
            message = SysExEncoder.encode_clip_state(track_idx, scene_idx, state, final_color)
            if message:
                self.c_surface._send_midi(tuple(message))
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip state T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_name(self, track_idx, scene_idx, name):
        """Send clip name to hardware"""
        try:
            name_bytes = name.encode('utf-8')[:12]  # Max 12 chars
            payload = [track_idx, scene_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_CLIP_NAME, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip name T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_loop_state(self, track_idx, scene_idx, loop_state):
        """Send clip loop state to hardware"""
        try:
            payload = [track_idx, scene_idx, 1 if loop_state else 0]
            self.c_surface._send_sysex_command(CMD_CLIP_LOOP, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip loop T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_muted_state(self, track_idx, scene_idx, muted_state):
        """Send clip muted state to hardware"""
        try:
            payload = [track_idx, scene_idx, 1 if muted_state else 0]
            self.c_surface._send_sysex_command(CMD_CLIP_MUTED, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip muted T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_warp_state(self, track_idx, scene_idx, warp_state):
        """Send clip warp state to hardware"""
        try:
            payload = [track_idx, scene_idx, 1 if warp_state else 0]
            self.c_surface._send_sysex_command(CMD_CLIP_WARP, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip warp T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_start_marker(self, track_idx, scene_idx, start_marker):
        """Send clip start marker to hardware"""
        try:
            # Convert to beats (simplified)
            start_beats = int(start_marker) & 0x7F
            start_fraction = int((start_marker - int(start_marker)) * 127) & 0x7F
            
            payload = [track_idx, scene_idx, start_beats, start_fraction]
            self.c_surface._send_sysex_command(CMD_CLIP_START, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip start T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_end_marker(self, track_idx, scene_idx, end_marker):
        """Send clip end marker to hardware"""
        try:
            # Convert to beats (simplified)
            end_beats = int(end_marker) & 0x7F
            end_fraction = int((end_marker - int(end_marker)) * 127) & 0x7F
            
            payload = [track_idx, scene_idx, end_beats, end_fraction]
            self.c_surface._send_sysex_command(CMD_CLIP_END, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip end T{track_idx}S{scene_idx}: {e}")
    
    def _send_scene_name(self, scene_idx, name):
        """Send scene name to hardware"""
        try:
            name_bytes = name.encode('utf-8')[:12]  # Max 12 chars
            payload = [scene_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_SCENE_NAME, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending scene name S{scene_idx}: {e}")
    
    def _send_scene_color(self, scene_idx, color_rgb):
        """Send scene color to hardware"""
        try:
            r, g, b = color_rgb
            # Convert to MIDI range
            r = min(127, max(0, r // 2))
            g = min(127, max(0, g // 2))
            b = min(127, max(0, b // 2))
            
            payload = [scene_idx, r, g, b]
            self.c_surface._send_sysex_command(CMD_SCENE_COLOR, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending scene color S{scene_idx}: {e}")
    
    def _send_scene_triggered_state(self, scene_idx, is_triggered):
        """Send scene triggered state to hardware"""
        try:
            payload = [scene_idx, 1 if is_triggered else 0]
            self.c_surface._send_sysex_command(CMD_SCENE_IS_TRIGGERED, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending scene triggered S{scene_idx}: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _clip_exists(self, track_idx, scene_idx):
        """Check if clip exists at position"""
        return (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes) and
                self.song.tracks[track_idx].clip_slots[scene_idx].has_clip)
    
    def _is_audio_clip(self, clip):
        """Check if clip is an audio clip"""
        return (clip and 
                hasattr(clip, 'is_audio_clip') and 
                clip.is_audio_clip)
    
    def _is_midi_clip(self, clip):
        """Check if clip is a MIDI clip"""  
        return (clip and 
                hasattr(clip, 'is_midi_clip') and 
                clip.is_midi_clip)
    
    def get_clip_info(self, track_idx, scene_idx):
        """Get complete clip information"""
        if (track_idx >= len(self.song.tracks) or 
            scene_idx >= len(self.song.scenes)):
            return None
            
        track = self.song.tracks[track_idx]
        clip_slot = track.clip_slots[scene_idx]
        
        info = {
            'has_clip': clip_slot.has_clip,
            'is_playing': clip_slot.is_playing,
            'is_triggered': clip_slot.is_triggered,
            'is_recording': getattr(clip_slot, 'is_recording', False)
        }
        
        if clip_slot.has_clip:
            clip = clip_slot.clip
            info.update({
                'name': clip.name,
                'color': ColorUtils.live_color_to_rgb(clip.color),
                'clip_type': 'audio' if self._is_audio_clip(clip) else 'midi' if self._is_midi_clip(clip) else 'unknown',
                'looping': getattr(clip, 'looping', False),
                'muted': getattr(clip, 'muted', False),
                'warping': getattr(clip, 'warping', False) if self._is_audio_clip(clip) else None,
                'start_marker': getattr(clip, 'start_marker', 0.0) if self._is_audio_clip(clip) else None,
                'end_marker': getattr(clip, 'end_marker', 0.0) if self._is_audio_clip(clip) else None,
                'length': getattr(clip, 'length', 0.0)
            })
        
        return info
    
    def get_scene_info(self, scene_idx):
        """Get complete scene information"""
        if scene_idx >= len(self.song.scenes):
            return None
            
        scene = self.song.scenes[scene_idx]
        return {
            'name': scene.name,
            'color': ColorUtils.live_color_to_rgb(scene.color),
            'is_triggered': scene.is_triggered,
            'is_empty': scene.is_empty
        }
    
    def send_complete_clip_state(self, track_idx, scene_idx):
        """Send complete state for a single clip"""
        if not self.c_surface._is_connected:
            return
            
        try:
            # Send clip state
            self._send_clip_state(track_idx, scene_idx)
            
            # Send additional clip info if clip exists
            if self._clip_exists(track_idx, scene_idx):
                clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
                
                self._send_clip_name(track_idx, scene_idx, clip.name)
                
                if hasattr(clip, 'looping'):
                    self._send_clip_loop_state(track_idx, scene_idx, clip.looping)
                
                if hasattr(clip, 'muted'):
                    self._send_clip_muted_state(track_idx, scene_idx, clip.muted)
                
                # Audio clip specific properties
                if self._is_audio_clip(clip):
                    if hasattr(clip, 'warping'):
                        self._send_clip_warp_state(track_idx, scene_idx, clip.warping)
                    
                    if hasattr(clip, 'start_marker'):
                        self._send_clip_start_marker(track_idx, scene_idx, clip.start_marker)
                    
                    if hasattr(clip, 'end_marker'):
                        self._send_clip_end_marker(track_idx, scene_idx, clip.end_marker)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip T{track_idx}S{scene_idx} state: {e}")
    
    def send_complete_scene_state(self, scene_idx):
        """Send complete state for a single scene"""
        if not self.c_surface._is_connected or scene_idx >= len(self.song.scenes):
            return
            
        try:
            scene = self.song.scenes[scene_idx]
            
            self._send_scene_name(scene_idx, scene.name)
            self._send_scene_color(scene_idx, ColorUtils.live_color_to_rgb(scene.color))
            self._send_scene_triggered_state(scene_idx, scene.is_triggered)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending scene S{scene_idx} state: {e}")
    
    def refresh_all_tracks(self):
        """Refresh clip listeners for all tracks (when tracks are added/removed)"""
        try:
            self.c_surface.log_message("🔄 Refreshing all clip listeners...")
            
            # Clean up all existing listeners
            self.cleanup_listeners()
            
            # Re-setup listeners for all current clips and scenes
            self.setup_listeners(max_tracks=8, max_scenes=8)
            
            self.c_surface.log_message("✅ All clip listeners refreshed")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error refreshing all clip listeners: {e}")
    
    def send_complete_state(self):
        """Send complete state for all clips and scenes"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete clip/scene state...")
            
            # Send all clip states
            for (track_idx, scene_idx) in self._clip_listeners.keys():
                self.send_complete_clip_state(track_idx, scene_idx)
            
            # Send all scene states
            for scene_idx in self._scene_listeners.keys():
                self.send_complete_scene_state(scene_idx)
            
            self.c_surface.log_message("✅ Clip/scene state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip/scene state: {e}")
    
    def add_clip_listener(self, track_idx, scene_idx):
        """Add listeners for a new clip position"""
        clip_key = (track_idx, scene_idx)
        if clip_key not in self._clip_listeners:
            self._setup_single_clip_listeners(track_idx, scene_idx)
            self.c_surface.log_message(f"✅ Added listeners for clip T{track_idx}S{scene_idx}")
    
    def add_scene_listener(self, scene_idx):
        """Add listeners for a new scene"""
        if scene_idx not in self._scene_listeners:
            self._setup_single_scene_listeners(scene_idx)
            self.c_surface.log_message(f"✅ Added listeners for scene S{scene_idx}")
    
    # ========================================
    # CLIP ACTIONS (for handling incoming commands)
    # ========================================
    
    def fire_clip(self, track_idx, scene_idx):
        """Fire clip at position"""
        try:
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                clip_slot = self.song.tracks[track_idx].clip_slots[scene_idx]
                clip_slot.fire()
                self.c_surface.log_message(f"🔥 Fired clip T{track_idx}S{scene_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error firing clip T{track_idx}S{scene_idx}: {e}")
    
    def stop_clip(self, track_idx, scene_idx):
        """Stop clip at position"""
        try:
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                clip_slot = self.song.tracks[track_idx].clip_slots[scene_idx]
                clip_slot.stop()
                self.c_surface.log_message(f"⏹️ Stopped clip T{track_idx}S{scene_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error stopping clip T{track_idx}S{scene_idx}: {e}")
    
    def fire_scene(self, scene_idx):
        """Fire scene"""
        try:
            if scene_idx < len(self.song.scenes):
                scene = self.song.scenes[scene_idx]
                scene.fire()
                self.c_surface.log_message(f"🎬 Fired scene S{scene_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error firing scene S{scene_idx}: {e}")

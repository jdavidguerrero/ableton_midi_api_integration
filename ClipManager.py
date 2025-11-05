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
            
            # FIXED: Add missing fired slot listener (queued state)
            if hasattr(clip_slot, 'add_fired_slot_listener'):
                fired_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_fired_changed(t_idx, s_idx)
                clip_slot.add_fired_slot_listener(fired_listener)
                listeners.append(('fired_slot', fired_listener))
            
            # FIXED: Add stop button availability
            if hasattr(clip_slot, 'add_has_stop_button_listener'):
                stop_button_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_clip_stop_button_changed(t_idx, s_idx)
                clip_slot.add_has_stop_button_listener(stop_button_listener)
                listeners.append(('has_stop_button', stop_button_listener))
            
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
            # Note: warping property exists but add_warping_listener does not exist in Live API
            # We track warping state through periodic checks or other clip listeners
            if self._is_audio_clip(clip) and hasattr(clip, 'warping'):
                self.c_surface.log_message(f"ℹ️ Warping property available for T{track_idx}S{scene_idx}: {clip.warping}")
            
            # Sample class listeners (for audio clips with samples)
            if self._is_audio_clip(clip) and hasattr(clip, 'sample') and clip.sample:
                self._setup_sample_listeners(track_idx, scene_idx, clip.sample, listeners)
            
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
    
    def _setup_sample_listeners(self, track_idx, scene_idx, sample, listeners):
        """Setup listeners for Sample class properties"""
        try:
            if DEBUG_ENABLED:
                self.c_surface.log_message(f"🎵 Setting up Sample listeners T{track_idx}S{scene_idx}")
            
            # Sample name listener
            if hasattr(sample, 'name'):
                sample_name_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_name_changed(t_idx, s_idx)
                try:
                    sample.add_name_listener(sample_name_listener)
                    listeners.append(('sample_name', sample_name_listener))
                except Exception:
                    pass  # Some sample objects may not support name listeners
            
            # Sample file path listener
            if hasattr(sample, 'file_path'):
                file_path_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_file_changed(t_idx, s_idx)
                try:
                    sample.add_file_path_listener(file_path_listener)
                    listeners.append(('sample_file_path', file_path_listener))
                except Exception:
                    pass  # Some versions may not support this
            
            # Sample length listener
            if hasattr(sample, 'length'):
                length_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_length_changed(t_idx, s_idx)
                try:
                    sample.add_length_listener(length_listener)
                    listeners.append(('sample_length', length_listener))
                except Exception:
                    pass
            
            # Sample gain listener
            if hasattr(sample, 'gain'):
                gain_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_gain_changed(t_idx, s_idx)
                try:
                    sample.add_gain_listener(gain_listener)
                    listeners.append(('sample_gain', gain_listener))
                except Exception:
                    pass
            
            # Sample reverse listener
            if hasattr(sample, 'reverse'):
                reverse_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_reverse_changed(t_idx, s_idx)
                try:
                    sample.add_reverse_listener(reverse_listener)
                    listeners.append(('sample_reverse', reverse_listener))
                except Exception:
                    pass
            
            # Sample slices listener (if available)
            if hasattr(sample, 'slices'):
                slices_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_slices_changed(t_idx, s_idx)
                try:
                    sample.add_slices_listener(slices_listener)
                    listeners.append(('sample_slices', slices_listener))
                except Exception:
                    pass
            
            # Sample warp markers listener (if available)
            if hasattr(sample, 'warp_markers'):
                warp_markers_listener = lambda t_idx=track_idx, s_idx=scene_idx: self._on_sample_warp_markers_changed(t_idx, s_idx)
                try:
                    sample.add_warp_markers_listener(warp_markers_listener)
                    listeners.append(('sample_warp_markers', warp_markers_listener))
                except Exception:
                    pass
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up sample listeners T{track_idx}S{scene_idx}: {e}")
    
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
                                    # warping listener doesn't exist in Live API - no removal needed
                                    pass
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
            self._send_grid_update()
    
    def _on_clip_playing_changed(self, track_idx, scene_idx):
        """Clip playing status changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"▶️ Clip T{track_idx}S{scene_idx} playing status changed")
            self._send_clip_state(track_idx, scene_idx)
            self._send_grid_update()
    
    def _on_clip_fired_changed(self, track_idx, scene_idx):
        """Handle clip fired/queued status change"""
        try:
            if self._is_valid_position(track_idx, scene_idx):
                clip_slot = self.song.tracks[track_idx].clip_slots[scene_idx]
                is_fired = getattr(clip_slot, 'is_fired', False)
                
                # Send clip queued state to hardware
                self._send_clip_queued_state(track_idx, scene_idx, is_fired)
                
                if LOG_LISTENER_EVENTS:
                    self.c_surface.log_message(f"🎯 Clip T{track_idx}S{scene_idx} fired/queued: {is_fired}")
        except Exception as e:
            self.c_surface.log_message(f"❌ Error in clip fired change T{track_idx}S{scene_idx}: {e}")
    
    def _on_clip_stop_button_changed(self, track_idx, scene_idx):
        """Handle stop button availability change"""
        try:
            if self._is_valid_position(track_idx, scene_idx):
                clip_slot = self.song.tracks[track_idx].clip_slots[scene_idx]
                has_stop_button = getattr(clip_slot, 'has_stop_button', False)
                
                # Send stop button state to hardware
                self._send_clip_stop_button_state(track_idx, scene_idx, has_stop_button)
                
                if LOG_LISTENER_EVENTS:
                    self.c_surface.log_message(f"🛑 Clip T{track_idx}S{scene_idx} stop button: {has_stop_button}")
        except Exception as e:
            self.c_surface.log_message(f"❌ Error in clip stop button change T{track_idx}S{scene_idx}: {e}")

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
            self._send_grid_update()
    
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
            # Only check warping for audio clips
            warp_state = False
            if self._is_audio_clip(clip) and hasattr(clip, 'warping'):
                warp_state = clip.warping
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
    # SAMPLE CLASS EVENT HANDLERS
    # ========================================
    
    def _on_sample_name_changed(self, track_idx, scene_idx):
        """Sample name changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                sample_name = clip.sample.name if hasattr(clip.sample, 'name') else 'Unknown'
                self.c_surface.log_message(f"🎵 Sample T{track_idx}S{scene_idx} name: '{sample_name}'")
                self._send_sample_info(track_idx, scene_idx, clip.sample)
    
    def _on_sample_file_changed(self, track_idx, scene_idx):
        """Sample file path changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                file_path = getattr(clip.sample, 'file_path', '')
                self.c_surface.log_message(f"📁 Sample T{track_idx}S{scene_idx} file: '{file_path}'")
                self._send_sample_info(track_idx, scene_idx, clip.sample)
    
    def _on_sample_length_changed(self, track_idx, scene_idx):
        """Sample length changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                length = getattr(clip.sample, 'length', 0.0)
                self.c_surface.log_message(f"⏱️ Sample T{track_idx}S{scene_idx} length: {length:.2f}")
                self._send_sample_length(track_idx, scene_idx, length)
    
    def _on_sample_gain_changed(self, track_idx, scene_idx):
        """Sample gain changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                gain = getattr(clip.sample, 'gain', 1.0)
                self.c_surface.log_message(f"🔊 Sample T{track_idx}S{scene_idx} gain: {gain:.2f}")
                self._send_sample_gain(track_idx, scene_idx, gain)
    
    def _on_sample_reverse_changed(self, track_idx, scene_idx):
        """Sample reverse state changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                reverse = getattr(clip.sample, 'reverse', False)
                self.c_surface.log_message(f"↩️ Sample T{track_idx}S{scene_idx} reverse: {reverse}")
                self._send_sample_reverse(track_idx, scene_idx, reverse)
    
    def _on_sample_slices_changed(self, track_idx, scene_idx):
        """Sample slices changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            self.c_surface.log_message(f"✂️ Sample T{track_idx}S{scene_idx} slices changed")
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                self._send_sample_slices(track_idx, scene_idx, clip.sample)
    
    def _on_sample_warp_markers_changed(self, track_idx, scene_idx):
        """Sample warp markers changed"""
        if self.c_surface._is_connected and self._clip_exists(track_idx, scene_idx):
            self.c_surface.log_message(f"🌊 Sample T{track_idx}S{scene_idx} warp markers changed")
            clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
            if hasattr(clip, 'sample') and clip.sample:
                self._send_sample_warp_markers(track_idx, scene_idx, clip.sample)
    
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
            # Validate indices are within valid range
            if track_idx < 0 or track_idx > 127:
                track_idx = 127  # Use 127 for invalid values
            if scene_idx < 0 or scene_idx > 127:
                scene_idx = 127  # Use 127 for invalid values
            
            # Convert to beats (simplified) and clamp to MIDI range
            start_beats = max(0, min(127, int(start_marker) & 0x7F))
            start_fraction = max(0, min(127, int((start_marker - int(start_marker)) * 127) & 0x7F))
            
            payload = [track_idx, scene_idx, start_beats, start_fraction]
            self.c_surface._send_sysex_command(CMD_CLIP_START, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip start T{track_idx}S{scene_idx}: {e}")
    
    def _send_clip_end_marker(self, track_idx, scene_idx, end_marker):
        """Send clip end marker to hardware"""
        try:
            # Validate indices are within valid range
            if track_idx < 0 or track_idx > 127:
                track_idx = 127  # Use 127 for invalid values
            if scene_idx < 0 or scene_idx > 127:
                scene_idx = 127  # Use 127 for invalid values
            
            # Convert to beats (simplified) and clamp to MIDI range
            end_beats = max(0, min(127, int(end_marker) & 0x7F))
            end_fraction = max(0, min(127, int((end_marker - int(end_marker)) * 127) & 0x7F))
            
            payload = [track_idx, scene_idx, end_beats, end_fraction]
            self.c_surface._send_sysex_command(CMD_CLIP_END, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip end T{track_idx}S{scene_idx}: {e}")
    
    # ========================================
    # SAMPLE CLASS SEND METHODS
    # ========================================
    
    def _send_sample_info(self, track_idx, scene_idx, sample):
        """Send comprehensive sample information to hardware"""
        try:
            sample_name = getattr(sample, 'name', 'Unknown')
            file_path = getattr(sample, 'file_path', '')
            
            # Get basic file info from file path
            filename = file_path.split('/')[-1] if file_path else sample_name
            name_bytes = filename.encode('utf-8')[:16]  # Max 16 chars for sample name
            
            payload = [track_idx, scene_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            
            # Add sample properties as flags
            flags = 0
            if getattr(sample, 'reverse', False):
                flags |= 0x01  # Reversed
            
            payload.append(flags)
            
            # Add basic sample info
            length = int(getattr(sample, 'length', 0.0) * 1000) & 0x3FFF  # Length in ms, max ~16 seconds
            gain = int(getattr(sample, 'gain', 1.0) * 127) & 0x7F  # Gain 0-127
            
            payload.extend([
                (length >> 7) & 0x7F,  # Length high byte
                length & 0x7F,         # Length low byte
                gain                   # Gain
            ])
            
            # Use existing CMD_CLIP_NAME for sample info
            self.c_surface._send_sysex_command(CMD_CLIP_NAME, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending sample info T{track_idx}S{scene_idx}: {e}")
    
    def _send_sample_length(self, track_idx, scene_idx, length):
        """Send sample length to hardware"""
        try:
            length_ms = int(length * 1000) & 0x3FFF  # Convert to ms, max ~16 seconds
            payload = [
                track_idx, scene_idx,
                (length_ms >> 7) & 0x7F,  # High byte
                length_ms & 0x7F          # Low byte
            ]
            self.c_surface._send_sysex_command(CMD_CLIP_START, payload)  # Reuse start command
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending sample length T{track_idx}S{scene_idx}: {e}")
    
    def _send_sample_gain(self, track_idx, scene_idx, gain):
        """Send sample gain to hardware"""
        try:
            gain_127 = int(gain * 127) & 0x7F
            payload = [track_idx, scene_idx, gain_127]
            self.c_surface._send_sysex_command(CMD_CLIP_LOOP, payload)  # Reuse loop command
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending sample gain T{track_idx}S{scene_idx}: {e}")
    
    def _send_sample_reverse(self, track_idx, scene_idx, reverse_state):
        """Send sample reverse state to hardware"""
        try:
            payload = [track_idx, scene_idx, 1 if reverse_state else 0]
            self.c_surface._send_sysex_command(CMD_CLIP_MUTED, payload)  # Reuse muted command
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending sample reverse T{track_idx}S{scene_idx}: {e}")
    
    def _send_sample_slices(self, track_idx, scene_idx, sample):
        """Send sample slices information to hardware"""
        try:
            if hasattr(sample, 'slices'):
                slice_count = len(sample.slices) if sample.slices else 0
                payload = [track_idx, scene_idx, min(slice_count, 127)]
                
                # Add slice timing info for first few slices
                for i, slice_obj in enumerate(sample.slices[:4]):
                    if slice_obj:
                        start_time = int(getattr(slice_obj, 'start_time', 0.0) * 100) & 0x7F
                        end_time = int(getattr(slice_obj, 'end_time', 0.0) * 100) & 0x7F
                        payload.extend([start_time, end_time])
                
                if len(payload) <= 20:  # Reasonable size limit
                    self.c_surface._send_sysex_command(CMD_CLIP_WARP, payload)  # Reuse warp command
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending sample slices T{track_idx}S{scene_idx}: {e}")
    
    def _send_sample_warp_markers(self, track_idx, scene_idx, sample):
        """Send sample warp markers to hardware"""
        try:
            if hasattr(sample, 'warp_markers'):
                marker_count = len(sample.warp_markers) if sample.warp_markers else 0
                payload = [track_idx, scene_idx, min(marker_count, 127)]
                
                # Add marker info for first few markers
                for marker in sample.warp_markers[:4]:
                    if marker:
                        beat_time = int(getattr(marker, 'beat_time', 0.0) * 100) & 0x7F
                        sample_time = int(getattr(marker, 'sample_time', 0.0) * 100) & 0x7F
                        payload.extend([beat_time, sample_time])
                
                if len(payload) <= 20:  # Reasonable size limit
                    self.c_surface._send_sysex_command(CMD_CLIP_END, payload)  # Reuse end command
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending sample warp markers T{track_idx}S{scene_idx}: {e}")
    
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

    def _send_neotrellis_clip_grid(self):
        """Send the colors of all clips in the 4x8 grid to the NeoTrellis."""
        if not self.c_surface._is_connected:
            return

        grid_data = []
        for track_idx in range(4): # 4 tracks (rows)
            for scene_idx in range(8): # 8 scenes (cols)
                color = (0, 0, 0) # Default to black
                if self._clip_exists(track_idx, scene_idx):
                    clip = self.song.tracks[track_idx].clip_slots[scene_idx].clip
                    color = ColorUtils.live_color_to_rgb(clip.color)
                grid_data.append(color)
        
        message = SysExEncoder.encode_neotrellis_clip_grid(grid_data)
        if message:
            self.c_surface._send_midi(tuple(message))
    
    # ========================================
    # MIDI CLIP NOTE MANIPULATION METHODS
    # ========================================
    
    def get_midi_clip_notes(self, track_idx, scene_idx, start_time=0.0, end_time=None):
        """Get MIDI notes from clip using Live API"""
        try:
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                track = self.song.tracks[track_idx]
                clip_slot = track.clip_slots[scene_idx]
                
                if clip_slot.has_clip and hasattr(clip_slot.clip, 'get_notes_extended'):
                    clip = clip_slot.clip
                    if hasattr(clip, 'is_midi_clip') and clip.is_midi_clip:
                        
                        # Use Live API's get_notes_extended for comprehensive note data
                        if end_time is None:
                            end_time = clip.length
                        
                        # Get notes from the specified time range
                        notes_data = clip.get_notes_extended(
                            from_time=start_time,
                            from_pitch=0,
                            time_span=end_time - start_time,
                            pitch_span=128
                        )
                        
                        notes = []
                        for note_data in notes_data:
                            notes.append({
                                'pitch': note_data.pitch,
                                'start_time': note_data.start_time,
                                'duration': note_data.duration,
                                'velocity': note_data.velocity,
                                'probability': getattr(note_data, 'probability', 1.0),
                                'velocity_deviation': getattr(note_data, 'velocity_deviation', 0),
                                'release_velocity': getattr(note_data, 'release_velocity', 64)
                            })
                        
                        self.c_surface.log_message(f"🎹 Got {len(notes)} MIDI notes from T{track_idx}S{scene_idx}")
                        return notes
                        
                    else:
                        self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} is not a MIDI clip")
                else:
                    self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} has no clip or no note access")
                    
            return []
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting MIDI notes T{track_idx}S{scene_idx}: {e}")
            return []
    
    def add_midi_note(self, track_idx, scene_idx, pitch, start_time, duration, velocity=100):
        """Add a single MIDI note to clip"""
        try:
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                track = self.song.tracks[track_idx]
                clip_slot = track.clip_slots[scene_idx]
                
                if clip_slot.has_clip:
                    clip = clip_slot.clip
                    if hasattr(clip, 'is_midi_clip') and clip.is_midi_clip:
                        
                        # Use Live API's set_notes_extended for adding notes
                        if hasattr(clip, 'set_notes_extended'):
                            # Create note tuple: (pitch, start_time, duration, velocity, muted)
                            new_notes = [(pitch, start_time, duration, velocity, False)]
                            
                            clip.set_notes_extended(
                                notes=new_notes,
                                from_time=start_time,
                                from_pitch=pitch,
                                time_span=duration,
                                pitch_span=1
                            )
                            
                            self.c_surface.log_message(
                                f"🎵 Added MIDI note T{track_idx}S{scene_idx}: "
                                f"P{pitch} @{start_time:.2f}s, dur={duration:.2f}s, vel={velocity}"
                            )
                            return True
                            
                        else:
                            self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} doesn't support note editing")
                    else:
                        self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} is not a MIDI clip")
                else:
                    self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} has no clip")
                    
            return False
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error adding MIDI note T{track_idx}S{scene_idx}: {e}")
            return False
    
    def remove_midi_notes(self, track_idx, scene_idx, start_time, end_time, pitch_range=None):
        """Remove MIDI notes from clip in specified time and pitch range"""
        try:
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                track = self.song.tracks[track_idx]
                clip_slot = track.clip_slots[scene_idx]
                
                if clip_slot.has_clip:
                    clip = clip_slot.clip
                    if hasattr(clip, 'is_midi_clip') and clip.is_midi_clip:
                        
                        if hasattr(clip, 'remove_notes_extended'):
                            from_pitch = pitch_range[0] if pitch_range else 0
                            pitch_span = (pitch_range[1] - pitch_range[0] + 1) if pitch_range else 128
                            
                            clip.remove_notes_extended(
                                from_time=start_time,
                                from_pitch=from_pitch,
                                time_span=end_time - start_time,
                                pitch_span=pitch_span
                            )
                            
                            pitch_info = f" pitches {from_pitch}-{from_pitch + pitch_span - 1}" if pitch_range else ""
                            self.c_surface.log_message(
                                f"🗑️ Removed MIDI notes T{track_idx}S{scene_idx}: "
                                f"{start_time:.2f}-{end_time:.2f}s{pitch_info}"
                            )
                            return True
                            
                        else:
                            self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} doesn't support note removal")
                    else:
                        self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} is not a MIDI clip")
                else:
                    self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} has no clip")
                    
            return False
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error removing MIDI notes T{track_idx}S{scene_idx}: {e}")
            return False
    
    def quantize_midi_clip(self, track_idx, scene_idx, quantization=4):
        """Quantize MIDI clip notes"""
        try:
            if (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes)):
                
                track = self.song.tracks[track_idx]
                clip_slot = track.clip_slots[scene_idx]
                
                if clip_slot.has_clip:
                    clip = clip_slot.clip
                    if hasattr(clip, 'is_midi_clip') and clip.is_midi_clip:
                        
                        if hasattr(clip, 'quantize'):
                            # Map quantization values: 1=1 bar, 2=1/2 note, 4=1/4 note, etc.
                            clip.quantize(quantization, 1.0)  # quantization, strength
                            
                            quant_names = {1: "1 bar", 2: "1/2", 4: "1/4", 8: "1/8", 16: "1/16", 32: "1/32"}
                            quant_name = quant_names.get(quantization, f"1/{quantization}")
                            
                            self.c_surface.log_message(
                                f"📊 Quantized MIDI clip T{track_idx}S{scene_idx} to {quant_name}"
                            )
                            return True
                            
                        else:
                            self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} doesn't support quantization")
                    else:
                        self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} is not a MIDI clip")
                else:
                    self.c_surface.log_message(f"⚠️ T{track_idx}S{scene_idx} has no clip")
                    
            return False
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error quantizing MIDI clip T{track_idx}S{scene_idx}: {e}")
            return False
    
    def duplicate_midi_clip_notes(self, src_track_idx, src_scene_idx, dst_track_idx, dst_scene_idx):
        """Duplicate MIDI notes from one clip to another"""
        try:
            # Get notes from source clip
            notes = self.get_midi_clip_notes(src_track_idx, src_scene_idx)
            if not notes:
                return False
                
            # Create destination clip if it doesn't exist
            if (dst_track_idx < len(self.song.tracks) and 
                dst_scene_idx < len(self.song.scenes)):
                
                dst_track = self.song.tracks[dst_track_idx]
                dst_clip_slot = dst_track.clip_slots[dst_scene_idx]
                
                if not dst_clip_slot.has_clip:
                    # Create a MIDI clip
                    if hasattr(dst_clip_slot, 'create_clip'):
                        dst_clip_slot.create_clip(4.0)  # 4 bars default length
                        
                if dst_clip_slot.has_clip:
                    dst_clip = dst_clip_slot.clip
                    if hasattr(dst_clip, 'is_midi_clip') and dst_clip.is_midi_clip:
                        
                        if hasattr(dst_clip, 'set_notes_extended'):
                            # Convert notes to tuple format
                            note_tuples = []
                            for note in notes:
                                note_tuples.append((
                                    note['pitch'],
                                    note['start_time'],
                                    note['duration'],
                                    note['velocity'],
                                    False  # not muted
                                ))
                            
                            # Clear existing notes and add new ones
                            if note_tuples:
                                # Get time span for replacement
                                min_time = min(note['start_time'] for note in notes)
                                max_time = max(note['start_time'] + note['duration'] for note in notes)
                                
                                dst_clip.set_notes_extended(
                                    notes=note_tuples,
                                    from_time=min_time,
                                    from_pitch=0,
                                    time_span=max_time - min_time,
                                    pitch_span=128
                                )
                                
                                self.c_surface.log_message(
                                    f"📋 Duplicated {len(notes)} MIDI notes: "
                                    f"T{src_track_idx}S{src_scene_idx} → T{dst_track_idx}S{dst_scene_idx}"
                                )
                                return True
                                
            return False
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error duplicating MIDI notes: {e}")
            return False
    
    def _send_midi_notes_data(self, track_idx, scene_idx, notes):
        """Send MIDI notes data to hardware"""
        try:
            # Send notes in batches to avoid oversized messages
            batch_size = 10
            for i in range(0, len(notes), batch_size):
                batch = notes[i:i + batch_size]
                payload = [track_idx, scene_idx, len(batch)]
                
                for note in batch:
                    # Pack note data: pitch, start_time_bytes, duration_bytes, velocity
                    start_time_ms = int(note['start_time'] * 1000) & 0xFFFF
                    duration_ms = int(note['duration'] * 1000) & 0xFFFF
                    
                    payload.extend([
                        note['pitch'] & 0x7F,
                        (start_time_ms >> 8) & 0x7F,
                        start_time_ms & 0x7F,
                        (duration_ms >> 8) & 0x7F,
                        duration_ms & 0x7F,
                        note['velocity'] & 0x7F
                    ])
                
                self.c_surface._send_sysex_command(CMD_MIDI_NOTES, payload)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending MIDI notes data: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _clip_exists(self, track_idx, scene_idx):
        """Check if clip exists at position"""
        return (track_idx < len(self.song.tracks) and 
                scene_idx < len(self.song.scenes) and
                self.song.tracks[track_idx].clip_slots[scene_idx].has_clip)
    
    def _is_audio_clip(self, clip):
        """Check if clip is audio clip with proper validation"""
        try:
            if not clip:
                return False
            # Primary check: is_audio_clip property
            if hasattr(clip, 'is_audio_clip'):
                return clip.is_audio_clip
            # Fallback: check for audio-specific properties
            elif hasattr(clip, 'sample') or hasattr(clip, 'warping'):
                return True
            # Another fallback: check if it's NOT a MIDI clip
            elif hasattr(clip, 'is_midi_clip'):
                return not clip.is_midi_clip
            # Default to False if we can't determine
            return False
        except Exception:
            return False
    
    def _is_midi_clip(self, clip):
        """Check if clip is MIDI clip with proper validation"""
        try:
            if not clip:
                return False
            # Primary check: is_midi_clip property
            if hasattr(clip, 'is_midi_clip'):
                return clip.is_midi_clip
            # Fallback: check for MIDI-specific properties
            elif (hasattr(clip, 'get_notes') or 
                  hasattr(clip, 'get_notes_extended') or
                  hasattr(clip, 'set_notes')):
                return True
            # Another fallback: check if it's NOT an audio clip
            elif hasattr(clip, 'is_audio_clip'):
                return not clip.is_audio_clip
            # Default to False if we can't determine
            return False
        except Exception:
            return False
    
    def _get_sample_info(self, clip):
        """Get comprehensive Sample class information from audio clip"""
        try:
            if not clip or not hasattr(clip, 'sample'):
                return None
                
            sample = clip.sample
            if not sample:
                return None
                
            sample_info = {
                'available': True,
                'name': getattr(sample, 'name', 'Unknown'),
                'file_path': getattr(sample, 'file_path', ''),
                'length': getattr(sample, 'length', 0.0),
                'sample_rate': getattr(sample, 'sample_rate', 44100),
                'bit_depth': getattr(sample, 'bit_depth', 16),
                'channels': getattr(sample, 'channels', 1),
                'beats_gran': getattr(sample, 'beats_gran', 1.0),
                'beats_user': getattr(sample, 'beats_user', 0.0),
                'gain': getattr(sample, 'gain', 1.0)
            }
            
            # Sample slicing information (if available)
            if hasattr(sample, 'slices'):
                sample_info['slices'] = []
                for slice_idx, slice_obj in enumerate(sample.slices[:16]):  # Max 16 slices
                    if slice_obj:
                        sample_info['slices'].append({
                            'index': slice_idx,
                            'start_time': getattr(slice_obj, 'start_time', 0.0),
                            'end_time': getattr(slice_obj, 'end_time', 0.0)
                        })
            
            # Sample warp markers (if available)
            if hasattr(sample, 'warp_markers'):
                sample_info['warp_markers'] = []
                for marker_idx, marker in enumerate(sample.warp_markers[:8]):  # Max 8 markers
                    if marker:
                        sample_info['warp_markers'].append({
                            'index': marker_idx,
                            'beat_time': getattr(marker, 'beat_time', 0.0),
                            'sample_time': getattr(marker, 'sample_time', 0.0)
                        })
            
            # Sample reverse state
            if hasattr(sample, 'reverse'):
                sample_info['reverse'] = sample.reverse
                
            return sample_info
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting sample info: {e}")
            return {'available': False, 'error': str(e)}
    
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
                'warping': (clip.warping if hasattr(clip, 'warping') else False) if self._is_audio_clip(clip) else None,
                'start_marker': getattr(clip, 'start_marker', 0.0) if self._is_audio_clip(clip) else None,
                'end_marker': getattr(clip, 'end_marker', 0.0) if self._is_audio_clip(clip) else None,
                'length': getattr(clip, 'length', 0.0),
                'sample_info': self._get_sample_info(clip) if self._is_audio_clip(clip) else None
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

            self._send_grid_update()
            
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
    
    def handle_midi_clip_command(self, command, payload):
        """Handle incoming MIDI clip commands from hardware"""
        try:
            if command == CMD_MIDI_NOTE_ADD and len(payload) >= 6:
                track_idx, scene_idx, pitch, velocity = payload[0], payload[1], payload[2], payload[3]
                start_time_ms = (payload[4] << 8) | payload[5]
                duration_ms = (payload[6] << 8) | payload[7] if len(payload) >= 8 else 500
                
                start_time = start_time_ms / 1000.0
                duration = duration_ms / 1000.0
                
                self.add_midi_note(track_idx, scene_idx, pitch, start_time, duration, velocity)
                
            elif command == CMD_MIDI_NOTE_REMOVE and len(payload) >= 6:
                track_idx, scene_idx = payload[0], payload[1]
                start_time_ms = (payload[2] << 8) | payload[3]
                end_time_ms = (payload[4] << 8) | payload[5]
                
                start_time = start_time_ms / 1000.0
                end_time = end_time_ms / 1000.0
                
                pitch_range = None
                if len(payload) >= 8:
                    pitch_range = (payload[6], payload[7])
                
                self.remove_midi_notes(track_idx, scene_idx, start_time, end_time, pitch_range)
                
            elif command == CMD_MIDI_CLIP_QUANTIZE and len(payload) >= 3:
                track_idx, scene_idx, quantization = payload[0], payload[1], payload[2]
                self.quantize_midi_clip(track_idx, scene_idx, quantization)
                
            elif command == CMD_MIDI_NOTES and len(payload) >= 2:
                track_idx, scene_idx = payload[0], payload[1]
                notes = self.get_midi_clip_notes(track_idx, scene_idx)
                if notes:
                    self._send_midi_notes_data(track_idx, scene_idx, notes)
                    
            else:
                self.c_surface.log_message(f"❓ Unknown MIDI clip command: 0x{command:02X}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling MIDI clip command 0x{command:02X}: {e}")

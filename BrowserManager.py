# BrowserManager.py - Navigation and Selection Management
"""
Manages navigation, selection and browser functionality
Based on Live Object Model: Application.View, Song.View, selection tracking
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class BrowserManager:
    """
    Manages all Navigation and Selection listeners and handlers
    Covers: Track selection, scene selection, view switching, navigation
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self.app = control_surface.application()
        self._listeners = []
        self._is_active = False
        
        self.c_surface.log_message("🔧 Initializing BrowserManager...")
        
        # Selection state tracking
        self._selected_track_idx = 0
        self._selected_scene_idx = 0
        self._current_view = "Session"  # Session or Arranger
        
    def setup_listeners(self):
        """Setup navigation and selection listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("📱 Setting up Browser/Navigation listeners...")
            
            # === SONG VIEW LISTENERS ===
            
            # Selected track
            selected_track_listener = lambda: self._on_selected_track_changed()
            self.song.view.add_selected_track_listener(selected_track_listener)
            self._listeners.append(('selected_track', selected_track_listener))
            
            # Selected scene
            selected_scene_listener = lambda: self._on_selected_scene_changed()
            self.song.view.add_selected_scene_listener(selected_scene_listener)
            self._listeners.append(('selected_scene', selected_scene_listener))
            
            # Detail clip (highlighted clip in detail view)
            if hasattr(self.song.view, 'detail_clip'):
                detail_clip_listener = lambda: self._on_detail_clip_changed()
                self.song.view.add_detail_clip_listener(detail_clip_listener)
                self._listeners.append(('detail_clip', detail_clip_listener))
            
            # Highlighted clip slot (Live 11.0+)
            if hasattr(self.song.view, 'add_highlighted_clip_slot_listener'):
                highlighted_clip_listener = lambda: self._on_highlighted_clip_slot_changed()
                self.song.view.add_highlighted_clip_slot_listener(highlighted_clip_listener)
                self._listeners.append(('highlighted_clip_slot', highlighted_clip_listener))
            else:
                self.c_surface.log_message("ℹ️ highlighted_clip_slot_listener not available (requires Live 11.0+)")
            
            # === APPLICATION VIEW LISTENERS ===
            
            # Focused document view (Session/Arranger)
            if hasattr(self.app.view, 'focused_document_view'):
                focused_view_listener = lambda: self._on_focused_document_view_changed()
                self.app.view.add_focused_document_view_listener(focused_view_listener)
                self._listeners.append(('focused_document_view', focused_view_listener))
            
            # Browse mode (Hot-Swap)
            if hasattr(self.app.view, 'browse_mode'):
                browse_mode_listener = lambda: self._on_browse_mode_changed()
                self.app.view.add_browse_mode_listener(browse_mode_listener)
                self._listeners.append(('browse_mode', browse_mode_listener))
            
            self._is_active = True
            self.c_surface.log_message(f"✅ Browser/Navigation listeners setup ({len(self._listeners)} listeners)")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up browser listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all navigation listeners"""
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 'selected_track':
                        self.song.view.remove_selected_track_listener(listener_func)
                    elif listener_type == 'selected_scene':
                        self.song.view.remove_selected_scene_listener(listener_func)
                    elif listener_type == 'detail_clip':
                        self.song.view.remove_detail_clip_listener(listener_func)
                    elif listener_type == 'highlighted_clip_slot':
                        self.song.view.remove_highlighted_clip_slot_listener(listener_func)
                    elif listener_type == 'focused_document_view':
                        self.app.view.remove_focused_document_view_listener(listener_func)
                    elif listener_type == 'browse_mode':
                        self.app.view.remove_browse_mode_listener(listener_func)
                except:
                    pass  # Ignore if already removed
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Browser/Navigation listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning browser listeners: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_selected_track_changed(self):
        """Selected track changed"""
        if self.c_surface._is_connected:
            selected_track = self.song.view.selected_track
            
            # Find track index
            track_idx = -1
            if selected_track:
                try:
                    # Check regular tracks
                    track_idx = list(self.song.tracks).index(selected_track)
                except ValueError:
                    try:
                        # Check return tracks
                        track_idx = len(self.song.tracks) + list(self.song.return_tracks).index(selected_track)
                    except ValueError:
                        # Check master track
                        if selected_track == self.song.master_track:
                            track_idx = len(self.song.tracks) + len(self.song.return_tracks)
            
            if track_idx != self._selected_track_idx:
                self._selected_track_idx = track_idx
                track_name = selected_track.name if selected_track else "None"
                self.c_surface.log_message(f"🎯 Selected track {track_idx}: {track_name}")
                self._send_selected_track(track_idx, track_name)
    
    def _on_selected_scene_changed(self):
        """Selected scene changed"""
        if self.c_surface._is_connected:
            selected_scene = self.song.view.selected_scene
            
            # Find scene index
            scene_idx = -1
            if selected_scene:
                try:
                    scene_idx = list(self.song.scenes).index(selected_scene)
                except ValueError:
                    pass
            
            if scene_idx != self._selected_scene_idx:
                self._selected_scene_idx = scene_idx
                scene_name = selected_scene.name if selected_scene else "None"
                self.c_surface.log_message(f"🎬 Selected scene {scene_idx}: {scene_name}")
                self._send_selected_scene(scene_idx, scene_name)
    
    def _on_detail_clip_changed(self):
        """Detail clip changed"""
        if self.c_surface._is_connected:
            detail_clip = self.song.view.detail_clip
            
            if detail_clip:
                # Find clip position
                track_idx, scene_idx = self._find_clip_position(detail_clip)
                self.c_surface.log_message(f"📋 Detail clip: T{track_idx}S{scene_idx} '{detail_clip.name}'")
                self._send_detail_clip(track_idx, scene_idx, detail_clip.name)
            else:
                self.c_surface.log_message("📋 Detail clip: None")
                self._send_detail_clip(-1, -1, "")
    
    def _on_highlighted_clip_slot_changed(self):
        """Highlighted clip slot changed"""
        if self.c_surface._is_connected:
            highlighted_slot = self.song.view.highlighted_clip_slot
            
            if highlighted_slot:
                # Find slot position
                track_idx, scene_idx = self._find_clip_slot_position(highlighted_slot)
                self.c_surface.log_message(f"💡 Highlighted slot: T{track_idx}S{scene_idx}")
                self._send_highlighted_clip_slot(track_idx, scene_idx)
            else:
                self.c_surface.log_message("💡 Highlighted slot: None")
                self._send_highlighted_clip_slot(-1, -1)
    
    def _on_focused_document_view_changed(self):
        """Focused document view changed"""
        if self.c_surface._is_connected:
            focused_view = self.app.view.focused_document_view
            
            if focused_view != self._current_view:
                self._current_view = focused_view
                self.c_surface.log_message(f"👁️ View: {focused_view}")
                self._send_view_change(focused_view)
    
    def _on_browse_mode_changed(self):
        """Browse mode (Hot-Swap) changed"""
        if self.c_surface._is_connected:
            browse_mode = self.app.view.browse_mode
            self.c_surface.log_message(f"🔍 Browse mode: {browse_mode}")
            self._send_browse_mode(browse_mode)
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_selected_track(self, track_idx, track_name):
        """Send selected track to hardware"""
        try:
            # Validate track_idx is within valid range
            if track_idx < 0 or track_idx > 127:
                track_idx = 127  # Use 127 for invalid values
            
            name_bytes = track_name.encode('utf-8')[:8] if track_name else []
            payload = [track_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_SELECTED_TRACK, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending selected track: {e}")
    
    def _send_selected_scene(self, scene_idx, scene_name):
        """Send selected scene to hardware"""
        try:
            # Validate scene_idx is within valid range
            if scene_idx < 0 or scene_idx > 127:
                scene_idx = 127  # Use 127 for invalid values
            
            name_bytes = scene_name.encode('utf-8')[:8] if scene_name else []
            payload = [scene_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_SELECTED_SCENE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending selected scene: {e}")
    
    def _send_detail_clip(self, track_idx, scene_idx, clip_name):
        """Send detail clip to hardware"""
        try:
            # Validate indices are within valid range
            if track_idx < 0 or track_idx > 127:
                track_idx = 127  # Use 127 for invalid values
            if scene_idx < 0 or scene_idx > 127:
                scene_idx = 127  # Use 127 for invalid values
            
            name_bytes = clip_name.encode('utf-8')[:8] if clip_name else []
            payload = [track_idx, scene_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_DETAIL_CLIP, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending detail clip: {e}")
    
    def _send_highlighted_clip_slot(self, track_idx, scene_idx):
        """Send highlighted clip slot to hardware"""
        try:
            payload = [
                track_idx if track_idx >= 0 else 127,
                scene_idx if scene_idx >= 0 else 127
            ]
            # Could add CMD_HIGHLIGHTED_SLOT = 0xB4 to consts.py
            # For now, reuse detail clip command with empty name
            payload.append(0)  # Empty name length
            self.c_surface._send_sysex_command(CMD_DETAIL_CLIP, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending highlighted slot: {e}")
    
    def _send_view_change(self, view_name):
        """Send view change to hardware"""
        try:
            # Map view names to view IDs
            view_map = {
                "Session": 0,
                "Arranger": 1,
                "Detail": 2,
                "Detail/Clip": 2,
                "Detail/DeviceChain": 3
            }
            
            view_id = view_map.get(view_name, 0)
            
            # Use the view switch encoder from MIDIUtils
            message = SysExEncoder.encode_view_switch(view_id)
            if message:
                self.c_surface._send_midi(tuple(message))
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending view change: {e}")
    
    def _send_browse_mode(self, browse_mode):
        """Send browse mode to hardware"""
        try:
            payload = [1 if browse_mode else 0]
            # Could add CMD_BROWSE_MODE = 0xB5 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending browse mode: {e}")
    
    # ========================================
    # NAVIGATION ACTIONS
    # ========================================
    
    def select_track(self, track_idx):
        """Select track by index"""
        try:
            if track_idx < len(self.song.tracks):
                track = self.song.tracks[track_idx]
                self.song.view.selected_track = track
                self.c_surface.log_message(f"🎯 Selected track {track_idx}: {track.name}")
            elif track_idx < len(self.song.tracks) + len(self.song.return_tracks):
                # Return track
                return_idx = track_idx - len(self.song.tracks)
                track = self.song.return_tracks[return_idx]
                self.song.view.selected_track = track
                self.c_surface.log_message(f"🎯 Selected return track {return_idx}: {track.name}")
            elif track_idx == len(self.song.tracks) + len(self.song.return_tracks):
                # Master track
                self.song.view.selected_track = self.song.master_track
                self.c_surface.log_message("🎯 Selected master track")
            else:
                self.c_surface.log_message(f"❌ Invalid track index: {track_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error selecting track {track_idx}: {e}")
    
    def select_scene(self, scene_idx):
        """Select scene by index"""
        try:
            if scene_idx < len(self.song.scenes):
                scene = self.song.scenes[scene_idx]
                self.song.view.selected_scene = scene
                self.c_surface.log_message(f"🎬 Selected scene {scene_idx}: {scene.name}")
            else:
                self.c_surface.log_message(f"❌ Invalid scene index: {scene_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error selecting scene {scene_idx}: {e}")
    
    def navigate_track(self, direction):
        """Navigate tracks (left/right)"""
        try:
            current_track = self.song.view.selected_track
            
            if direction > 0:  # Right (next track)
                if current_track in self.song.tracks:
                    current_idx = list(self.song.tracks).index(current_track)
                    if current_idx < len(self.song.tracks) - 1:
                        self.select_track(current_idx + 1)
                    elif self.song.return_tracks:
                        self.select_track(len(self.song.tracks))  # First return track
                    else:
                        self.select_track(len(self.song.tracks) + len(self.song.return_tracks))  # Master
                        
                elif current_track in self.song.return_tracks:
                    current_idx = list(self.song.return_tracks).index(current_track)
                    if current_idx < len(self.song.return_tracks) - 1:
                        self.select_track(len(self.song.tracks) + current_idx + 1)
                    else:
                        self.select_track(len(self.song.tracks) + len(self.song.return_tracks))  # Master
                        
                # If at master, stay there
                
            else:  # Left (previous track)
                if current_track == self.song.master_track:
                    if self.song.return_tracks:
                        self.select_track(len(self.song.tracks) + len(self.song.return_tracks) - 1)  # Last return
                    else:
                        self.select_track(len(self.song.tracks) - 1)  # Last regular track
                        
                elif current_track in self.song.return_tracks:
                    current_idx = list(self.song.return_tracks).index(current_track)
                    if current_idx > 0:
                        self.select_track(len(self.song.tracks) + current_idx - 1)
                    else:
                        self.select_track(len(self.song.tracks) - 1)  # Last regular track
                        
                elif current_track in self.song.tracks:
                    current_idx = list(self.song.tracks).index(current_track)
                    if current_idx > 0:
                        self.select_track(current_idx - 1)
                        
        except Exception as e:
            self.c_surface.log_message(f"❌ Error navigating track: {e}")
    
    def navigate_scene(self, direction):
        """Navigate scenes (up/down)"""
        try:
            current_scene = self.song.view.selected_scene
            
            if current_scene in self.song.scenes:
                current_idx = list(self.song.scenes).index(current_scene)
                
                if direction > 0:  # Down (next scene)
                    if current_idx < len(self.song.scenes) - 1:
                        self.select_scene(current_idx + 1)
                else:  # Up (previous scene)
                    if current_idx > 0:
                        self.select_scene(current_idx - 1)
                        
        except Exception as e:
            self.c_surface.log_message(f"❌ Error navigating scene: {e}")
    
    def switch_view(self, view_name):
        """Switch to specified view"""
        try:
            if hasattr(self.app.view, 'focus_view'):
                self.app.view.focus_view(view_name)
                self.c_surface.log_message(f"👁️ Switched to {view_name} view")
            else:
                self.c_surface.log_message("❌ View switching not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error switching to {view_name} view: {e}")
    
    def toggle_browse_mode(self):
        """Toggle browse mode (Hot-Swap)"""
        try:
            if hasattr(self.app.view, 'toggle_browse'):
                self.app.view.toggle_browse()
                self.c_surface.log_message("🔍 Toggled browse mode")
            else:
                self.c_surface.log_message("❌ Browse mode not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling browse mode: {e}")
    
    def scroll_view(self, direction, view_name=""):
        """Scroll in specified view"""
        try:
            if hasattr(self.app.view, 'scroll_view'):
                # direction: 0=up, 1=down, 2=left, 3=right
                self.app.view.scroll_view(direction, view_name, False)
                direction_names = ["up", "down", "left", "right"]
                dir_name = direction_names[direction] if direction < 4 else "unknown"
                self.c_surface.log_message(f"📜 Scrolled {dir_name} in {view_name or 'current'} view")
            else:
                self.c_surface.log_message("❌ View scrolling not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error scrolling view: {e}")
    
    def zoom_view(self, direction, view_name=""):
        """Zoom in specified view"""
        try:
            if hasattr(self.app.view, 'zoom_view'):
                # direction: 0=up/in, 1=down/out, 2=left, 3=right
                self.app.view.zoom_view(direction, view_name, False)
                zoom_names = ["in", "out", "left", "right"]
                zoom_name = zoom_names[direction] if direction < 4 else "unknown"
                self.c_surface.log_message(f"🔍 Zoomed {zoom_name} in {view_name or 'current'} view")
            else:
                self.c_surface.log_message("❌ View zooming not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error zooming view: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _find_clip_position(self, clip):
        """Find track and scene index for a clip"""
        try:
            for track_idx, track in enumerate(self.song.tracks):
                for scene_idx, clip_slot in enumerate(track.clip_slots):
                    if clip_slot.has_clip and clip_slot.clip == clip:
                        return track_idx, scene_idx
            return -1, -1
        except:
            return -1, -1
    
    def _find_clip_slot_position(self, clip_slot):
        """Find track and scene index for a clip slot"""
        try:
            for track_idx, track in enumerate(self.song.tracks):
                for scene_idx, slot in enumerate(track.clip_slots):
                    if slot == clip_slot:
                        return track_idx, scene_idx
            return -1, -1
        except:
            return -1, -1
    
    def get_navigation_info(self):
        """Get complete navigation information"""
        try:
            selected_track = self.song.view.selected_track
            selected_scene = self.song.view.selected_scene
            
            # Find indices
            track_idx = -1
            if selected_track:
                if selected_track in self.song.tracks:
                    track_idx = list(self.song.tracks).index(selected_track)
                elif selected_track in self.song.return_tracks:
                    track_idx = len(self.song.tracks) + list(self.song.return_tracks).index(selected_track)
                elif selected_track == self.song.master_track:
                    track_idx = len(self.song.tracks) + len(self.song.return_tracks)
            
            scene_idx = -1
            if selected_scene and selected_scene in self.song.scenes:
                scene_idx = list(self.song.scenes).index(selected_scene)
            
            return {
                'selected_track_idx': track_idx,
                'selected_track_name': selected_track.name if selected_track else "",
                'selected_scene_idx': scene_idx,
                'selected_scene_name': selected_scene.name if selected_scene else "",
                'current_view': self._current_view,
                'browse_mode': getattr(self.app.view, 'browse_mode', False),
                'total_tracks': len(self.song.tracks),
                'total_return_tracks': len(self.song.return_tracks),
                'total_scenes': len(self.song.scenes),
                'detail_clip': self.song.view.detail_clip.name if hasattr(self.song.view, 'detail_clip') and self.song.view.detail_clip else ""
            }
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting navigation info: {e}")
            return {}
    
    def send_complete_state(self):
        """Send complete navigation state to hardware"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete navigation state...")
            
            # Get current state
            info = self.get_navigation_info()
            
            # Send selections
            self._send_selected_track(info['selected_track_idx'], info['selected_track_name'])
            self._send_selected_scene(info['selected_scene_idx'], info['selected_scene_name'])
            
            # Send view
            self._send_view_change(info['current_view'])
            
            # Send browse mode
            self._send_browse_mode(info['browse_mode'])
            
            # Send detail clip if available
            if hasattr(self.song.view, 'detail_clip') and self.song.view.detail_clip:
                detail_clip = self.song.view.detail_clip
                track_idx, scene_idx = self._find_clip_position(detail_clip)
                self._send_detail_clip(track_idx, scene_idx, detail_clip.name)
            
            self.c_surface.log_message("✅ Navigation state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending navigation state: {e}")
    
    def handle_navigation_command(self, command, payload):
        """Handle incoming navigation commands from hardware"""
        try:
            # Ring navigation commands should NOT be handled here
            # They're handled by SessionRing in PushClone._route_command
            if command in [CMD_RING_NAVIGATE, CMD_RING_SELECT, CMD_RING_POSITION]:
                self.c_surface.log_message(f"⚠️ Ring command 0x{command:02X} reached BrowserManager (routing error)")
                return

            if command == CMD_SELECTED_TRACK and len(payload) >= 1:
                track_idx = payload[0]
                if track_idx != 127:  # 127 = invalid
                    self.select_track(track_idx)

            elif command == CMD_SELECTED_SCENE and len(payload) >= 1:
                scene_idx = payload[0]
                if scene_idx != 127:  # 127 = invalid
                    self.select_scene(scene_idx)

            elif command == CMD_SWITCH_VIEW and len(payload) >= 1:
                view_id = payload[0]
                view_names = ["Session", "Arranger", "Detail", "Detail/DeviceChain"]
                if view_id < len(view_names):
                    self.switch_view(view_names[view_id])

            else:
                self.c_surface.log_message(f"❓ Unknown navigation command: 0x{command:02X}")

        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling navigation command 0x{command:02X}: {e}")
    
    def set_grid_position(self, track_idx, scene_idx):
        """Set grid position (track and scene selection)"""
        try:
            self.select_track(track_idx)
            self.select_scene(scene_idx)
            self.c_surface.log_message(f"🎯 Grid position: T{track_idx}S{scene_idx}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting grid position T{track_idx}S{scene_idx}: {e}")
    
    def navigate_grid(self, track_direction, scene_direction):
        """Navigate grid by relative amount"""
        try:
            if track_direction != 0:
                self.navigate_track(track_direction)
            if scene_direction != 0:
                self.navigate_scene(scene_direction)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error navigating grid: {e}")

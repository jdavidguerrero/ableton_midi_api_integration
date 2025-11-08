# SessionRing.py - Session Ring Management
"""
Manages the 4x8 session window (ring) for Push-style navigation
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class SessionRing:
    """
    Manages the 4x8 session ring (window) for clip launching
    Provides navigation and track/scene selection
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        
        self.c_surface.log_message("🔧 Initializing SessionRing...")
        
        # Ring dimensions (tracks x scenes)
        self.ring_width = 4   # tracks visible
        self.ring_height = 8  # scenes visible

        # Current ring position
        self.track_offset = 0   # Starting track index
        self.scene_offset = 0   # Starting scene index

        # Selection tracking
        self.selected_track_index = 0
        self.selected_scene_index = 0

        # Session Overview mode (Push 3 style zoom-out)
        self.overview_mode = False
        self.overview_zoom = 4  # Each pad represents 4x4 cells in overview
        
        # Listeners
        self._listeners = []
        self._is_active = False
        
    def setup_listeners(self):
        """Setup ring-related listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("🎯 Setting up Session Ring listeners...")
            
            # Track selection changes
            track_listener = lambda: self._on_selected_track_changed()
            self.song.view.add_selected_track_listener(track_listener)
            self._listeners.append(('selected_track', track_listener))
            
            # Scene selection changes
            scene_listener = lambda: self._on_selected_scene_changed()
            self.song.view.add_selected_scene_listener(scene_listener)
            self._listeners.append(('selected_scene', scene_listener))
            
            # Track list changes (tracks added/removed)
            tracks_listener = lambda: self._on_tracks_changed()
            self.song.add_tracks_listener(tracks_listener)
            self._listeners.append(('tracks', tracks_listener))
            
            # Scene list changes (scenes added/removed)
            scenes_listener = lambda: self._on_scenes_changed()
            self.song.add_scenes_listener(scenes_listener)
            self._listeners.append(('scenes', scenes_listener))
            
            # Initialize ring position based on current selection
            self._update_ring_from_selection()
            
            self._is_active = True
            self.c_surface.log_message("✅ Session Ring listeners setup")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up ring listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all ring listeners"""
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 'selected_track':
                        self.song.view.remove_selected_track_listener(listener_func)
                    elif listener_type == 'selected_scene':
                        self.song.view.remove_selected_scene_listener(listener_func)
                    elif listener_type == 'tracks':
                        self.song.remove_tracks_listener(listener_func)
                    elif listener_type == 'scenes':
                        self.song.remove_scenes_listener(listener_func)
                except:
                    pass
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Session Ring listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning ring listeners: {e}")
    
    # ========================================
    # RING POSITION MANAGEMENT
    # ========================================
    
    def _update_ring_from_selection(self):
        """Update ring position to follow selected track/scene"""
        try:
            # Get current selection indices
            selected_track = self.song.view.selected_track
            selected_scene = self.song.view.selected_scene
            
            # Find track index
            track_index = 0
            for i, track in enumerate(self.song.tracks):
                if track == selected_track:
                    track_index = i
                    break
            
            # Find scene index
            scene_index = 0
            for i, scene in enumerate(self.song.scenes):
                if scene == selected_scene:
                    scene_index = i
                    break
            
            self.selected_track_index = track_index
            self.selected_scene_index = scene_index
            
            # Update ring position to include selection
            self._update_ring_to_include(track_index, scene_index)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error updating ring from selection: {e}")
    
    def _update_ring_to_include(self, track_idx, scene_idx):
        """Update ring position to include specified track/scene"""
        old_track_offset = self.track_offset
        old_scene_offset = self.scene_offset
        
        # Adjust track offset if needed
        if track_idx < self.track_offset:
            self.track_offset = track_idx
        elif track_idx >= self.track_offset + self.ring_width:
            self.track_offset = track_idx - self.ring_width + 1
        
        # Adjust scene offset if needed
        if scene_idx < self.scene_offset:
            self.scene_offset = scene_idx
        elif scene_idx >= self.scene_offset + self.ring_height:
            self.scene_offset = scene_idx - self.ring_height + 1
        
        # Clamp offsets to valid ranges
        max_track_offset = max(0, len(self.song.tracks) - self.ring_width)
        max_scene_offset = max(0, len(self.song.scenes) - self.ring_height)
        
        self.track_offset = max(0, min(self.track_offset, max_track_offset))
        self.scene_offset = max(0, min(self.scene_offset, max_scene_offset))
        
        # Set the session highlight
        self.c_surface.set_session_highlight(self.track_offset, self.scene_offset, self.ring_width, self.ring_height)
        
        # Send ring update if position changed
        if (self.track_offset != old_track_offset or 
            self.scene_offset != old_scene_offset):
            self._send_ring_position()
            self._send_ring_clips()
    
    def navigate_ring(self, direction):
        """
        Navigate ring in specified direction
        Args:
            direction (str): 'left', 'right', 'up', 'down'
        """
        try:
            old_track_offset = self.track_offset
            old_scene_offset = self.scene_offset
            
            if direction == 'left':
                self.track_offset = max(0, self.track_offset - 1)
            elif direction == 'right':
                max_offset = max(0, len(self.song.tracks) - self.ring_width)
                self.track_offset = min(max_offset, self.track_offset + 1)
            elif direction == 'up':
                self.scene_offset = max(0, self.scene_offset - 1)
            elif direction == 'down':
                max_offset = max(0, len(self.song.scenes) - self.ring_height)
                self.scene_offset = min(max_offset, self.scene_offset + 1)
            
            # Update if position changed
            if (self.track_offset != old_track_offset or 
                self.scene_offset != old_scene_offset):
                
                self.c_surface.log_message(
                    f"🎯 Ring navigated {direction}: T{self.track_offset} S{self.scene_offset}"
                )
                
                self._send_ring_position()
                self._send_ring_clips()
                
                # Update selected track/scene if needed
                self._update_selection_to_ring()
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error navigating ring {direction}: {e}")
    
    def _update_selection_to_ring(self):
        """Update Live's selection to match ring position"""
        try:
            # Select track at current ring position if different
            current_track_idx = self.track_offset + (self.ring_width // 2)  # Center of ring
            current_scene_idx = self.scene_offset + (self.ring_height // 2)  # Center of ring
            
            if (current_track_idx < len(self.song.tracks) and
                current_track_idx != self.selected_track_index):
                self.song.view.selected_track = self.song.tracks[current_track_idx]
                
            if (current_scene_idx < len(self.song.scenes) and
                current_scene_idx != self.selected_scene_index):
                self.song.view.selected_scene = self.song.scenes[current_scene_idx]
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error updating selection to ring: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_selected_track_changed(self):
        """Handle track selection changes"""
        if self.c_surface._is_connected:
            try:
                selected_track = self.song.view.selected_track
                track_index = 0
                
                for i, track in enumerate(self.song.tracks):
                    if track == selected_track:
                        track_index = i
                        break
                
                old_index = self.selected_track_index
                self.selected_track_index = track_index
                
                if track_index != old_index:
                    self.c_surface.log_message(f"🎯 Track selection changed: {track_index}")
                    self._update_ring_to_include(track_index, self.selected_scene_index)
                    self._send_track_selection(track_index)
                
            except Exception as e:
                self.c_surface.log_message(f"❌ Error handling track selection: {e}")
    
    def _on_selected_scene_changed(self):
        """Handle scene selection changes"""
        if self.c_surface._is_connected:
            try:
                selected_scene = self.song.view.selected_scene
                scene_index = 0
                
                for i, scene in enumerate(self.song.scenes):
                    if scene == selected_scene:
                        scene_index = i
                        break
                
                old_index = self.selected_scene_index
                self.selected_scene_index = scene_index
                
                if scene_index != old_index:
                    self.c_surface.log_message(f"🎯 Scene selection changed: {scene_index}")
                    self._update_ring_to_include(self.selected_track_index, scene_index)
                    self._send_scene_selection(scene_index)
                
            except Exception as e:
                self.c_surface.log_message(f"❌ Error handling scene selection: {e}")
    
    def _on_tracks_changed(self):
        """Handle tracks added/removed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message("🎯 Tracks changed, updating ring")
            # Re-clamp ring position
            max_track_offset = max(0, len(self.song.tracks) - self.ring_width)
            self.track_offset = min(self.track_offset, max_track_offset)
            self._send_ring_position()
            self._send_ring_clips()
    
    def _on_scenes_changed(self):
        """Handle scenes added/removed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message("🎯 Scenes changed, updating ring")
            # Re-clamp ring position
            max_scene_offset = max(0, len(self.song.scenes) - self.ring_height)
            self.scene_offset = min(self.scene_offset, max_scene_offset)
            self._send_ring_position()
            self._send_ring_clips()
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_ring_position(self):
        """Send current ring position to hardware using 14-bit encoding"""
        try:
            from .MIDIUtils import SysExEncoder

            # Use 14-bit encoding for offsets (supports up to 16,384 tracks/scenes)
            # MSB = upper 7 bits, LSB = lower 7 bits
            track_offset_msb = (self.track_offset >> 7) & 0x7F
            track_offset_lsb = self.track_offset & 0x7F
            scene_offset_msb = (self.scene_offset >> 7) & 0x7F
            scene_offset_lsb = self.scene_offset & 0x7F

            # Payload: [track_msb, track_lsb, scene_msb, scene_lsb, width, height, overview_mode]
            payload = [
                track_offset_msb,
                track_offset_lsb,
                scene_offset_msb,
                scene_offset_lsb,
                self.ring_width & 0x7F,
                self.ring_height & 0x7F,
                1 if self.overview_mode else 0
            ]
            self.c_surface._send_sysex_command(CMD_RING_POSITION, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending ring position: {e}")
    
    def _send_ring_clips(self):
        """Send all clips in current ring to hardware using a single grid message."""
        try:
            if not self.c_surface._is_connected:
                return
            
            # Get the clip manager and send the single, consolidated grid update
            clip_manager = self.c_surface.get_manager('clip')
            if clip_manager:
                clip_manager._send_neotrellis_clip_grid()
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending ring clips: {e}")
    
    def _send_track_selection(self, track_index):
        """Send track selection change to hardware with 14-bit encoding"""
        try:
            # Calculate relative position within ring
            relative_track = track_index - self.track_offset
            is_in_ring = 0 <= relative_track < self.ring_width

            # Use 14-bit encoding for track index
            track_msb = (track_index >> 7) & 0x7F
            track_lsb = track_index & 0x7F

            # Payload: [track_msb, track_lsb, is_in_ring]
            payload = [track_msb, track_lsb, 1 if is_in_ring else 0]
            self.c_surface._send_sysex_command(CMD_TRACK_SELECT, payload)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending track selection: {e}")
    
    def _send_scene_selection(self, scene_index):
        """Send scene selection change to hardware with 14-bit encoding"""
        try:
            # Calculate relative position within ring
            relative_scene = scene_index - self.scene_offset
            is_in_ring = 0 <= relative_scene < self.ring_height

            # Use 14-bit encoding for scene index
            scene_msb = (scene_index >> 7) & 0x7F
            scene_lsb = scene_index & 0x7F

            # Payload: [scene_msb, scene_lsb, is_in_ring]
            payload = [scene_msb, scene_lsb, 1 if is_in_ring else 0]
            self.c_surface._send_sysex_command(CMD_SCENE_SELECT, payload)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending scene selection: {e}")
    
    # ========================================
    # SESSION OVERVIEW MODE (Push 3 style)
    # ========================================

    def toggle_overview_mode(self):
        """Toggle Session Overview mode on/off"""
        try:
            self.overview_mode = not self.overview_mode
            state = "enabled" if self.overview_mode else "disabled"
            self.c_surface.log_message(f"🔍 Session Overview: {state}")

            if self.overview_mode:
                self._send_overview_grid()
            else:
                # Return to normal mode
                self._send_ring_position()
                self._send_ring_clips()

        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling overview mode: {e}")

    def _send_overview_grid(self):
        """
        Send overview grid to hardware
        Each pad represents multiple tracks/scenes (zoom-out view)

        Example with zoom=4:
        - Pad (0,0) represents tracks 0-3, scenes 0-3
        - Pad (1,0) represents tracks 4-7, scenes 0-3
        - etc.
        """
        try:
            if not self.c_surface._is_connected:
                return

            # Build overview grid (4x8 pads)
            grid_data = []

            for scene_idx in range(self.ring_height):  # 8 scenes
                for track_idx in range(self.ring_width):  # 4 tracks
                    # Calculate absolute track/scene range this pad represents
                    abs_track_start = track_idx * self.overview_zoom
                    abs_track_end = abs_track_start + self.overview_zoom
                    abs_scene_start = scene_idx * self.overview_zoom
                    abs_scene_end = abs_scene_start + self.overview_zoom

                    # Check if this region has any clips
                    has_clips = self._count_clips_in_region(
                        abs_track_start, abs_track_end,
                        abs_scene_start, abs_scene_end
                    )

                    # Determine color based on clip density
                    if has_clips == 0:
                        # No clips - dark gray
                        color = (20, 20, 20)
                    elif has_clips < self.overview_zoom * self.overview_zoom // 2:
                        # Few clips - medium gray
                        color = (60, 60, 60)
                    elif has_clips < self.overview_zoom * self.overview_zoom:
                        # Many clips - bright gray
                        color = (100, 100, 100)
                    else:
                        # Full - white
                        color = (127, 127, 127)

                    # Check if this region contains currently selected track/scene
                    if (abs_track_start <= self.selected_track_index < abs_track_end and
                        abs_scene_start <= self.selected_scene_index < abs_scene_end):
                        # Highlight selection in blue
                        color = (50, 100, 255)

                    grid_data.extend(color)

            # Send overview grid using CMD_SESSION_OVERVIEW_GRID
            self.c_surface._send_sysex_command(CMD_SESSION_OVERVIEW_GRID, grid_data)

        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending overview grid: {e}")

    def _count_clips_in_region(self, track_start, track_end, scene_start, scene_end):
        """Count number of clips in a region"""
        try:
            clip_count = 0

            for track_idx in range(track_start, track_end):
                if track_idx >= len(self.song.tracks):
                    break

                track = self.song.tracks[track_idx]

                for scene_idx in range(scene_start, scene_end):
                    if scene_idx >= len(track.clip_slots):
                        break

                    clip_slot = track.clip_slots[scene_idx]
                    if clip_slot.has_clip:
                        clip_count += 1

            return clip_count

        except Exception as e:
            return 0

    def handle_overview_pad_press(self, ring_track, ring_scene):
        """
        Handle pad press in overview mode
        Zoom into the region represented by this pad
        """
        try:
            # Calculate absolute position this pad represents
            abs_track = ring_track * self.overview_zoom
            abs_scene = ring_scene * self.overview_zoom

            # Exit overview mode
            self.overview_mode = False

            # Move ring to this position
            self.track_offset = abs_track
            self.scene_offset = abs_scene

            # Clamp to valid ranges
            max_track_offset = max(0, len(self.song.tracks) - self.ring_width)
            max_scene_offset = max(0, len(self.song.scenes) - self.ring_height)
            self.track_offset = min(self.track_offset, max_track_offset)
            self.scene_offset = min(self.scene_offset, max_scene_offset)

            # Send updated state
            self._send_ring_position()
            self._send_ring_clips()

            self.c_surface.log_message(
                f"🔍 Zoomed to T{self.track_offset} S{self.scene_offset}"
            )

        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling overview pad: {e}")

    # ========================================
    # PUBLIC INTERFACE
    # ========================================
    
    def get_ring_info(self):
        """Get current ring information"""
        return {
            'track_offset': self.track_offset,
            'scene_offset': self.scene_offset,
            'ring_width': self.ring_width,
            'ring_height': self.ring_height,
            'selected_track': self.selected_track_index,
            'selected_scene': self.selected_scene_index,
            'total_tracks': len(self.song.tracks),
            'total_scenes': len(self.song.scenes),
            'overview_mode': self.overview_mode,
            'overview_zoom': self.overview_zoom,
            'max_visible_tracks': self.ring_width * self.overview_zoom if self.overview_mode else self.ring_width,
            'max_visible_scenes': self.ring_height * self.overview_zoom if self.overview_mode else self.ring_height
        }
    
    def get_absolute_position(self, ring_track, ring_scene):
        """Convert ring-relative position to absolute track/scene indices"""
        return (self.track_offset + ring_track, self.scene_offset + ring_scene)
    
    def get_ring_position(self, absolute_track, absolute_scene):
        """Convert absolute position to ring-relative position"""
        ring_track = absolute_track - self.track_offset
        ring_scene = absolute_scene - self.scene_offset
        
        # Return None if outside ring
        if (ring_track < 0 or ring_track >= self.ring_width or
            ring_scene < 0 or ring_scene >= self.ring_height):
            return None
            
        return (ring_track, ring_scene)
    
    def is_in_ring(self, absolute_track, absolute_scene):
        """Check if absolute position is within current ring"""
        return (self.track_offset <= absolute_track < self.track_offset + self.ring_width and
                self.scene_offset <= absolute_scene < self.scene_offset + self.ring_height)
    
    def send_complete_state(self):
        """Send complete ring state to hardware"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("🎯 Sending complete ring state...")
            self._send_ring_position()
            self._send_ring_clips()
            self._send_track_selection(self.selected_track_index)
            self._send_scene_selection(self.selected_scene_index)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending ring state: {e}")
    
    def handle_navigation_command(self, command, payload):
        """Handle navigation commands from hardware"""
        try:
            self.c_surface.log_message(f"🔵 SessionRing received CMD:0x{command:02X} with {len(payload)} bytes")

            if command == CMD_RING_NAVIGATE and len(payload) >= 1:
                direction_map = {0: 'left', 1: 'right', 2: 'up', 3: 'down'}
                direction = direction_map.get(payload[0])
                self.c_surface.log_message(f"🔵 CMD_RING_NAVIGATE: payload[0]={payload[0]} → direction='{direction}'")
                if direction:
                    self.navigate_ring(direction)
                else:
                    self.c_surface.log_message(f"⚠️ Unknown direction value: {payload[0]}")

            elif command == CMD_RING_SELECT and len(payload) >= 2:
                ring_track, ring_scene = payload[0], payload[1]

                # Check if in overview mode
                if self.overview_mode:
                    # Handle overview pad press (zoom in)
                    self.handle_overview_pad_press(ring_track, ring_scene)
                else:
                    # Normal mode - update selection
                    absolute_track, absolute_scene = self.get_absolute_position(ring_track, ring_scene)

                    # Update Live's selection
                    if absolute_track < len(self.song.tracks):
                        self.song.view.selected_track = self.song.tracks[absolute_track]
                    if absolute_scene < len(self.song.scenes):
                        self.song.view.selected_scene = self.song.scenes[absolute_scene]

            elif command == CMD_SESSION_OVERVIEW:
                # Toggle overview mode
                self.toggle_overview_mode()

        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling navigation command 0x{command:02X}: {e}")
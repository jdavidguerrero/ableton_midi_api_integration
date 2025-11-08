# SessionOverview.py - Enhanced Session Overview with Zoom Levels
"""
Enhanced Session Overview Manager for Push Clone
Features:
- Adaptive zoom levels (1:1, 2:1, 4:1, 8:1)
- Ring position indicator
- Track-colored clip representation
- Dynamic updates
- Navigation in overview mode
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class SessionOverview:
    """
    Manages enhanced session overview with multiple zoom levels
    """

    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()

        # Overview state
        self._is_active = False
        self._zoom_level = 1  # 1:1, 2:1, 4:1, 8:1

        # Grid dimensions (your hardware)
        self.display_width = 8   # 8 pads horizontal
        self.display_height = 4  # 4 pads vertical

        # Overview viewport position
        self.overview_track_offset = 0
        self.overview_scene_offset = 0

        # Listeners for dynamic updates
        self._overview_listeners = []

    # ========================================
    # ZOOM LEVEL MANAGEMENT
    # ========================================

    def set_zoom_level(self, zoom):
        """
        Set overview zoom level
        Args:
            zoom (int): 1, 2, 4, or 8
                1:1 = cada pad = 1 clip (8x4 clips visible)
                2:1 = cada pad = 2x2 clips (16x8 clips visible)
                4:1 = cada pad = 4x4 clips (32x16 clips visible)
                8:1 = cada pad = 8x8 clips (64x32 clips visible)
        """
        if zoom in [1, 2, 4, 8]:
            old_zoom = self._zoom_level
            self._zoom_level = zoom

            self.c_surface.log_message(f"🔍 Overview zoom: {old_zoom}:1 → {zoom}:1")

            # Recalculate overview viewport
            self._recalculate_viewport()

            # Send updated overview
            if self._is_active:
                self.send_overview()

            return True
        return False

    def cycle_zoom(self):
        """Cycle through zoom levels: 1 → 2 → 4 → 8 → 1"""
        zoom_cycle = [1, 2, 4, 8]
        current_idx = zoom_cycle.index(self._zoom_level)
        next_idx = (current_idx + 1) % len(zoom_cycle)
        self.set_zoom_level(zoom_cycle[next_idx])

    def _recalculate_viewport(self):
        """Recalculate overview viewport based on zoom and ring position"""
        try:
            # Get session ring position
            session_ring = self.c_surface.get_manager('session_ring')
            if not session_ring:
                return

            ring_info = session_ring.get_ring_info()
            ring_track = ring_info['track_offset']
            ring_scene = ring_info['scene_offset']

            # Center overview on ring position
            visible_tracks = self.display_width * self._zoom_level
            visible_scenes = self.display_height * self._zoom_level

            # Center the ring in the overview
            self.overview_track_offset = max(0, ring_track - (visible_tracks // 2))
            self.overview_scene_offset = max(0, ring_scene - (visible_scenes // 2))

            # Clamp to session bounds
            max_track_offset = max(0, len(self.song.tracks) - visible_tracks)
            max_scene_offset = max(0, len(self.song.scenes) - visible_scenes)

            self.overview_track_offset = min(self.overview_track_offset, max_track_offset)
            self.overview_scene_offset = min(self.overview_scene_offset, max_scene_offset)

        except Exception as e:
            self.c_surface.log_message(f"❌ Error recalculating viewport: {e}")

    # ========================================
    # OVERVIEW ACTIVATION
    # ========================================

    def activate(self):
        """Activate session overview mode"""
        if self._is_active:
            return

        try:
            self._is_active = True

            # Setup dynamic listeners
            self._setup_overview_listeners()

            # Recalculate viewport
            self._recalculate_viewport()

            # Send overview data
            self.send_overview()

            self.c_surface.log_message(f"🔍 Session Overview activated (zoom {self._zoom_level}:1)")

        except Exception as e:
            self.c_surface.log_message(f"❌ Error activating overview: {e}")

    def deactivate(self):
        """Deactivate session overview mode"""
        if not self._is_active:
            return

        try:
            self._is_active = False

            # Remove listeners
            self._cleanup_overview_listeners()

            self.c_surface.log_message("🔍 Session Overview deactivated")

        except Exception as e:
            self.c_surface.log_message(f"❌ Error deactivating overview: {e}")

    def toggle(self):
        """Toggle overview mode on/off"""
        if self._is_active:
            self.deactivate()
        else:
            self.activate()

    # ========================================
    # DYNAMIC LISTENERS
    # ========================================

    def _setup_overview_listeners(self):
        """Setup listeners for dynamic overview updates"""
        try:
            # Listen to clip changes in visible area
            tracks = self.song.tracks
            scenes = self.song.scenes

            visible_tracks = self.display_width * self._zoom_level
            visible_scenes = self.display_height * self._zoom_level

            for track_idx in range(self.overview_track_offset,
                                  min(len(tracks), self.overview_track_offset + visible_tracks)):
                track = tracks[track_idx]

                for scene_idx in range(self.overview_scene_offset,
                                      min(len(scenes), self.overview_scene_offset + visible_scenes)):
                    if scene_idx < len(track.clip_slots):
                        clip_slot = track.clip_slots[scene_idx]

                        # Listen to playing status changes
                        listener = lambda t=track_idx, s=scene_idx: self._on_overview_clip_changed(t, s)
                        clip_slot.add_playing_status_listener(listener)
                        self._overview_listeners.append(('playing', track_idx, scene_idx, listener))

            self.c_surface.log_message(f"✅ Setup {len(self._overview_listeners)} overview listeners")

        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up overview listeners: {e}")

    def _cleanup_overview_listeners(self):
        """Remove all overview listeners"""
        try:
            tracks = self.song.tracks

            for listener_type, track_idx, scene_idx, listener_func in self._overview_listeners:
                try:
                    if track_idx < len(tracks):
                        track = tracks[track_idx]
                        if scene_idx < len(track.clip_slots):
                            clip_slot = track.clip_slots[scene_idx]
                            if listener_type == 'playing':
                                clip_slot.remove_playing_status_listener(listener_func)
                except:
                    pass

            self._overview_listeners = []

        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning overview listeners: {e}")

    def _on_overview_clip_changed(self, track_idx, scene_idx):
        """Handle clip change in overview area"""
        if self._is_active and self.c_surface._is_connected:
            # Update just the changed region
            self._update_overview_region(track_idx, scene_idx)

    # ========================================
    # OVERVIEW RENDERING
    # ========================================

    def send_overview(self):
        """Send complete overview grid to hardware"""
        try:
            if not self.c_surface._is_connected:
                return

            overview_data = []
            tracks = self.song.tracks
            scenes = self.song.scenes

            # Get session ring info for indicator
            session_ring = self.c_surface.get_manager('session_ring')
            ring_info = session_ring.get_ring_info() if session_ring else None

            # Calculate visible range
            visible_tracks = self.display_width * self._zoom_level
            visible_scenes = self.display_height * self._zoom_level

            # Render grid (8x4 pads)
            for pad_y in range(self.display_height):
                for pad_x in range(self.display_width):
                    # Calculate which clips this pad represents
                    start_track = self.overview_track_offset + (pad_x * self._zoom_level)
                    start_scene = self.overview_scene_offset + (pad_y * self._zoom_level)

                    # Aggregate state for this pad region
                    pad_color = self._calculate_pad_color(
                        start_track, start_scene,
                        self._zoom_level, self._zoom_level,
                        ring_info
                    )

                    overview_data.extend(pad_color)  # R, G, B

            # Send overview grid (8x4 * 3 bytes RGB = 96 bytes)
            self.c_surface._send_sysex_command(CMD_SESSION_OVERVIEW_GRID, overview_data)

            # Send zoom level and viewport info
            metadata = [
                self._zoom_level,
                self.overview_track_offset & 0x7F,
                self.overview_scene_offset & 0x7F,
                (len(tracks) & 0x7F),  # Total tracks
                (len(scenes) & 0x7F)   # Total scenes
            ]
            self.c_surface._send_sysex_command(CMD_SESSION_OVERVIEW, metadata)

        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending overview: {e}")

    def _calculate_pad_color(self, start_track, start_scene, width, height, ring_info):
        """
        Calculate aggregated color for a pad region
        Returns: (R, G, B) tuple
        """
        try:
            tracks = self.song.tracks
            scenes = self.song.scenes

            # Check if this region overlaps with ring viewport
            is_ring_region = False
            if ring_info:
                ring_track_start = ring_info['track_offset']
                ring_track_end = ring_track_start + ring_info['ring_width']
                ring_scene_start = ring_info['scene_offset']
                ring_scene_end = ring_scene_start + ring_info['ring_height']

                # Check overlap
                track_overlap = (start_track < ring_track_end and
                               start_track + width > ring_track_start)
                scene_overlap = (start_scene < ring_scene_end and
                               start_scene + height > ring_scene_start)
                is_ring_region = track_overlap and scene_overlap

            # Count clips in this region
            total_slots = 0
            has_clip_count = 0
            playing_count = 0
            queued_count = 0
            recording_count = 0

            # Aggregate track colors
            track_colors = []

            for t in range(start_track, min(start_track + width, len(tracks))):
                track = tracks[t]
                track_colors.append(ColorUtils.live_color_to_rgb(track.color))

                for s in range(start_scene, min(start_scene + height, len(scenes))):
                    if s < len(track.clip_slots):
                        clip_slot = track.clip_slots[s]
                        total_slots += 1

                        if clip_slot.has_clip:
                            has_clip_count += 1

                            if clip_slot.is_playing:
                                playing_count += 1
                            elif clip_slot.is_triggered:
                                queued_count += 1
                            elif hasattr(clip_slot, 'is_recording') and clip_slot.is_recording:
                                recording_count += 1

            # Calculate color based on state
            if playing_count > 0:
                # Green for playing (full brightness)
                base_color = (0, 255, 0)
                intensity = min(1.0, playing_count / max(1, total_slots))
            elif recording_count > 0:
                # Red for recording
                base_color = (255, 0, 0)
                intensity = min(1.0, recording_count / max(1, total_slots))
            elif queued_count > 0:
                # Yellow for queued
                base_color = (255, 255, 0)
                intensity = min(1.0, queued_count / max(1, total_slots))
            elif has_clip_count > 0:
                # Use average track color for clips present
                if track_colors:
                    avg_r = sum(c[0] for c in track_colors) // len(track_colors)
                    avg_g = sum(c[1] for c in track_colors) // len(track_colors)
                    avg_b = sum(c[2] for c in track_colors) // len(track_colors)
                    base_color = (avg_r, avg_g, avg_b)
                else:
                    base_color = (64, 64, 64)  # Gray
                intensity = 0.3 + (0.4 * has_clip_count / max(1, total_slots))
            else:
                # Empty - dark
                base_color = (0, 0, 0)
                intensity = 0.0

            # Apply ring indicator (white border/overlay)
            if is_ring_region:
                # Mix with white to indicate ring position
                r = int(base_color[0] * intensity * 0.7 + 255 * 0.3)
                g = int(base_color[1] * intensity * 0.7 + 255 * 0.3)
                b = int(base_color[2] * intensity * 0.7 + 255 * 0.3)
            else:
                r = int(base_color[0] * intensity)
                g = int(base_color[1] * intensity)
                b = int(base_color[2] * intensity)

            # Clamp to 0-127 (MIDI range)
            return (min(127, r // 2), min(127, g // 2), min(127, b // 2))

        except Exception as e:
            self.c_surface.log_message(f"❌ Error calculating pad color: {e}")
            return (0, 0, 0)

    def _update_overview_region(self, track_idx, scene_idx):
        """Update specific region of overview (optimization)"""
        # TODO: Implement partial update for performance
        # For now, just refresh entire overview
        self.send_overview()

    # ========================================
    # NAVIGATION IN OVERVIEW MODE
    # ========================================

    def navigate_overview(self, direction):
        """
        Navigate overview viewport
        Args:
            direction (str): 'left', 'right', 'up', 'down'
        """
        try:
            step_size = self._zoom_level  # Move by zoom amount

            if direction == 'left':
                self.overview_track_offset = max(0, self.overview_track_offset - step_size)
            elif direction == 'right':
                max_offset = max(0, len(self.song.tracks) - (self.display_width * self._zoom_level))
                self.overview_track_offset = min(max_offset, self.overview_track_offset + step_size)
            elif direction == 'up':
                self.overview_scene_offset = max(0, self.overview_scene_offset - step_size)
            elif direction == 'down':
                max_offset = max(0, len(self.song.scenes) - (self.display_height * self._zoom_level))
                self.overview_scene_offset = min(max_offset, self.overview_scene_offset + step_size)

            if self._is_active:
                self.send_overview()

        except Exception as e:
            self.c_surface.log_message(f"❌ Error navigating overview: {e}")

    def jump_to_overview_position(self, pad_x, pad_y):
        """
        Jump ring to position clicked in overview
        Args:
            pad_x, pad_y: Pad coordinates (0-7, 0-3)
        """
        try:
            # Calculate absolute track/scene from pad position
            target_track = self.overview_track_offset + (pad_x * self._zoom_level)
            target_scene = self.overview_scene_offset + (pad_y * self._zoom_level)

            # Update session ring position
            session_ring = self.c_surface.get_manager('session_ring')
            if session_ring:
                # Center ring on clicked position
                ring_info = session_ring.get_ring_info()
                new_track_offset = max(0, target_track - (ring_info['ring_width'] // 2))
                new_scene_offset = max(0, target_scene - (ring_info['ring_height'] // 2))

                # Update ring (this will trigger a re-render)
                session_ring.track_offset = new_track_offset
                session_ring.scene_offset = new_scene_offset
                session_ring._send_ring_position()
                session_ring._send_ring_clips()

                self.c_surface.log_message(f"🎯 Jumped to T{target_track} S{target_scene}")

        except Exception as e:
            self.c_surface.log_message(f"❌ Error jumping to position: {e}")

    # ========================================
    # PUBLIC INTERFACE
    # ========================================

    def get_overview_info(self):
        """Get current overview state"""
        return {
            'is_active': self._is_active,
            'zoom_level': self._zoom_level,
            'track_offset': self.overview_track_offset,
            'scene_offset': self.overview_scene_offset,
            'visible_tracks': self.display_width * self._zoom_level,
            'visible_scenes': self.display_height * self._zoom_level,
            'total_tracks': len(self.song.tracks),
            'total_scenes': len(self.song.scenes)
        }

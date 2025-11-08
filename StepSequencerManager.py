# StepSequencerManager.py - Step Sequencer Management
"""
Manages the step sequencer functionality
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class StepSequencerManager:
    """
    Manages all Step Sequencer level listeners and handlers
    Covers: Note sequencing, resolution, page navigation
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self._is_active = False
        
        self.c_surface.log_message("🔧 Initializing StepSequencerManager...")
        
        # Enhanced step sequencer state
        self._notes = [] # List of notes in the sequence
        self._resolution = 16 # 1/16 notes by default (higher resolution)
        self._page = 0 # Current page of the sequencer
        self._clip = None
        self._listeners = []
        
        # Hold-to-edit functionality
        self._held_step = -1  # Currently held step (-1 = none)
        self._hold_start_time = 0
        self._hold_threshold = 500  # ms to trigger hold mode
        
        # Step editing parameters
        self._editing_velocity = 100
        self._editing_length = 0.25  # Quarter note default
        self._editing_microtiming = 0.0  # No timing offset
        
        # Grid dimensions
        self._steps_per_page = 32  # 4x8 grid
        self._total_steps = 64     # 4 bars at 1/16 resolution
        
        # Playhead chase
        self._last_playhead_position = -1

    def setup_listeners(self):
        if self._is_active:
            return
        
        try:
            self.c_surface.log_message("🎵 Setting up Step Sequencer listeners...")
            
            # Listen to detail clip changes
            detail_clip_listener = lambda: self._on_detail_clip_changed()
            self.song.view.add_detail_clip_listener(detail_clip_listener)
            self._listeners.append(('detail_clip', detail_clip_listener))

            # Listen to song time changes
            song_time_listener = lambda: self._on_song_time_changed()
            self.song.add_current_song_time_listener(song_time_listener)
            self._listeners.append(('current_song_time', song_time_listener))

            self._is_active = True
            self.c_surface.log_message("✅ Step Sequencer listeners setup")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up step sequencer listeners: {e}")

    def cleanup_listeners(self):
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 'detail_clip':
                        self.song.view.remove_detail_clip_listener(listener_func)
                    elif listener_type == 'current_song_time':
                        self.song.remove_current_song_time_listener(listener_func)
                except:
                    pass # Ignore if already removed
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Step Sequencer listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning step sequencer listeners: {e}")

    def _on_detail_clip_changed(self):
        if self.c_surface._is_connected:
            clip = self.song.view.detail_clip
            if clip and clip.is_midi_clip:
                self._clip = clip
                self._update_notes()
                self.send_grid_state()
            else:
                self._clip = None
                self._notes = []
                self.send_grid_state()

    def _on_song_time_changed(self):
        if self.c_surface._is_connected and self._clip:
            self.send_grid_state()

    def _update_notes(self):
        if self._clip:
            self._notes = self._clip.get_notes_extended(0, 0, self._clip.length, 128)
        else:
            self._notes = []

    def send_grid_state(self):
        if not self.c_surface._is_connected:
            return

        grid_data = [0] * 32
        if self._clip:
            # Populate grid with notes
            for note in self._notes:
                # This is a simplified logic, needs to be improved
                # to handle resolution and pages
                if self._page == 0:
                    step = int(note.start_time * self._resolution)
                    if 0 <= step < 32:
                        grid_data[step] = 1

            # Show playhead
            playhead = int(self.song.current_song_time * self._resolution) % 32
            grid_data[playhead] = 2

        message = SysExEncoder.encode_step_sequencer_state(grid_data)
        if message:
            self.c_surface._send_midi(tuple(message))

    def send_complete_state(self):
        self.send_grid_state()

    def handle_step_sequencer_command(self, command, payload):
        if not self._is_active or not self._clip:
            return

        if command == CMD_STEP_SEQUENCER_NOTE:
            if len(payload) >= 2:
                step = payload[0]
                velocity = payload[1]
                self._handle_note_toggle(step, velocity)
        elif command == CMD_STEP_SEQUENCER_RESOLUTION:
            if len(payload) >= 1:
                self._resolution = payload[0]
                self.send_grid_state()
        elif command == CMD_STEP_SEQUENCER_PAGE:
            if len(payload) >= 1:
                self._page = payload[0]
                self.send_grid_state()

    def _handle_note_toggle(self, step, velocity):
        if not self._clip:
            return

        time = float(step) / self._resolution
        pitch = 60 # Default to C4 for now
        duration = 1.0 / self._resolution

        # Check if there is a note at this step
        note_exists = False
        for note in self._notes:
            if abs(note.start_time - time) < 0.01:
                # Note exists, so remove it
                self._clip.remove_notes_extended(time, pitch, 0.1, 1)
                note_exists = True
                break
        
        if not note_exists:
            # Note does not exist, so add it
            new_note = (pitch, time, duration, velocity, False)
            self._clip.set_notes_extended([new_note])

        self._update_notes()
        self.send_grid_state()
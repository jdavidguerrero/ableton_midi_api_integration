# AutomationManager.py - Automation and Control Management
"""
Manages automation recording, control surface integration and advanced features
Based on Live Object Model: Song automation properties, ControlSurface integration
"""

from .consts import *
from .MIDIUtils import SysExEncoder

class AutomationManager:
    """
    Manages all Automation-level listeners and handlers
    Covers: Automation recording, re-enable automation, control surface features
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self.app = control_surface.application()
        self._listeners = []
        self._is_active = False
        
        self.c_surface.log_message("🔧 Initializing AutomationManager...")
        
        # Automation state tracking
        self._automation_recording = False
        
    def setup_listeners(self):
        """Setup automation listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("🤖 Setting up Automation listeners...")
            
            # === AUTOMATION RECORDING ===
            
            # Re-enable automation
            if hasattr(self.song, 'add_re_enable_automation_listener'):
                re_enable_listener = lambda: self._on_re_enable_automation_changed()
                self.song.add_re_enable_automation_listener(re_enable_listener)
                self._listeners.append(('re_enable_automation', re_enable_listener))
            else:
                self.c_surface.log_message("⚠️ re_enable_automation_listener not available in this Live version")
            
            # === ARRANGEMENT/SESSION INTERACTION ===
            
            # Back to arrangement (handled in TransportManager, but we can add specific automation context)
            if hasattr(self.song, 'add_back_to_arrangement_listener'):
                back_to_arrangement_listener = lambda: self._on_back_to_arrangement_changed()
                self.song.add_back_to_arrangement_listener(back_to_arrangement_listener)
                self._listeners.append(('back_to_arrangement', back_to_arrangement_listener))
            else:
                self.c_surface.log_message("⚠️ back_to_arrangement_listener not available in this Live version")
            
            # === CONTROL SURFACE FEATURES ===
            
            # Can undo/redo
            if hasattr(self.song, 'add_can_undo_listener'):
                can_undo_listener = lambda: self._on_can_undo_changed()
                self.song.add_can_undo_listener(can_undo_listener)
                self._listeners.append(('can_undo', can_undo_listener))
            else:
                self.c_surface.log_message("⚠️ can_undo_listener not available in this Live version")
            
            if hasattr(self.song, 'add_can_redo_listener'):
                can_redo_listener = lambda: self._on_can_redo_changed()
                self.song.add_can_redo_listener(can_redo_listener)
                self._listeners.append(('can_redo', can_redo_listener))
            else:
                self.c_surface.log_message("⚠️ can_redo_listener not available in this Live version")
            
            # === CLIP AUTOMATION ===
            
            # Automation arm (if available)
            if hasattr(self.song, 'exclusive_arm'):
                exclusive_arm_listener = lambda: self._on_exclusive_arm_changed()
                self.song.add_exclusive_arm_listener(exclusive_arm_listener)
                self._listeners.append(('exclusive_arm', exclusive_arm_listener))
            
            # === GROOVE AND QUANTIZATION ===
            
            # Clip trigger quantization
            if hasattr(self.song, 'clip_trigger_quantization'):
                clip_quantization_listener = lambda: self._on_clip_trigger_quantization_changed()
                self.song.add_clip_trigger_quantization_listener(clip_quantization_listener)
                self._listeners.append(('clip_trigger_quantization', clip_quantization_listener))
            
            # Global quantization
            if hasattr(self.song, 'midi_recording_quantization'):
                midi_quantization_listener = lambda: self._on_midi_recording_quantization_changed()
                self.song.add_midi_recording_quantization_listener(midi_quantization_listener)
                self._listeners.append(('midi_recording_quantization', midi_quantization_listener))
            
            # === ADVANCED FEATURES ===
            
            # Session automation record
            if hasattr(self.song, 'session_automation_record'):
                session_auto_listener = lambda: self._on_session_automation_record_changed()
                self.song.add_session_automation_record_listener(session_auto_listener)
                self._listeners.append(('session_automation_record', session_auto_listener))
            
            # Capture and insert scene
            if hasattr(self.song, 'can_capture_midi'):
                capture_midi_listener = lambda: self._on_can_capture_midi_changed()
                self.song.add_can_capture_midi_listener(capture_midi_listener)
                self._listeners.append(('can_capture_midi', capture_midi_listener))
            
            self._is_active = True
            self.c_surface.log_message(f"✅ Automation listeners setup ({len(self._listeners)} listeners)")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up automation listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all automation listeners"""
        if not self._is_active:
            return
            
        try:
            for listener_type, listener_func in self._listeners:
                try:
                    if listener_type == 're_enable_automation':
                        self.song.remove_re_enable_automation_listener(listener_func)
                    elif listener_type == 'back_to_arrangement':
                        self.song.remove_back_to_arrangement_listener(listener_func)
                    elif listener_type == 'can_undo':
                        self.song.remove_can_undo_listener(listener_func)
                    elif listener_type == 'can_redo':
                        self.song.remove_can_redo_listener(listener_func)
                    elif listener_type == 'exclusive_arm':
                        self.song.remove_exclusive_arm_listener(listener_func)
                    elif listener_type == 'clip_trigger_quantization':
                        self.song.remove_clip_trigger_quantization_listener(listener_func)
                    elif listener_type == 'midi_recording_quantization':
                        self.song.remove_midi_recording_quantization_listener(listener_func)
                    elif listener_type == 'session_automation_record':
                        self.song.remove_session_automation_record_listener(listener_func)
                    elif listener_type == 'can_capture_midi':
                        self.song.remove_can_capture_midi_listener(listener_func)
                except:
                    pass  # Ignore if already removed
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ Automation listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning automation listeners: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_re_enable_automation_changed(self):
        """Re-enable automation state changed"""
        if self.c_surface._is_connected:
            re_enable = getattr(self.song, 're_enable_automation', False)
            self.c_surface.log_message(f"🔄 Re-enable automation: {re_enable}")
            self._send_re_enable_automation_state(re_enable)
    
    def _on_back_to_arrangement_changed(self):
        """Back to arrangement state changed (automation context)"""
        if self.c_surface._is_connected:
            back_to_arrangement = self.song.back_to_arrangement
            self.c_surface.log_message(f"🔙 Back to arrangement (automation): {back_to_arrangement}")
            self._send_back_to_arrangement_state(back_to_arrangement)
    
    def _on_can_undo_changed(self):
        """Can undo state changed"""
        if self.c_surface._is_connected:
            can_undo = getattr(self.song, 'can_undo', False)
            self.c_surface.log_message(f"↶ Can undo: {can_undo}")
            self._send_undo_redo_state(can_undo, getattr(self.song, 'can_redo', False))
    
    def _on_can_redo_changed(self):
        """Can redo state changed"""
        if self.c_surface._is_connected:
            can_redo = getattr(self.song, 'can_redo', False)
            self.c_surface.log_message(f"↷ Can redo: {can_redo}")
            self._send_undo_redo_state(getattr(self.song, 'can_undo', False), can_redo)
    
    def _on_exclusive_arm_changed(self):
        """Exclusive arm state changed"""
        if self.c_surface._is_connected:
            exclusive_arm = getattr(self.song, 'exclusive_arm', False)
            self.c_surface.log_message(f"🎯 Exclusive arm: {exclusive_arm}")
            self._send_exclusive_arm_state(exclusive_arm)
    
    def _on_clip_trigger_quantization_changed(self):
        """Clip trigger quantization changed"""
        if self.c_surface._is_connected:
            quantization = getattr(self.song, 'clip_trigger_quantization', 0)
            self.c_surface.log_message(f"📏 Clip trigger quantization: {quantization}")
            self._send_clip_quantization_state(quantization)
    
    def _on_midi_recording_quantization_changed(self):
        """MIDI recording quantization changed"""
        if self.c_surface._is_connected:
            quantization = getattr(self.song, 'midi_recording_quantization', 0)
            self.c_surface.log_message(f"🎹 MIDI recording quantization: {quantization}")
            self._send_midi_quantization_state(quantization)
    
    def _on_session_automation_record_changed(self):
        """Session automation record changed"""
        if self.c_surface._is_connected:
            session_auto = getattr(self.song, 'session_automation_record', False)
            self.c_surface.log_message(f"🤖 Session automation record: {session_auto}")
            self._send_session_automation_record_state(session_auto)
    
    def _on_can_capture_midi_changed(self):
        """Can capture MIDI changed"""
        if self.c_surface._is_connected:
            can_capture = getattr(self.song, 'can_capture_midi', False)
            self.c_surface.log_message(f"🎤 Can capture MIDI: {can_capture}")
            self._send_can_capture_midi_state(can_capture)
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_re_enable_automation_state(self, re_enable):
        """Send re-enable automation state to hardware"""
        try:
            payload = [1 if re_enable else 0]
            self.c_surface._send_sysex_command(CMD_RE_ENABLE_AUTOMATION, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending re-enable automation: {e}")
    
    def _send_back_to_arrangement_state(self, back_to_arrangement):
        """Send back to arrangement state to hardware"""
        try:
            payload = [1 if back_to_arrangement else 0]
            self.c_surface._send_sysex_command(CMD_BACK_TO_ARRANGER, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending back to arrangement: {e}")
    
    def _send_undo_redo_state(self, can_undo, can_redo):
        """Send undo/redo state to hardware"""
        try:
            undo_byte = 1 if can_undo else 0
            redo_byte = 1 if can_redo else 0
            payload = [undo_byte, redo_byte]
            # Could add CMD_UNDO_REDO = 0xC3 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending undo/redo state: {e}")
    
    def _send_exclusive_arm_state(self, exclusive_arm):
        """Send exclusive arm state to hardware"""
        try:
            payload = [1 if exclusive_arm else 0]
            # Could add CMD_EXCLUSIVE_ARM = 0xC4 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending exclusive arm: {e}")
    
    def _send_clip_quantization_state(self, quantization):
        """Send clip trigger quantization to hardware"""
        try:
            # Map quantization values to hardware-friendly format
            quant_map = {
                0: 0,   # None
                1: 1,   # 1 Bar
                2: 2,   # 1/2 Note
                3: 3,   # 1/4 Note
                4: 4,   # 1/8 Note
                5: 5,   # 1/16 Note
                6: 6    # 1/32 Note
            }
            quant_value = quant_map.get(quantization, 0)
            
            payload = [quant_value]
            # Could add CMD_CLIP_QUANTIZATION = 0xC5 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending clip quantization: {e}")
    
    def _send_midi_quantization_state(self, quantization):
        """Send MIDI recording quantization to hardware"""
        try:
            # Similar mapping as clip quantization
            quant_map = {
                0: 0,   # None
                1: 1,   # 1 Bar
                2: 2,   # 1/2 Note
                3: 3,   # 1/4 Note
                4: 4,   # 1/8 Note
                5: 5,   # 1/16 Note
                6: 6    # 1/32 Note
            }
            quant_value = quant_map.get(quantization, 0)
            
            payload = [quant_value]
            self.c_surface._send_sysex_command(CMD_TRANSPORT_QUANTIZE, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending MIDI quantization: {e}")
    
    def _send_session_automation_record_state(self, session_auto):
        """Send session automation record state to hardware"""
        try:
            payload = [1 if session_auto else 0]
            self.c_surface._send_sysex_command(CMD_AUTOMATION_RECORD, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending session automation record: {e}")
    
    def _send_can_capture_midi_state(self, can_capture):
        """Send can capture MIDI state to hardware"""
        try:
            payload = [1 if can_capture else 0]
            # Could add CMD_CAN_CAPTURE_MIDI = 0xC6 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending can capture MIDI: {e}")
    
    # ========================================
    # AUTOMATION ACTIONS
    # ========================================
    
    def toggle_automation_record(self):
        """Toggle automation recording (session)"""
        try:
            if hasattr(self.song, 'session_automation_record'):
                current_state = self.song.session_automation_record
                self.song.session_automation_record = not current_state
                new_state = "enabled" if not current_state else "disabled"
                self.c_surface.log_message(f"🤖 Automation record {new_state}")
            else:
                self.c_surface.log_message("❌ Session automation record not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling automation record: {e}")
    
    def trigger_re_enable_automation(self):
        """Trigger re-enable automation"""
        try:
            if hasattr(self.song, 're_enable_automation'):
                self.song.re_enable_automation = True
                self.c_surface.log_message("🔄 Re-enabled automation")
            else:
                self.c_surface.log_message("❌ Re-enable automation not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error re-enabling automation: {e}")
    
    def undo(self):
        """Perform undo"""
        try:
            if hasattr(self.song, 'can_undo') and self.song.can_undo:
                if hasattr(self.song, 'undo'):
                    self.song.undo()
                    self.c_surface.log_message("↶ Undo performed")
                else:
                    self.c_surface.log_message("❌ Undo function not available")
            else:
                self.c_surface.log_message("❌ Cannot undo")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error performing undo: {e}")
    
    def redo(self):
        """Perform redo"""
        try:
            if hasattr(self.song, 'can_redo') and self.song.can_redo:
                if hasattr(self.song, 'redo'):
                    self.song.redo()
                    self.c_surface.log_message("↷ Redo performed")
                else:
                    self.c_surface.log_message("❌ Redo function not available")
            else:
                self.c_surface.log_message("❌ Cannot redo")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error performing redo: {e}")
    
    def capture_and_insert_scene(self):
        """Capture and insert scene"""
        try:
            if hasattr(self.song, 'capture_and_insert_scene'):
                self.song.capture_and_insert_scene()
                self.c_surface.log_message("📸 Captured and inserted scene")
            else:
                self.c_surface.log_message("❌ Capture and insert scene not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error capturing scene: {e}")
    
    def capture_midi(self):
        """Capture MIDI"""
        try:
            if hasattr(self.song, 'can_capture_midi') and self.song.can_capture_midi:
                if hasattr(self.song, 'capture_midi'):
                    self.song.capture_midi()
                    self.c_surface.log_message("🎤 MIDI captured")
                else:
                    self.c_surface.log_message("❌ MIDI capture function not available")
            else:
                self.c_surface.log_message("❌ Cannot capture MIDI")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error capturing MIDI: {e}")
    
    def set_clip_trigger_quantization(self, quantization):
        """Set clip trigger quantization"""
        try:
            if hasattr(self.song, 'clip_trigger_quantization'):
                # quantization: 0=None, 1=1Bar, 2=1/2, 3=1/4, 4=1/8, 5=1/16, 6=1/32
                self.song.clip_trigger_quantization = quantization
                quant_names = ["None", "1 Bar", "1/2", "1/4", "1/8", "1/16", "1/32"]
                quant_name = quant_names[quantization] if quantization < len(quant_names) else f"Value {quantization}"
                self.c_surface.log_message(f"📏 Clip trigger quantization: {quant_name}")
            else:
                self.c_surface.log_message("❌ Clip trigger quantization not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting clip quantization: {e}")
    
    def set_midi_recording_quantization(self, quantization):
        """Set MIDI recording quantization"""
        try:
            if hasattr(self.song, 'midi_recording_quantization'):
                # Similar values as clip trigger quantization
                self.song.midi_recording_quantization = quantization
                quant_names = ["None", "1 Bar", "1/2", "1/4", "1/8", "1/16", "1/32"]
                quant_name = quant_names[quantization] if quantization < len(quant_names) else f"Value {quantization}"
                self.c_surface.log_message(f"🎹 MIDI recording quantization: {quant_name}")
            else:
                self.c_surface.log_message("❌ MIDI recording quantization not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting MIDI quantization: {e}")
    
    def toggle_exclusive_arm(self):
        """Toggle exclusive arm mode"""
        try:
            if hasattr(self.song, 'exclusive_arm'):
                self.song.exclusive_arm = not self.song.exclusive_arm
                state = "enabled" if self.song.exclusive_arm else "disabled"
                self.c_surface.log_message(f"🎯 Exclusive arm {state}")
            else:
                self.c_surface.log_message("❌ Exclusive arm not available")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error toggling exclusive arm: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_automation_info(self):
        """Get complete automation information"""
        try:
            return {
                're_enable_automation': getattr(self.song, 're_enable_automation', False),
                'back_to_arrangement': getattr(self.song, 'back_to_arrangement', False),
                'can_undo': getattr(self.song, 'can_undo', False),
                'can_redo': getattr(self.song, 'can_redo', False),
                'exclusive_arm': getattr(self.song, 'exclusive_arm', False),
                'clip_trigger_quantization': getattr(self.song, 'clip_trigger_quantization', 0),
                'midi_recording_quantization': getattr(self.song, 'midi_recording_quantization', 0),
                'session_automation_record': getattr(self.song, 'session_automation_record', False),
                'can_capture_midi': getattr(self.song, 'can_capture_midi', False),
                'arrangement_overdub': self.song.arrangement_overdub,
                'overdub': self.song.overdub
            }
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting automation info: {e}")
            return {}
    
    def send_complete_state(self):
        """Send complete automation state to hardware"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete automation state...")
            
            # Get current state
            info = self.get_automation_info()
            
            # Send automation states
            self._send_re_enable_automation_state(info['re_enable_automation'])
            self._send_back_to_arrangement_state(info['back_to_arrangement'])
            self._send_undo_redo_state(info['can_undo'], info['can_redo'])
            self._send_exclusive_arm_state(info['exclusive_arm'])
            self._send_clip_quantization_state(info['clip_trigger_quantization'])
            self._send_midi_quantization_state(info['midi_recording_quantization'])
            self._send_session_automation_record_state(info['session_automation_record'])
            self._send_can_capture_midi_state(info['can_capture_midi'])
            
            self.c_surface.log_message("✅ Automation state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending automation state: {e}")
    
    def handle_automation_command(self, command, payload):
        """Handle incoming automation commands from hardware"""
        try:
            if command == CMD_AUTOMATION_RECORD:
                self.toggle_automation_record()
            elif command == CMD_RE_ENABLE_AUTOMATION:
                self.trigger_re_enable_automation()
            elif command == CMD_BACK_TO_ARRANGER:
                # This might be handled by TransportManager, but we can also handle it here
                self.song.back_to_arrangement = True
            elif command == CMD_TRANSPORT_QUANTIZE and len(payload) >= 1:
                quantization = payload[0]
                self.set_midi_recording_quantization(quantization)
            else:
                self.c_surface.log_message(f"❓ Unknown automation command: 0x{command:02X}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling automation command 0x{command:02X}: {e}")
    
    # ========================================
    # ADVANCED AUTOMATION FEATURES
    # ========================================
    
    def start_automation_recording(self, track_idx=None, param_idx=None):
        """Start automation recording for specific parameter"""
        try:
            # This would require more specific implementation based on 
            # how you want to handle parameter automation
            self._automation_recording = True
            self.c_surface.log_message("🔴 Started automation recording")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error starting automation recording: {e}")
    
    def stop_automation_recording(self):
        """Stop automation recording"""
        try:
            self._automation_recording = False
            self.c_surface.log_message("⏹️ Stopped automation recording")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error stopping automation recording: {e}")
    
    def clear_automation(self, track_idx, param_idx):
        """Clear automation for specific parameter"""
        try:
            # Implementation would depend on how parameters are tracked
            # This is a placeholder for clearing parameter automation
            self.c_surface.log_message(f"🧹 Cleared automation for T{track_idx}P{param_idx}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error clearing automation T{track_idx}P{param_idx}: {e}")
    
    def quantize_automation(self, track_idx, param_idx, quantization):
        """Quantize automation for specific parameter"""
        try:
            # Implementation would depend on parameter tracking
            quant_names = ["None", "1 Bar", "1/2", "1/4", "1/8", "1/16", "1/32"]
            quant_name = quant_names[quantization] if quantization < len(quant_names) else f"Value {quantization}"
            self.c_surface.log_message(f"📏 Quantized automation T{track_idx}P{param_idx} to {quant_name}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error quantizing automation T{track_idx}P{param_idx}: {e}")
    
    def get_automation_recording_state(self):
        """Get current automation recording state"""
        return {
            'is_recording': self._automation_recording,
            'session_automation_record': getattr(self.song, 'session_automation_record', False),
            'arrangement_overdub': self.song.arrangement_overdub
        }

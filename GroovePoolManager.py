# GroovePoolManager.py - Groove Pool Management
"""
Manages GroovePool functionality from Live Object Model
Based on Live Object Model: Song.groove_pool properties and methods
"""

from .consts import *
from .MIDIUtils import SysExEncoder

class GroovePoolManager:
    """
    Manages all GroovePool-level listeners and handlers
    Covers: Groove templates, groove amount, timing, randomization
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self._listeners = []
        self._is_active = False
        
        self.c_surface.log_message("🔧 Initializing GroovePoolManager...")
        
        # Groove pool state tracking
        self._groove_templates = {}
        self._selected_groove_idx = -1
        
    def setup_listeners(self):
        """Setup groove pool listeners"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message("🎵 Setting up GroovePool listeners...")
            
            # === GROOVE POOL LISTENERS ===
            
            # Check if groove_pool exists (Live 9.0+)
            if hasattr(self.song, 'groove_pool') and self.song.groove_pool:
                groove_pool = self.song.groove_pool
                
                # Groove templates listener (if available)
                if hasattr(groove_pool, 'grooves'):
                    grooves_listener = lambda: self._on_grooves_changed()
                    try:
                        # Note: groove_pool listeners may not exist in all versions
                        if hasattr(groove_pool, 'add_grooves_listener'):
                            groove_pool.add_grooves_listener(grooves_listener)
                            self._listeners.append(('grooves', grooves_listener))
                        else:
                            self.c_surface.log_message("ℹ️ GroovePool listeners not available - using periodic updates")
                    except Exception as e:
                        self.c_surface.log_message(f"⚠️ Cannot add groove pool listeners: {e}")
                
                # Track groove templates
                self._track_groove_templates()
                
            else:
                self.c_surface.log_message("ℹ️ GroovePool not available in this Live version")
            
            self._is_active = True
            self.c_surface.log_message(f"✅ GroovePool listeners setup ({len(self._listeners)} listeners)")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up groove pool listeners: {e}")
    
    def cleanup_listeners(self):
        """Remove all groove pool listeners"""
        if not self._is_active:
            return
            
        try:
            groove_pool = getattr(self.song, 'groove_pool', None)
            if groove_pool:
                for listener_type, listener_func in self._listeners:
                    try:
                        if listener_type == 'grooves':
                            if hasattr(groove_pool, 'remove_grooves_listener'):
                                groove_pool.remove_grooves_listener(listener_func)
                    except:
                        pass  # Ignore if already removed
            
            self._listeners = []
            self._is_active = False
            self.c_surface.log_message("✅ GroovePool listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning groove pool listeners: {e}")
    
    def _track_groove_templates(self):
        """Track available groove templates"""
        try:
            if hasattr(self.song, 'groove_pool') and self.song.groove_pool:
                groove_pool = self.song.groove_pool
                if hasattr(groove_pool, 'grooves'):
                    self._groove_templates = {}
                    for idx, groove in enumerate(groove_pool.grooves):
                        if groove and hasattr(groove, 'name'):
                            self._groove_templates[idx] = {
                                'name': groove.name,
                                'timing': getattr(groove, 'timing_amount', 0.0),
                                'random': getattr(groove, 'random_amount', 0.0),
                                'velocity': getattr(groove, 'velocity_amount', 0.0)
                            }
                    
                    self.c_surface.log_message(f"🎵 Found {len(self._groove_templates)} groove templates")
        except Exception as e:
            self.c_surface.log_message(f"❌ Error tracking groove templates: {e}")
    
    # ========================================
    # EVENT HANDLERS
    # ========================================
    
    def _on_grooves_changed(self):
        """Groove templates changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message("🎵 Groove templates changed")
            self._track_groove_templates()
            self._send_groove_templates_list()
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_groove_templates_list(self):
        """Send groove templates list to hardware"""
        try:
            templates_data = []
            for idx, template_info in self._groove_templates.items():
                name_bytes = template_info['name'].encode('utf-8')[:8]
                template_data = [idx, len(name_bytes)] + list(name_bytes)
                templates_data.extend(template_data)
            
            # Limit to reasonable size
            if len(templates_data) <= 100:
                payload = [len(self._groove_templates)] + templates_data
                self.c_surface._send_sysex_command(CMD_GROOVE_POOL, payload)
            else:
                self.c_surface.log_message("⚠️ Too many groove templates to send")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending groove templates: {e}")
    
    def _send_groove_amount(self, track_idx, groove_amount):
        """Send groove amount for track to hardware"""
        try:
            amount_127 = int(groove_amount * 127)
            payload = [track_idx, amount_127]
            # Could add CMD_GROOVE_AMOUNT = 0xD1 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending groove amount: {e}")
    
    def _send_selected_groove_template(self, track_idx, groove_idx):
        """Send selected groove template for track"""
        try:
            payload = [track_idx, groove_idx if groove_idx >= 0 else 127]
            # Could add CMD_GROOVE_TEMPLATE = 0xD2 to consts.py
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending groove template: {e}")
    
    # ========================================
    # GROOVE ACTIONS
    # ========================================
    
    def set_track_groove_amount(self, track_idx, groove_amount):
        """Set groove amount for track"""
        try:
            if hasattr(self.c_surface, '_get_track_safe'):
                track = self.c_surface._get_track_safe(track_idx)
            else:
                # Fallback for older implementations
                if track_idx < len(self.song.tracks):
                    track = self.song.tracks[track_idx]
                else:
                    track = None
                    
            if track and hasattr(track, 'groove_amount'):
                track.groove_amount = max(0.0, min(1.0, groove_amount))
                self.c_surface.log_message(f"🎵 Track {track_idx} groove amount: {groove_amount:.2f}")
                self._send_groove_amount(track_idx, groove_amount)
            elif track:
                self.c_surface.log_message(f"ℹ️ Track {track_idx} doesn't support groove amount")
            else:
                self.c_surface.log_message(f"❌ Invalid track index: {track_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting groove amount T{track_idx}: {e}")
    
    def set_track_groove_template(self, track_idx, groove_idx):
        """Set groove template for track"""
        try:
            if hasattr(self.c_surface, '_get_track_safe'):
                track = self.c_surface._get_track_safe(track_idx)
            else:
                # Fallback for older implementations
                if track_idx < len(self.song.tracks):
                    track = self.song.tracks[track_idx]
                else:
                    track = None
                    
            if track and hasattr(self.song, 'groove_pool') and self.song.groove_pool:
                groove_pool = self.song.groove_pool
                if (hasattr(groove_pool, 'grooves') and 
                    groove_idx < len(groove_pool.grooves) and 
                    hasattr(track, 'groove')):
                    
                    if groove_idx >= 0:
                        track.groove = groove_pool.grooves[groove_idx]
                        template_name = self._groove_templates.get(groove_idx, {}).get('name', f'Template {groove_idx}')
                        self.c_surface.log_message(f"🎵 Track {track_idx} groove: {template_name}")
                    else:
                        track.groove = None
                        self.c_surface.log_message(f"🎵 Track {track_idx} groove cleared")
                    
                    self._send_selected_groove_template(track_idx, groove_idx)
                    
                elif track:
                    self.c_surface.log_message(f"❌ Invalid groove template index: {groove_idx}")
            else:
                self.c_surface.log_message(f"❌ Invalid track or groove pool not available: {track_idx}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting groove template T{track_idx}: {e}")
    
    def clear_track_groove(self, track_idx):
        """Clear groove from track"""
        self.set_track_groove_template(track_idx, -1)
    
    def get_track_groove_info(self, track_idx):
        """Get groove information for track"""
        try:
            if hasattr(self.c_surface, '_get_track_safe'):
                track = self.c_surface._get_track_safe(track_idx)
            else:
                if track_idx < len(self.song.tracks):
                    track = self.song.tracks[track_idx]
                else:
                    track = None
                    
            if track:
                groove_amount = getattr(track, 'groove_amount', 0.0)
                groove_template = getattr(track, 'groove', None)
                
                groove_idx = -1
                groove_name = "None"
                
                if groove_template and hasattr(self.song, 'groove_pool'):
                    groove_pool = self.song.groove_pool
                    if hasattr(groove_pool, 'grooves'):
                        try:
                            groove_idx = list(groove_pool.grooves).index(groove_template)
                            groove_name = getattr(groove_template, 'name', f'Template {groove_idx}')
                        except ValueError:
                            pass
                
                return {
                    'groove_amount': groove_amount,
                    'groove_template_idx': groove_idx,
                    'groove_template_name': groove_name,
                    'has_groove_support': hasattr(track, 'groove_amount')
                }
            
            return None
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting groove info T{track_idx}: {e}")
            return None
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_groove_pool_info(self):
        """Get complete groove pool information"""
        try:
            if not hasattr(self.song, 'groove_pool') or not self.song.groove_pool:
                return {'available': False, 'templates': []}
            
            groove_pool = self.song.groove_pool
            templates = []
            
            if hasattr(groove_pool, 'grooves'):
                for idx, groove in enumerate(groove_pool.grooves):
                    if groove:
                        templates.append({
                            'index': idx,
                            'name': getattr(groove, 'name', f'Template {idx}'),
                            'timing_amount': getattr(groove, 'timing_amount', 0.0),
                            'random_amount': getattr(groove, 'random_amount', 0.0),
                            'velocity_amount': getattr(groove, 'velocity_amount', 0.0)
                        })
            
            return {
                'available': True,
                'templates': templates,
                'total_templates': len(templates)
            }
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting groove pool info: {e}")
            return {'available': False, 'templates': []}
    
    def send_complete_state(self):
        """Send complete groove pool state to hardware"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete groove pool state...")
            
            # Send groove templates list
            self._send_groove_templates_list()
            
            # Send groove settings for all tracks
            for track_idx in range(len(self.song.tracks)):
                groove_info = self.get_track_groove_info(track_idx)
                if groove_info and groove_info['has_groove_support']:
                    self._send_groove_amount(track_idx, groove_info['groove_amount'])
                    self._send_selected_groove_template(track_idx, groove_info['groove_template_idx'])
            
            self.c_surface.log_message("✅ Groove pool state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending groove pool state: {e}")
    
    def handle_groove_command(self, command, payload):
        """Handle incoming groove commands from hardware"""
        try:
            if command == CMD_GROOVE_POOL and len(payload) >= 2:
                track_idx = payload[0]
                groove_idx = payload[1] if payload[1] != 127 else -1
                self.set_track_groove_template(track_idx, groove_idx)
                
            # Add more groove commands as needed
            # elif command == CMD_GROOVE_AMOUNT and len(payload) >= 2:
            #     track_idx = payload[0]
            #     groove_amount = payload[1] / 127.0
            #     self.set_track_groove_amount(track_idx, groove_amount)
                
            else:
                self.c_surface.log_message(f"❓ Unknown groove command: 0x{command:02X}")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling groove command 0x{command:02X}: {e}")
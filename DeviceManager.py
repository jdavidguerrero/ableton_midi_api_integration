# DeviceManager.py - Device and Parameter Management
"""
Manages Device-level properties and parameter functionality
Based on Live Object Model: Device, DeviceParameter, RackDevice, DrumPad
"""

from .consts import *
from .MIDIUtils import SysExEncoder, ColorUtils

class DeviceManager:
    """
    Manages all Device-level listeners and handlers
    Covers: Device properties, parameters, racks, drum pads
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        self.song = control_surface.song()
        self._device_listeners = {}  # (track_idx, device_idx): [listeners]
        self._param_listeners = {}   # (track_idx, device_idx, param_idx): [listeners]
        self._drum_listeners = {}    # (track_idx, device_idx): [drum_listeners]
        self._is_active = False
        
        # Device view state with enhanced parameter paging
        self._current_track = 0
        self._current_device = 0
        self._current_param_page = 0
        self._params_per_page = 8
        
        # Soft takeover for encoders
        self._encoder_values = {}  # (track, device, param): last_hardware_value
        self._takeover_threshold = 5  # MIDI units for smooth takeover
        self._takeover_active = {}   # (track, device, param): is_taken_over
        
    def setup_listeners(self, max_tracks=8, max_devices_per_track=8):
        """Setup device listeners with enhanced parameter paging support"""
        if self._is_active:
            return
            
        try:
            self.c_surface.log_message(f"🎛️ Setting up Device listeners for {max_tracks} tracks...")
            
            for track_idx in range(min(max_tracks, len(self.song.tracks))):
                self._setup_track_device_listeners(track_idx, max_devices_per_track)
            
            self._is_active = True
            self.c_surface.log_message(f"✅ Device listeners setup for {len(self._device_listeners)} devices")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up device listeners: {e}")
    
    def _setup_track_device_listeners(self, track_idx, max_devices):
        """Setup device listeners for all devices in a track"""
        try:
            if track_idx >= len(self.song.tracks):
                return
                
            track = self.song.tracks[track_idx]
            devices = list(track.devices)  # Convert to list for indexing
            
            for device_idx in range(min(max_devices, len(devices))):
                self._setup_single_device_listeners(track_idx, device_idx)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up track {track_idx} device listeners: {e}")
    
    def _setup_single_device_listeners(self, track_idx, device_idx):
        """Setup listeners for a single device"""
        device_key = (track_idx, device_idx)
        if device_key in self._device_listeners:
            return  # Already setup
            
        try:
            if track_idx >= len(self.song.tracks):
                return
                
            track = self.song.tracks[track_idx]
            devices = list(track.devices)
            
            if device_idx >= len(devices):
                return
                
            device = devices[device_idx]
            listeners = []
            
            # === BASIC DEVICE PROPERTIES ===
            
            # Device name
            name_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_device_name_changed(t_idx, d_idx)
            device.add_name_listener(name_listener)
            listeners.append(('name', name_listener))
            
            # Device enabled state (compatibility check)
            if hasattr(device, 'add_is_active_listener'):
                is_active_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_device_enabled_changed(t_idx, d_idx)
                device.add_is_active_listener(is_active_listener)
                listeners.append(('is_active', is_active_listener))
            else:
                self.c_surface.log_message(f"⚠️ Device T{track_idx}D{device_idx} ({device.__class__.__name__}) doesn't support is_enabled listener")
            
            # === DEVICE PARAMETERS ===
            self._setup_device_parameter_listeners(track_idx, device_idx, device, listeners)
            
            # === RACK DEVICE SPECIFIC ===
            if hasattr(device, 'can_have_chains') and device.can_have_chains:
                self._setup_rack_device_listeners(track_idx, device_idx, device, listeners)
            
            # === DRUM RACK SPECIFIC ===
            if hasattr(device, 'can_have_drum_pads') and device.can_have_drum_pads:
                self._setup_drum_rack_listeners(track_idx, device_idx, device)
            
            # === DEVICE TYPE SPECIFIC ===
            self._setup_device_type_listeners(track_idx, device_idx, device, listeners)
            
            # Store all listeners for this device
            self._device_listeners[device_key] = listeners
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up device T{track_idx}D{device_idx} listeners: {e}")
    
    def _setup_device_parameter_listeners(self, track_idx, device_idx, device, listeners):
        """Setup parameter listeners for a device"""
        try:
            # Parameters (with validation)
            device_class = device.__class__.__name__
            param_count = 0
            
            for param_idx, param in enumerate(device.parameters[:8]):  # First 8 params
                try:
                    # Check if parameter is valid and has listener support
                    if hasattr(param, 'add_value_listener') and hasattr(param, 'value'):
                        param_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=param_idx: self._on_parameter_value_changed(t_idx, d_idx, p_idx)
                        param.add_value_listener(param_listener)
                        listeners.append((f'param_{param_idx}', param_listener))
                        
                        # Store in param listeners registry
                        param_key = (track_idx, device_idx, param_idx)
                        self._param_listeners[param_key] = [('value', param_listener)]
                        param_count += 1
                    else:
                        self.c_surface.log_message(f"⚠️ Parameter T{track_idx}D{device_idx}P{param_idx} ({param.name if hasattr(param, 'name') else 'Unknown'}) doesn't support listeners")
                except Exception as param_error:
                    self.c_surface.log_message(f"⚠️ Error setting up parameter T{track_idx}D{device_idx}P{param_idx}: {param_error}")
            
            self.c_surface.log_message(f"✅ Setup {param_count}/8 parameters for {device_class} T{track_idx}D{device_idx}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up parameter listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_rack_device_listeners(self, track_idx, device_idx, device, listeners):
        """Setup listeners for RackDevice with comprehensive Chain class support"""
        try:
            if DEBUG_ENABLED:
                self.c_surface.log_message(f"🔗 Setting up RackDevice listeners T{track_idx}D{device_idx}")
            
            # Chain selection listener
            if hasattr(device, 'view') and hasattr(device.view, 'selected_chain'):
                chain_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_selected_chain_changed(t_idx, d_idx)
                device.view.add_selected_chain_listener(chain_listener)
                listeners.append(('selected_chain', chain_listener))
            
            # Chains list listener
            if hasattr(device, 'chains'):
                chains_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_chains_changed(t_idx, d_idx)
                device.add_chains_listener(chains_listener)
                listeners.append(('chains', chains_listener))
                
                # Individual chain listeners (enhanced Chain class integration)
                for chain_idx, chain in enumerate(device.chains[:8]):  # Support up to 8 chains
                    if chain:
                        self._setup_single_chain_listeners(track_idx, device_idx, chain_idx, chain, listeners)
            
            # Rack macro controls (RackDevice macros property)
            if hasattr(device, 'macros'):
                for macro_idx, macro in enumerate(device.macros[:8]):
                    if macro and hasattr(macro, 'value'):
                        macro_listener = lambda t_idx=track_idx, d_idx=device_idx, m_idx=macro_idx: self._on_rack_macro_changed(t_idx, d_idx, m_idx)
                        macro.add_value_listener(macro_listener)
                        listeners.append((f'macro_{macro_idx}', macro_listener))
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up rack listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_single_chain_listeners(self, track_idx, device_idx, chain_idx, chain, listeners):
        """Setup listeners for a single Chain class instance"""
        try:
            # Chain name listener
            if hasattr(chain, 'name'):
                chain_name_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_name_changed(t_idx, d_idx, c_idx)
                chain.add_name_listener(chain_name_listener)
                listeners.append((f'chain_{chain_idx}_name', chain_name_listener))
            
            # Chain color listener
            if hasattr(chain, 'color'):
                chain_color_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_color_changed(t_idx, d_idx, c_idx)
                chain.add_color_listener(chain_color_listener)
                listeners.append((f'chain_{chain_idx}_color', chain_color_listener))
            
            # Chain mute/solo listeners
            if hasattr(chain, 'mute'):
                chain_mute_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_mute_changed(t_idx, d_idx, c_idx)
                chain.add_mute_listener(chain_mute_listener)
                listeners.append((f'chain_{chain_idx}_mute', chain_mute_listener))
            
            if hasattr(chain, 'solo'):
                chain_solo_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_solo_changed(t_idx, d_idx, c_idx)
                chain.add_solo_listener(chain_solo_listener)
                listeners.append((f'chain_{chain_idx}_solo', chain_solo_listener))
            
            # Chain devices listener (Chain.devices property)
            if hasattr(chain, 'devices'):
                chain_devices_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_devices_changed(t_idx, d_idx, c_idx)
                chain.add_devices_listener(chain_devices_listener)
                listeners.append((f'chain_{chain_idx}_devices', chain_devices_listener))
            
            # Chain mixer device (Chain.mixer_device property)
            if hasattr(chain, 'mixer_device') and chain.mixer_device:
                self._setup_chain_mixer_listeners(track_idx, device_idx, chain_idx, chain.mixer_device, listeners)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up chain {chain_idx} listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_chain_mixer_listeners(self, track_idx, device_idx, chain_idx, mixer_device, listeners):
        """Setup listeners for Chain mixer device (ChainMixerDevice)"""
        try:
            # Chain volume
            if hasattr(mixer_device, 'volume') and hasattr(mixer_device.volume, 'value'):
                volume_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_volume_changed(t_idx, d_idx, c_idx)
                mixer_device.volume.add_value_listener(volume_listener)
                listeners.append((f'chain_{chain_idx}_volume', volume_listener))
            
            # Chain pan
            if hasattr(mixer_device, 'panning') and hasattr(mixer_device.panning, 'value'):
                pan_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_pan_changed(t_idx, d_idx, c_idx)
                mixer_device.panning.add_value_listener(pan_listener)
                listeners.append((f'chain_{chain_idx}_pan', pan_listener))
            
            # Chain sends
            if hasattr(mixer_device, 'sends'):
                for send_idx, send in enumerate(mixer_device.sends[:4]):
                    if send and hasattr(send, 'value'):
                        send_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx, s_idx=send_idx: self._on_chain_send_changed(t_idx, d_idx, c_idx, s_idx)
                        send.add_value_listener(send_listener)
                        listeners.append((f'chain_{chain_idx}_send_{send_idx}', send_listener))
            
            # Chain crossfade assignment
            if hasattr(mixer_device, 'crossfade_assign'):
                crossfade_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_crossfade_changed(t_idx, d_idx, c_idx)
                mixer_device.add_crossfade_assign_listener(crossfade_listener)
                listeners.append((f'chain_{chain_idx}_crossfade', crossfade_listener))
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up chain mixer listeners T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _setup_drum_rack_listeners(self, track_idx, device_idx, drum_rack):
        """Setup listeners for drum rack specific functionality"""
        try:
            drum_listeners = []
            
            # Drum pads (typically 0-127, but we'll focus on first 16)
            if hasattr(drum_rack, 'drum_pads'):
                for pad_idx in range(16):  # C-1 to D#0 (36-51)
                    pad_note = pad_idx + 36  # MIDI note number
                    
                    if pad_note < len(drum_rack.drum_pads):
                        drum_pad = drum_rack.drum_pads[pad_note]
                        
                        if drum_pad:  # Pad exists
                            # Pad name
                            if hasattr(drum_pad, 'name'):
                                pad_name_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=pad_idx: self._on_drum_pad_name_changed(t_idx, d_idx, p_idx)
                                drum_pad.add_name_listener(pad_name_listener)
                                drum_listeners.append((f'pad_{pad_idx}_name', pad_name_listener))
                            
                            # Pad mute state (Live Object Model DrumPad.mute)
                            if hasattr(drum_pad, 'mute'):
                                pad_mute_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=pad_idx: self._on_drum_pad_mute_changed(t_idx, d_idx, p_idx)
                                drum_pad.add_mute_listener(pad_mute_listener)
                                drum_listeners.append((f'pad_{pad_idx}_mute', pad_mute_listener))
                            
                            # Pad solo state (Live Object Model DrumPad.solo)
                            if hasattr(drum_pad, 'solo'):
                                pad_solo_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=pad_idx: self._on_drum_pad_solo_changed(t_idx, d_idx, p_idx)
                                drum_pad.add_solo_listener(pad_solo_listener)
                                drum_listeners.append((f'pad_{pad_idx}_solo', pad_solo_listener))
                            
                            # Pad chains (if has chains)
                            if hasattr(drum_pad, 'chains') and drum_pad.chains:
                                pad_chains_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=pad_idx: self._on_drum_pad_chains_changed(t_idx, d_idx, p_idx)
                                drum_pad.add_chains_listener(pad_chains_listener)
                                drum_listeners.append((f'pad_{pad_idx}_chains', pad_chains_listener))
                            
                            # Pad canonical parent (for accessing nested devices/samples)
                            if hasattr(drum_pad, 'canonical_parent'):
                                try:
                                    parent = drum_pad.canonical_parent
                                    if hasattr(parent, 'sample') and parent.sample:
                                        # Sample properties (file path, etc.)
                                        sample = parent.sample
                                        if hasattr(sample, 'add_file_path_listener'):
                                            sample_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=pad_idx: self._on_drum_pad_sample_changed(t_idx, d_idx, p_idx)
                                            sample.add_file_path_listener(sample_listener)
                                            drum_listeners.append((f'pad_{pad_idx}_sample', sample_listener))
                                except Exception:
                                    pass  # Some pads may not have samples
            
            # Selected drum pad
            if hasattr(drum_rack, 'view') and hasattr(drum_rack.view, 'selected_drum_pad'):
                selected_pad_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_selected_drum_pad_changed(t_idx, d_idx)
                drum_rack.view.add_selected_drum_pad_listener(selected_pad_listener)
                drum_listeners.append(('selected_drum_pad', selected_pad_listener))
            
            # Store drum listeners
            drum_key = (track_idx, device_idx)
            self._drum_listeners[drum_key] = drum_listeners
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up drum rack listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_device_type_listeners(self, track_idx, device_idx, device, listeners):
        """Setup listeners for specific device types"""
        try:
            device_class = device.__class__.__name__
            device_type = getattr(device, 'type', 'unknown')
            
            self.c_surface.log_message(f"🔌 Device T{track_idx}D{device_idx} class: {device_class}, type: {device_type}")
            
            # Plugin Device (VST, AU, VST3)
            if device_class == 'PluginDevice' or 'plugin' in device_class.lower():
                self._setup_plugin_device_listeners(track_idx, device_idx, device, listeners)
            
            # Simpler device
            elif hasattr(device, 'sample') and device_class == 'SimplerDevice':
                self._setup_simpler_listeners(track_idx, device_idx, device, listeners)
            
            # Wavetable device
            elif device_class == 'WavetableDevice':
                self._setup_wavetable_listeners(track_idx, device_idx, device, listeners)
            
            # EQ Eight
            elif device_class == 'Eq8Device':
                self._setup_eq8_listeners(track_idx, device_idx, device, listeners)
            
            # Operator
            elif device_class == 'OperatorDevice':
                self._setup_operator_listeners(track_idx, device_idx, device, listeners)
            
            # Compressor
            elif device_class == 'Compressor2Device':
                self._setup_compressor_listeners(track_idx, device_idx, device, listeners)
            
            # Compressor
            elif device_class == 'CompressorDevice':
                self._setup_compressor_listeners(track_idx, device_idx, device, listeners)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up device type listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_plugin_device_listeners(self, track_idx, device_idx, device, listeners):
        """Setup PluginDevice-specific listeners (VST/AU/VST3)"""
        try:
            self.c_surface.log_message(f"🔌 Setting up PluginDevice listeners T{track_idx}D{device_idx}")
            
            # Plugin preset changes
            if hasattr(device, 'selected_preset_index'):
                preset_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_plugin_preset_changed(t_idx, d_idx)
                try:
                    if hasattr(device, 'add_preset_listener'):
                        device.add_preset_listener(preset_listener)
                        listeners.append(('plugin_preset', preset_listener))
                except AttributeError:
                    self.c_surface.log_message(f"ℹ️ Plugin preset listener not available for T{track_idx}D{device_idx}")
            
            # Plugin program/bank changes
            if hasattr(device, 'selected_program_name'):
                program_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_plugin_program_changed(t_idx, d_idx)
                try:
                    if hasattr(device, 'add_program_listener'):
                        device.add_program_listener(program_listener)
                        listeners.append(('plugin_program', program_listener))
                except AttributeError:
                    self.c_surface.log_message(f"ℹ️ Plugin program listener not available for T{track_idx}D{device_idx}")
            
            # Plugin latency reporting
            if hasattr(device, 'latency_in_ms'):
                latency_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_plugin_latency_changed(t_idx, d_idx)
                try:
                    if hasattr(device, 'add_latency_listener'):
                        device.add_latency_listener(latency_listener)
                        listeners.append(('plugin_latency', latency_listener))
                except AttributeError:
                    pass  # Latency listeners are optional
            
            # Plugin window state (if available)
            if hasattr(device, 'is_showing_plugin_ui'):
                ui_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_plugin_ui_changed(t_idx, d_idx)
                try:
                    if hasattr(device, 'add_ui_listener'):
                        device.add_ui_listener(ui_listener)
                        listeners.append(('plugin_ui', ui_listener))
                except AttributeError:
                    pass  # UI listeners are optional
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up PluginDevice listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_operator_listeners(self, track_idx, device_idx, device, listeners):
        """Setup Operator-specific listeners"""
        try:
            self.c_surface.log_message(f"🎡 Setting up Operator listeners T{track_idx}D{device_idx}")
            # Operator has 4 operators (A, B, C, D) with complex FM synthesis
            # Could add specific operator parameter listeners here
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up Operator listeners: {e}")
    
    def _setup_compressor_listeners(self, track_idx, device_idx, device, listeners):
        """Setup Compressor-specific listeners"""
        try:
            self.c_surface.log_message(f"🎧 Setting up Compressor listeners T{track_idx}D{device_idx}")
            # Compressor2 specific parameters can be monitored
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up Compressor listeners: {e}")
    
    def _setup_simpler_listeners(self, track_idx, device_idx, device, listeners):
        """Setup Simpler device specific listeners"""
        try:
            if hasattr(device, 'sample') and device.sample:
                sample = device.sample
                
                # Sample name
                if hasattr(sample, 'name'):
                    sample_name_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_simpler_sample_name_changed(t_idx, d_idx)
                    sample.add_name_listener(sample_name_listener)
                    listeners.append(('sample_name', sample_name_listener))
                
                # Sample length
                if hasattr(sample, 'length'):
                    sample_length_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_simpler_sample_length_changed(t_idx, d_idx)
                    # Note: length property exists but add_length_listener does not exist in Live API
                    # Length changes can be tracked through other device parameter listeners
                    listeners.append(('sample_length', sample_length_listener))
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up Simpler listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_wavetable_listeners(self, track_idx, device_idx, device, listeners):
        """Setup Wavetable device specific listeners"""
        try:
            # Wavetable specific parameters would go here
            # This is a placeholder for wavetable-specific functionality
            pass
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up Wavetable listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_eq8_listeners(self, track_idx, device_idx, device, listeners):
        """Setup EQ Eight device specific listeners"""
        try:
            # EQ bands
            if hasattr(device, 'bands'):
                for band_idx, band in enumerate(device.bands[:8]):  # 8 bands
                    if hasattr(band, 'gain'):
                        band_gain_listener = lambda t_idx=track_idx, d_idx=device_idx, b_idx=band_idx: self._on_eq_band_gain_changed(t_idx, d_idx, b_idx)
                        band.gain.add_value_listener(band_gain_listener)
                        listeners.append((f'band_{band_idx}_gain', band_gain_listener))
                    
                    if hasattr(band, 'frequency'):
                        band_freq_listener = lambda t_idx=track_idx, d_idx=device_idx, b_idx=band_idx: self._on_eq_band_freq_changed(t_idx, d_idx, b_idx)
                        band.frequency.add_value_listener(band_freq_listener)
                        listeners.append((f'band_{band_idx}_freq', band_freq_listener))
                        
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up EQ8 listeners T{track_idx}D{device_idx}: {e}")
    
    def _setup_compressor_listeners(self, track_idx, device_idx, device, listeners):
        """Setup Compressor device specific listeners"""
        try:
            # Compressor specific parameters would go here
            pass
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up Compressor listeners T{track_idx}D{device_idx}: {e}")
    
    def cleanup_listeners(self):
        """Remove all device listeners"""
        if not self._is_active:
            return
            
        try:
            # Clean up device listeners
            for (track_idx, device_idx), listeners in self._device_listeners.items():
                self._cleanup_device_listeners(track_idx, device_idx, listeners)
            
            # Clean up parameter listeners
            for (track_idx, device_idx, param_idx), listeners in self._param_listeners.items():
                self._cleanup_parameter_listeners(track_idx, device_idx, param_idx, listeners)
            
            # Clean up drum listeners
            for (track_idx, device_idx), listeners in self._drum_listeners.items():
                self._cleanup_drum_listeners(track_idx, device_idx, listeners)
            
            self._device_listeners = {}
            self._param_listeners = {}
            self._drum_listeners = {}
            self._is_active = False
            self.c_surface.log_message("✅ Device listeners cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning device listeners: {e}")
    
    def _cleanup_device_listeners(self, track_idx, device_idx, listeners):
        """Clean up listeners for a specific device"""
        try:
            if track_idx >= len(self.song.tracks):
                return
                
            track = self.song.tracks[track_idx]
            devices = list(track.devices)
            
            if device_idx >= len(devices):
                return
                
            device = devices[device_idx]
            
            for listener_type, listener_func in listeners:
                try:
                    if listener_type == 'name':
                        device.remove_name_listener(listener_func)
                    elif listener_type == 'is_active':
                        if hasattr(device, 'remove_is_active_listener'):
                            device.remove_is_active_listener(listener_func)
                    elif listener_type.startswith('param_'):
                        param_idx = int(listener_type.split('_')[1])
                        if param_idx < len(device.parameters):
                            device.parameters[param_idx].remove_value_listener(listener_func)
                    elif listener_type == 'selected_chain':
                        device.view.remove_selected_chain_listener(listener_func)
                    elif listener_type == 'chains':
                        device.remove_chains_listener(listener_func)
                    elif listener_type.startswith('chain_'):
                        # Handle Chain class listener cleanup
                        parts = listener_type.split('_')
                        if len(parts) >= 3:
                            chain_idx = int(parts[1])
                            listener_attr = '_'.join(parts[2:])
                            
                            if hasattr(device, 'chains') and chain_idx < len(device.chains):
                                chain = device.chains[chain_idx]
                                
                                # Chain property listeners
                                if listener_attr == 'name' and hasattr(chain, 'remove_name_listener'):
                                    chain.remove_name_listener(listener_func)
                                elif listener_attr == 'color' and hasattr(chain, 'remove_color_listener'):
                                    chain.remove_color_listener(listener_func)
                                elif listener_attr == 'mute' and hasattr(chain, 'remove_mute_listener'):
                                    chain.remove_mute_listener(listener_func)
                                elif listener_attr == 'solo' and hasattr(chain, 'remove_solo_listener'):
                                    chain.remove_solo_listener(listener_func)
                                elif listener_attr == 'devices' and hasattr(chain, 'remove_devices_listener'):
                                    chain.remove_devices_listener(listener_func)
                                
                                # Chain mixer device listeners
                                elif hasattr(chain, 'mixer_device') and chain.mixer_device:
                                    mixer = chain.mixer_device
                                    if listener_attr == 'volume' and hasattr(mixer.volume, 'remove_value_listener'):
                                        mixer.volume.remove_value_listener(listener_func)
                                    elif listener_attr == 'pan' and hasattr(mixer.panning, 'remove_value_listener'):
                                        mixer.panning.remove_value_listener(listener_func)
                                    elif listener_attr == 'crossfade' and hasattr(mixer, 'remove_crossfade_assign_listener'):
                                        mixer.remove_crossfade_assign_listener(listener_func)
                                    elif listener_attr.startswith('send_'):
                                        send_idx = int(listener_attr.split('_')[1])
                                        if hasattr(mixer, 'sends') and send_idx < len(mixer.sends):
                                            send = mixer.sends[send_idx]
                                            if hasattr(send, 'remove_value_listener'):
                                                send.remove_value_listener(listener_func)
                    
                    elif listener_type.startswith('macro_'):
                        # Handle rack macro cleanup
                        macro_idx = int(listener_type.split('_')[1])
                        if hasattr(device, 'macros') and macro_idx < len(device.macros):
                            macro = device.macros[macro_idx]
                            if hasattr(macro, 'remove_value_listener'):
                                macro.remove_value_listener(listener_func)
                except:
                    pass
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning device T{track_idx}D{device_idx} listeners: {e}")
    
    def _cleanup_parameter_listeners(self, track_idx, device_idx, param_idx, listeners):
        """Clean up listeners for a specific parameter"""
        try:
            if track_idx >= len(self.song.tracks):
                return
                
            track = self.song.tracks[track_idx]
            devices = list(track.devices)
            
            if device_idx >= len(devices):
                return
                
            device = devices[device_idx]
            
            if param_idx >= len(device.parameters):
                return
                
            param = device.parameters[param_idx]
            
            for listener_type, listener_func in listeners:
                try:
                    if listener_type == 'value':
                        param.remove_value_listener(listener_func)
                except:
                    pass
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning param T{track_idx}D{device_idx}P{param_idx} listeners: {e}")
    
    def _cleanup_drum_listeners(self, track_idx, device_idx, listeners):
        """Clean up drum rack listeners"""
        try:
            # Implementation would be similar to other cleanup methods
            pass
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning drum T{track_idx}D{device_idx} listeners: {e}")
    
    # ========================================
    # DEVICE EVENT HANDLERS
    # ========================================
    
    def _on_device_name_changed(self, track_idx, device_idx):
        """Device name changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device:
                self.c_surface.log_message(f"🎛️ Device T{track_idx}D{device_idx} name: '{device.name}'")
                self._send_device_name(track_idx, device_idx, device.name)
    
    def _on_device_enabled_changed(self, track_idx, device_idx):
        """Device enabled state changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device:
                self.c_surface.log_message(f"🔘 Device T{track_idx}D{device_idx} enabled: {device.is_active}")
                self._send_device_enabled_state(track_idx, device_idx, device.is_active)
    
    def _on_parameter_value_changed(self, track_idx, device_idx, param_idx):
        """Device parameter value changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and param_idx < len(device.parameters):
                param = device.parameters[param_idx]
                self.c_surface.log_message(f"🎚️ Param T{track_idx}D{device_idx}P{param_idx}: {param.value:.2f}")
                self._send_parameter_value(track_idx, device_idx, param_idx, param.value, param.name)
    
    def _on_selected_chain_changed(self, track_idx, device_idx):
        """Rack device selected chain changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'view') and hasattr(device.view, 'selected_chain'):
                selected_chain = device.view.selected_chain
                chain_idx = list(device.chains).index(selected_chain) if selected_chain else -1
                self.c_surface.log_message(f"🔗 Device T{track_idx}D{device_idx} selected chain: {chain_idx}")
                self._send_selected_chain(track_idx, device_idx, chain_idx)
    
    def _on_chains_changed(self, track_idx, device_idx):
        """Rack device chains changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"🔗 Device T{track_idx}D{device_idx} chains changed")
            self._send_device_chains(track_idx, device_idx)
    
    def _on_chain_name_changed(self, track_idx, device_idx, chain_idx):
        """Individual chain name changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                self.c_surface.log_message(f"🔗 Chain T{track_idx}D{device_idx}C{chain_idx} name: '{chain.name}'")
                self._send_chain_name(track_idx, device_idx, chain_idx, chain.name)
    
    def _on_chain_color_changed(self, track_idx, device_idx, chain_idx):
        """Individual chain color changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                color_rgb = ColorUtils.live_color_to_rgb(chain.color)
                self.c_surface.log_message(f"🎨 Chain T{track_idx}D{device_idx}C{chain_idx} color: {color_rgb}")
                self._send_chain_color(track_idx, device_idx, chain_idx, color_rgb)
    
    def _on_chain_mute_changed(self, track_idx, device_idx, chain_idx):
        """Chain mute state changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'mute'):
                    self.c_surface.log_message(f"🔇 Chain T{track_idx}D{device_idx}C{chain_idx} mute: {chain.mute}")
                    self._send_chain_mute(track_idx, device_idx, chain_idx, chain.mute)
    
    def _on_chain_solo_changed(self, track_idx, device_idx, chain_idx):
        """Chain solo state changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'solo'):
                    self.c_surface.log_message(f"🔊 Chain T{track_idx}D{device_idx}C{chain_idx} solo: {chain.solo}")
                    self._send_chain_solo(track_idx, device_idx, chain_idx, chain.solo)
    
    def _on_chain_devices_changed(self, track_idx, device_idx, chain_idx):
        """Chain devices changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"🎛️ Chain T{track_idx}D{device_idx}C{chain_idx} devices changed")
            self._send_chain_devices(track_idx, device_idx, chain_idx)
    
    def _on_chain_volume_changed(self, track_idx, device_idx, chain_idx):
        """Chain volume changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'mixer_device') and chain.mixer_device:
                    mixer = chain.mixer_device
                    if hasattr(mixer, 'volume') and hasattr(mixer.volume, 'value'):
                        volume = mixer.volume.value
                        self.c_surface.log_message(f"🔊 Chain T{track_idx}D{device_idx}C{chain_idx} volume: {volume:.2f}")
                        self._send_chain_volume(track_idx, device_idx, chain_idx, volume)
    
    def _on_chain_pan_changed(self, track_idx, device_idx, chain_idx):
        """Chain pan changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'mixer_device') and chain.mixer_device:
                    mixer = chain.mixer_device
                    if hasattr(mixer, 'panning') and hasattr(mixer.panning, 'value'):
                        pan = mixer.panning.value
                        self.c_surface.log_message(f"🔄 Chain T{track_idx}D{device_idx}C{chain_idx} pan: {pan:.2f}")
                        self._send_chain_pan(track_idx, device_idx, chain_idx, pan)
    
    def _on_chain_send_changed(self, track_idx, device_idx, chain_idx, send_idx):
        """Chain send changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'mixer_device') and chain.mixer_device:
                    mixer = chain.mixer_device
                    if hasattr(mixer, 'sends') and send_idx < len(mixer.sends):
                        send = mixer.sends[send_idx]
                        if hasattr(send, 'value'):
                            value = send.value
                            self.c_surface.log_message(f"📤 Chain T{track_idx}D{device_idx}C{chain_idx}S{send_idx} send: {value:.2f}")
                            self._send_chain_send(track_idx, device_idx, chain_idx, send_idx, value)
    
    def _on_chain_crossfade_changed(self, track_idx, device_idx, chain_idx):
        """Chain crossfade assignment changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'mixer_device') and chain.mixer_device:
                    mixer = chain.mixer_device
                    if hasattr(mixer, 'crossfade_assign'):
                        assign = mixer.crossfade_assign
                        self.c_surface.log_message(f"⚖️ Chain T{track_idx}D{device_idx}C{chain_idx} crossfade: {assign}")
                        self._send_chain_crossfade(track_idx, device_idx, chain_idx, assign)
    
    def _on_rack_macro_changed(self, track_idx, device_idx, macro_idx):
        """Rack macro parameter changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'macros') and macro_idx < len(device.macros):
                macro = device.macros[macro_idx]
                if hasattr(macro, 'value'):
                    value = macro.value
                    self.c_surface.log_message(f"🎚️ Rack T{track_idx}D{device_idx} macro {macro_idx}: {value:.2f}")
                    self._send_rack_macro(track_idx, device_idx, macro_idx, value)
    
    def _on_drum_pad_name_changed(self, track_idx, device_idx, pad_idx):
        """Drum pad name changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'drum_pads'):
                pad_note = pad_idx + 36
                if pad_note < len(device.drum_pads) and device.drum_pads[pad_note]:
                    drum_pad = device.drum_pads[pad_note]
                    self.c_surface.log_message(f"🥁 Drum pad T{track_idx}D{device_idx}P{pad_idx} name: '{drum_pad.name}'")
                    self._send_drum_pad_name(track_idx, device_idx, pad_idx, drum_pad.name)
                    self._send_drum_pad_info(track_idx, device_idx, pad_idx)
    
    def _on_drum_pad_mute_changed(self, track_idx, device_idx, pad_idx):
        """Drum pad mute state changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'drum_pads'):
                pad_note = pad_idx + 36
                if pad_note < len(device.drum_pads) and device.drum_pads[pad_note]:
                    drum_pad = device.drum_pads[pad_note]
                    if hasattr(drum_pad, 'mute'):
                        self.c_surface.log_message(f"🔇 Drum pad T{track_idx}D{device_idx}P{pad_idx} mute: {drum_pad.mute}")
                        self._send_drum_pad_info(track_idx, device_idx, pad_idx)
    
    def _on_drum_pad_solo_changed(self, track_idx, device_idx, pad_idx):
        """Drum pad solo state changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'drum_pads'):
                pad_note = pad_idx + 36
                if pad_note < len(device.drum_pads) and device.drum_pads[pad_note]:
                    drum_pad = device.drum_pads[pad_note]
                    if hasattr(drum_pad, 'solo'):
                        self.c_surface.log_message(f"🔊 Drum pad T{track_idx}D{device_idx}P{pad_idx} solo: {drum_pad.solo}")
                        self._send_drum_pad_info(track_idx, device_idx, pad_idx)
    
    def _on_drum_pad_sample_changed(self, track_idx, device_idx, pad_idx):
        """Drum pad sample changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"🎧 Drum pad T{track_idx}D{device_idx}P{pad_idx} sample changed")
            self._send_drum_pad_info(track_idx, device_idx, pad_idx)
    
    def _on_plugin_preset_changed(self, track_idx, device_idx):
        """Plugin preset changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device:
                preset_name = getattr(device, 'selected_preset_name', 'Unknown')
                preset_index = getattr(device, 'selected_preset_index', -1)
                self.c_surface.log_message(f"🎵 Plugin T{track_idx}D{device_idx} preset: {preset_name} ({preset_index})")
                self._send_plugin_preset_info(track_idx, device_idx, preset_index, preset_name)
    
    def _on_plugin_program_changed(self, track_idx, device_idx):
        """Plugin program/bank changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device:
                program_name = getattr(device, 'selected_program_name', 'Unknown')
                self.c_surface.log_message(f"🎹 Plugin T{track_idx}D{device_idx} program: {program_name}")
                self._send_plugin_program_info(track_idx, device_idx, program_name)
    
    def _on_plugin_latency_changed(self, track_idx, device_idx):
        """Plugin latency changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device:
                latency = getattr(device, 'latency_in_ms', 0.0)
                self.c_surface.log_message(f"⏱️ Plugin T{track_idx}D{device_idx} latency: {latency:.1f}ms")
                self._send_plugin_latency_info(track_idx, device_idx, latency)
    
    def _on_plugin_ui_changed(self, track_idx, device_idx):
        """Plugin UI visibility changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device:
                ui_visible = getattr(device, 'is_showing_plugin_ui', False)
                self.c_surface.log_message(f"🖥️ Plugin T{track_idx}D{device_idx} UI visible: {ui_visible}")
                self._send_plugin_ui_info(track_idx, device_idx, ui_visible)
    
    def _on_drum_pad_chains_changed(self, track_idx, device_idx, pad_idx):
        """Drum pad chains changed"""
        if self.c_surface._is_connected:
            self.c_surface.log_message(f"🥁 Drum pad T{track_idx}D{device_idx}P{pad_idx} chains changed")
            self._send_drum_pad_state(track_idx, device_idx, pad_idx)
            # Update complete NeoTrellis grid
            self._send_neotrellis_drum_grid(track_idx, device_idx)
    
    def _on_selected_drum_pad_changed(self, track_idx, device_idx):
        """Selected drum pad changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'view') and hasattr(device.view, 'selected_drum_pad'):
                selected_pad = device.view.selected_drum_pad
                pad_note = selected_pad.note if selected_pad else -1
                pad_idx = pad_note - 36 if pad_note >= 36 else -1
                self.c_surface.log_message(f"🥁 Device T{track_idx}D{device_idx} selected drum pad: {pad_idx}")
                self._send_selected_drum_pad(track_idx, device_idx, pad_idx)
                # Update complete NeoTrellis grid to show selection
                self._send_neotrellis_drum_grid(track_idx, device_idx)
    
    # Device type specific handlers
    def _on_simpler_sample_name_changed(self, track_idx, device_idx):
        """Simpler sample name changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'sample') and device.sample:
                sample_name = device.sample.name
                self.c_surface.log_message(f"🎵 Simpler T{track_idx}D{device_idx} sample: '{sample_name}'")
                self._send_simpler_sample_info(track_idx, device_idx, sample_name)
    
    def _on_simpler_sample_length_changed(self, track_idx, device_idx):
        """Simpler sample length changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'sample') and device.sample:
                sample_length = device.sample.length
                self.c_surface.log_message(f"📏 Simpler T{track_idx}D{device_idx} length: {sample_length}")
    
    def _on_eq_band_gain_changed(self, track_idx, device_idx, band_idx):
        """EQ band gain changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'bands') and band_idx < len(device.bands):
                band = device.bands[band_idx]
                gain = band.gain.value if hasattr(band, 'gain') else 0.0
                self.c_surface.log_message(f"🎚️ EQ T{track_idx}D{device_idx}B{band_idx} gain: {gain:.2f}")
    
    def _on_eq_band_freq_changed(self, track_idx, device_idx, band_idx):
        """EQ band frequency changed"""
        if self.c_surface._is_connected:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'bands') and band_idx < len(device.bands):
                band = device.bands[band_idx]
                freq = band.frequency.value if hasattr(band, 'frequency') else 0.0
                self.c_surface.log_message(f"🎵 EQ T{track_idx}D{device_idx}B{band_idx} freq: {freq:.1f}Hz")
    
    # ========================================
    # SEND METHODS
    # ========================================
    
    def _send_device_name(self, track_idx, device_idx, name):
        """Send device name to hardware"""
        try:
            name_bytes = name.encode('utf-8')[:12]  # Max 12 chars
            payload = [track_idx, device_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_DEVICE_LIST, payload)  # Reuse device list command
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending device name T{track_idx}D{device_idx}: {e}")
    
    def _send_device_enabled_state(self, track_idx, device_idx, is_enabled):
        """Send device enabled state to hardware"""
        try:
            payload = [track_idx, device_idx, 1 if is_enabled else 0]
            self.c_surface._send_sysex_command(CMD_DEVICE_ENABLE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending device enabled T{track_idx}D{device_idx}: {e}")
    
    def _send_parameter_value(self, track_idx, device_idx, param_idx, value, param_name):
        """Send parameter value to hardware"""
        try:
            # Validate and clamp value to MIDI range 0-127
            value_127 = int(value * 127)  # Convert to 0-127 range
            value_127 = max(0, min(127, value_127))  # Clamp to valid MIDI range
            
            display_str = f"{value:.2f}"
            
            # Use the parameter encoding from MIDIUtils
            message = SysExEncoder.encode_param_value(track_idx, device_idx, param_idx, value_127, display_str)
            if message:
                self.c_surface._send_midi(tuple(message))
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending parameter T{track_idx}D{device_idx}P{param_idx}: {e}")
    
    def _send_selected_chain(self, track_idx, device_idx, chain_idx):
        """Send selected chain to hardware"""
        try:
            payload = [track_idx, device_idx, chain_idx if chain_idx >= 0 else 127]
            self.c_surface._send_sysex_command(CMD_CHAIN_SELECT, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending selected chain T{track_idx}D{device_idx}: {e}")
    
    def _send_device_chains(self, track_idx, device_idx):
        """Send device chains info to hardware"""
        try:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains'):
                chains_info = []
                for chain in device.chains[:4]:  # Max 4 chains
                    chains_info.append({
                        'name': chain.name,
                        'enabled': True,  # Chains don't have enabled state typically
                        'index': list(device.chains).index(chain)
                    })
                
                # Use device list encoding
                message = SysExEncoder.encode_device_list(track_idx, chains_info)
                if message:
                    self.c_surface._send_midi(tuple(message))
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending device chains T{track_idx}D{device_idx}: {e}")
    
    def _send_chain_name(self, track_idx, device_idx, chain_idx, name):
        """Send chain name to hardware"""
        try:
            name_bytes = name.encode('utf-8')[:12]  # Max 12 chars
            payload = [track_idx, device_idx, chain_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_DEVICE_CHAIN, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain name T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_color(self, track_idx, device_idx, chain_idx, color_rgb):
        """Send chain color to hardware"""
        try:
            r, g, b = color_rgb
            # Convert to MIDI range
            r = min(127, max(0, r // 2))
            g = min(127, max(0, g // 2))
            b = min(127, max(0, b // 2))
            
            payload = [track_idx, device_idx, chain_idx, r, g, b]
            self.c_surface._send_sysex_command(CMD_DEVICE_CHAIN, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain color T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_mute(self, track_idx, device_idx, chain_idx, mute_state):
        """Send chain mute state to hardware"""
        try:
            payload = [track_idx, device_idx, chain_idx, 1 if mute_state else 0]
            self.c_surface._send_sysex_command(CMD_CHAIN_MUTE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain mute T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_solo(self, track_idx, device_idx, chain_idx, solo_state):
        """Send chain solo state to hardware"""
        try:
            payload = [track_idx, device_idx, chain_idx, 1 if solo_state else 0]
            self.c_surface._send_sysex_command(CMD_CHAIN_SOLO, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain solo T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_devices(self, track_idx, device_idx, chain_idx):
        """Send chain devices list to hardware"""
        try:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'chains') and chain_idx < len(device.chains):
                chain = device.chains[chain_idx]
                if hasattr(chain, 'devices'):
                    device_names = []
                    for chain_device in chain.devices[:4]:  # Max 4 devices per chain
                        if chain_device:
                            name_bytes = chain_device.name.encode('utf-8')[:8]
                            device_names.extend([len(name_bytes)] + list(name_bytes))
                    
                    payload = [track_idx, device_idx, chain_idx, len(chain.devices)] + device_names
                    if len(payload) <= 50:  # Reasonable size limit
                        self.c_surface._send_sysex_command(CMD_DEVICE_CHAIN, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain devices T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_volume(self, track_idx, device_idx, chain_idx, volume):
        """Send chain volume to hardware"""
        try:
            volume_127 = int(volume * 127)
            payload = [track_idx, device_idx, chain_idx, volume_127]
            self.c_surface._send_sysex_command(CMD_CHAIN_VOLUME, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain volume T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_pan(self, track_idx, device_idx, chain_idx, pan):
        """Send chain pan to hardware"""
        try:
            pan_127 = int((pan + 1.0) * 63.5)  # Convert -1.0 to 1.0 range to 0-127
            payload = [track_idx, device_idx, chain_idx, pan_127]
            self.c_surface._send_sysex_command(CMD_CHAIN_PAN, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain pan T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_chain_send(self, track_idx, device_idx, chain_idx, send_idx, value):
        """Send chain send level to hardware"""
        try:
            send_127 = int(value * 127)
            payload = [track_idx, device_idx, chain_idx, send_idx, send_127]
            self.c_surface._send_sysex_command(CMD_CHAIN_SEND, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain send T{track_idx}D{device_idx}C{chain_idx}S{send_idx}: {e}")
    
    def _send_chain_crossfade(self, track_idx, device_idx, chain_idx, assign):
        """Send chain crossfade assignment to hardware"""
        try:
            # Convert crossfade assign to number: 0=A, 1=None, 2=B
            assign_val = 0 if assign == 0 else (2 if assign == 2 else 1)
            payload = [track_idx, device_idx, chain_idx, assign_val]
            self.c_surface._send_sysex_command(CMD_CHAIN_CROSSFADE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending chain crossfade T{track_idx}D{device_idx}C{chain_idx}: {e}")
    
    def _send_rack_macro(self, track_idx, device_idx, macro_idx, value):
        """Send rack macro value to hardware"""
        try:
            value_127 = int(value * 127)
            payload = [track_idx, device_idx, macro_idx, value_127]
            self.c_surface._send_sysex_command(CMD_RACK_MACRO, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending rack macro T{track_idx}D{device_idx}M{macro_idx}: {e}")
    
    def _send_drum_pad_name(self, track_idx, device_idx, pad_idx, name):
        """Send drum pad name to hardware"""
        try:
            name_bytes = name.encode('utf-8')[:8]  # Max 8 chars for pad names
            payload = [track_idx, device_idx, pad_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            self.c_surface._send_sysex_command(CMD_DRUM_PAD_STATE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending drum pad name T{track_idx}D{device_idx}P{pad_idx}: {e}")
    
    def _send_drum_pad_state(self, track_idx, device_idx, pad_idx):
        """Send drum pad state to hardware"""
        try:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'drum_pads'):
                pad_note = pad_idx + 36
                has_pad = (pad_note < len(device.drum_pads) and 
                          device.drum_pads[pad_note] is not None)
                
                payload = [track_idx, device_idx, pad_idx, 1 if has_pad else 0]
                self.c_surface._send_sysex_command(CMD_DRUM_PAD_STATE, payload)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending drum pad state T{track_idx}D{device_idx}P{pad_idx}: {e}")
    
    def _send_selected_drum_pad(self, track_idx, device_idx, pad_idx):
        """Send selected drum pad to hardware"""
        try:
            payload = [track_idx, device_idx, pad_idx if pad_idx >= 0 else 127]
            self.c_surface._send_sysex_command(CMD_DRUM_RACK_STATE, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending selected drum pad T{track_idx}D{device_idx}: {e}")
    
    def _send_drum_pad_info(self, track_idx, device_idx, pad_idx):
        """Send comprehensive drum pad information to hardware"""
        try:
            device = self._get_device(track_idx, device_idx)
            if device and hasattr(device, 'drum_pads'):
                pad_note = pad_idx + 36
                if pad_note < len(device.drum_pads) and device.drum_pads[pad_note]:
                    drum_pad = device.drum_pads[pad_note]
                    
                    # Pack drum pad data
                    name_bytes = drum_pad.name.encode('utf-8')[:8] if hasattr(drum_pad, 'name') else []
                    
                    payload = [
                        track_idx, device_idx, pad_idx, pad_note,  # Basic indices
                        len(name_bytes)  # Name length
                    ]
                    payload.extend(list(name_bytes))  # Pad name
                    
                    # Pad state flags
                    flags = 0
                    if hasattr(drum_pad, 'mute') and drum_pad.mute:
                        flags |= 0x01  # Muted
                    if hasattr(drum_pad, 'solo') and drum_pad.solo:
                        flags |= 0x02  # Solo
                    if hasattr(drum_pad, 'chains') and drum_pad.chains:
                        flags |= 0x04  # Has chains
                    
                    # Check for sample
                    has_sample = False
                    if hasattr(drum_pad, 'canonical_parent'):
                        try:
                            parent = drum_pad.canonical_parent
                            has_sample = (hasattr(parent, 'sample') and 
                                        parent.sample is not None and
                                        hasattr(parent.sample, 'file_path') and
                                        parent.sample.file_path != '')
                        except Exception:
                            pass
                    
                    if has_sample:
                        flags |= 0x08  # Has sample
                    
                    payload.append(flags)
                    
                    # Chain count
                    chain_count = 0
                    if hasattr(drum_pad, 'chains') and drum_pad.chains:
                        chain_count = len(drum_pad.chains)
                    payload.append(min(chain_count, 255))  # Max 255 chains
                    
                    self.c_surface._send_sysex_command(CMD_DRUM_PAD_STATE, payload)
                    
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending drum pad info T{track_idx}D{device_idx}P{pad_idx}: {e}")
    
    def _send_plugin_preset_info(self, track_idx, device_idx, preset_index, preset_name):
        """Send plugin preset information to hardware"""
        try:
            name_bytes = preset_name.encode('utf-8')[:16] if preset_name else []
            payload = [
                track_idx, device_idx,
                (preset_index >> 8) & 0x7F,  # High byte
                preset_index & 0x7F,         # Low byte  
                len(name_bytes)
            ]
            payload.extend(list(name_bytes))
            
            # Could add CMD_PLUGIN_PRESET = 0x71 to consts.py
            self.c_surface._send_sysex_command(0x71, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending plugin preset info: {e}")
    
    def _send_plugin_program_info(self, track_idx, device_idx, program_name):
        """Send plugin program information to hardware"""
        try:
            name_bytes = program_name.encode('utf-8')[:16] if program_name else []
            payload = [track_idx, device_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            
            # Could add CMD_PLUGIN_PROGRAM = 0x72 to consts.py
            self.c_surface._send_sysex_command(0x72, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending plugin program info: {e}")
    
    def _send_plugin_latency_info(self, track_idx, device_idx, latency_ms):
        """Send plugin latency information to hardware"""
        try:
            # Convert float latency to integer milliseconds
            latency_int = int(latency_ms) & 0x3FFF  # Max ~16 seconds
            
            payload = [
                track_idx, device_idx,
                (latency_int >> 7) & 0x7F,  # High 7 bits
                latency_int & 0x7F           # Low 7 bits
            ]
            
            # Could add CMD_PLUGIN_LATENCY = 0x73 to consts.py
            self.c_surface._send_sysex_command(0x73, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending plugin latency info: {e}")
    
    def _send_plugin_ui_info(self, track_idx, device_idx, ui_visible):
        """Send plugin UI visibility information to hardware"""
        try:
            payload = [track_idx, device_idx, 1 if ui_visible else 0]
            
            # Could add CMD_PLUGIN_UI = 0x74 to consts.py
            self.c_surface._send_sysex_command(0x74, payload)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending plugin UI info: {e}")
    
    def _send_neotrellis_drum_grid(self, track_idx, device_idx):
        """Send complete NeoTrellis drum grid state (4x8 = 32 pads)"""
        try:
            device = self._get_device(track_idx, device_idx)
            if not device or not hasattr(device, 'can_have_drum_pads') or not device.can_have_drum_pads:
                return
            
            # NeoTrellis 4x8 grid (32 pads total)
            grid_data = []
            
            for row in range(4):
                for col in range(8):
                    pad_idx = row * 8 + col  # 0-31
                    pad_note = pad_idx + 36  # Standard drum mapping starts at C2 (36)
                    
                    # Check if drum pad exists and has content
                    if (hasattr(device, 'drum_pads') and 
                        pad_note < len(device.drum_pads) and 
                        device.drum_pads[pad_note]):
                        
                        drum_pad = device.drum_pads[pad_note]
                        
                        # Determine color based on pad state
                        has_sample = bool(drum_pad.chains and len(drum_pad.chains) > 0)
                        is_active = has_sample and any(chain.is_active for chain in drum_pad.chains)
                        
                        # Color mapping: 0=empty, 1=loaded, 2=active, 3=selected
                        if is_active:
                            color = 2  # Active (bright)
                        elif has_sample:
                            color = 1  # Loaded (dim)
                        else:
                            color = 0  # Empty
                            
                        # Check if this is the selected pad
                        if (hasattr(device, 'view') and 
                            hasattr(device.view, 'selected_drum_pad') and
                            device.view.selected_drum_pad and
                            device.view.selected_drum_pad == drum_pad):
                            color = 3  # Selected
                    else:
                        color = 0  # Empty/no pad
                    
                    grid_data.append(color)
            
            # Send grid state: track, device, 32 color bytes
            payload = [track_idx, device_idx] + grid_data
            self.c_surface._send_sysex_command(CMD_NEOTRELLIS_GRID, payload, silent=True)
            
            self.c_surface.log_message(f"🎛️ Sent NeoTrellis grid for T{track_idx}D{device_idx}")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending NeoTrellis grid T{track_idx}D{device_idx}: {e}")
    
    def _send_simpler_sample_info(self, track_idx, device_idx, sample_name):
        """Send Simpler sample info to hardware"""
        try:
            name_bytes = sample_name.encode('utf-8')[:12]  # Max 12 chars
            payload = [track_idx, device_idx, len(name_bytes)]
            payload.extend(list(name_bytes))
            # Could use a specific simpler command or reuse device name
            self.c_surface._send_sysex_command(CMD_DEVICE_LIST, payload)
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending simpler sample T{track_idx}D{device_idx}: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _get_device(self, track_idx, device_idx):
        """Get device by track and device index"""
        try:
            if track_idx >= len(self.song.tracks):
                return None
                
            track = self.song.tracks[track_idx]
            devices = list(track.devices)
            
            if device_idx >= len(devices):
                return None
                
            return devices[device_idx]
            
        except:
            return None
    
    def get_device_info(self, track_idx, device_idx):
        """Get complete device information"""
        device = self._get_device(track_idx, device_idx)
        if not device:
            return None
            
        info = {
            'name': device.name,
            'is_active': device.is_active,
            'class_name': device.__class__.__name__,
            'parameters': []
        }
        
        # Add parameter info
        for param_idx, param in enumerate(device.parameters[:8]):
            info['parameters'].append({
                'index': param_idx,
                'name': param.name,
                'value': param.value,
                'min': param.min,
                'max': param.max
            })
        
        # Add RackDevice and Chain class comprehensive info
        if hasattr(device, 'can_have_chains') and device.can_have_chains:
            info['chains'] = []
            for chain_idx, chain in enumerate(device.chains[:8]):  # Support up to 8 chains
                chain_info = {
                    'index': chain_idx,
                    'name': getattr(chain, 'name', f'Chain {chain_idx}'),
                    'color': ColorUtils.live_color_to_rgb(getattr(chain, 'color', 0)),
                    'mute': getattr(chain, 'mute', False),
                    'solo': getattr(chain, 'solo', False),
                    'devices': []
                }
                
                # Chain devices list (Chain.devices property)
                if hasattr(chain, 'devices'):
                    for device_idx, chain_device in enumerate(chain.devices[:4]):
                        if chain_device:
                            chain_info['devices'].append({
                                'index': device_idx,
                                'name': chain_device.name,
                                'is_active': getattr(chain_device, 'is_active', True),
                                'class_name': chain_device.__class__.__name__
                            })
                
                # Chain mixer device info (ChainMixerDevice)
                if hasattr(chain, 'mixer_device') and chain.mixer_device:
                    mixer = chain.mixer_device
                    chain_info['mixer'] = {
                        'volume': getattr(mixer.volume, 'value', 1.0) if hasattr(mixer, 'volume') else 1.0,
                        'pan': getattr(mixer.panning, 'value', 0.0) if hasattr(mixer, 'panning') else 0.0,
                        'crossfade_assign': getattr(mixer, 'crossfade_assign', 1),
                        'sends': []
                    }
                    
                    # Chain sends
                    if hasattr(mixer, 'sends'):
                        for send_idx, send in enumerate(mixer.sends[:4]):
                            if send:
                                chain_info['mixer']['sends'].append({
                                    'index': send_idx,
                                    'value': getattr(send, 'value', 0.0)
                                })
                
                info['chains'].append(chain_info)
            
            # Selected chain info
            if hasattr(device, 'view') and hasattr(device.view, 'selected_chain'):
                selected_chain = device.view.selected_chain
                info['selected_chain_idx'] = list(device.chains).index(selected_chain) if selected_chain else -1
            
            # Rack macro controls
            if hasattr(device, 'macros'):
                info['macros'] = []
                for macro_idx, macro in enumerate(device.macros[:8]):
                    if macro:
                        info['macros'].append({
                            'index': macro_idx,
                            'name': getattr(macro, 'name', f'Macro {macro_idx}'),
                            'value': getattr(macro, 'value', 0.0),
                            'min': getattr(macro, 'min', 0.0),
                            'max': getattr(macro, 'max', 1.0)
                        })
        
        if hasattr(device, 'can_have_drum_pads') and device.can_have_drum_pads:
            info['drum_pads'] = []
            for pad_idx in range(16):
                pad_note = pad_idx + 36
                if pad_note < len(device.drum_pads) and device.drum_pads[pad_note]:
                    drum_pad = device.drum_pads[pad_note]
                    # Complete DrumPad info according to Live Object Model
                    pad_info = {
                        'index': pad_idx,
                        'note': pad_note,
                        'name': getattr(drum_pad, 'name', f'Pad {pad_idx}'),
                        'mute': getattr(drum_pad, 'mute', False),
                        'solo': getattr(drum_pad, 'solo', False),
                        'has_chains': bool(hasattr(drum_pad, 'chains') and drum_pad.chains),
                        'chain_count': len(drum_pad.chains) if hasattr(drum_pad, 'chains') and drum_pad.chains else 0
                    }
                    
                    # Sample information (if available)
                    if hasattr(drum_pad, 'canonical_parent'):
                        try:
                            parent = drum_pad.canonical_parent
                            if hasattr(parent, 'sample') and parent.sample:
                                sample = parent.sample
                                pad_info.update({
                                    'has_sample': True,
                                    'sample_file': getattr(sample, 'file_path', ''),
                                    'sample_length': getattr(sample, 'length', 0.0),
                                    'sample_rate': getattr(sample, 'sample_rate', 44100)
                                })
                            else:
                                pad_info['has_sample'] = False
                        except Exception:
                            pad_info['has_sample'] = False
                    else:
                        pad_info['has_sample'] = False
                    
                    info['drum_pads'].append(pad_info)
        
        return info
    
    def send_complete_device_state(self, track_idx, device_idx):
        """Send complete state for a single device"""
        if not self.c_surface._is_connected:
            return
            
        try:
            device = self._get_device(track_idx, device_idx)
            if not device:
                return
            
            # Send device basic info
            self._send_device_name(track_idx, device_idx, device.name)
            self._send_device_enabled_state(track_idx, device_idx, device.is_active)
            
            # Send parameters
            for param_idx, param in enumerate(device.parameters[:8]):
                self._send_parameter_value(track_idx, device_idx, param_idx, param.value, param.name)
            
            # Send device-specific info
            if hasattr(device, 'can_have_chains') and device.can_have_chains:
                self._send_device_chains(track_idx, device_idx)
                
                if hasattr(device, 'view') and hasattr(device.view, 'selected_chain'):
                    selected_chain = device.view.selected_chain
                    chain_idx = list(device.chains).index(selected_chain) if selected_chain else -1
                    self._send_selected_chain(track_idx, device_idx, chain_idx)
            
            if hasattr(device, 'can_have_drum_pads') and device.can_have_drum_pads:
                # Send complete NeoTrellis drum grid (32 pads with colors)
                self._send_neotrellis_drum_grid(track_idx, device_idx)
                
                # Send individual drum pad states for compatibility
                for pad_idx in range(16):
                    self._send_drum_pad_state(track_idx, device_idx, pad_idx)
                
                # Send selected drum pad
                if hasattr(device, 'view') and hasattr(device.view, 'selected_drum_pad'):
                    selected_pad = device.view.selected_drum_pad
                    pad_note = selected_pad.note if selected_pad else -1
                    pad_idx = pad_note - 36 if pad_note >= 36 else -1
                    self._send_selected_drum_pad(track_idx, device_idx, pad_idx)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending device T{track_idx}D{device_idx} state: {e}")
    
    def refresh_track_devices(self, track_idx):
        """Refresh device listeners for a specific track when devices change"""
        try:
            if track_idx >= len(self.song.tracks):
                return
                
            track = self.song.tracks[track_idx]
            self.c_surface.log_message(f"🔄 Refreshing devices for track {track_idx}...")
            
            # Clean up existing device listeners for this track
            keys_to_remove = [(t_idx, d_idx) for (t_idx, d_idx) in self._device_listeners.keys() if t_idx == track_idx]
            for key in keys_to_remove:
                track_idx_old, device_idx_old = key
                listeners = self._device_listeners[key]
                self._cleanup_device_listeners(track_idx_old, device_idx_old, listeners)
                del self._device_listeners[key]
            
            # Setup listeners for all current devices in this track
            if hasattr(track, 'devices'):
                for device_idx, device in enumerate(track.devices):
                    if device:
                        self._setup_single_device_listeners(track_idx, device_idx)
                        self.c_surface.log_message(f"🎛️ Setup device T{track_idx}D{device_idx}: {device.name}")
            
            self.c_surface.log_message(f"✅ Track {track_idx} device listeners refreshed")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error refreshing track {track_idx} devices: {e}")
    
    def refresh_all_tracks(self):
        """Refresh device listeners for all tracks (when tracks are added/removed)"""
        try:
            self.c_surface.log_message("🔄 Refreshing all device listeners...")
            
            # Clean up all existing listeners
            self.cleanup_listeners()
            
            # Re-setup listeners for all current tracks and devices
            self.setup_listeners(max_tracks=8, max_devices_per_track=8)
            
            self.c_surface.log_message("✅ All device listeners refreshed")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error refreshing all device listeners: {e}")
    
    def send_complete_state(self):
        """Send complete state for all devices"""
        if not self.c_surface._is_connected:
            return
            
        try:
            self.c_surface.log_message("📡 Sending complete device state...")
            
            for (track_idx, device_idx) in self._device_listeners.keys():
                self.send_complete_device_state(track_idx, device_idx)
            
            self.c_surface.log_message("✅ Device state sent")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending device state: {e}")
    
    # ========================================
    # DEVICE NAVIGATION
    # ========================================
    
    def select_device(self, track_idx, device_idx):
        """Select device for parameter editing"""
        old_track = self._current_track
        old_device = self._current_device
        
        self._current_track = track_idx
        self._current_device = device_idx
        self._current_param_page = 0
        
        # Reset encoder takeover when switching devices
        if old_track != track_idx or old_device != device_idx:
            self.reset_encoder_takeover(old_track, old_device)
        
        device = self._get_device(track_idx, device_idx)
        if device:
            self.c_surface.log_message(f"🎯 Selected device T{track_idx}D{device_idx}: {device.name}")
            self.send_complete_device_state(track_idx, device_idx)
    
    def navigate_device(self, direction):
        """Navigate to next/previous device"""
        try:
            if direction > 0:  # Next device
                self._current_device += 1
            else:  # Previous device
                self._current_device = max(0, self._current_device - 1)
            
            # Check if device exists
            device = self._get_device(self._current_track, self._current_device)
            if device:
                self.select_device(self._current_track, self._current_device)
            else:
                # Wrap around or stay at boundary
                self._current_device = max(0, self._current_device - 1)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error navigating device: {e}")
    
    def change_parameter_page(self, direction):
        """Change parameter page for current device"""
        try:
            device = self._get_device(self._current_track, self._current_device)
            if not device:
                return
                
            total_params = len(device.parameters)
            total_pages = (total_params + 7) // 8  # 8 params per page
            
            if direction > 0:  # Next page
                self._current_param_page = min(total_pages - 1, self._current_param_page + 1)
            else:  # Previous page
                self._current_param_page = max(0, self._current_param_page - 1)
            
            self.c_surface.log_message(f"📄 Device T{self._current_track}D{self._current_device} page: {self._current_param_page}/{total_pages}")
            
            # Send current page parameters
            self._send_device_param_page(self._current_track, self._current_device, self._current_param_page)
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error changing parameter page: {e}")
    
    def _send_device_param_page(self, track_idx, device_idx, page):
        """Send current parameter page to hardware"""
        try:
            device = self._get_device(track_idx, device_idx)
            if not device:
                return
                
            total_params = len(device.parameters)
            total_pages = (total_params + 7) // 8
            start_param = page * 8
            
            params_info = []
            for i in range(8):
                param_idx = start_param + i
                if param_idx < total_params:
                    param = device.parameters[param_idx]
                    params_info.append({
                        'index': param_idx,
                        'value': int(param.value * 127),
                        'name': param.name
                    })
                else:
                    params_info.append({'index': 0xFF})  # Empty slot
            
            # Use device params encoding from MIDIUtils
            message = SysExEncoder.encode_device_params(track_idx, device_idx, page, total_pages, params_info)
            if message:
                self.c_surface._send_midi(tuple(message))
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending device param page T{track_idx}D{device_idx}: {e}")
    
    # ========================================
    # SOFT TAKEOVER FOR ENCODERS
    # ========================================
    
    def handle_encoder_change(self, track_idx, device_idx, param_idx, hardware_value):
        """Handle encoder changes with soft takeover"""
        try:
            device = self._get_device(track_idx, device_idx)
            if not device or param_idx >= len(device.parameters):
                return
                
            param = device.parameters[param_idx]
            param_key = (track_idx, device_idx, param_idx)
            
            # Current parameter value in hardware range (0-127)
            current_value_127 = int(param.value * 127)
            
            # Check if this encoder is already taken over
            is_taken_over = self._takeover_active.get(param_key, False)
            
            if not is_taken_over:
                # Check if hardware value is close enough to take over
                diff = abs(hardware_value - current_value_127)
                if diff <= self._takeover_threshold:
                    # Takeover achieved
                    self._takeover_active[param_key] = True
                    self.c_surface.log_message(
                        f"🎹 Encoder takeover T{track_idx}D{device_idx}P{param_idx}: {param.name}"
                    )
                else:
                    # Not taken over yet - ignore this change
                    return
            
            # Update parameter value
            normalized_value = hardware_value / 127.0
            param_range = param.max - param.min
            new_value = param.min + (normalized_value * param_range)
            param.value = new_value
            
            # Store the hardware value
            self._encoder_values[param_key] = hardware_value
            
            self.c_surface.log_message(
                f"🎹 Encoder T{track_idx}D{device_idx}P{param_idx}: {param.name} = {new_value:.2f}"
            )
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error handling encoder change: {e}")
    
    def reset_encoder_takeover(self, track_idx=None, device_idx=None):
        """Reset encoder takeover state"""
        try:
            if track_idx is not None and device_idx is not None:
                # Reset specific device encoders
                keys_to_reset = [k for k in self._takeover_active.keys() 
                               if k[0] == track_idx and k[1] == device_idx]
                for key in keys_to_reset:
                    del self._takeover_active[key]
                    if key in self._encoder_values:
                        del self._encoder_values[key]
                
                self.c_surface.log_message(
                    f"🔄 Reset encoder takeover for T{track_idx}D{device_idx}"
                )
            else:
                # Reset all encoders
                self._takeover_active.clear()
                self._encoder_values.clear()
                self.c_surface.log_message("🔄 Reset all encoder takeover")
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error resetting encoder takeover: {e}")
    
    def get_encoder_takeover_info(self):
        """Get current encoder takeover information"""
        return {
            'active_encoders': len(self._takeover_active),
            'takeover_threshold': self._takeover_threshold,
            'encoders': dict(self._takeover_active)
        }

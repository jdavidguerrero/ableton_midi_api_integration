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
        
        # Device view state
        self._current_track = 0
        self._current_device = 0
        self._current_param_page = 0
        
    def setup_listeners(self, max_tracks=8, max_devices_per_track=8):
        """Setup device listeners for specified tracks and devices"""
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
            if hasattr(device, 'add_is_enabled_listener'):
                is_enabled_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_device_enabled_changed(t_idx, d_idx)
                device.add_is_enabled_listener(is_enabled_listener)
                listeners.append(('is_enabled', is_enabled_listener))
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
        """Setup listeners for rack devices (Instrument/Audio Racks)"""
        try:
            # Chain selection
            if hasattr(device, 'view') and hasattr(device.view, 'selected_chain'):
                chain_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_selected_chain_changed(t_idx, d_idx)
                device.view.add_selected_chain_listener(chain_listener)
                listeners.append(('selected_chain', chain_listener))
            
            # Chains list
            if hasattr(device, 'chains'):
                chains_listener = lambda t_idx=track_idx, d_idx=device_idx: self._on_chains_changed(t_idx, d_idx)
                device.add_chains_listener(chains_listener)
                listeners.append(('chains', chains_listener))
                
                # Individual chain listeners
                for chain_idx, chain in enumerate(device.chains[:4]):  # First 4 chains
                    if hasattr(chain, 'name'):
                        chain_name_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_name_changed(t_idx, d_idx, c_idx)
                        chain.add_name_listener(chain_name_listener)
                        listeners.append((f'chain_{chain_idx}_name', chain_name_listener))
                    
                    if hasattr(chain, 'is_auto_colored'):
                        chain_color_listener = lambda t_idx=track_idx, d_idx=device_idx, c_idx=chain_idx: self._on_chain_color_changed(t_idx, d_idx, c_idx)
                        chain.add_color_listener(chain_color_listener)
                        listeners.append((f'chain_{chain_idx}_color', chain_color_listener))
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up rack listeners T{track_idx}D{device_idx}: {e}")
    
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
                            
                            # Pad chains (if has chains)
                            if hasattr(drum_pad, 'chains') and drum_pad.chains:
                                pad_chains_listener = lambda t_idx=track_idx, d_idx=device_idx, p_idx=pad_idx: self._on_drum_pad_chains_changed(t_idx, d_idx, p_idx)
                                drum_pad.add_chains_listener(pad_chains_listener)
                                drum_listeners.append((f'pad_{pad_idx}_chains', pad_chains_listener))
            
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
            
            # Simpler device
            if hasattr(device, 'sample') and device_class == 'SimplerDevice':
                self._setup_simpler_listeners(track_idx, device_idx, device, listeners)
            
            # Wavetable device
            elif device_class == 'WavetableDevice':
                self._setup_wavetable_listeners(track_idx, device_idx, device, listeners)
            
            # EQ Eight
            elif device_class == 'Eq8Device':
                self._setup_eq8_listeners(track_idx, device_idx, device, listeners)
            
            # Compressor
            elif device_class == 'CompressorDevice':
                self._setup_compressor_listeners(track_idx, device_idx, device, listeners)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting up device type listeners T{track_idx}D{device_idx}: {e}")
    
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
                    sample.add_length_listener(sample_length_listener)
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
                    elif listener_type == 'is_enabled':
                        if hasattr(device, 'remove_is_enabled_listener'):
                            device.remove_is_enabled_listener(listener_func)
                    elif listener_type.startswith('param_'):
                        param_idx = int(listener_type.split('_')[1])
                        if param_idx < len(device.parameters):
                            device.parameters[param_idx].remove_value_listener(listener_func)
                    elif listener_type == 'selected_chain':
                        device.view.remove_selected_chain_listener(listener_func)
                    elif listener_type == 'chains':
                        device.remove_chains_listener(listener_func)
                    # Add more cleanup cases as needed
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
                self.c_surface.log_message(f"🔘 Device T{track_idx}D{device_idx} enabled: {device.is_enabled}")
                self._send_device_enabled_state(track_idx, device_idx, device.is_enabled)
    
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
            self.c_surface._send_sysex_command(CMD_DEVICE_CHAIN, payload)
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
            self.c_surface._send_sysex_command(CMD_NEOTRELLIS_GRID, payload)
            
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
            'is_enabled': device.is_enabled,
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
        
        # Add device-specific info
        if hasattr(device, 'can_have_chains') and device.can_have_chains:
            info['chains'] = []
            for chain in device.chains[:4]:
                info['chains'].append({
                    'name': chain.name,
                    'color': ColorUtils.live_color_to_rgb(chain.color)
                })
        
        if hasattr(device, 'can_have_drum_pads') and device.can_have_drum_pads:
            info['drum_pads'] = []
            for pad_idx in range(16):
                pad_note = pad_idx + 36
                if pad_note < len(device.drum_pads) and device.drum_pads[pad_note]:
                    drum_pad = device.drum_pads[pad_note]
                    info['drum_pads'].append({
                        'index': pad_idx,
                        'note': pad_note,
                        'name': drum_pad.name
                    })
        
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
            self._send_device_enabled_state(track_idx, device_idx, device.is_enabled)
            
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
        self._current_track = track_idx
        self._current_device = device_idx
        self._current_param_page = 0
        
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

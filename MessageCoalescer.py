# MessageCoalescer.py - Performance-optimized message batching
"""
Manages message coalescing for optimal hardware communication performance
Limits refresh rate to 60fps and batches LED updates
"""

import time
from threading import Timer
from .consts import *
from .MIDIUtils import SysExEncoder

class MessageCoalescer:
    """
    Coalesces messages for optimal performance
    - Groups LED updates in time windows (2-4ms)
    - Limits refresh rate to 60fps max
    - Prevents message flooding
    """
    
    def __init__(self, control_surface):
        self.c_surface = control_surface
        
        # Performance settings
        self.target_fps = 60
        self.frame_time_ms = 1000.0 / self.target_fps  # ~16.67ms per frame
        self.coalesce_window_ms = 4.0  # Group messages within 4ms
        
        # Message batching
        self._pending_messages = {}  # command -> latest_payload
        self._last_send_time = 0
        self._flush_timer = None
        self._frame_timer = None
        
        # Message priorities
        self._priority_commands = {
            CMD_TRANSPORT: 1,  # High priority
            CMD_CLIP_STATE: 2,
            CMD_DEVICE_PARAMS: 2,
            CMD_STEP_SEQUENCER_STATE: 3,
            CMD_NEOTRELLIS_GRID: 3,
            CMD_RING_POSITION: 2
        }
        
        # Statistics
        self._messages_coalesced = 0
        self._messages_sent = 0
        self._frames_dropped = 0
        
        # State tracking for deltas
        self._last_states = {}  # command -> last_payload
        
    def queue_message(self, command, payload, priority_override=None):
        """Queue a message for coalesced sending"""
        try:
            current_time = time.time() * 1000  # Convert to ms
            
            # Check if this is a duplicate of the last state
            if self._is_duplicate_state(command, payload):
                return  # Skip duplicate
            
            # Determine message priority
            priority = priority_override or self._priority_commands.get(command, 4)
            
            # Store message with metadata
            message_data = {
                'payload': payload,
                'priority': priority,
                'timestamp': current_time,
                'command': command
            }
            
            # For LED updates, only keep the latest
            if self._is_led_command(command):
                self._pending_messages[command] = message_data
            else:
                # For other commands, create unique key to avoid overwriting
                unique_key = f"{command}_{len(self._pending_messages)}"
                self._pending_messages[unique_key] = message_data
            
            self._messages_coalesced += 1
            
            # Schedule flush if not already scheduled
            self._schedule_flush()
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error queuing message: {e}")
    
    def _is_duplicate_state(self, command, payload):
        """Check if this payload is identical to the last one sent"""
        try:
            last_payload = self._last_states.get(command)
            if last_payload is None:
                return False
                
            # Compare payloads
            if len(payload) != len(last_payload):
                return False
                
            for i, byte in enumerate(payload):
                if byte != last_payload[i]:
                    return False
                    
            return True  # Identical payload
            
        except Exception:
            return False
    
    def _is_led_command(self, command):
        """Check if command is an LED update that can be coalesced"""
        led_commands = {
            CMD_CLIP_STATE,
            CMD_NEOTRELLIS_GRID, 
            CMD_NEOTRELLIS_CLIP_GRID,
            CMD_STEP_SEQUENCER_STATE,
            CMD_DEVICE_PARAMS,
            CMD_MIXER_STATE,
            CMD_TRANSPORT
        }
        return command in led_commands
    
    def _schedule_flush(self):
        """Schedule message flush based on frame rate"""
        try:
            current_time = time.time() * 1000
            
            # Cancel existing timer
            if self._flush_timer:
                self._flush_timer.cancel()
            
            # Calculate when to flush
            time_since_last_send = current_time - self._last_send_time
            
            if time_since_last_send >= self.frame_time_ms:
                # Enough time has passed - flush immediately
                self._flush_messages()
            else:
                # Schedule flush at next frame boundary
                delay_ms = self.frame_time_ms - time_since_last_send
                self._flush_timer = Timer(delay_ms / 1000.0, self._flush_messages)
                self._flush_timer.start()
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error scheduling flush: {e}")
    
    def _flush_messages(self):
        """Flush all pending messages to hardware"""
        try:
            if not self._pending_messages:
                return
                
            current_time = time.time() * 1000
            
            # Check frame rate limit
            time_since_last = current_time - self._last_send_time
            if time_since_last < self.frame_time_ms:
                self._frames_dropped += 1
                return  # Drop this frame to maintain 60fps limit
            
            # Sort messages by priority (lower number = higher priority)
            messages = list(self._pending_messages.values())
            messages.sort(key=lambda x: x['priority'])
            
            # Group messages into batches for efficient sending
            led_batch = []
            control_batch = []
            
            for msg in messages:
                if self._is_led_command(msg['command']):
                    led_batch.append(msg)
                else:
                    control_batch.append(msg)
            
            # Send control messages first (higher priority)
            for msg in control_batch:
                self._send_single_message(msg)
            
            # Send LED updates in optimized batches
            self._send_led_batch(led_batch)
            
            # Update statistics
            self._messages_sent += len(messages)
            self._last_send_time = current_time
            
            # Clear pending messages
            self._pending_messages.clear()
            
            # Log performance stats occasionally
            if self._messages_sent % 100 == 0:
                self._log_performance_stats()
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error flushing messages: {e}")
    
    def _send_single_message(self, message_data):
        """Send a single message"""
        try:
            command = message_data['command']
            payload = message_data['payload']
            
            # Create and send SysEx
            sysex_message = SysExEncoder.create_sysex(command, payload)
            if sysex_message:
                self.c_surface._send_midi(tuple(sysex_message))
                
                # Store state for duplicate detection
                self._last_states[command] = payload.copy() if hasattr(payload, 'copy') else list(payload)
                
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending message 0x{message_data['command']:02X}: {e}")
    
    def _send_led_batch(self, led_messages):
        """Send LED messages in optimized batches"""
        try:
            if not led_messages:
                return
            
            # For LED updates, we can send them in sequence quickly
            # since they're just visual updates
            for msg in led_messages:
                self._send_single_message(msg)
                
            # Could implement frame compression here:
            # - Combine multiple grid updates into single message
            # - Use delta compression for partial updates
            # - Skip updates for LEDs that haven't changed
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error sending LED batch: {e}")
    
    def _log_performance_stats(self):
        """Log performance statistics"""
        try:
            coalesce_ratio = (self._messages_coalesced / max(1, self._messages_sent)) * 100
            
            self.c_surface.log_message(
                f"📊 Message Performance: "
                f"Coalesced={self._messages_coalesced}, "
                f"Sent={self._messages_sent}, "
                f"Ratio={coalesce_ratio:.1f}%, "
                f"Dropped={self._frames_dropped}"
            )
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error logging stats: {e}")
    
    def force_flush(self):
        """Force immediate flush of all pending messages"""
        try:
            if self._flush_timer:
                self._flush_timer.cancel()
                self._flush_timer = None
            
            self._flush_messages()
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error forcing flush: {e}")
    
    def set_frame_rate(self, fps):
        """Set target frame rate"""
        try:
            self.target_fps = max(1, min(120, fps))  # Clamp 1-120fps
            self.frame_time_ms = 1000.0 / self.target_fps
            
            self.c_surface.log_message(f"🎯 Message coalescer frame rate: {self.target_fps}fps")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error setting frame rate: {e}")
    
    def get_performance_info(self):
        """Get performance information"""
        try:
            return {
                'target_fps': self.target_fps,
                'frame_time_ms': self.frame_time_ms,
                'coalesce_window_ms': self.coalesce_window_ms,
                'pending_messages': len(self._pending_messages),
                'messages_coalesced': self._messages_coalesced,
                'messages_sent': self._messages_sent,
                'frames_dropped': self._frames_dropped,
                'coalesce_ratio': (self._messages_coalesced / max(1, self._messages_sent)) * 100
            }
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error getting performance info: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup coalescer resources"""
        try:
            # Cancel any pending timers
            if self._flush_timer:
                self._flush_timer.cancel()
                self._flush_timer = None
            
            if self._frame_timer:
                self._frame_timer.cancel()
                self._frame_timer = None
            
            # Force send any remaining messages
            self.force_flush()
            
            # Clear state
            self._pending_messages.clear()
            self._last_states.clear()
            
            self.c_surface.log_message("✅ Message coalescer cleaned up")
            
        except Exception as e:
            self.c_surface.log_message(f"❌ Error cleaning up coalescer: {e}")
    
    # ========================================
    # FRAME COMPRESSION METHODS (Future)
    # ========================================
    
    def _create_grid_delta(self, command, new_grid, old_grid):
        """Create delta update for grid changes (future optimization)"""
        try:
            if not old_grid or len(new_grid) != len(old_grid):
                return new_grid  # Send full frame
            
            # Find changed positions
            changes = []
            for i, (new_val, old_val) in enumerate(zip(new_grid, old_grid)):
                if new_val != old_val:
                    changes.append((i, new_val))
            
            # If too many changes, send full frame
            if len(changes) > len(new_grid) // 2:
                return new_grid
            
            # Create delta message
            delta_payload = []
            for pos, val in changes:
                delta_payload.extend([pos, val])
            
            return delta_payload
            
        except Exception:
            return new_grid  # Fallback to full frame
    
    def _compress_led_frame(self, messages):
        """Compress multiple LED updates into single frame (future)"""
        try:
            # Group by grid type
            grids = {}
            for msg in messages:
                command = msg['command']
                if command in grids:
                    grids[command] = msg['payload']  # Keep latest
                else:
                    grids[command] = msg['payload']
            
            # Could implement:
            # - Run-length encoding for sparse grids
            # - Delta compression between frames
            # - Smart batching of related updates
            
            return list(grids.items())
            
        except Exception:
            return [(msg['command'], msg['payload']) for msg in messages]
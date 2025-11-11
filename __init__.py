# __init__.py - Entry Point
from .PushClone import PushClone
import logging

# Get the logger for the script
logger = logging.getLogger(__name__)

def create_instance(c_instance):
    """
    Entry point for Live to create our control surface instance.
    c_instance: Live's C++ instance for communication
    """
    # Log a version number to help verify script updates
    logger.info("--- PushClone Script v1.0.6 (2025-11-11) Loading ---")
    return PushClone(c_instance)

def get_capabilities():
    """
    Declare script capabilities to Live
    """
    return {
        'ports': 1,  # Number of MIDI ports needed
        'has_drum_rack_mode': True,
        'has_keyboard_mode': True,
        'non_realtime_processing': False
    }
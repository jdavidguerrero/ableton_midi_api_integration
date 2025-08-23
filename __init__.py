# __init__.py - Entry Point (sin cambios)
from .PushClone import PushClone

def create_instance(c_instance):
    """
    Entry point for Live to create our control surface instance.
    c_instance: Live's C++ instance for communication
    """
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
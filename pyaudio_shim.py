"""
pyaudio_shim.py — PyAudio compatibility shim
=============================================
PyAudioWPatch is installed (Python 3.14 compatible fork of PyAudio).
SpeechRecognition does `import pyaudio` internally, so we register
PyAudioWPatch under the 'pyaudio' name before SR is imported anywhere.

This module is imported first in voice.py to fix the compatibility.
"""
import sys

# Only patch if pyaudio isn't already available natively
try:
    import pyaudio  # noqa — already works
except ImportError:
    try:
        import pyaudiowpatch as _paw
        sys.modules['pyaudio'] = _paw
    except ImportError:
        pass  # Neither available — voice will show a graceful error

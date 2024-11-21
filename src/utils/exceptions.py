class TTSError(Exception):
    """Base class for TTS errors"""
    pass

class AudioRecordingError(TTSError):
    """Error in audio recording"""
    pass

class AudioProcessingError(TTSError):
    """Error in audio processing"""
    pass

class SyllableNotFoundError(TTSError):
    """Required syllable not found"""
    pass 
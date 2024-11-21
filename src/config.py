from dataclasses import dataclass

@dataclass
class TTSConfig:
    """Configuration for TTS system"""
    sample_rate: int = 44100
    recording_duration: float = 1.5
    silence_threshold: float = -35
    min_silence_duration: float = 0.2
    crossfade_duration: float = 0.02
    gap_duration: float = 0.3
    
    # Audio processing
    use_noise_reduction: bool = True
    use_pitch_correction: bool = False
    
    # Performance
    use_caching: bool = True
    cache_size: int = 1000
    
    # Paths
    dataset_dir: str = "dataset"
    words_file: str = "words.txt" 
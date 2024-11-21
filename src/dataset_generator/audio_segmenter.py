import librosa
import numpy as np
import soundfile as sf

class AudioSegmenter:
    def __init__(self, min_silence_duration=0.2, silence_threshold=-35):
        self.min_silence_duration = min_silence_duration
        self.silence_threshold = silence_threshold
        
    def improve_audio_quality(self, audio, sr):
        """Enhance audio quality"""
        # Noise reduction
        audio_denoised = librosa.effects.preemphasis(audio)
        
        # Remove DC offset
        audio_centered = audio_denoised - np.mean(audio_denoised)
        
        # Trim silence
        audio_trimmed, _ = librosa.effects.trim(
            audio_centered,
            top_db=20,
            frame_length=512,
            hop_length=128
        )
        
        return audio_trimmed
        
    def segment_audio(self, audio, sr):
        """Split audio array into segments based on silence"""
        # First, ensure audio is mono and improve quality
        if len(audio.shape) > 1:
            audio = audio[:, 0]
            
        # Improve audio quality
        audio = self.improve_audio_quality(audio, sr)
        
        # Get silence intervals for segmentation
        intervals = librosa.effects.split(
            audio,
            top_db=self.silence_threshold,
            frame_length=1024,
            hop_length=256
        )
        
        segments = []
        timestamps = []
        
        # If no intervals found, use the entire audio
        if len(intervals) == 0 and len(audio) > 0:
            segments.append(audio)
            timestamps.append({
                "start": 0,
                "end": len(audio) / sr
            })
        else:
            for i, interval in enumerate(intervals):
                start, end = interval
                segment = audio[start:end]
                
                # Only add segments that are long enough
                if len(segment) > self.min_silence_duration * sr:
                    # Additional quality improvement for each segment
                    segment = self.improve_audio_quality(segment, sr)
                    
                    if len(segment) > 0:
                        segments.append(segment)
                        timestamps.append({
                            "start": float(start) / sr,
                            "end": float(end) / sr
                        })
                
        return segments, sr, timestamps
    
    def save_segment(self, segment, sr, filepath):
        """Save a single audio segment"""
        if len(segment) > 0:
            # Final quality improvement before saving
            segment = self.improve_audio_quality(segment, sr)
            sf.write(filepath, segment, sr)
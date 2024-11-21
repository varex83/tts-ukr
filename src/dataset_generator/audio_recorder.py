import sounddevice as sd
import numpy as np
from datetime import datetime

class AudioRecorder:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def record(self, duration):
        """Record audio and return the numpy array directly"""
        print("Recording...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1
        )
        sd.wait()
        print("Recording complete")
        return audio, self.sample_rate 
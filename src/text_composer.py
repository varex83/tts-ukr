import argparse
from pathlib import Path
import random
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime
from src.dataset_generator.syllable_extractor import split_into_syllables
from functools import lru_cache

class TextComposer:
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = Path(dataset_dir)
        self.available_words = self._load_available_words()
        self.syllables_map = self._load_syllables_map()
        self.available_syllables = self._load_available_syllables()
        
        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_available_words(self):
        """Load words that have recordings"""
        available = {}
        for path in self.dataset_dir.iterdir():
            if path.is_dir():
                recording = path / "recording.wav"
                if recording.exists():
                    available[path.name] = path
        return available
    
    def _load_syllables_map(self):
        """Load syllables mapping from the syllables file"""
        syllables_file = self.dataset_dir / "unique_syllables.txt"
        syllables_map = {}
        
        if syllables_file.exists():
            with open(syllables_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        word = parts[0]
                        syllables = parts[1:]
                        syllables_map[word] = syllables
        return syllables_map
    
    def _load_available_syllables(self):
        """Create a map of available syllables from recorded syllables"""
        available_syllables = {}
        
        for path in self.dataset_dir.iterdir():
            if not path.is_dir():
                continue
                
            recording = path / "recording.wav"
            if recording.exists():
                syllable = path.name
                if syllable not in available_syllables:
                    available_syllables[syllable] = []
                available_syllables[syllable].append(recording)
        
        print("\nAvailable syllables:")
        for syllable, recordings in available_syllables.items():
            print(f"  {syllable}: {len(recordings)} recordings")
        
        return available_syllables
    
    def _crossfade(self, audio1, audio2, overlap_duration=0.02):
        """Apply crossfade between two audio segments"""
        if len(audio1) == 0 or len(audio2) == 0:
            return np.concatenate([audio1, audio2])
            
        # Calculate overlap in samples
        overlap_samples = int(44100 * overlap_duration)  # Assuming 44100 Hz
        
        if overlap_samples > len(audio1) or overlap_samples > len(audio2):
            overlap_samples = min(len(audio1), len(audio2)) // 2
        
        # Create fade curves
        fade_out = np.linspace(1.0, 0.0, overlap_samples)
        fade_in = np.linspace(0.0, 1.0, overlap_samples)
        
        # Apply crossfade
        audio1_end = audio1[:-overlap_samples] if len(audio1) > overlap_samples else np.array([])
        overlap1 = audio1[-overlap_samples:] if len(audio1) > overlap_samples else audio1
        overlap2 = audio2[:overlap_samples] if len(audio2) > overlap_samples else audio2
        audio2_rest = audio2[overlap_samples:] if len(audio2) > overlap_samples else np.array([])
        
        # Combine with crossfade
        overlap_mix = (overlap1 * fade_out + overlap2 * fade_in)
        
        return np.concatenate([audio1_end, overlap_mix, audio2_rest])
    
    @lru_cache(maxsize=1000)
    def _get_syllable_audio(self, syllable_path):
        """Cache frequently used syllable recordings"""
        audio, sr = sf.read(str(syllable_path))
        return audio, sr
    
    def get_word_audio(self, word):
        """Get the audio for a word, either as a whole or composed from syllables"""
        # Try to get the complete word recording first
        if word in self.available_words:
            word_dir = self.available_words[word]
            recording = word_dir / "recording.wav"
            if recording.exists():
                return self._get_syllable_audio(recording)
        
        # If word not available, try to compose it from syllables
        if word not in self.syllables_map:
            syllables = split_into_syllables(word)
        else:
            syllables = self.syllables_map[word]
        
        # Try to compose from syllables
        combined_audio = None
        sample_rate = None
        missing_syllables = []
        
        print(f"Trying to compose '{word}' from syllables: {' '.join(syllables)}")
        
        for syllable in syllables:
            if syllable in self.available_syllables:
                recording = random.choice(self.available_syllables[syllable])
                audio, sr = sf.read(str(recording))
                
                if sample_rate is None:
                    sample_rate = sr
                
                # Apply crossfade when combining syllables
                if combined_audio is None:
                    combined_audio = audio
                else:
                    combined_audio = self._crossfade(combined_audio, audio)
            else:
                missing_syllables.append(syllable)
        
        if missing_syllables:
            print(f"Missing syllables: {', '.join(missing_syllables)}")
            return None
        
        if combined_audio is not None and sample_rate:
            return combined_audio, sample_rate
        
        return None
    
    def play_text(self, text, gap_seconds=0.3, save_output=False):
        """Play the audio for the given text and optionally save it"""
        words = text.split()
        combined_audio = None
        sample_rate = None
        
        for i, word in enumerate(words):
            result = self.get_word_audio(word)
            if result is not None:
                audio, sr = result
                if sample_rate is None:
                    sample_rate = sr
                
                # Add pre-word gap (except for first word)
                if combined_audio is not None:
                    gap = np.zeros(int(sr * gap_seconds))
                    combined_audio = np.concatenate([combined_audio, gap])
                    # Apply crossfade between words
                    combined_audio = self._crossfade(combined_audio, audio, overlap_duration=0.01)
                else:
                    combined_audio = audio
                
                # Add post-word gap for punctuation or sentence end
                if i < len(words) - 1:
                    if word.endswith(('.', '!', '?', ',')):
                        gap = np.zeros(int(sr * gap_seconds * 2))
                        combined_audio = np.concatenate([combined_audio, gap])
            else:
                print(f"Warning: Cannot play word '{word}' - no recording or syllables available")
        
        if combined_audio is not None and sample_rate:
            # Save the output if requested
            if save_output:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.output_dir / f"tts_output_{timestamp}.wav"
                sf.write(output_path, combined_audio, sample_rate)
                print(f"\nOutput saved to: {output_path}")
            
            # Play the audio
            sd.play(combined_audio, sample_rate)
            sd.wait()
            return True
        
        return False

def main():
    parser = argparse.ArgumentParser(description='Compose and play text using recorded words')
    parser.add_argument('--words', type=int, default=5, help='Number of words to compose')
    parser.add_argument('--text', type=str, help='Specific text to play')
    parser.add_argument('--gap', type=float, default=0.3, help='Gap between words in seconds')
    parser.add_argument('--all-words', action='store_true', 
                       help='Use all known words, not just recorded ones')
    parser.add_argument('--save', action='store_true',
                       help='Save the output audio to a file')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Directory to save output files')
    args = parser.parse_args()
    
    composer = TextComposer()
    composer.output_dir = Path(args.output_dir)
    composer.output_dir.mkdir(exist_ok=True)
    
    if args.text:
        text = args.text
        print(f"\nPlaying text: {text}")
    else:
        text = composer.compose_text(args.words, not args.all_words)
        print(f"\nComposed text: {text}")
    
    print("\nPlaying audio...")
    if not composer.play_text(text, args.gap, save_output=args.save):
        print("Failed to play audio. Make sure you have recordings for the words.")

if __name__ == "__main__":
    main() 
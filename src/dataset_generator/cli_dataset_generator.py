import argparse
from pathlib import Path
from .audio_recorder import AudioRecorder
from .audio_segmenter import AudioSegmenter
from datetime import datetime
import soundfile as sf

def load_words(file_path):
    """Load and split words from file, handling spaces, newlines, and hyphens as separators"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Replace hyphens with spaces before splitting
        content = content.replace('-', ' ')
        words = [word.strip() for word in content.replace('\n', ' ').split(' ')]
        return [word for word in words if word]

def get_recorded_words(output_dir):
    """Get list of words that have already been recorded"""
    output_path = Path(output_dir)
    return {path.name for path in output_dir.iterdir() if (path / "recording.wav").exists()}

def main():
    parser = argparse.ArgumentParser(description='Record Ukrainian words for TTS dataset')
    parser.add_argument('--words', type=str, help='File containing words to record')
    parser.add_argument('--output', type=str, default='dataset', help='Output directory')
    parser.add_argument('--duration', type=float, default=1.5, help='Recording duration in seconds')
    parser.add_argument('--skip-recorded', action='store_true', 
                       help='Skip words that have already been recorded')
    parser.add_argument('--syllables-mode', action='store_true',
                       help='Record syllables instead of complete words')
    args = parser.parse_args()
    
    recorder = AudioRecorder()
    segmenter = AudioSegmenter()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    if args.words:
        # In syllables mode, each line contains: word syllable1 syllable2 ...
        # We want to record the syllables, not the complete word
        if args.syllables_mode:
            syllables_to_record = set()
            with open(args.words, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        syllables_to_record.update(parts[1:])  # Skip the word itself
            words = sorted(syllables_to_record)
        else:
            words = load_words(args.words)
            
        recorded_words = get_recorded_words(output_dir) if args.skip_recorded else set()
        
        if args.skip_recorded:
            words_to_record = [w for w in words if w not in recorded_words]
            skipped = len(words) - len(words_to_record)
            if skipped > 0:
                print(f"\nSkipping {skipped} already recorded {'syllables' if args.syllables_mode else 'words'}.")
            words = words_to_record
        
        total_words = len(words)
        
        if total_words == 0:
            print(f"No new {'syllables' if args.syllables_mode else 'words'} to record!")
            return
            
        print(f"\nLoaded {total_words} {'syllables' if args.syllables_mode else 'words'} to record.")
        print("Press Ctrl+C at any time to save progress and exit.")
        
        try:
            for idx, word in enumerate(words, 1):
                print(f"\n[{idx}/{total_words}] Please pronounce: {word}")
                print("Press Enter when ready to record, or 's' to skip...")
                
                user_input = input().strip().lower()
                if user_input == 's':
                    print(f"Skipped: {word}")
                    continue
                
                # Record audio
                audio, sr = recorder.record(args.duration)
                
                # Create word directory
                word_dir = output_dir / word
                word_dir.mkdir(exist_ok=True)
                
                # Save raw recording
                raw_path = word_dir / "raw.wav"
                sf.write(raw_path, audio, sr)
                
                # Segment and save the best segment
                segments, sr, timestamps = segmenter.segment_audio(audio, sr)
                
                # Save the first clear segment as the main recording
                if segments:
                    recording_path = word_dir / "recording.wav"
                    segmenter.save_segment(segments[0], sr, recording_path)
                    print(f"✓ Recorded and saved: {word}")
                else:
                    print(f"! No clear recording detected for: {word}")
                    # Keep raw recording even if segmentation failed
                
        except KeyboardInterrupt:
            print("\n\nRecording session interrupted. Progress has been saved.")
            print(f"Recorded {idx-1} out of {total_words} {'syllables' if args.syllables_mode else 'words'}.")
            return
            
        print(f"\nAll {'syllables' if args.syllables_mode else 'words'} have been recorded successfully!")

    else:
        print("Free recording mode: Press Ctrl+C to stop")
        try:
            while True:
                input("Press Enter to start recording...")
                audio, sr = recorder.record(args.duration)
                segments, sr, timestamps = segmenter.segment_audio(audio, sr)

                if segments:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    recording_dir = output_dir / f"recording_{timestamp}"
                    recording_dir.mkdir(exist_ok=True)
                    
                    # Save raw recording
                    raw_path = recording_dir / "raw.wav"
                    sf.write(raw_path, audio, sr)
                    
                    # Save segmented recording
                    recording_path = recording_dir / "recording.wav"
                    segmenter.save_segment(segments[0], sr, recording_path)
                    print("✓ Recording saved")

        except KeyboardInterrupt:
            print("\nRecording session ended")

if __name__ == "__main__":
    main()
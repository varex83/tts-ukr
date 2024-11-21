import re
from pathlib import Path

def is_vowel(char):
    """Check if character is a Ukrainian vowel"""
    vowels = set('аеєиіїоуюя')
    return char.lower() in vowels

def split_into_syllables(word):
    """
    Split Ukrainian word into syllables using basic rules:
    1. Each syllable must contain exactly one vowel
    2. Consonants between vowels are distributed according to Ukrainian pronunciation rules
    3. Single consonant between vowels goes with the following vowel
    4. Multiple consonants are split according to pronunciation rules
    5. Apostrophe (') and soft sign (ь) are treated as part of the previous consonant
    """
    # Preprocess: join apostrophe and soft sign with previous letter
    word = word.lower()
    processed_word = ""
    skip_next = False
    
    for i, char in enumerate(word):
        if skip_next:
            skip_next = False
            continue
        if i < len(word) - 1 and word[i + 1] in "'ь":
            processed_word += char + word[i + 1]
            skip_next = True
        else:
            processed_word += char
    
    word = processed_word
    syllables = []
    current = ""
    
    # Handle single-letter words
    if len(word) <= 1:
        return [word]
    
    # Find all vowels positions (ignoring apostrophes and soft sign)
    vowel_positions = []
    for i, char in enumerate(word):
        if is_vowel(char):
            vowel_positions.append(i)
    
    # If no vowels found, return the whole word
    if not vowel_positions:
        return [word]
    
    # Process each segment between vowels
    for i, vowel_pos in enumerate(vowel_positions):
        # Handle the part before the first vowel
        if i == 0:
            if vowel_pos > 0:
                current = word[:vowel_pos]
            current += word[vowel_pos]
            
        # Handle parts between vowels
        else:
            prev_vowel_pos = vowel_positions[i-1]
            consonants = word[prev_vowel_pos + 1:vowel_pos]
            
            # If there are consonants between vowels
            if consonants:
                # If only one consonant (or consonant with modifier), it goes with the following vowel
                if len(consonants.replace("'", "").replace("ь", "")) == 1:
                    syllables.append(current)
                    current = consonants + word[vowel_pos]
                # If multiple consonants, split them
                else:
                    # Find split point (before modifiers if present)
                    base_consonants = consonants.replace("'", "").replace("ь", "")
                    split_point = len(base_consonants) // 2
                    
                    # Adjust split point to keep modifiers with their consonants
                    actual_split = 0
                    consonant_count = 0
                    for j, c in enumerate(consonants):
                        if c not in "'ь":
                            consonant_count += 1
                        if consonant_count > split_point:
                            actual_split = j
                            break
                    
                    syllables.append(current + consonants[:actual_split])
                    current = consonants[actual_split:] + word[vowel_pos]
            else:
                syllables.append(current)
                current = word[vowel_pos]
        
        # Handle the last syllable
        if i == len(vowel_positions) - 1:
            remaining = word[vowel_pos + 1:]
            current += remaining
            syllables.append(current)
    
    # Handle special cases
    result = []
    for syl in syllables:
        if syl:
            result.append(syl)
    
    return result if result else [word]

def process_text_file(input_file, output_file):
    """Process text file and extract unique syllables"""
    
    # Read input file and split by whitespace and hyphens
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
        # Replace hyphens with spaces before splitting
        text = text.replace('-', ' ')
    
    # Split into words, clean and remove duplicates
    words = [word.strip(".,!?:;()[]{}\"'") for word in text.split()]
    words = [word.lower() for word in words if word and all(c.isalpha() or c in "'ь" for c in word)]
    words = sorted(set(words))  # Get unique words and sort them
    
    # Save words with their syllables (simple format)
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in words:
            syllables = split_into_syllables(word)
            f.write(f"{word} {' '.join(syllables)}\n")

def main():
    input_file = "words.txt"
    output_file = "dataset/unique_syllables.txt"
    
    Path("dataset").mkdir(exist_ok=True)
    
    print("Extracting syllables...")
    process_text_file(input_file, output_file)
    print(f"\nSyllables saved to: {output_file}")

if __name__ == "__main__":
    main() 
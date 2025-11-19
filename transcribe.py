#!/usr/bin/env python3
"""
Continuous context-aware transcription with anti-repetition safeguards
Words appear progressively with conversation context for accuracy
"""

import subprocess
import soundfile as sf
import numpy as np
from scipy import signal
from faster_whisper import WhisperModel
import sys

print('')
print('='*60)
print('  CONTINUOUS VOICE TRANSCRIPTION')
print('  (Robust with anti-repetition protection)')
print('='*60)
print('')

# Load model
print('Loading model...')
model = WhisperModel('tiny', device='cpu', compute_type='int8')

print('')
print('Ready! Speak naturally - transcription will flow continuously.')
print('Press Ctrl+C to stop')
print('')
print('-' * 60)
print('')

# Context management
context_buffer = []  # Store recent transcriptions for context
MAX_CONTEXT_CHUNKS = 4  # Keep last ~20-30 seconds of context
CHUNK_DURATION = 5  # Record in 5-second chunks
MIN_AUDIO_ENERGY = 0.001  # Minimum audio energy to consider as speech
MIN_WORDS = 2  # Minimum words to consider valid transcription

segment_num = 0
first_output = True
last_text = ""

def is_repetition(new_text, previous_text, threshold=0.7):
    """
    Check if new text is mostly a repetition of previous text
    Returns True if it's a repetition (should be skipped)
    """
    if not previous_text or not new_text:
        return False
    
    # Normalize for comparison
    new_words = new_text.lower().split()
    prev_words = previous_text.lower().split()
    
    if len(new_words) < 3:
        return False
    
    # Check if new text is just repeating the end of previous text
    # Get last N words from previous text
    check_length = min(len(prev_words), 10)
    prev_end = ' '.join(prev_words[-check_length:])
    
    # Check if new text starts with or is similar to previous ending
    new_start = ' '.join(new_words[:check_length])
    
    # Simple similarity check
    matching_words = sum(1 for word in new_words if word in prev_end.split())
    similarity = matching_words / len(new_words) if new_words else 0
    
    return similarity > threshold

def has_sufficient_audio(audio_data, threshold=MIN_AUDIO_ENERGY):
    """
    Check if audio has sufficient energy to likely contain speech
    """
    rms = np.sqrt(np.mean(audio_data**2))
    max_amp = np.max(np.abs(audio_data))
    
    # Check both RMS and max amplitude
    return rms > threshold and max_amp > threshold * 10

try:
    while True:
        segment_num += 1

        # Record
        audio_file = f'/tmp/seg_{segment_num}.wav'

        # Silent recording (no progress messages to keep output clean)
        subprocess.run(
            ['arecord', '-D', 'plughw:0,0', '-f', 'S16_LE',
             '-r', '48000', '-c', '2', '-d', str(CHUNK_DURATION), audio_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Process audio
        audio, sr = sf.read(audio_file)
        audio = audio[:, 0]  # Use LEFT channel only
        audio = signal.resample(audio, int(len(audio) * 16000 / sr))
        
        # Check audio energy BEFORE applying gain
        if not has_sufficient_audio(audio):
            # Skip transcription for silence
            import os
            try:
                os.remove(audio_file)
            except:
                pass
            continue
        
        audio = audio * 30.0  # 30x gain
        audio = np.clip(audio, -1.0, 1.0)

        proc_file = f'/tmp/proc_{segment_num}.wav'
        sf.write(proc_file, audio, 16000)

        # Transcribe WITHOUT initial_prompt to prevent hallucinations
        segments, info = model.transcribe(
            proc_file,
            language='en',
            beam_size=5,
            vad_filter=True,  # Enable VAD to filter silence
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Minimum silence duration
                threshold=0.5  # VAD threshold
            ),
            temperature=0.0
        )

        text = ' '.join([s.text for s in segments]).strip()

        # Validation checks
        if text:
            word_count = len(text.split())
            
            # Skip if too few words (likely noise)
            if word_count < MIN_WORDS:
                import os
                try:
                    os.remove(audio_file)
                    os.remove(proc_file)
                except:
                    pass
                continue
            
            # Skip if it's a repetition of the last transcription
            if is_repetition(text, last_text):
                # Detected repetition loop - skip this output
                import os
                try:
                    os.remove(audio_file)
                    os.remove(proc_file)
                except:
                    pass
                continue
            
            # Valid transcription - display it
            context_buffer.append(text)
            if len(context_buffer) > MAX_CONTEXT_CHUNKS:
                context_buffer.pop(0)

            # Progressive display
            if not first_output:
                # Add space before new text for natural flow
                print(' ' + text, end='', flush=True)
            else:
                print(text, end='', flush=True)
                first_output = False
            
            # Update last text for repetition detection
            last_text = text

        # Cleanup
        import os
        try:
            os.remove(audio_file)
            os.remove(proc_file)
        except:
            pass

except KeyboardInterrupt:
    print('')
    print('')
    print('-' * 60)
    print('Transcription stopped')
    print('='*60)
    sys.exit(0)

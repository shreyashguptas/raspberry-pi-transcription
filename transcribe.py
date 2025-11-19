#!/usr/bin/env python3
"""
Simple working transcription - using EXACT method that worked before
"""

import subprocess
import soundfile as sf
import numpy as np
from scipy import signal
from faster_whisper import WhisperModel

print('')
print('='*60)
print('  VOICE TRANSCRIPTION')
print('='*60)
print('')

# Load model
print('Loading model...')
model = WhisperModel('tiny', device='cpu', compute_type='int8')

print('')
print('Ready! Starting continuous transcription...')
print('Press Ctrl+C to stop')
print('')

segment_num = 0

try:
    while True:
        segment_num += 1

        # Record
        audio_file = f'/tmp/seg_{segment_num}.wav'

        print(f'[{segment_num}] Recording 5s...', end=' ', flush=True)

        subprocess.run(
            ['arecord', '-D', 'plughw:0,0', '-f', 'S16_LE',
             '-r', '48000', '-c', '2', '-d', '5', audio_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Process - EXACT method that worked
        audio, sr = sf.read(audio_file)
        audio = audio[:, 0]  # Use LEFT channel only
        audio = signal.resample(audio, int(len(audio) * 16000 / sr))  # 48k->16k
        audio = audio * 30.0  # 30x gain
        audio = np.clip(audio, -1.0, 1.0)

        proc_file = f'/tmp/proc_{segment_num}.wav'
        sf.write(proc_file, audio, 16000)

        # Transcribe - EXACT parameters that worked
        segments, info = model.transcribe(
            proc_file,
            language='en',
            beam_size=5,
            vad_filter=False,
            temperature=0.0
        )

        text = ' '.join([s.text for s in segments]).strip()

        # Display
        if text:
            print(f'" {text}"')
        else:
            print('(silence)')

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
    print('='*60)
    print('Stopped')
    print('='*60)

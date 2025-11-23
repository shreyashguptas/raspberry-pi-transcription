#!/usr/bin/env python3
"""
Interactive Hailo Whisper Transcription for Raspberry Pi 5 with Hailo-8L
Records audio and performs real-time transcription using hardware acceleration.
"""

import os
import sys
import time
import subprocess
import tempfile
import signal
import numpy as np
from simple_term_menu import TerminalMenu

# Add Hailo examples to path
hailo_path = os.path.expanduser("~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition")
if os.path.exists(hailo_path):
    sys.path.insert(0, hailo_path)

try:
    # Import Hailo modules
    from app.hailo_whisper_pipeline import HailoWhisperPipeline
    from common.audio_utils import load_audio
    from common.preprocessing import preprocess
    from common.postprocessing import clean_transcription as postprocess_text
except ImportError as e:
    print(f"❌ Error importing Hailo modules: {e}")
    print("\nPlease ensure you've run setup.py in the Hailo repository:")
    print("  cd ~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition")
    print("  python3 setup.py")
    sys.exit(1)

# Configuration
class Config:
    def __init__(self):
        # Hailo settings
        self.hw_arch = 'hailo8l'
        self.model_variant = 'base'  # 'tiny' for 10s chunks, 'base' for 5s chunks

        # Audio settings
        self.device = 'plughw:0,0'
        self.sample_rate = 48000
        self.channels = 2

        # Paths (h8l is the directory name for hailo8l)
        self.hef_dir = os.path.join(hailo_path, 'app', 'hefs', 'h8l')
        self.decoder_dir = os.path.join(hailo_path, 'app', 'decoder_assets')

    @property
    def chunk_duration(self):
        return 10 if self.model_variant == 'tiny' else 5

    def display_summary(self):
        """Display configuration summary"""
        print('')
        print('='*70)
        print('  CONFIGURATION SUMMARY')
        print('='*70)
        print('')
        print('HAILO SETTINGS:')
        print(f'  Model Variant: {self.model_variant}')
        print(f'  Hardware: {self.hw_arch} (Hailo-8L)')
        print(f'  Chunk Duration: {self.chunk_duration}s')
        print('')
        print('AUDIO SETTINGS:')
        print(f'  Device: {self.device}')
        print(f'  Sample Rate: {self.sample_rate} Hz')
        print(f'  Channels: {self.channels} (stereo)')
        print('='*70)
        print('')

# Global variable for clean shutdown
running = True
pipeline = None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\nStopping transcription...")
    running = False
    if pipeline:
        pipeline.stop()
    sys.exit(0)

def record_audio(duration=10, device='plughw:0,0', sample_rate=48000, channels=2):
    """Record audio from microphone and save to temp file"""
    # Create temp file for audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        audio_file = tmp.name

    # Record using arecord
    cmd = [
        'arecord',
        '-D', device,
        '-f', 'S16_LE',
        '-r', str(sample_rate),
        '-c', str(channels),
        '-d', str(duration),
        audio_file
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration+5)
        if result.returncode != 0:
            print(f"Recording error: {result.stderr}")
            return None

        # Verify file exists and has content
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
            return audio_file
        else:
            print("Recording failed - no audio data")
            return None

    except subprocess.TimeoutExpired:
        print("Recording timeout")
        return None
    except Exception as e:
        print(f"Recording error: {e}")
        return None

def format_transcription(text):
    """Format transcription text"""
    if not text:
        return ""

    # Apply Hailo's postprocessing
    text = postprocess_text(text)

    # Clean up whitespace
    text = ' '.join(text.split())

    return text.strip()

def show_welcome():
    """Display welcome screen"""
    print('')
    print('='*70)
    print('  HAILO WHISPER INTERACTIVE TRANSCRIPTION')
    print('  Hardware-accelerated real-time speech-to-text on Raspberry Pi 5')
    print('='*70)
    print('')

def menu_preset(config):
    """Show preset configuration menu"""
    options = [
        "Fastest (tiny model, 10s chunks)",
        "Balanced (base model, 5s chunks) [Recommended]",
        "Custom (configure all options)"
    ]

    menu = TerminalMenu(
        options,
        title="Select Configuration Preset:",
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()

    if choice == 0:  # Fastest
        config.model_variant = 'tiny'
        return False  # Skip custom menus
    elif choice == 1:  # Balanced (default)
        config.model_variant = 'base'
        return False
    else:  # Custom
        return True

def menu_model_variant(config):
    """Model variant selection menu"""
    options = [
        "tiny (10s chunks, fastest)",
        "base (5s chunks, better quality) [Recommended]"
    ]

    variant_map = ['tiny', 'base']
    current_idx = variant_map.index(config.model_variant) if config.model_variant in variant_map else 1

    menu = TerminalMenu(
        options,
        title="Select Hailo Model Variant:",
        cursor_index=current_idx,
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()
    config.model_variant = variant_map[choice]

def menu_audio_device(config):
    """Audio device selection menu"""
    # Get available audio devices
    try:
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        # Parse output for card numbers
        print("\nAvailable audio devices:")
        print(result.stdout)
    except:
        pass

    options = [
        f"plughw:0,0 (default) [Current: {config.device}]",
        "Custom device string"
    ]

    menu = TerminalMenu(
        options,
        title="Select Audio Device:",
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()

    if choice == 1:  # Custom
        print("\nEnter custom device string (e.g., plughw:1,0): ", end='')
        custom_device = input().strip()
        if custom_device:
            config.device = custom_device

def main():
    """Main transcription loop"""
    global pipeline

    # Show welcome screen
    show_welcome()

    # Create config and show menu
    config = Config()

    # Show preset menu
    show_custom = menu_preset(config)

    # If custom selected, show detailed menus
    if show_custom:
        menu_model_variant(config)
        menu_audio_device(config)

    # Display configuration summary
    config.display_summary()

    input("Press Enter to start transcription with these settings...")

    print("\n" + "="*60)
    print("  HAILO WHISPER TRANSCRIPTION")
    print("  Model: {} | Hardware: {}".format(config.model_variant, config.hw_arch))
    print("="*60)

    # Verify Hailo HAT
    try:
        result = subprocess.run(['hailortcli', 'fw-control', 'identify'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("\n⚠️  Warning: Hailo device check failed")
            print("Continuing anyway...")
    except:
        print("\n⚠️  Warning: Could not verify Hailo device")

    # Verify audio device
    print("\nChecking audio device...")
    result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
    if config.device.split(':')[1] not in result.stdout:
        print("⚠️  Warning: Audio device may not be available")
    else:
        print("✓ Audio device found")

    # Test recording
    print("\nTesting audio recording...")
    test_file = record_audio(1, config.device, config.sample_rate, config.channels)
    if test_file:
        os.remove(test_file)
        print("✓ Audio recording works")
    else:
        print("❌ Audio recording failed")
        return

    # Initialize pipeline
    print("\nInitializing Hailo pipeline...")
    try:
        # Construct HEF paths (files are in model-specific subdirectories)
        # Note: tiny model has "15dB" in name, base model doesn't
        if config.model_variant == 'tiny':
            encoder_hef = f"{config.model_variant}-whisper-encoder-{config.chunk_duration}s_15dB_h8l.hef"
        else:  # base model
            encoder_hef = f"{config.model_variant}-whisper-encoder-{config.chunk_duration}s_h8l.hef"

        decoder_hef = f"{config.model_variant}-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"

        encoder_path = os.path.join(config.hef_dir, config.model_variant, encoder_hef)
        decoder_path = os.path.join(config.hef_dir, config.model_variant, decoder_hef)

        # Verify files exist
        if not os.path.exists(encoder_path):
            print(f"❌ Encoder HEF not found: {encoder_path}")
            return
        if not os.path.exists(decoder_path):
            print(f"❌ Decoder HEF not found: {decoder_path}")
            return

        # Create pipeline
        pipeline = HailoWhisperPipeline(
            encoder_model_path=encoder_path,
            decoder_model_path=decoder_path,
            variant=config.model_variant,
            host="arm64"
        )
        print("✓ Pipeline initialized")

    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return

    # Main transcription loop
    print("\n" + "="*60)
    print("  TRANSCRIPTION ACTIVE")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")

    signal.signal(signal.SIGINT, signal_handler)
    recording_num = 0

    while running:
        recording_num += 1

        # Record audio
        print(f"\n[{recording_num}] Recording {config.chunk_duration}s...", end='', flush=True)
        start_time = time.time()
        audio_file = record_audio(config.chunk_duration, config.device, config.sample_rate, config.channels)
        record_duration = time.time() - start_time

        if not audio_file:
            print(" ❌ FAILED")
            time.sleep(1)
            continue

        print(f" ✓ ({record_duration:.1f}s)", flush=True)

        try:
            # Load audio (handles conversion to 16kHz mono)
            print(f"[{recording_num}] Processing...", end='', flush=True)
            audio = load_audio(audio_file)

            # Generate mel spectrograms
            mel_spectrograms = preprocess(
                audio,
                is_nhwc=True,
                chunk_length=config.chunk_duration,
                chunk_offset=0
            )

            if not mel_spectrograms:
                print(" ⚠️  No audio")
                continue

            # Process through pipeline
            for i, mel in enumerate(mel_spectrograms):
                # Send mel directly as-is, matching official implementation
                pipeline.send_data(mel)
                time.sleep(0.1)

                # Get transcription (blocks until result available)
                transcription = pipeline.get_transcription()

                if transcription:
                    text = format_transcription(transcription)
                    if text:
                        print(f" ✓\n📝 {text}", flush=True)
                    else:
                        print(" [silence]", flush=True)
                else:
                    print(" [no transcription]", flush=True)

        except Exception as e:
            print(f"Processing error: {e}")

        finally:
            # Clean up temp file
            try:
                os.remove(audio_file)
            except:
                pass

    # Cleanup
    if pipeline:
        pipeline.stop()
    print("\n✓ Transcription stopped")

if __name__ == "__main__":
    main()
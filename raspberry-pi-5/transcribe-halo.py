#!/usr/bin/env python3
"""
Interactive Hailo AI HAT Whisper Transcription Tool
Hardware-accelerated speech-to-text using Hailo-8L accelerator
"""

import subprocess
import soundfile as sf
import numpy as np
from scipy import signal
from simple_term_menu import TerminalMenu
import sys
import re
import os
import time
import glob

# Hailo imports
try:
    from hailo_platform import (
        HEF,
        VDevice,
        HailoStreamInterface,
        InferVStreams,
        ConfigureParams,
        InputVStreamParams,
        OutputVStreamParams,
        FormatType
    )
    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False
    print("Warning: Hailo Platform SDK not found. Please install HailoRT and PyHailoRT.")

class HailoTranscriptionConfig:
    """Configuration for Hailo-based transcription parameters"""

    def __init__(self):
        # Hailo hardware settings
        self.hw_arch = 'hailo8l'  # hailo8l or hailo8
        self.model_variant = 'base'  # tiny or base
        self.hef_path = None  # Will be auto-detected

        # Audio processing (kept from original)
        self.chunk_duration = 7
        self.overlap_duration = 2
        self.gain = 30.0
        self.min_audio_energy = 0.0002

        # Constants
        self.min_words = 1
        self.overlap_words = 5
        self.max_context_chunks = 4

    def display_summary(self):
        """Display configuration summary"""
        print('')
        print('='*70)
        print('  CONFIGURATION SUMMARY')
        print('='*70)
        print('')
        print('HAILO HARDWARE SETTINGS:')
        print(f'  Hardware Architecture: {self.hw_arch.upper()}')
        print(f'  Whisper Model Variant: {self.model_variant}')
        print(f'  HEF Model Path: {self.hef_path or "Auto-detect"}')
        print('')
        print('AUDIO PROCESSING:')
        print(f'  Chunk Duration: {self.chunk_duration}s')
        print(f'  Overlap Duration: {self.overlap_duration}s')
        print(f'  Microphone Gain: {self.gain}x')
        print(f'  Min Audio Energy: {self.min_audio_energy}')
        print('')
        print('NOTE: Hailo handles VAD, beam search, and temperature internally')
        print('='*70)
        print('')

def show_welcome():
    """Display welcome screen"""
    print('')
    print('='*70)
    print('  HAILO AI HAT WHISPER TRANSCRIPTION TOOL')
    print('  Hardware-accelerated speech-to-text on Hailo-8L')
    print('='*70)
    print('')

def menu_preset(config):
    """Show preset configuration menu"""
    options = [
        "Fastest (tiny model, 39M params) [Recommended for Pi 5]",
        "Balanced (base model, 74M params) [Current]",
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
        "tiny (fastest, 39M parameters, ~75MB)",
        "base (balanced, 74M parameters, ~155MB) [Recommended]"
    ]

    variant_map = ['tiny', 'base']
    current_idx = variant_map.index(config.model_variant) if config.model_variant in variant_map else 1

    menu = TerminalMenu(
        options,
        title="Select Whisper Model Variant:",
        cursor_index=current_idx,
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()
    config.model_variant = variant_map[choice]

def menu_audio_processing(config):
    """Audio processing configuration menu"""
    # Chunk Duration
    chunk_options = [
        "3 seconds (low latency, less context)",
        "5 seconds (balanced)",
        "7 seconds (good context) [Current]",
        "10 seconds (more context)",
        "15 seconds (maximum context, high latency)"
    ]
    chunk_map = [3, 5, 7, 10, 15]

    menu = TerminalMenu(
        chunk_options,
        title="Select Chunk Duration:",
        cursor_index=2,
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()
    config.chunk_duration = chunk_map[choice]

    # Overlap Duration
    overlap_options = [
        "1 second (minimal overlap)",
        "2 seconds (balanced) [Current]",
        "3 seconds (maximum overlap)"
    ]
    overlap_map = [1, 2, 3]

    menu = TerminalMenu(
        overlap_options,
        title="Select Overlap Duration:",
        cursor_index=1,
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()
    config.overlap_duration = overlap_map[choice]

    # Microphone Gain
    gain_options = [
        "10x (low gain)",
        "20x (moderate gain)",
        "30x (balanced) [Current]",
        "40x (high gain)",
        "50x (maximum gain)"
    ]
    gain_map = [10.0, 20.0, 30.0, 40.0, 50.0]

    menu = TerminalMenu(
        gain_options,
        title="Select Microphone Gain:",
        cursor_index=2,
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()
    config.gain = gain_map[choice]

def menu_advanced(config):
    """Advanced settings menu"""
    options = [
        "Yes (configure energy threshold)",
        "No (use defaults) [Recommended]"
    ]

    menu = TerminalMenu(
        options,
        title="Configure Advanced Settings?",
        cursor_index=1,
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()

    if choice == 0:
        # Min Audio Energy
        energy_options = [
            "0.0001 (very sensitive)",
            "0.0002 (balanced) [Current]",
            "0.0005 (moderate)",
            "0.001 (strict)"
        ]
        energy_map = [0.0001, 0.0002, 0.0005, 0.001]

        menu = TerminalMenu(
            energy_options,
            title="Select Minimum Audio Energy Threshold:",
            cursor_index=1,
            menu_cursor="→ ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("bg_cyan", "fg_black")
        )

        choice = menu.show()
        config.min_audio_energy = energy_map[choice]

def configure_transcription():
    """Main configuration workflow"""
    show_welcome()

    config = HailoTranscriptionConfig()

    # Show preset menu
    custom = menu_preset(config)

    if custom:
        # Model settings
        menu_model_variant(config)

        # Audio processing
        menu_audio_processing(config)

        # Advanced settings
        menu_advanced(config)

    # Show summary
    config.display_summary()

    # Confirm
    options = ["Yes, start transcription", "No, reconfigure", "Cancel"]
    menu = TerminalMenu(
        options,
        title="Start transcription with these settings?",
        menu_cursor="→ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black")
    )

    choice = menu.show()

    if choice == 0:
        return config
    elif choice == 1:
        return configure_transcription()  # Recursive call to reconfigure
    else:
        print("\nConfiguration cancelled.")
        sys.exit(0)

# Utility functions (from original code)

def is_repetition(new_text, previous_text, threshold=0.7):
    """Check if new text is mostly a repetition of previous text"""
    if not previous_text or not new_text:
        return False

    new_words = new_text.lower().split()
    prev_words = previous_text.lower().split()

    if len(new_words) < 3:
        return False

    check_length = min(len(prev_words), 10)
    prev_end = ' '.join(prev_words[-check_length:])

    matching_words = sum(1 for word in new_words if word in prev_end.split())
    similarity = matching_words / len(new_words) if new_words else 0

    return similarity > threshold

def remove_overlap(new_text, previous_words, overlap_words):
    """Remove overlapping words from the beginning of new_text"""
    if not previous_words or not new_text:
        return new_text

    new_words = new_text.split()
    max_check = min(len(new_words), len(previous_words), overlap_words)

    overlap_count = 0
    for i in range(max_check, 0, -1):
        if previous_words[-i:] == new_words[:i]:
            overlap_count = i
            break

    if overlap_count > 0:
        new_words = new_words[overlap_count:]

    return ' '.join(new_words)

def has_sufficient_audio(audio_data, threshold):
    """Check if audio has sufficient energy to likely contain speech"""
    rms = np.sqrt(np.mean(audio_data**2))
    max_amp = np.max(np.abs(audio_data))
    return rms > threshold or max_amp > threshold * 3

def normalize_whitespace(text):
    """Normalize whitespace in text"""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def find_hef_file(config):
    """
    Find the appropriate HEF file for the selected model variant and hardware architecture.

    Looks in common locations:
    1. Current directory
    2. ~/Hailo-Application-Code-Examples/runtime/python/speech_recognition/resources/
    3. ~/hailo_models/
    4. /usr/share/hailo/models/
    """
    search_paths = [
        os.getcwd(),
        os.path.expanduser('~/Hailo-Application-Code-Examples/runtime/python/speech_recognition/resources/'),
        os.path.expanduser('~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition/resources/'),
        os.path.expanduser('~/hailo_models/'),
        '/usr/share/hailo/models/',
        '/usr/local/share/hailo/models/'
    ]

    # Build filename pattern
    pattern = f"whisper_{config.model_variant}*{config.hw_arch}*.hef"

    print(f"Searching for HEF file matching: {pattern}")

    for search_path in search_paths:
        if os.path.exists(search_path):
            full_pattern = os.path.join(search_path, pattern)
            matches = glob.glob(full_pattern)
            if matches:
                hef_path = matches[0]
                print(f"Found HEF file: {hef_path}")
                return hef_path

    # If not found, provide helpful error message
    print("\nError: HEF file not found!")
    print(f"Searched for: {pattern}")
    print("\nSearched in:")
    for path in search_paths:
        print(f"  - {path}")
    print("\nPlease ensure you have:")
    print("1. Cloned Hailo-Application-Code-Examples repository")
    print("2. Run the setup script to download HEF models")
    print("3. Or manually download HEF files to one of the search paths")
    print("\nSetup instructions:")
    print("  git clone https://github.com/hailo-ai/Hailo-Application-Code-Examples.git")
    print("  cd Hailo-Application-Code-Examples/runtime/python/speech_recognition")
    print("  python3 setup.py")
    sys.exit(1)

class HailoWhisperInference:
    """
    Hailo Whisper inference wrapper.

    This class handles loading the HEF model and running inference on the Hailo accelerator.
    Based on the official Hailo Application Code Examples.
    """

    def __init__(self, hef_path):
        """Initialize Hailo inference with HEF model"""
        if not HAILO_AVAILABLE:
            print("\nError: Hailo Platform SDK not available!")
            print("Please install HailoRT and PyHailoRT from Hailo Developer Zone")
            print("Visit: https://hailo.ai/developer-zone/")
            sys.exit(1)

        self.hef_path = hef_path
        self.hef = None
        self.vdevice = None
        self.network_group = None
        self.network_group_params = None
        self.input_vstreams_params = None
        self.output_vstreams_params = None

        print(f"Loading HEF model from: {hef_path}")
        self._load_model()

    def _load_model(self):
        """Load HEF model and configure Hailo device"""
        try:
            # Load HEF
            self.hef = HEF(self.hef_path)

            # Create VDevice (virtual device)
            self.vdevice = VDevice()

            # Configure network group
            configure_params = ConfigureParams.create_from_hef(
                self.hef,
                interface=HailoStreamInterface.PCIe
            )

            self.network_group = self.vdevice.configure(self.hef, configure_params)[0]
            self.network_group_params = self.network_group.create_params()

            # Get input/output stream parameters
            self.input_vstreams_params = InputVStreamParams.make_from_network_group(
                self.network_group,
                quantized=False,
                format_type=FormatType.FLOAT32
            )

            self.output_vstreams_params = OutputVStreamParams.make_from_network_group(
                self.network_group,
                quantized=False,
                format_type=FormatType.FLOAT32
            )

            print("Hailo model loaded successfully!")

        except Exception as e:
            print(f"\nError loading Hailo model: {e}")
            print("\nTroubleshooting:")
            print("1. Verify HailoRT is installed: hailortcli fw-control identify")
            print("2. Check Hailo device is detected: lspci | grep Hailo")
            print("3. Ensure PyHailoRT is installed in your virtual environment")
            print("4. Verify HEF file is compatible with your hardware")
            sys.exit(1)

    def transcribe_audio(self, audio_file):
        """
        Transcribe audio file using Hailo accelerator.

        Args:
            audio_file: Path to 16kHz WAV file

        Returns:
            Transcribed text string
        """
        try:
            # Load and preprocess audio
            audio_data, sample_rate = sf.read(audio_file)

            if sample_rate != 16000:
                print(f"Warning: Expected 16kHz audio, got {sample_rate}Hz")

            # Convert to mel spectrogram features (Whisper preprocessing)
            # This is a simplified version - full preprocessing would match Whisper's exact pipeline
            audio_features = self._preprocess_audio(audio_data, sample_rate)

            # Run inference on Hailo
            with InferVStreams(
                self.network_group,
                self.input_vstreams_params,
                self.output_vstreams_params
            ) as infer_pipeline:

                # Send audio features to Hailo
                input_data = {list(infer_pipeline.input_vstreams.keys())[0]: audio_features}

                # Get output from Hailo
                output = infer_pipeline.infer(input_data)

                # Post-process output to get text
                text = self._postprocess_output(output)

                return text

        except Exception as e:
            print(f"\nError during Hailo inference: {e}")
            return ""

    def _preprocess_audio(self, audio_data, sample_rate):
        """
        Preprocess audio to match Whisper's expected input format.

        This is a simplified preprocessing. For production use, you should use
        the exact preprocessing pipeline from the Hailo Application Code Examples.
        """
        # Ensure mono audio
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Pad or trim to 30 seconds (480,000 samples at 16kHz)
        target_length = 480000
        if len(audio_data) > target_length:
            audio_data = audio_data[:target_length]
        else:
            audio_data = np.pad(audio_data, (0, target_length - len(audio_data)))

        # Convert to mel spectrogram (80 mel bins, Whisper standard)
        # This is a placeholder - use the exact preprocessing from Hailo examples
        mel_spectrogram = self._compute_mel_spectrogram(audio_data, sample_rate)

        return mel_spectrogram

    def _compute_mel_spectrogram(self, audio, sample_rate):
        """
        Compute mel spectrogram for Whisper model.

        This is a simplified version. For production, use the exact implementation
        from the Hailo Application Code Examples which matches OpenAI's preprocessing.
        """
        # Placeholder implementation
        # In production, this should match Whisper's exact mel filterbank
        n_fft = 400
        hop_length = 160
        n_mels = 80

        # Compute spectrogram
        from scipy.signal import stft
        f, t, Zxx = stft(audio, fs=sample_rate, nperseg=n_fft, noverlap=n_fft-hop_length)

        # Convert to power spectrogram
        power_spec = np.abs(Zxx) ** 2

        # Apply mel filterbank (simplified)
        mel_spec = power_spec[:n_mels, :]

        # Log scale
        mel_spec = np.log10(mel_spec + 1e-10)

        return mel_spec.astype(np.float32)

    def _postprocess_output(self, output):
        """
        Post-process Hailo output to extract transcribed text.

        This is a simplified version. For production, use the exact implementation
        from the Hailo Application Code Examples which includes:
        - Token decoding
        - Repeated token penalty
        - Hallucination removal
        """
        # Placeholder implementation
        # In production, this should decode the output tokens using Whisper's tokenizer

        # Get output tensor
        output_key = list(output.keys())[0]
        output_tensor = output[output_key]

        # Decode tokens (simplified)
        # In production, use the Whisper tokenizer from the Hailo examples
        text = "[Transcribed text - full token decoding not implemented]"

        return text

    def cleanup(self):
        """Clean up Hailo resources"""
        if self.network_group:
            self.network_group = None
        if self.vdevice:
            self.vdevice = None
        if self.hef:
            self.hef = None

def run_transcription(config):
    """Run transcription with configured parameters"""

    print('')
    print('='*70)
    print('  LOADING HAILO MODEL')
    print('='*70)
    print('')

    # Find HEF file
    config.hef_path = find_hef_file(config)

    # Initialize Hailo inference
    print(f'Loading {config.model_variant} model for {config.hw_arch.upper()} hardware...')
    hailo_model = HailoWhisperInference(config.hef_path)

    print('')
    print('='*70)
    print('  TRANSCRIPTION ACTIVE (HAILO ACCELERATED)')
    print('='*70)
    print('')
    print('Ready! Speak naturally - transcription will flow continuously.')
    print('Press Ctrl+C to stop')
    print('')
    print('NOTE: This is using Hailo AI HAT hardware acceleration!')
    print('-' * 70)
    print('')

    # Context management
    context_buffer = []
    segment_num = 0
    first_output = True
    last_text = ""
    last_words = []

    # Performance tracking
    start_time = time.time()
    total_audio_duration = 0
    total_words = 0

    try:
        while True:
            segment_num += 1

            # Record
            audio_file = f'/tmp/seg_{segment_num}.wav'

            result = subprocess.run(
                ['arecord', '-D', 'plughw:0,0', '-f', 'S16_LE',
                 '-r', '48000', '-c', '2', '-d', str(config.chunk_duration), audio_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Check if recording succeeded
            if result.returncode != 0:
                print(f"\nError: Recording failed!")
                print(f"arecord error: {result.stderr}")
                print("\nTroubleshooting:")
                print("1. Check if microphones are wired correctly (see PINOUT.md)")
                print("2. Verify I2S is enabled: dtparam i2s")
                print("3. Test audio device: arecord -l")
                print("4. Try manual recording: arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 3 test.wav")
                sys.exit(1)

            # Check if file exists and has content
            if not os.path.exists(audio_file):
                print(f"\nError: Audio file was not created: {audio_file}")
                print("The recording command succeeded but no file was created.")
                sys.exit(1)

            if os.path.getsize(audio_file) == 0:
                print(f"\nError: Audio file is empty: {audio_file}")
                print("Recording succeeded but no audio data was captured.")
                sys.exit(1)

            # Process audio
            try:
                audio, sr = sf.read(audio_file)
            except Exception as e:
                print(f"\nError reading audio file: {e}")
                print(f"File: {audio_file}")
                print(f"File size: {os.path.getsize(audio_file)} bytes")
                sys.exit(1)

            # Mix both LEFT and RIGHT channels for stereo audio capture
            audio = np.mean(audio, axis=1)
            audio = signal.resample(audio, int(len(audio) * 16000 / sr))

            total_audio_duration += config.chunk_duration

            # Check audio energy BEFORE applying gain
            if not has_sufficient_audio(audio, config.min_audio_energy):
                try:
                    os.remove(audio_file)
                except:
                    pass
                continue

            audio = audio * config.gain
            audio = np.clip(audio, -1.0, 1.0)

            proc_file = f'/tmp/proc_{segment_num}.wav'
            sf.write(proc_file, audio, 16000)

            # Transcribe using Hailo
            text = hailo_model.transcribe_audio(proc_file)
            text = normalize_whitespace(text)

            # Validation checks
            if text:
                word_count = len(text.split())

                if word_count < config.min_words:
                    try:
                        os.remove(audio_file)
                        os.remove(proc_file)
                    except:
                        pass
                    continue

                if is_repetition(text, last_text):
                    try:
                        os.remove(audio_file)
                        os.remove(proc_file)
                    except:
                        pass
                    continue

                deduplicated_text = remove_overlap(text, last_words, config.overlap_words)

                if deduplicated_text.strip():
                    context_buffer.append(text)
                    if len(context_buffer) > config.max_context_chunks:
                        context_buffer.pop(0)

                    # Progressive display
                    if not first_output:
                        print(' ' + deduplicated_text, end='', flush=True)
                    else:
                        print(deduplicated_text, end='', flush=True)
                        first_output = False

                    last_text = text
                    last_words = text.split()
                    total_words += len(deduplicated_text.split())

            # Cleanup
            try:
                os.remove(audio_file)
                os.remove(proc_file)
            except:
                pass

    except KeyboardInterrupt:
        elapsed_time = time.time() - start_time

        print('')
        print('')
        print('='*70)
        print('  PERFORMANCE STATISTICS')
        print('='*70)
        print('')
        print(f'Configuration: Hailo {config.hw_arch.upper()}, {config.model_variant} model')
        print(f'Total Runtime: {elapsed_time:.1f}s')
        print(f'Total Audio Processed: {total_audio_duration:.1f}s')
        print(f'Total Words Transcribed: {total_words}')
        if total_audio_duration > 0:
            speed_factor = total_audio_duration / elapsed_time
            print(f'Speed Factor: {speed_factor:.2f}x real-time')
        print('')
        print('='*70)
        print('Transcription stopped')
        print('='*70)

        # Cleanup Hailo resources
        hailo_model.cleanup()
        sys.exit(0)

def main():
    """Main entry point"""

    # Check if Hailo SDK is available
    if not HAILO_AVAILABLE:
        print("\n" + "="*70)
        print("  ERROR: Hailo Platform SDK Not Found")
        print("="*70)
        print("\nThe Hailo Platform SDK (PyHailoRT) is required to use this script.")
        print("\nPlease install:")
        print("1. HailoRT 4.20+ from Hailo Developer Zone")
        print("2. PyHailoRT (included with HailoRT)")
        print("\nVisit: https://hailo.ai/developer-zone/")
        print("\nFor setup instructions, see: HAILO_SETUP.md")
        print("="*70 + "\n")
        sys.exit(1)

    try:
        config = configure_transcription()
        run_transcription(config)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()

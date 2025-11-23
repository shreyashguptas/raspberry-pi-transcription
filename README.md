# Hailo-Accelerated Whisper Transcription on Raspberry Pi 5

Real-time speech-to-text transcription using OpenAI's Whisper model accelerated by the Hailo-8L AI processor on Raspberry Pi 5 with dual INMP441 I2S microphones.

**Features:**
- ⚡ Hardware-accelerated inference with Hailo-8L (13 TOPS)
- 🎤 High-quality 48kHz stereo audio recording
- 🔄 Real-time continuous transcription
- 💻 CPU fallback mode available
- 🎯 Optimized for Raspberry Pi 5

---

## Hardware Requirements

### Essential Components
- **Raspberry Pi 5** (4GB or 8GB RAM)
- **Hailo AI HAT** (M.2 HAT+ with Hailo-8L accelerator)
- **2x INMP441 I2S Microphones** (stereo setup)
- **Official 27W USB-C Power Supply** (required for stable Hailo operation)
- **32GB+ MicroSD Card** with Raspberry Pi OS Bookworm 64-bit

### Microphone Wiring
See **[PINOUT.md](PINOUT.md)** for complete wiring diagram.

**Quick Reference:**
- Both mics share: VDD (3.3V), GND, SD (GPIO20), WS (GPIO19), SCK (GPIO18)
- **Left mic**: L/R pin → GND
- **Right mic**: L/R pin → VDD

---

## System Prerequisites

### Operating System
**Required:** Raspberry Pi OS Bookworm (64-bit)

```bash
# Verify your OS
cat /etc/os-release | grep VERSION_CODENAME
# Must show: VERSION_CODENAME=bookworm

uname -m
# Must show: aarch64
```

⚠️ **Important:** Hailo packages are ONLY available for Debian 12 (Bookworm). Other versions are not supported.

### Python Version
**Required:** Python 3.11

```bash
python3 --version
# Must show: Python 3.11.x
```

---

## Installation

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt full-upgrade -y

# Install HailoRT (includes runtime, drivers, Python bindings)
sudo apt install -y hailo-all

# Install system Python packages
sudo apt install -y python3-full python3-dev python3-pip

# Install audio dependencies
sudo apt install -y alsa-utils libsndfile1

# Reboot to load Hailo kernel driver
sudo reboot
```

### Step 2: Configure I2S Audio for Dual Microphones

Edit `/boot/firmware/config.txt`:

```bash
sudo nano /boot/firmware/config.txt
```

**Add these lines in the audio section:**

```bash
# I2S Audio Configuration for Dual INMP441 Microphones
dtparam=i2s=on
dtoverlay=i2s-mmap
dtoverlay=googlevoicehat-soundcard
```

**Save and reboot:**

```bash
sudo reboot
```

### Step 3: Verify Hailo Hardware

```bash
# Check PCIe detection
lspci | grep -i hailo
# Expected: "Hailo Technologies Ltd. Hailo-8 AI Processor"

# Verify firmware
hailortcli fw-control identify
# Expected: Device info with Hailo-8L, firmware version, serial number

# Check Python bindings (system-wide)
python3 -c "from hailo_platform import HEF; print('Hailo Python bindings OK')"
# Expected: "Hailo Python bindings OK"
```

### Step 4: Verify Audio Hardware

```bash
# List audio devices
arecord -l
# Expected: card 0: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar]

# Test 48kHz stereo recording (5 seconds)
arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 5 test.wav

# Check file was created
ls -lh test.wav
# Expected: ~960KB file (5 sec * 48000 Hz * 2 ch * 2 bytes)
```

**To test audio on your Mac:**

```bash
# On your Mac, copy the test file:
scp pi@raspberrypi.local:~/test.wav ~/Desktop/

# Play it:
afplay ~/Desktop/test.wav
```

### Step 5: Clone Hailo Examples

```bash
cd ~
git clone https://github.com/hailo-ai/Hailo-Application-Code-Examples.git
cd Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition

# Download Whisper model files (tiny model for Hailo-8L)
python3 setup.py
```

### Step 6: Clone This Repository

```bash
cd ~
git clone https://github.com/shreyashguptas/sbc-audio-transcription.git
cd sbc-audio-transcription
```

### Step 7: Create Virtual Environment

⚠️ **REQUIRED:** Use `--system-site-packages` flag to access system-installed Hailo packages (`hailo_platform`). This is the official Hailo standard for Raspberry Pi 5.

⚠️ **NOTE:** PyTorch 2.6.0 is required and included in `requirements.txt`. This matches the official Hailo speech recognition setup.

```bash
# Create Python 3.11 virtual environment with system site packages
# This allows access to HailoRT Python bindings installed via apt
python3 -m venv --system-site-packages venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (includes PyTorch 2.6.0)
pip install -r requirements.txt
```

---

## Running Transcription

### Hailo-Accelerated Mode (Recommended)

```bash
cd ~/sbc-audio-transcription
source venv/bin/activate
python transcribe-halo.py
```

**Features:**
- Hardware-accelerated inference on Hailo-8L
- Real-time continuous transcription
- 48kHz stereo audio recording
- Automatic chunking with overlap
- Low latency

### CPU Mode (Fallback)

```bash
cd ~/sbc-audio-transcription
source venv/bin/activate
python transcribe.py
```

**When to use:**
- Testing without Hailo hardware
- Debugging audio issues
- Comparing accuracy

---

## Configuration

Audio and processing parameters are configured in `transcribe-halo.py`:

```python
class HailoTranscriptionConfig:
    # Audio hardware (48kHz stereo for dual INMP441)
    audio_sample_rate = 48000  # Hz
    audio_channels = 2         # Stereo

    # Processing
    chunk_duration = 10        # seconds (for tiny model)
    overlap_duration = 2       # seconds
    gain = 30.0               # Microphone gain multiplier
    min_audio_energy = 0.0002 # Energy threshold for silence detection

    # Hailo hardware
    hw_arch = 'hailo8l'       # For Raspberry Pi 5 AI HAT
    model_variant = 'tiny'    # tiny or base
```

---

## Known Issues & Solutions

### Issue: "Input buffer size 0" Error

**Cause:** This error typically occurs when the virtual environment is not set up correctly or when using incompatible PyTorch versions.

**Solution:**
1. Ensure you're using `--system-site-packages` when creating the venv
2. Use the exact PyTorch version from requirements.txt (2.6.0)
3. Recreate the environment:
   ```bash
   rm -rf venv
   python3 -m venv --system-site-packages venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

**Verify correct setup:**
```bash
source venv/bin/activate
python3 -c "import torch; import hailo_platform; print(f'torch: {torch.__version__}, hailo: OK')"
# Should print: torch: 2.6.0, hailo: OK
```

### Issue: "No module named 'hailo_platform'" Error

**Cause:** Virtual environment was created WITHOUT `--system-site-packages` flag, blocking access to system-installed HailoRT Python bindings.

**Solution:**
1. Delete the existing venv: `rm -rf venv`
2. Recreate with system site packages:
   ```bash
   cd ~/sbc-audio-transcription
   python3 -m venv --system-site-packages venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

**Verify Hailo access:**
```bash
source venv/bin/activate
python3 -c "import hailo_platform; print('Hailo OK')"
# Should print: Hailo OK
```

**Why this flag is needed:** On Raspberry Pi 5, HailoRT is installed system-wide via `sudo apt install hailo-all`. The `--system-site-packages` flag allows the venv to access these system packages while still maintaining isolation for pip-installed packages. This is the official Hailo standard for RPi5.

### Issue: Audio Recording Fails

**Check driver loading:**
```bash
lsmod | grep snd
arecord -l
```

**Verify config.txt:**
```bash
cat /boot/firmware/config.txt | grep -E 'i2s|voice'
```

Should show:
```
dtparam=i2s=on
dtoverlay=i2s-mmap
dtoverlay=googlevoicehat-soundcard
```

### Issue: Hailo Not Detected

**Check PCIe:**
```bash
lspci | grep -i hailo
dmesg | grep -i hailo
```

**Reinstall driver:**
```bash
sudo apt install --reinstall hailo-all
sudo reboot
```

---

## Audio Quality Tips

1. **Microphone Placement:** Position mics 10-15cm from speaker for best results
2. **Gain Adjustment:** Modify `self.gain = 30.0` in config if audio is too quiet/loud
3. **Test Recording:**
   ```bash
   # Increase gain with mixer (if available)
   amixer -c 0 set Capture 100%
   ```
4. **Verify Stereo:** Both channels should show waveforms in audio analysis tools

---

## Project Structure

```
sbc-audio-transcription/
├── README.md                 # This file - comprehensive setup guide
├── PINOUT.md                 # Microphone wiring diagram
├── requirements.txt          # Python dependencies (NO PyTorch)
├── transcribe-halo.py        # Hailo-accelerated transcription
├── transcribe.py             # CPU fallback version
└── .gitignore               # Git ignore rules
```

---

## Technical Details

### Audio Pipeline
1. **Recording:** arecord → 48kHz stereo S16_LE
2. **Preprocessing:** Resample to 16kHz mono (Whisper requirement)
3. **Feature Extraction:** Convert to mel spectrogram
4. **Inference:** Hailo-8L accelerated encoder/decoder
5. **Postprocessing:** Token to text conversion

### Hailo Models
- **Encoder:** `tiny-whisper-encoder-10s_15dB_h8l.hef`
- **Decoder:** `tiny-whisper-decoder-fixed-sequence-matmul-split_h8l.hef`
- **Quantization:** INT8 for Hailo-8L
- **Chunk Size:** 10 seconds (tiny model)

### Performance
- **Hailo-8L (13 TOPS):** ~2-3x real-time (processes 10s audio in ~3-5s)
- **CPU Only:** ~0.1x real-time (very slow)
- **Latency:** 3-5 seconds from speech to transcription

---

## Troubleshooting

### Debug Audio

```bash
# Test microphone levels
arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 10 test-debug.wav -V stereo

# Check file size (should be ~1.9MB for 10 seconds)
ls -lh test-debug.wav

# Copy to Mac for playback testing
scp test-debug.wav user@mac-hostname:~/Desktop/
```

### Check Hailo Logs

```bash
# Real-time logs
tail -f ~/sbc-audio-transcription/hailort.log

# Search for errors
grep -i error ~/sbc-audio-transcription/hailort.log
```

### Verify Dependencies

```bash
source venv/bin/activate

# Check for conflicts
pip list | grep -E 'torch|tensorflow|keras'
# Should be EMPTY!

# Verify required packages
pip list | grep -E 'numpy|soundfile|transformers|scipy'
```

---

## Contributing

Contributions welcome! Please ensure:
1. Code works on Raspberry Pi 5 with Hailo-8L
2. No PyTorch/TensorFlow dependencies added
3. Audio tested at 48kHz stereo
4. Documentation updated

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

- [Hailo AI](https://hailo.ai/) for the Hailo-8L accelerator and examples
- [OpenAI](https://openai.com/) for the Whisper model
- [Raspberry Pi Foundation](https://www.raspberrypi.org/) for the incredible Pi 5 hardware

---

## Support

**Issues?** Open a GitHub issue with:
- Error messages
- Output of `hailortcli fw-control identify`
- Output of `arecord -l`
- Python version: `python3 --version`
- OS version: `cat /etc/os-release`

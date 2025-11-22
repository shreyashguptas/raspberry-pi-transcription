# Hailo AI HAT Setup Guide for Raspberry Pi 5

Complete guide to set up hardware-accelerated Whisper transcription using the Hailo AI HAT on Raspberry Pi 5.

---

## Quick Start

```bash
# 1. Install HailoRT
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y hailo-all
sudo reboot

# 2. Verify installation
lspci | grep Hailo
hailortcli fw-control identify

# 3. Clone and setup Hailo Application Code Examples
cd ~
git clone https://github.com/hailo-ai/Hailo-Application-Code-Examples.git
cd Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition
python3 setup.py

# 4. Run transcription (from your project directory)
cd ~/sbc-audio-transcription/raspberry-pi-5
source venv/bin/activate
python transcribe-halo.py
```

---

## Hardware Requirements

### What You Need

- **Raspberry Pi 5** (4GB or 8GB recommended)
- **Hailo AI HAT** (M.2 HAT+ with Hailo-8L accelerator)
  - Hailo-8L variant: 13 TOPS
  - Connects via M.2 M-Key slot
- **2x INMP441 I2S Microphones** (already set up from transcribe.py)
- **Power Supply**: Official Raspberry Pi 5 27W USB-C power supply recommended
- **MicroSD Card**: 32GB+ with Raspberry Pi OS Bookworm 64-bit

### Hardware Installation

1. **Power off** your Raspberry Pi 5 completely
2. **Install M.2 HAT+** on Raspberry Pi 5 GPIO header
3. **Connect Hailo AI HAT** to M.2 M-Key slot on the HAT+
4. **Secure with standoffs** to prevent movement
5. **Power on** and verify detection:
   ```bash
   lspci | grep -i hailo
   # Expected output:
   # 0001:01:00.0 Co-processor: Hailo Technologies Ltd. Hailo-8 AI Processor (rev 01)
   ```

---

## System Prerequisites

### Operating System

**Required:** Raspberry Pi OS Bookworm (64-bit)

```bash
# Check your OS version
cat /etc/os-release

# Should show:
# VERSION_CODENAME=bookworm
# Architecture must be: aarch64
```

**Important:** Hailo packages are only available for **Debian 12 (Bookworm)**. If you're running Debian 13 (Trixie) or another version, you must reinstall with Bookworm.

**Download:** https://www.raspberrypi.com/software/operating-systems/
- Select: **Raspberry Pi OS Lite (64-bit)** or **Raspberry Pi OS with Desktop (64-bit)**
- Both work equally well - Lite is recommended for headless/SSH use

### Kernel Version

**Recommended:** Kernel 6.6.31 or later

```bash
uname -r
# Should show: 6.x.x or higher
```

If older:
```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

### Architecture

**Required:** 64-bit ARM (aarch64)

```bash
uname -m
# Must show: aarch64
```

If you see `armv7l` or `arm64`, you're running 32-bit OS and must reinstall with 64-bit version.

---

## Installing HailoRT

### Installation

The **hailo-all** package includes everything you need:
- HailoRT runtime library
- Python bindings (python3-hailort)
- Kernel driver (hailo-dkms)
- Firmware tools

```bash
# Update system
sudo apt update
sudo apt full-upgrade -y

# Install Hailo packages
sudo apt install -y hailo-all

# Reboot to load kernel driver
sudo reboot
```

### Verify Installation

After reboot, verify everything is working:

```bash
# 1. Check hardware detection
lspci | grep -i hailo
# Expected: "Hailo Technologies Ltd. Hailo-8 AI Processor"

# 2. Verify HailoRT
hailortcli fw-control identify
# Expected: Shows device info (Hailo-8L, firmware version, serial number)

# 3. Check Python bindings
python3 -c "from hailo_platform import HEF; print('PyHailoRT OK')"
# Expected: "PyHailoRT OK"

# 4. Verify kernel driver
lsmod | grep hailo
# Expected: Shows hailo_pci module loaded
```

**Troubleshooting:**

If `hailortcli` command not found:
```bash
dpkg -l | grep hailort
# Should show hailort and python3-hailort packages installed
```

If no Hailo device detected:
```bash
lspci  # Check if any PCIe devices are detected
# Verify HAT is properly seated and Pi is powered adequately
```

---

## Setting Up Hailo Application Code Examples

The official Hailo repository contains pre-trained Whisper models and inference code.

### Clone Repository

```bash
cd ~
git clone https://github.com/hailo-ai/Hailo-Application-Code-Examples.git
cd Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition
```

### Run Setup Script

This downloads all Whisper HEF models and installs dependencies:

```bash
python3 setup.py
```

**What this does:**
1. Creates virtual environment: `whisper_env/`
2. Installs Python dependencies:
   - `transformers` - For Whisper tokenizer
   - `torch` - For audio preprocessing
   - `sounddevice`, `scipy` - Audio processing
3. Downloads HEF model files (~400MB total):
   - Tiny model encoder + decoder (for Hailo-8L)
   - Base model encoder + decoder (for Hailo-8L)
   - Files stored in `app/hefs/h8l/` directory
4. Downloads tokenization assets (~180MB)

**Time required:** 5-15 minutes depending on internet speed

### Verify Setup

```bash
# Check HEF files were downloaded
ls ~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition/app/hefs/h8l/

# Expected structure:
# base/
#   base-whisper-encoder-5s_h8l.hef
#   base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef
# tiny/
#   tiny-whisper-encoder-10s_15dB_h8l.hef
#   tiny-whisper-decoder-fixed-sequence-matmul-split_h8l.hef
```

---

## Running transcribe-halo.py

### Activate Your Project Environment

```bash
cd ~/sbc-audio-transcription/raspberry-pi-5
source venv/bin/activate
```

### Run the Script

```bash
python transcribe-halo.py
```

### Interactive Menu

You'll see an interactive menu to configure:

1. **Preset Selection:**
   - **Fastest** - Tiny model, 10s chunks (2-5x real-time speed)
   - **Balanced** - Base model, 5s chunks (1.5-3x real-time) [Recommended]
   - **Custom** - Configure all options manually

2. **Model Selection** (if Custom):
   - `tiny` - Fastest, basic accuracy (39M parameters)
   - `base` - Better accuracy, still fast (74M parameters)

3. **Audio Processing** (if Custom):
   - Overlap duration (1-3 seconds)
   - Microphone gain (10-50x)
   - Energy threshold

### Expected Output

```
======================================================================
  HAILO AI HAT WHISPER TRANSCRIPTION TOOL
  Hardware-accelerated speech-to-text on Hailo-8L
======================================================================

Loading base model on HAILO8L hardware...
Encoder HEF: base-whisper-encoder-5s_h8l.hef
Decoder HEF: base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef

======================================================================
  TRANSCRIPTION ACTIVE (HAILO ACCELERATED)
======================================================================

Ready! Speak naturally - transcription will flow continuously.
Press Ctrl+C to stop

NOTE: Using Hailo AI HAT with base model
----------------------------------------------------------------------

[Your transcription appears here in real-time]
```

### Usage

- **Speak naturally** into the INMP441 microphones
- Transcription appears in **real-time** as you speak
- **Ctrl+C** to stop and see performance statistics

### Performance Statistics

When you stop (Ctrl+C), you'll see:

```
======================================================================
  PERFORMANCE STATISTICS
======================================================================

Configuration: Hailo HAILO8L, base model
Total Runtime: 60.5s
Total Audio Processed: 105.0s
Total Words Transcribed: 234
Speed Factor: 1.74x real-time

======================================================================
Transcription stopped
======================================================================
```

**Speed Factor explained:**
- **< 1.0x** = Slower than real-time (falling behind)
- **= 1.0x** = Exactly real-time
- **> 1.0x** = Faster than real-time (can handle continuous speech)

---

## Performance Notes

### Expected Performance (Hailo-8L)

| Model | Chunk Size | Expected Speed | Accuracy | Best For |
|-------|-----------|----------------|----------|----------|
| `tiny` | 10 seconds | 2-5x real-time | Basic | Maximum speed |
| `base` | 5 seconds | 1.5-3x real-time | Good | Balanced (recommended) |

### Factors Affecting Performance

1. **Model size**: Tiny is faster, base is more accurate
2. **Chunk duration**: Longer chunks = more context but higher latency
3. **Background noise**: Clean audio = better accuracy
4. **CPU usage**: Preprocessing still runs on CPU (torch)
5. **Power supply**: Inadequate power can throttle Hailo accelerator

### Monitoring Hailo

```bash
# Check Hailo temperature
watch -n 1 hailortcli fw-control temp-info

# Monitor Hailo in top
htop
# Look for hailort process - CPU usage should be LOW (most work on Hailo)
```

### Current Limitations

- **English only**: Current HEF models support English language only
- **Torch dependency**: Audio preprocessing requires PyTorch (will be removed in future Hailo updates)
- **Two models**: Only tiny and base variants available (no small/medium/large)
- **Fixed chunk sizes**: Tiny uses 10s, base uses 5s (determined by HEF compilation)

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    transcribe-halo.py                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [INMP441 Mics] → [arecord 48kHz stereo]                       │
│         ↓                                                       │
│  [Mix channels, resample to 16kHz, apply gain]                 │
│         ↓                                                       │
│  [Official Hailo Preprocessing]                                │
│         ↓                                                       │
│  [Generate Mel Spectrogram - 80 bins]                          │
│         ↓                                                       │
│  ┌─────────────────────────────────────┐                       │
│  │   Hailo-8L AI Accelerator (PCIe)    │                       │
│  │                                      │                       │
│  │  Encoder HEF → Decoder HEF           │                       │
│  │     (Hardware acceleration)          │                       │
│  └─────────────────────────────────────┘                       │
│         ↓                                                       │
│  [Tokenizer - Decode to text]                                  │
│         ↓                                                       │
│  [Postprocessing - Remove repetitions]                         │
│         ↓                                                       │
│  [Deduplication - Handle overlaps]                             │
│         ↓                                                       │
│  [Display real-time transcription]                             │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Your code** (transcribe-halo.py):
   - Interactive menu system
   - INMP441 microphone recording (48kHz stereo)
   - Audio preprocessing (mixing, resampling, gain)
   - Deduplication logic for overlapping chunks
   - Performance tracking

2. **Official Hailo code** (imported):
   - `HailoWhisperPipeline` - Manages Hailo inference
   - Mel spectrogram generation (Whisper-specific)
   - Tokenization (Whisper tokenizer from transformers)
   - Post-processing (repetition removal, text cleaning)

3. **Hailo hardware**:
   - Encoder and decoder run on Hailo-8L accelerator
   - PCIe interface for low latency
   - ~10W power consumption during inference

---

## Comparison: CPU vs Hailo

| Feature | transcribe.py (CPU) | transcribe-halo.py (Hailo) |
|---------|-------------------|--------------------------|
| **Hardware** | Raspberry Pi 5 CPU | Hailo-8L accelerator |
| **Models** | All sizes (tiny → large-v3) | tiny, base only |
| **Languages** | 100+ languages | English only (current) |
| **Speed (base)** | 1-2x real-time | 1.5-3x real-time |
| **Power** | ~8-12W | ~15-18W (CPU + Hailo) |
| **Setup** | pip install | Requires hailo-all + setup |
| **Flexibility** | Highly configurable | Fixed models |

**When to use each:**

- **Use transcribe.py (CPU):**
  - Need multilingual support
  - Want larger models (small/medium/large)
  - Prefer maximum flexibility
  - Don't have Hailo HAT

- **Use transcribe-halo.py (Hailo):**
  - English-only transcription
  - Need maximum speed
  - Have Hailo HAT installed
  - Want to offload CPU

---

## File Locations Reference

| Description | Path |
|------------|------|
| **Your project** | `~/sbc-audio-transcription/raspberry-pi-5/` |
| **transcribe-halo.py** | `~/sbc-audio-transcription/raspberry-pi-5/transcribe-halo.py` |
| **Hailo repo** | `~/Hailo-Application-Code-Examples/` |
| **Whisper code** | `~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition/` |
| **HEF models** | `~/Hailo-Application-Code-Examples/.../app/hefs/h8l/base/` |
| **Tokenization assets** | `~/Hailo-Application-Code-Examples/.../app/decoder_assets/base/` |

---

## Additional Resources

### Documentation

- **Hailo Developer Zone:** https://hailo.ai/developer-zone/
- **Hailo Community:** https://community.hailo.ai/
- **Official Examples:** https://github.com/hailo-ai/Hailo-Application-Code-Examples

### Useful Commands

```bash
# Check Hailo status
hailortcli fw-control identify

# Monitor temperature
hailortcli fw-control temp-info

# List all Hailo packages
dpkg -l | grep hailo

# Test audio recording
arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 3 test.wav && aplay test.wav

# Check I2S microphones
arecord -l
```

---

**Last Updated:** 2025-11-22
**Raspberry Pi:** Pi 5
**Hailo HAT:** Hailo-8L (13 TOPS)
**Models:** tiny, base (English only)

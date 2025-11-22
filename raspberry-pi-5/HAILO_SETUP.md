# Hailo AI HAT Setup Guide

This guide will help you set up the Hailo AI HAT for hardware-accelerated Whisper transcription on your Raspberry Pi 5.

## 🚨 TROUBLESHOOTING "Unable to locate package hailo-all"?

**Run this diagnostic script immediately:**

```bash
cd ~/sbc-audio-transcription/raspberry-pi-5
./check_hailo_requirements.sh
```

This will identify exactly what's wrong and give you specific fix instructions.

---

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [System Prerequisites](#system-prerequisites)
3. [Installing HailoRT](#installing-hailort)
4. [Installing Hailo Application Code Examples](#installing-hailo-application-code-examples)
5. [Verifying Installation](#verifying-installation)
6. [Running transcribe-halo.py](#running-transcribe-halopy)
7. [Troubleshooting](#troubleshooting)
8. [Performance Comparison](#performance-comparison)

---

## Hardware Requirements

### What You Have

- **Raspberry Pi 5** (with M.2 HAT+)
- **Hailo-8L AI Accelerator** (13 TOPS variant)
- **INMP441 I2S Microphones** (dual microphone setup)

### Hardware Setup

1. **Physical Installation:**
   - Ensure the Raspberry Pi M.2 HAT is properly connected to your Pi 5
   - Install the Hailo AI HAT on top of the M.2 HAT
   - Verify all connections are secure

2. **Verify Hardware Detection:**
   ```bash
   # Check if Hailo device is detected via PCIe
   lspci | grep -i hailo
   ```

   You should see output similar to:
   ```
   0000:01:00.0 Co-processor: Hailo Technologies Ltd. Hailo-8 AI Processor
   ```

---

## System Prerequisites

### Operating System

- **Raspberry Pi OS** (Bookworm or later recommended)
- **Python 3.10 or 3.11** (Python 3.13 may work but not officially tested with Hailo)

Check your Python version:
```bash
python3 --version
```

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Install System Dependencies

```bash
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    ffmpeg \
    libportaudio2 \
    libasound2-dev \
    libsndfile1 \
    git
```

---

## Installing HailoRT

HailoRT is the runtime software required to communicate with the Hailo AI accelerator.

**IMPORTANT NOTE (2025):** The old installation method using `hailo-ai.github.io` repository is obsolete and will return 404 errors. All Hailo packages are now included in the standard Raspberry Pi repository.

### Pre-Installation Diagnostic (RECOMMENDED)

**Run this diagnostic script first to check if your system is compatible:**

```bash
cd ~/sbc-audio-transcription/raspberry-pi-5
chmod +x check_hailo_requirements.sh
./check_hailo_requirements.sh
```

This will check:
- ✅ OS version (must be Raspberry Pi OS Bookworm 64-bit)
- ✅ Architecture (must be aarch64)
- ✅ Kernel version (>= 6.6.31)
- ✅ Repository configuration
- ✅ Package availability
- ✅ Hardware detection
- ✅ Existing installation status

The script will give you specific instructions based on your system configuration.

---

### Quick Start (TL;DR)

**BEFORE installing, run these diagnostic commands to check your system:**

```bash
# Check OS version (MUST be Raspberry Pi OS Bookworm 64-bit)
cat /etc/os-release

# Check architecture (MUST be aarch64)
uname -m

# Check repository configuration
cat /etc/apt/sources.list.d/raspi.list
```

**Expected output:**
- OS: `VERSION_CODENAME=bookworm` and `Debian GNU/Linux 12`
- Architecture: `aarch64`
- Repository: `deb http://archive.raspberrypi.com/debian/ bookworm main`

**If all checks pass, install:**

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After reboot:

```bash
sudo apt install -y hailo-all
sudo reboot
```

**If you get "Unable to locate package hailo-all"**, see [Troubleshooting](#troubleshooting) section below.

---

### Option 1: Using hailo-all Package (Recommended for Raspberry Pi 5)

The easiest way to install HailoRT on Raspberry Pi 5. As of 2025, Hailo packages are included in the standard Raspberry Pi repository - no special configuration needed!

**Prerequisites:**
- 64-bit Raspberry Pi OS Bookworm (FULL version, not lite)
- Kernel version > 6.6.31

```bash
# Update your system first
sudo apt update
sudo apt full-upgrade -y

# Reboot after upgrade
sudo reboot
```

After reboot:

```bash
# Install hailo-all package (includes HailoRT, drivers, and PyHailoRT)
sudo apt install -y hailo-all

# Reboot to load kernel modules
sudo reboot
```

**What gets installed:**
- HailoRT 4.20.0+ (runtime library)
- hailo-dkms (kernel driver)
- python3-hailort (Python bindings)
- hailo-tappas-core (processing libraries)
- All required dependencies

### Option 2: Manual Installation from Raspberry Pi Archive

If the `hailo-all` package method doesn't work, you can download and install manually:

**Download directly from Raspberry Pi archive:**

```bash
# Download the latest hailo-all package
wget http://archive.raspberrypi.com/debian/pool/main/h/hailo-all/hailo-all_4.20.0_all.deb

# Install it
sudo apt install -y ./hailo-all_4.20.0_all.deb

# Reboot to load kernel modules
sudo reboot
```

**Verify Installation:**

```bash
hailortcli fw-control identify
```

Expected output:
```
Executing on device: 0000:01:00.0
Identifying board
Control Protocol Version: 2
Firmware Version: 4.XX.X (release)
Logger Version: 0
Board Name: Hailo-8
Device Architecture: HAILO8L
```

### Option 3: Installation from Hailo Developer Zone

For the absolute latest versions or if you need specific builds:

1. **Register for Hailo Developer Zone:**
   - Visit: https://hailo.ai/developer-zone/request-access/
   - Create a free account
   - Accept the terms and conditions

2. **Download HailoRT:**
   - Login at: https://hailo.ai/developer-zone/software-downloads/
   - Navigate to: Product: Accelerators → Sub-package: HailoRT → OS: Linux
   - Download: **HailoRT 4.20+** for ARM64
   - Download the .deb package for your architecture

3. **Install HailoRT:**
   ```bash
   sudo apt install -y ./hailort_*.deb
   sudo reboot
   ```

### Installing PyHailoRT

PyHailoRT is the Python interface to HailoRT.

**If you installed `hailo-all` (Option 1 or 2):**
- ✅ PyHailoRT (`python3-hailort`) is already installed system-wide as part of the package
- ✅ Your virtual environment will automatically inherit it if created with `--system-site-packages`
- ✅ No additional installation needed!

**Verify it's installed:**
```bash
dpkg -l | grep python3-hailort
```

**Creating virtual environment with system packages access:**
```bash
cd ~/sbc-audio-transcription/raspberry-pi-5
python3 -m venv --system-site-packages venv
source venv/bin/activate
python3 -c "from hailo_platform import HEF, VDevice; print('PyHailoRT available!')"
```

**If you need to reinstall your venv with system packages:**
```bash
# Remove old venv
rm -rf venv

# Create new venv with system site packages
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Reinstall project dependencies
pip install -r requirements.txt
```

---

## Installing Hailo Application Code Examples

The Hailo Application Code Examples repository contains pre-compiled HEF (Hailo Executable Format) models and reference implementations.

### Clone the Repository

```bash
cd ~
git clone https://github.com/hailo-ai/Hailo-Application-Code-Examples.git
cd Hailo-Application-Code-Examples
```

### Set Up Whisper Models

```bash
# Navigate to the speech recognition example
cd runtime/python/speech_recognition

# Run the setup script to download HEF models
python3 setup.py
```

This will:
- Create a virtual environment
- Download pre-compiled Whisper HEF models (tiny and base)
- Install required Python dependencies

**Important:** The HEF models will be downloaded to:
```
~/Hailo-Application-Code-Examples/runtime/python/speech_recognition/resources/
```

The `transcribe-halo.py` script will automatically search for models in this location.

### Available Models

After setup, you'll have:
- **whisper_tiny_hailo8l.hef** (~75MB, fastest)
- **whisper_base_hailo8l.hef** (~155MB, balanced)

---

## Verifying Installation

### 1. Check Hailo Device

```bash
# Verify device is detected
lspci | grep -i hailo

# Get device information
hailortcli fw-control identify

# Check device status
hailortcli run --help
```

### 2. Test PyHailoRT Import

```bash
# Activate your virtual environment
source ~/sbc-audio-transcription/raspberry-pi-5/venv/bin/activate

# Test import
python3 -c "from hailo_platform import HEF, VDevice; print('PyHailoRT import successful!')"
```

If you see "PyHailoRT import successful!", you're ready to go!

### 3. Test Official Hailo Whisper Example

Before using `transcribe-halo.py`, test the official example:

```bash
cd ~/Hailo-Application-Code-Examples/runtime/python/speech_recognition

# Activate their virtual environment
source whisper_env/bin/activate

# Run the example with your hardware
python3 -m app.app_hailo_whisper --hw-arch hailo8l --variant tiny
```

Speak into your microphone. If you see transcribed text, Hailo is working!

---

## Running transcribe-halo.py

Once everything is installed and verified, you can use the custom transcription script.

### First Time Setup

```bash
# Navigate to your project directory
cd ~/sbc-audio-transcription/raspberry-pi-5

# Activate your virtual environment
source venv/bin/activate

# Ensure dependencies are installed
pip install -r requirements.txt
```

### Run the Script

```bash
python3 transcribe-halo.py
```

### Interactive Configuration

The script will present an interactive menu:

1. **Select Preset:**
   - Fastest (tiny model) - Recommended for real-time transcription
   - Balanced (base model) - Better quality, slightly slower
   - Custom - Configure all options

2. **Configure Audio Processing:**
   - Chunk duration (3-15 seconds)
   - Overlap duration (1-3 seconds)
   - Microphone gain (10x-50x)

3. **Start Transcription:**
   - Speak naturally into your INMP441 microphones
   - Press `Ctrl+C` to stop and see performance statistics

### Example Session

```
======================================================================
  HAILO AI HAT WHISPER TRANSCRIPTION TOOL
  Hardware-accelerated speech-to-text on Hailo-8L
======================================================================

Select Configuration Preset:
→ Fastest (tiny model, 39M params) [Recommended for Pi 5]
  Balanced (base model, 74M params) [Current]
  Custom (configure all options)

======================================================================
  CONFIGURATION SUMMARY
======================================================================

HAILO HARDWARE SETTINGS:
  Hardware Architecture: HAILO8L
  Whisper Model Variant: tiny
  HEF Model Path: ~/Hailo-Application-Code-Examples/.../whisper_tiny_hailo8l.hef

AUDIO PROCESSING:
  Chunk Duration: 7s
  Overlap Duration: 2s
  Microphone Gain: 30x
  Min Audio Energy: 0.0002

NOTE: Hailo handles VAD, beam search, and temperature internally
======================================================================

Start transcription with these settings?
→ Yes, start transcription
  No, reconfigure
  Cancel

======================================================================
  LOADING HAILO MODEL
======================================================================

Loading tiny model for HAILO8L hardware...
Hailo model loaded successfully!

======================================================================
  TRANSCRIPTION ACTIVE (HAILO ACCELERATED)
======================================================================

Ready! Speak naturally - transcription will flow continuously.
Press Ctrl+C to stop

NOTE: This is using Hailo AI HAT hardware acceleration!
----------------------------------------------------------------------

Hello, this is a test of the Hailo AI transcription system...
```

---

## Troubleshooting

### Issue: "Unable to locate package hailo-all"

**This is the most common issue.** Follow these steps in order:

#### Step 1: Check Your System

```bash
# Check OS version
cat /etc/os-release

# Check architecture
uname -m

# Check kernel version
uname -r
```

**Required:**
- OS: Raspberry Pi OS Bookworm (Debian 12) - 64-bit
- Architecture: `aarch64` (NOT `armv7l`)
- Kernel: >= 6.6.31

**If you have 32-bit OS (`armv7l`):** You MUST reinstall with 64-bit Raspberry Pi OS. Hailo requires 64-bit.

**If you have Ubuntu or other OS:** Install Raspberry Pi OS Bookworm 64-bit instead.

#### Step 2: Check Available Packages

```bash
# Search for hailo packages in your repositories
apt-cache search hailo

# Check if repository is accessible
curl -I http://archive.raspberrypi.com/debian/pool/main/h/hailo-all/
```

**If no hailo packages found:** Your repositories aren't configured correctly. Continue to Step 3.

#### Step 3: Fix Repository Configuration

```bash
# Check current repository configuration
cat /etc/apt/sources.list.d/raspi.list

# If file doesn't exist or is incorrect, create it:
echo "deb http://archive.raspberrypi.com/debian/ bookworm main" | sudo tee /etc/apt/sources.list.d/raspi.list

# Update package lists
sudo apt update

# Try searching again
apt-cache search hailo
```

#### Step 4: Manual Installation (If Package Still Not Found)

If the package is truly not available in your repositories, download and install manually:

```bash
# Download the hailo-all package directly
wget http://archive.raspberrypi.com/debian/pool/main/h/hailo-all/hailo-all_4.20.0_all.deb

# Check if download succeeded
ls -lh hailo-all_4.20.0_all.deb

# Install it
sudo apt install -y ./hailo-all_4.20.0_all.deb

# Reboot
sudo reboot
```

**If wget fails (404 error):** The version might be different. Check available versions:

```bash
# List available versions
curl http://archive.raspberrypi.com/debian/pool/main/h/hailo-all/ 2>/dev/null | grep -o 'hailo-all_[0-9.]*_all.deb' | sort -V | tail -5
```

#### Step 5: Alternative - Install Core Components Separately

If `hailo-all` metapackage isn't available, install components individually:

```bash
# Search for individual hailo packages
apt-cache search hailort

# Install core components
sudo apt install -y hailort python3-hailort hailo-dkms

# Reboot
sudo reboot
```

#### Step 6: Check Raspberry Pi OS Version

```bash
# Check exact Raspberry Pi OS version
cat /etc/rpi-issue
```

**If you're on an older Raspberry Pi OS:**
- Consider updating to the latest Raspberry Pi OS Bookworm
- Backup your data first
- Download from: https://www.raspberrypi.com/software/operating-systems/

#### Step 7: Last Resort - Hailo Developer Zone

If all else fails, register and download from Hailo directly:

1. Visit: https://hailo.ai/developer-zone/request-access/
2. Register (free)
3. Download HailoRT .deb for ARM64
4. Install manually:
   ```bash
   sudo apt install -y ./hailort_*.deb
   sudo reboot
   ```

### Issue: "Hailo Platform SDK Not Found"

**Cause:** PyHailoRT is not installed or not accessible.

**Solutions:**
1. If using `hailo-all`, ensure your venv doesn't isolate system packages:
   ```bash
   cd ~/sbc-audio-transcription/raspberry-pi-5
   python3 -m venv --system-site-packages venv
   source venv/bin/activate
   ```

2. Verify python3-hailort is installed:
   ```bash
   dpkg -l | grep hailort
   ```

3. Check installation:
   ```bash
   python3 -c "import hailo_platform; print(hailo_platform.__file__)"
   ```
   Should output something like: `/usr/lib/python3/dist-packages/hailo_platform/__init__.py`

### Issue: "HEF file not found"

**Cause:** Whisper HEF models not downloaded or not in expected location.

**Solutions:**
1. Run the Hailo setup script:
   ```bash
   cd ~/Hailo-Application-Code-Examples/runtime/python/speech_recognition
   python3 setup.py
   ```

2. Verify models exist:
   ```bash
   ls -lh ~/Hailo-Application-Code-Examples/runtime/python/speech_recognition/resources/*.hef
   ```

3. Manually specify HEF path in the script if needed.

### Issue: "Device not detected" (lspci shows nothing)

**Cause:** Hailo hardware not properly connected or driver not loaded.

**Solutions:**
1. Check physical connections:
   - Reseat the Hailo AI HAT
   - Ensure M.2 HAT is properly connected to Pi 5

2. Verify PCIe is enabled:
   ```bash
   # Check boot config
   grep pcie /boot/config.txt

   # Should see: dtparam=pciex1
   ```

3. Reload driver:
   ```bash
   sudo modprobe hailo_pci
   lsmod | grep hailo
   ```

4. Reboot and try again:
   ```bash
   sudo reboot
   ```

### Issue: "Recording failed" or "Audio device not found"

**Cause:** INMP441 microphones not properly configured.

**Solutions:**
1. Verify I2S is enabled:
   ```bash
   dtparam i2s
   ```

2. Check audio devices:
   ```bash
   arecord -l
   ```

3. Test recording manually:
   ```bash
   arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 3 test.wav
   aplay test.wav
   ```

4. See `PINOUT.md` for microphone wiring details.

### Issue: Slow or No Transcription Output

**Cause:** Model may not be running on Hailo hardware.

**Solutions:**
1. Check Hailo is being used:
   ```bash
   # Monitor Hailo temperature (indicates activity)
   watch -n 1 hailortcli fw-control temp-info
   ```

2. Verify HEF file is for correct hardware:
   - File should contain `hailo8l` in the name
   - Not `hailo8` or `hailo10h`

3. Check system resources:
   ```bash
   htop  # CPU should be low if Hailo is doing the work
   ```

### Issue: "ImportError: cannot import name 'HEF'"

**Cause:** Old version of PyHailoRT or incorrect import.

**Solutions:**
1. Update HailoRT and PyHailoRT to 4.20+

2. Check import syntax:
   ```python
   from hailo_platform import HEF, VDevice
   # Not: import hailo
   ```

3. Verify version:
   ```bash
   pip show hailort
   hailortcli --version
   ```

---

## Performance Comparison

### Expected Performance

| Configuration | Model | Hardware | Speed Factor | Notes |
|--------------|-------|----------|--------------|-------|
| transcribe.py | tiny | Pi 5 CPU | ~0.8-1.2x | CPU-bound, good baseline |
| transcribe.py | base | Pi 5 CPU | ~0.5-0.8x | Slower but better quality |
| transcribe-halo.py | tiny | Hailo-8L | ~3-5x | Hardware accelerated |
| transcribe-halo.py | base | Hailo-8L | ~2-3x | Best quality with acceleration |

**Speed Factor**: Ratio of audio processed to real-time (higher is better)
- 1x = real-time (7 seconds audio processed in 7 seconds)
- 2x = twice real-time (7 seconds audio processed in 3.5 seconds)
- 0.5x = half real-time (7 seconds audio processed in 14 seconds)

### Measuring Performance

Both scripts display performance statistics when you press `Ctrl+C`:

```
======================================================================
  PERFORMANCE STATISTICS
======================================================================

Configuration: Hailo HAILO8L, tiny model
Total Runtime: 120.5s
Total Audio Processed: 350.0s
Total Words Transcribed: 1247
Speed Factor: 2.90x real-time

======================================================================
```

### Tips for Optimal Performance

1. **Use tiny model for real-time:** Best speed-to-quality ratio on Hailo-8L

2. **Adjust chunk duration:**
   - Shorter (3-5s) = lower latency, less context
   - Longer (10-15s) = better context, higher latency

3. **Monitor system temperature:**
   ```bash
   vcgencmd measure_temp  # Pi 5 CPU
   hailortcli fw-control temp-info  # Hailo accelerator
   ```

4. **Optimize overlap:**
   - 2 seconds overlap is balanced
   - Less overlap = faster but may miss words at boundaries

---

## Additional Resources

### Official Documentation

- **Hailo Developer Zone:** https://hailo.ai/developer-zone/
- **HailoRT Documentation:** https://github.com/hailo-ai/hailort
- **Application Code Examples:** https://github.com/hailo-ai/Hailo-Application-Code-Examples
- **Community Forum:** https://community.hailo.ai/

### Related Projects

- **Wyoming Protocol Integration:** https://github.com/mpeex/wyoming-hailo-whisper
- **FastAPI Server:** https://github.com/CStrue/raspberrypi5-hailo8L-whisper-server
- **Hailo RPi5 Examples:** https://github.com/hailo-ai/hailo-rpi5-examples

### Model Information

- **OpenAI Whisper:** https://github.com/openai/whisper
- **Whisper Model Card:** https://github.com/openai/whisper/blob/main/model-card.md
- **Faster-Whisper:** https://github.com/SYSTRAN/faster-whisper

---

## Comparison: transcribe.py vs transcribe-halo.py

### When to Use transcribe.py (CPU-based)

**Pros:**
- No additional hardware required
- Supports all Whisper model sizes (tiny to large-v3)
- Full control over VAD parameters
- Multi-language support
- More mature and tested

**Cons:**
- Slower, CPU-bound
- May not achieve real-time on larger models
- Higher CPU usage and heat

**Best for:**
- Testing and development
- Offline transcription of audio files
- Multi-language transcription
- Maximum quality with large models

### When to Use transcribe-halo.py (Hailo-accelerated)

**Pros:**
- Hardware acceleration on Hailo-8L
- Much faster (2-5x speed improvement)
- Lower CPU usage
- Real-time transcription capability
- Optimized for edge deployment

**Cons:**
- Requires Hailo AI HAT hardware
- English language only (currently)
- Limited to tiny and base models
- Less control over transcription parameters
- Newer, less tested

**Best for:**
- Real-time transcription
- Production deployment on Pi 5
- Energy-efficient continuous operation
- English-only applications

---

## Next Steps

1. **Test both scripts** and compare performance for your use case
2. **Experiment with configurations** to find optimal settings
3. **Monitor temperature** during extended use
4. **Consider use case:**
   - Development/testing → `transcribe.py`
   - Production/real-time → `transcribe-halo.py`

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Verify all prerequisites are met
3. Test with the official Hailo examples first
4. Check Hailo Community Forum for known issues
5. Review project documentation and pinout guides

---

**Last Updated:** 2025-01-21
**Hailo-8L (13 TOPS)** on **Raspberry Pi 5**

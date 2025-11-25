#!/bin/bash
#
# install-pi5.sh - Complete ReSpeaker 2-Mic HAT setup for Raspberry Pi 5 + Bookworm
#
# Usage:
#   1. Clone this repo: git clone https://github.com/shreyashguptas/sbc-audio-transcription.git
#   2. Run: cd sbc-audio-transcription && sudo ./install-pi5.sh
#   3. Reboot when prompted
#
# This script handles everything:
#   - Installs all dependencies (dkms, i2c-tools, kernel headers, etc.)
#   - Clones the seeed-voicecard driver repository
#   - Configures /boot/firmware/config.txt correctly for Pi 5
#   - Copies overlay files to the correct location
#   - Compiles and installs kernel modules via DKMS
#
# The original seeed-voicecard install.sh has Pi 5 Bookworm compatibility issues:
#   - Writes to wrong config file (/boot/config.txt instead of /boot/firmware/config.txt)
#   - Assumes dkms is pre-installed
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VOICECARD_REPO="https://github.com/respeaker/seeed-voicecard.git"
VOICECARD_DIR="/tmp/seeed-voicecard"
CONFIG="/boot/firmware/config.txt"
OVERLAYS_DIR="/boot/firmware/overlays"
MODULES_FILE="/etc/modules"

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  ReSpeaker 2-Mic HAT Installer for Pi 5 + Bookworm  ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo

# ------------------------------------------------------------------------------
# Pre-flight checks
# ------------------------------------------------------------------------------

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root (use sudo)${NC}" 1>&2
   exit 1
fi

# Get the actual user (not root) for home directory
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)

# Check for Pi 5
echo -e "${BLUE}Checking system...${NC}"
if grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Raspberry Pi 5 detected"
else
    echo -e "${YELLOW}Warning: This script is designed for Raspberry Pi 5${NC}"
    echo "Detected: $(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for Bookworm
if grep -q "bookworm" /etc/os-release 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Debian Bookworm detected"
else
    echo -e "${YELLOW}Warning: This script is designed for Debian Bookworm${NC}"
    echo "Detected: $(grep VERSION_CODENAME /etc/os-release 2>/dev/null || echo 'Unknown')"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check architecture
if [[ "$(uname -m)" == "aarch64" ]]; then
    echo -e "  ${GREEN}✓${NC} 64-bit ARM architecture"
else
    echo -e "${RED}Error: This script requires 64-bit ARM (aarch64)${NC}"
    echo "Detected: $(uname -m)"
    exit 1
fi

echo

# ------------------------------------------------------------------------------
# Step 1: Install dependencies
# ------------------------------------------------------------------------------
echo -e "${GREEN}[1/7] Installing system dependencies...${NC}"
apt-get update
apt-get install -y \
    dkms \
    git \
    i2c-tools \
    libasound2-plugins \
    raspberrypi-kernel-headers \
    alsa-utils

echo -e "  ${GREEN}✓${NC} Dependencies installed"
echo

# ------------------------------------------------------------------------------
# Step 2: Clone seeed-voicecard repository
# ------------------------------------------------------------------------------
echo -e "${GREEN}[2/7] Cloning seeed-voicecard driver repository...${NC}"

# Clean up any previous clone
if [[ -d "$VOICECARD_DIR" ]]; then
    echo "  Removing previous clone..."
    rm -rf "$VOICECARD_DIR"
fi

git clone --depth 1 "$VOICECARD_REPO" "$VOICECARD_DIR"
echo -e "  ${GREEN}✓${NC} Repository cloned to $VOICECARD_DIR"
echo

# ------------------------------------------------------------------------------
# Step 3: Configure /boot/firmware/config.txt
# ------------------------------------------------------------------------------
echo -e "${GREEN}[3/7] Configuring $CONFIG...${NC}"

# Backup config
cp "$CONFIG" "${CONFIG}.backup.$(date +%Y%m%d%H%M%S)"
echo "  - Created backup of config.txt"

# Enable I2C
if grep -q "^#dtparam=i2c_arm=on" "$CONFIG"; then
    sed -i 's/^#dtparam=i2c_arm=on/dtparam=i2c_arm=on/' "$CONFIG"
    echo "  - Enabled i2c_arm (uncommented)"
elif ! grep -q "^dtparam=i2c_arm=on" "$CONFIG"; then
    echo "dtparam=i2c_arm=on" >> "$CONFIG"
    echo "  - Added dtparam=i2c_arm=on"
else
    echo "  - i2c_arm already enabled"
fi

# Enable I2S
if ! grep -q "^dtparam=i2s=on" "$CONFIG"; then
    echo "dtparam=i2s=on" >> "$CONFIG"
    echo "  - Added dtparam=i2s=on"
else
    echo "  - i2s already enabled"
fi

# Add i2s-mmap overlay
if ! grep -q "^dtoverlay=i2s-mmap" "$CONFIG"; then
    echo "dtoverlay=i2s-mmap" >> "$CONFIG"
    echo "  - Added dtoverlay=i2s-mmap"
else
    echo "  - i2s-mmap overlay already present"
fi

# Add seeed-2mic-voicecard overlay
if ! grep -q "^dtoverlay=seeed-2mic-voicecard" "$CONFIG"; then
    echo "dtoverlay=seeed-2mic-voicecard" >> "$CONFIG"
    echo "  - Added dtoverlay=seeed-2mic-voicecard"
else
    echo "  - seeed-2mic-voicecard overlay already present"
fi

echo -e "  ${GREEN}✓${NC} Config updated"
echo

# ------------------------------------------------------------------------------
# Step 4: Copy overlay files
# ------------------------------------------------------------------------------
echo -e "${GREEN}[4/7] Installing device tree overlays...${NC}"

cp "$VOICECARD_DIR/seeed-2mic-voicecard.dtbo" "$OVERLAYS_DIR/"
echo "  - Installed seeed-2mic-voicecard.dtbo"

# Copy additional overlays if present
for overlay in seeed-4mic-voicecard.dtbo seeed-8mic-voicecard.dtbo; do
    if [[ -f "$VOICECARD_DIR/$overlay" ]]; then
        cp "$VOICECARD_DIR/$overlay" "$OVERLAYS_DIR/"
        echo "  - Installed $overlay"
    fi
done

echo -e "  ${GREEN}✓${NC} Overlays installed"
echo

# ------------------------------------------------------------------------------
# Step 5: Configure kernel modules
# ------------------------------------------------------------------------------
echo -e "${GREEN}[5/7] Configuring kernel modules...${NC}"

if ! grep -q "^snd-soc-seeed-voicecard" "$MODULES_FILE"; then
    echo "snd-soc-seeed-voicecard" >> "$MODULES_FILE"
    echo "  - Added snd-soc-seeed-voicecard to /etc/modules"
else
    echo "  - snd-soc-seeed-voicecard already in /etc/modules"
fi

if ! grep -q "^snd-soc-wm8960" "$MODULES_FILE"; then
    echo "snd-soc-wm8960" >> "$MODULES_FILE"
    echo "  - Added snd-soc-wm8960 to /etc/modules"
else
    echo "  - snd-soc-wm8960 already in /etc/modules"
fi

echo -e "  ${GREEN}✓${NC} Kernel modules configured"
echo

# ------------------------------------------------------------------------------
# Step 6: Compile drivers via DKMS
# ------------------------------------------------------------------------------
echo -e "${GREEN}[6/7] Compiling kernel modules (this may take a few minutes)...${NC}"

cd "$VOICECARD_DIR"

# Run the original install script for DKMS compilation
# We suppress config.txt related output since we handle that ourselves
echo "  Running seeed-voicecard install.sh for DKMS..."
if ./install.sh 2>&1 | tee /tmp/seeed-install.log | grep -E "^(dkms|Building|running|DKMS)" || true; then
    :
fi

# Verify DKMS installation
if dkms status 2>/dev/null | grep -q "seeed-voicecard"; then
    echo -e "  ${GREEN}✓${NC} DKMS modules compiled and installed"
else
    echo -e "${YELLOW}  Warning: DKMS status unclear, check /tmp/seeed-install.log${NC}"
fi

echo

# ------------------------------------------------------------------------------
# Step 7: Setup ALSA config
# ------------------------------------------------------------------------------
echo -e "${GREEN}[7/7] Setting up ALSA configuration...${NC}"

# Create voicecard config directory
mkdir -p /etc/voicecard

# Copy ALSA state files
if [[ -f "$VOICECARD_DIR/wm8960_asound.state" ]]; then
    cp "$VOICECARD_DIR/wm8960_asound.state" /etc/voicecard/
    echo "  - Installed ALSA state file"
fi

if [[ -f "$VOICECARD_DIR/asound_2mic.conf" ]]; then
    cp "$VOICECARD_DIR/asound_2mic.conf" /etc/voicecard/
    echo "  - Installed ALSA config"
fi

# Copy and enable the seeed-voicecard service
if [[ -f "$VOICECARD_DIR/seeed-voicecard.service" ]]; then
    cp "$VOICECARD_DIR/seeed-voicecard.service" /lib/systemd/system/
    cp "$VOICECARD_DIR/seeed-voicecard" /usr/bin/
    chmod +x /usr/bin/seeed-voicecard
    systemctl daemon-reload
    systemctl enable seeed-voicecard.service
    echo "  - Enabled seeed-voicecard service"
fi

echo -e "  ${GREEN}✓${NC} ALSA configured"
echo

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------
echo -e "${BLUE}Cleaning up...${NC}"
rm -rf "$VOICECARD_DIR"
echo "  - Removed temporary files"
echo

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}          Installation Complete!                      ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo
echo -e "Please ${YELLOW}reboot${NC} your Raspberry Pi to apply changes:"
echo
echo -e "  ${BLUE}sudo reboot${NC}"
echo
echo "After reboot, verify the installation with:"
echo
echo "  arecord -l"
echo "  # Expected: card X: seeed2micvoicec [seeed-2mic-voicecard]"
echo
echo "  ls /dev/i2c*"
echo "  # Expected: /dev/i2c-1"
echo
echo "  # Test recording (5 seconds):"
echo "  arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 5 test.wav"
echo

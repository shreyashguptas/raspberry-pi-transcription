#!/bin/bash
# Hailo AI HAT Requirements Checker
# Diagnoses system configuration for Hailo installation

echo "======================================================================"
echo "  HAILO AI HAT REQUIREMENTS CHECKER"
echo "======================================================================"
echo ""

# Check 1: OS Version
echo "CHECK 1: Operating System"
echo "----------------------------------------"
if [ -f /etc/os-release ]; then
    OS_NAME=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
    OS_VERSION=$(grep VERSION_CODENAME /etc/os-release | cut -d'=' -f2)
    echo "OS: $OS_NAME"
    echo "Version Codename: $OS_VERSION"

    if [ "$OS_VERSION" = "bookworm" ]; then
        echo "✅ OS Version: PASS (Bookworm)"
    else
        echo "❌ OS Version: FAIL (Need Bookworm, got $OS_VERSION)"
        echo "   Solution: Install Raspberry Pi OS Bookworm 64-bit"
    fi
else
    echo "❌ Cannot detect OS version"
fi
echo ""

# Check 2: Architecture
echo "CHECK 2: Architecture"
echo "----------------------------------------"
ARCH=$(uname -m)
echo "Architecture: $ARCH"
if [ "$ARCH" = "aarch64" ]; then
    echo "✅ Architecture: PASS (64-bit)"
else
    echo "❌ Architecture: FAIL (Need aarch64, got $ARCH)"
    echo "   Solution: Install 64-bit Raspberry Pi OS"
fi
echo ""

# Check 3: Kernel Version
echo "CHECK 3: Kernel Version"
echo "----------------------------------------"
KERNEL=$(uname -r)
echo "Kernel: $KERNEL"
KERNEL_MAJOR=$(echo $KERNEL | cut -d'.' -f1)
KERNEL_MINOR=$(echo $KERNEL | cut -d'.' -f2)
KERNEL_PATCH=$(echo $KERNEL | cut -d'.' -f3 | grep -o '^[0-9]*')

if [ "$KERNEL_MAJOR" -ge 6 ] && [ "$KERNEL_MINOR" -ge 6 ] && [ "$KERNEL_PATCH" -ge 31 ]; then
    echo "✅ Kernel: PASS (>= 6.6.31)"
else
    echo "⚠️  Kernel: WARNING (Recommended >= 6.6.31)"
    echo "   Solution: Run sudo apt full-upgrade -y && sudo reboot"
fi
echo ""

# Check 4: Repository Configuration
echo "CHECK 4: Repository Configuration"
echo "----------------------------------------"
if [ -f /etc/apt/sources.list.d/raspi.list ]; then
    echo "Repository file exists: ✅"
    if grep -q "archive.raspberrypi.com" /etc/apt/sources.list.d/raspi.list; then
        echo "✅ Raspberry Pi repository configured"
        grep "archive.raspberrypi" /etc/apt/sources.list.d/raspi.list | head -1
    else
        echo "❌ Raspberry Pi repository not found in raspi.list"
        echo "   Solution: Run the following command:"
        echo '   echo "deb http://archive.raspberrypi.com/debian/ bookworm main" | sudo tee /etc/apt/sources.list.d/raspi.list'
    fi
else
    echo "❌ Repository file missing: /etc/apt/sources.list.d/raspi.list"
    echo "   Solution: Run the following command:"
    echo '   echo "deb http://archive.raspberrypi.com/debian/ bookworm main" | sudo tee /etc/apt/sources.list.d/raspi.list'
fi
echo ""

# Check 5: Package Availability
echo "CHECK 5: Hailo Package Availability"
echo "----------------------------------------"
echo "Updating package lists..."
sudo apt update -qq 2>&1 | grep -i "error\|fail" || echo "Update completed"
echo ""

echo "Searching for Hailo packages..."
HAILO_PACKAGES=$(apt-cache search hailo 2>/dev/null | grep -i hailo)
if [ -n "$HAILO_PACKAGES" ]; then
    echo "✅ Hailo packages found:"
    echo "$HAILO_PACKAGES" | head -5

    # Check specifically for hailo-all
    if apt-cache show hailo-all &>/dev/null; then
        echo ""
        echo "✅ hailo-all package is available"
        HAILO_VERSION=$(apt-cache show hailo-all | grep "^Version:" | head -1 | awk '{print $2}')
        echo "   Available version: $HAILO_VERSION"
    else
        echo ""
        echo "⚠️  hailo-all metapackage not found, but other hailo packages exist"
        echo "   Solution: Try installing core components:"
        echo "   sudo apt install -y hailort python3-hailort hailo-dkms"
    fi
else
    echo "❌ No Hailo packages found in repositories"
    echo "   Solution: Manual installation required"
    echo "   Download from: http://archive.raspberrypi.com/debian/pool/main/h/hailo-all/"
fi
echo ""

# Check 6: Hardware Detection
echo "CHECK 6: Hailo Hardware Detection"
echo "----------------------------------------"
if command -v lspci &> /dev/null; then
    HAILO_DEVICE=$(lspci 2>/dev/null | grep -i hailo)
    if [ -n "$HAILO_DEVICE" ]; then
        echo "✅ Hailo device detected:"
        echo "   $HAILO_DEVICE"
    else
        echo "❌ No Hailo device detected via PCIe"
        echo "   Troubleshooting:"
        echo "   1. Check physical connection of Hailo AI HAT"
        echo "   2. Ensure M.2 HAT is properly seated"
        echo "   3. Run: lspci (to see all PCIe devices)"
    fi
else
    echo "⚠️  lspci command not available"
    echo "   Install with: sudo apt install -y pciutils"
fi
echo ""

# Check 7: Existing Installation
echo "CHECK 7: Existing Hailo Installation"
echo "----------------------------------------"
if command -v hailortcli &> /dev/null; then
    echo "✅ HailoRT CLI found"
    HAILORT_VERSION=$(hailortcli --version 2>/dev/null | head -1)
    echo "   Version: $HAILORT_VERSION"

    # Try to identify device
    echo ""
    echo "Attempting to identify Hailo device..."
    hailortcli fw-control identify 2>&1 | head -10
else
    echo "❌ HailoRT not installed"
fi

# Check if python3-hailort is installed
if dpkg -l | grep -q python3-hailort; then
    echo "✅ python3-hailort package installed"
else
    echo "❌ python3-hailort not installed"
fi
echo ""

# Summary and Recommendations
echo "======================================================================"
echo "  SUMMARY AND RECOMMENDATIONS"
echo "======================================================================"
echo ""

# Count failures
FAIL_COUNT=0

if [ "$OS_VERSION" != "bookworm" ]; then
    ((FAIL_COUNT++))
fi

if [ "$ARCH" != "aarch64" ]; then
    ((FAIL_COUNT++))
fi

if [ -z "$HAILO_PACKAGES" ]; then
    ((FAIL_COUNT++))
fi

# Provide recommendation
if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ System appears ready for Hailo installation!"
    echo ""
    if command -v hailortcli &> /dev/null; then
        echo "HailoRT is already installed. Test with:"
        echo "  hailortcli fw-control identify"
    else
        echo "Install Hailo packages with:"
        echo "  sudo apt install -y hailo-all"
        echo "  sudo reboot"
        echo ""
        echo "OR try individual components:"
        echo "  sudo apt install -y hailort python3-hailort hailo-dkms"
        echo "  sudo reboot"
    fi
else
    echo "⚠️  Found $FAIL_COUNT critical issue(s)"
    echo ""
    echo "NEXT STEPS:"
    echo ""

    if [ "$OS_VERSION" != "bookworm" ] || [ "$ARCH" != "aarch64" ]; then
        echo "1. ❌ Operating System Issue"
        echo "   You need: Raspberry Pi OS Bookworm 64-bit"
        echo "   Download from: https://www.raspberrypi.com/software/operating-systems/"
        echo "   Select: Raspberry Pi OS (64-bit) with Desktop"
        echo ""
    fi

    if [ -z "$HAILO_PACKAGES" ]; then
        echo "2. ❌ Packages Not Available in Repositories"
        echo "   Try manual installation:"
        echo "   wget http://archive.raspberrypi.com/debian/pool/main/h/hailo-all/hailo-all_4.20.0_all.deb"
        echo "   sudo apt install -y ./hailo-all_4.20.0_all.deb"
        echo "   sudo reboot"
        echo ""
        echo "   Alternative: Register at Hailo Developer Zone"
        echo "   https://hailo.ai/developer-zone/request-access/"
        echo ""
    fi
fi

echo "======================================================================"
echo "For detailed instructions, see: HAILO_SETUP.md"
echo "======================================================================"

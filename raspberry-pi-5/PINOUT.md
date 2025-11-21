# INMP441 Microphone Pinout for Raspberry Pi 5

## Wiring Configuration

This project uses **TWO INMP441 I2S MEMS microphones** in stereo configuration connected to the Raspberry Pi 5 for improved audio capture.

### Pin Connections (Stereo - Two Microphones)

**Shared Pins** (connect both microphones to these):

| Function     | Raspberry Pi 5 Pin | GPIO/Physical |
|--------------|-------------------|---------------|
| VDD (Power)  | 3.3V              | Pin 1         |
| GND (Ground) | GND               | Pin 6         |
| SD (Data)    | GPIO20            | Pin 38        |
| WS (Word Select) | GPIO19        | Pin 35        |
| SCK (Clock)  | GPIO18            | Pin 12        |

**Channel Selection** (different for each mic):

| Microphone   | L/R Pin Connection | Channel |
|--------------|-------------------|---------|
| Microphone 1 | GND (any GND pin) | LEFT    |
| Microphone 2 | 3.3V (VDD)        | RIGHT   |

### Detailed Wiring

#### Microphone 1 (LEFT Channel):
- VDD → 3.3V (Pin 1)
- GND → GND (Pin 6)
- SD → GPIO20 (Pin 38)
- WS → GPIO19 (Pin 35)
- SCK → GPIO18 (Pin 12)
- **L/R → GND** (any GND pin)

#### Microphone 2 (RIGHT Channel):
- VDD → 3.3V (Pin 1)
- GND → GND (Pin 6)
- SD → GPIO20 (Pin 38)
- WS → GPIO19 (Pin 35)
- SCK → GPIO18 (Pin 12)
- **L/R → 3.3V** (VDD or Pin 1)

### Important Notes

- **Stereo Setup**: Both microphones share the same I2S bus, but output on different channels based on L/R pin
- **Channel Selection**: L/R pin determines channel - GND = LEFT, VDD = RIGHT
- **Audio Device**: Configured as `plughw:0,0` in ALSA
- **Format**: 48kHz, Stereo, S16_LE
- **Processing**: Both LEFT and RIGHT channels mixed together for optimal audio capture

### I2S Configuration

The I2S interface is enabled in `/boot/firmware/config.txt`:

```
dtparam=i2s=on
dtoverlay=googlevoicehat-soundcard
```

### Audio Processing

The script uses:
- **Stereo mixing**: Both LEFT and RIGHT channels averaged together for optimal audio quality
- **Sample rate conversion**: 48kHz → 16kHz
- **Gain**: 30x amplification
- **Clipping protection**: Values clipped to [-1.0, 1.0]

### Testing the Microphone

To verify the microphone is working:

```bash
arecord -D plughw:0,0 -f S16_LE -r 48000 -c 2 -d 5 test.wav
aplay test.wav
```

---

**Last Updated**: 2025-11-21 (Updated to stereo dual-microphone configuration)
**Project**: Voice Transcription with Faster-Whisper

# INMP441 Microphone Pinout for Raspberry Pi 5

## Stereo Dual-Microphone Wiring

This setup uses **TWO INMP441 I2S MEMS microphones** in stereo configuration.

### Shared Connections (Both Microphones)

Both microphones connect to these same pins:

| INMP441 Pin | Raspberry Pi 5 Pin | GPIO/Physical |
|-------------|-------------------|---------------|
| VDD         | 3.3V              | Pin 1         |
| GND         | GND               | Pin 6         |
| SD          | GPIO20            | Pin 38        |
| WS          | GPIO19            | Pin 35        |
| SCK         | GPIO18            | Pin 12        |

### Channel Selection (Different for Each Mic)

The **L/R pin** determines which channel each microphone outputs on:

| Microphone   | L/R Pin → | Channel |
|--------------|-----------|---------|
| Microphone 1 | **GND**   | LEFT    |
| Microphone 2 | **3.3V**  | RIGHT   |

### Complete Wiring Diagram

**Microphone 1 (LEFT Channel):**
```
VDD → 3.3V (Pin 1)
GND → GND (Pin 6)
SD  → GPIO20 (Pin 38)
WS  → GPIO19 (Pin 35)
SCK → GPIO18 (Pin 12)
L/R → GND (any GND pin)
```

**Microphone 2 (RIGHT Channel):**
```
VDD → 3.3V (Pin 1)
GND → GND (Pin 6)
SD  → GPIO20 (Pin 38)
WS  → GPIO19 (Pin 35)
SCK → GPIO18 (Pin 12)
L/R → 3.3V (VDD or Pin 1)
```

---

**Note**: Both microphones share the same I2S bus. The L/R pin setting determines which channel (LEFT or RIGHT) each microphone transmits on.

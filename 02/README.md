# Keyboard 2 - aximi

Inspired by: https://github.com/sadekbaroudi/fingerpunch/tree/master/keyboards/ximi/v1

## Hardware notes

### Controller:

- Pro Micro - 12 pins

### Switches:

- Kailh Choc Low Profile 1350 (v1)
  - Crystal Red
  - Dimensions:

### Trackball:

- Sensor: PMW3360

SPI Communications
GD (GND) -- Connects to any GND on the controller.
VI (V In) -- Power connects to a power supply pin on the controller.
MI (MISO) -- The SPI "Master In Slave Out" pin.
MO (MOSI) -- The SPI "Master Out Slave In" pin.
SC (SCLK) -- The serial clock pin to sync data.
SS (Slave Select or Chip Select - CS) -- The pin the controller uses to notify the sensor that it wants to talk.

On a Pro Micro the SPI pins are:

SCLK - 15
MISO - 16
MOSI - 17

On a Arduino Nano clone the SPI pins are:

SS - D10
MOSI - D11
MISO - D12
SCLK - D13

CS is good on D9 Perhaps

Then you just need to set the 'CS' pin in the config, as that can go anywhere.

# TRRS

One data pin: B4
The other two VCC and GND

Which ones don't matter, just keep them the same.

## Firmware

Test your config:

```sh
qmk compile -kb handwired/aximi -km vial
```

Then flash it: (from vial folder)

```sh
qmk flash -kb handwired/aximi -km vial
```

## KiCad

Arduino nano model from:

- https://github.com/g200kg/kicad-lib-arduino

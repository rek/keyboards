# Keyboard 2

Inspired by: https://github.com/sadekbaroudi/fingerpunch/tree/master/keyboards/ximi/v1

## Hardware notes

Controller:

- Arduino Nano - 15 pins
  - Atmel MEGA 328PB - U
  - Which is: atmega328p

Switches:

- Kailh Choc Low Profile 1350
  - Crystal Red
-

Trackball:

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

## Firmware

Test your config:

```sh
qmk compile -kb handwired/aximi -km default
```

Then flash it:

```sh
qmk flash -kb handwired/aximi -km default
```

To flash onto Arduino UNO:

```sh
avrdude -p atmega328p -c arduino -U flash:w:handwired_aximi_default.hex:i -P /dev/ttyACM0
```

To flash onto Nano:

```sh
avrdude -p atmega328p -c arduino -U flash:w:handwired_aximi_default.hex:i -P /dev/ttyUSB0
```

## Flash bootloader

If you have a 328PB without a bootloader (aka: a cheap clone)

Then use the USPISP

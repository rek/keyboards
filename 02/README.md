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

## Firmware

Test your config:

```sh
qmk compile -kb handwired/aximi -km default
```

Then flash it:

```sh
qmk flash -kb handwired/aximi -km default
```

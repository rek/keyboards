### Controller:

- Arduino Nano - 15 pins

  - Atmel MEGA 328PB - U
  - Which is:

  ```sh
      "processor": "atmega328p",
      "bootloader": "usbasploader",
  ```

- Can support baud rates up to 115200 reliably

When choosing pins, make sure to pick the ATMega pins definitions from the Pinout

But I stopped using this and Went with Pro Micro instead, as Nano was too hand to get the bootloader working with QMK

## Flash bootloader

If you have a 328PB without a bootloader (aka: a cheap clone)

Then you need to use USBISP to flash a bootloader onto the MCU

To flash onto Arduino UNO:

```sh
avrdude -p atmega328p -c arduino -U flash:w:handwired_aximi_default.hex:i -P /dev/ttyACM0
```

To flash onto Nano:

```sh
avrdude -p atmega328p -c arduino -U flash:w:handwired_aximi_default.hex:i -P /dev/ttyUSB0
```

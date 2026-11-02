# Keyboard 01 — Vial firmware

Same Dactyl-Manuform 5x6 (62 keys) hardware as `../keymap/`, but built with
**Vial** so keys are remapped live in the Vial app. No recompile, no reflash.

Layout, layers and thumb keys are copied from `../keymap/keymap.c`
(BASE / LOWER / RAISE, plus one spare layer).

| File | Purpose |
|------|---------|
| `info.json` | Pins, split config, 62-key `LAYOUT` (same matrix as `../keymap/info.json`) |
| `config.h` | `MASTER_LEFT`, Vial table sizes |
| `rules.mk` | Keyboard-level build options (empty) |
| `keymaps/vial/` | `keymap.c`, `config.h` (Vial UID), `rules.mk`, `vial.json` (UI layout) |

## Build setup

Needs the **vial-qmk** fork (`~/dev/forks/vial-qmk`), not mainline QMK. Link this
folder into it once:

```sh
ln -s ~/dev/keyboards/01/vial ~/dev/forks/vial-qmk/keyboards/handwired/dactyl_manuform_62
```

It needs the same avr-gcc workaround flags as keyboard 02. The reasons are in
`../../02/qmk-v3/README.md`, "Required workarounds".

## Compile

```sh
cd ~/dev/forks/vial-qmk
CPATH=/usr/lib/avr/include QMK_HOME=$PWD qmk compile -kb handwired/dactyl_manuform_62 -km vial \
  -e 'EXTRAFLAGS=-Wno-error -mrelax -B/usr/lib/avr/lib/avr5 -L/usr/lib/avr/lib/avr5' \
  -e 'EXTRALDFLAGS=-Wl,--relax'
```

Size: 24670 / 28672 bytes (~4 KB free). `QMK_SETTINGS = no` in
`keymaps/vial/rules.mk` is what makes it fit. Without it the build is ~36 bytes
over. The cost is that Vial's "QMK Settings" tab is missing; everything else works.

## First flash (no reset button)

The boards have no reset button. To enter the bootloader (the mode that accepts
new firmware):

- **Left half (USB master):** hold the `LOWER` thumb key and press `QK_BOOT`
  (`_LOWER`, row 2, far left, in the old firmware). Or hold the top-left key
  (`Esc`) while plugging in USB. Bootmagic is on in this build.
- **Right half:** shorten the Pro Micro `RST` pin to `GND` with tweezers or a
  wire, twice quickly. QK_BOOT only resets the half with USB.

Then flash each half. `-bl avrdude` is a plain flash. It does not write
handedness to EEPROM, because this board uses `MASTER_LEFT` instead of `EE_HANDS`.

```sh
cd ~/dev/forks/vial-qmk
CPATH=/usr/lib/avr/include QMK_HOME=$PWD qmk flash -kb handwired/dactyl_manuform_62 -km vial -bl avrdude \
  -e 'EXTRAFLAGS=-Wno-error -mrelax -B/usr/lib/avr/lib/avr5 -L/usr/lib/avr/lib/avr5' \
  -e 'EXTRALDFLAGS=-Wl,--relax'
```

Run it, then put the half in bootloader mode when it waits. Repeat for the other half.

## After the first flash

Open the Vial app (https://vial.rocks or the desktop app) and remap away.
`QK_BOOT` is on `_LOWER` here, and Vial's "Special" tab also has a Bootloader
key, so later firmware updates need no hardware reset. Keep one on a layer.

Plug USB into the **left** half.

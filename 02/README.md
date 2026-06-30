# Keyboard 02 — aximi

Inspired by: https://github.com/sadekbaroudi/fingerpunch/tree/master/keyboards/ximi/v1

Split 42-key Kailh Choc V1 keyboard. Two Pro Micro (atmega32u4) halves over TRRS serial.

---

## PCB history

### PCB v1 (`pcb/`)

Original single-sided design. Worked well as a left half. No dedicated right PCB.

### PCB v2 (`pcb-left-v1/`, `pcb-right-v1/`)

Intended to be a proper left + right pair. Due to a mirroring error in KiCad the
"right" PCB was generated with all components on the wrong copper layers, making it
effectively a second left. This version went into production — **many copies exist**.

The `pcb-right-v1/` files in this repo have since been corrected (F.Cu ↔ B.Cu layer
swap so hotswap sockets sit on F.Cu and the Pro Micro/TRRS/diodes on B.Cu), but the
boards already ordered match the original two-lefts layout.

### PCB v3 (next production run)

Uses the corrected `pcb-right-v1/` files. True left + right pair, assembles without
any firmware workarounds.

### PCB v4 (`pcb-v4/`) — in progress

Based on the v3 left half. Key change: switching to a reversible Kailh Choc V1 hotswap
footprint (`Kailh_socket_PG1350_reversible`) so the hotswap socket can be soldered on
either side of the board, making a single PCB usable as either left or right half.

**Status:** all 21 switch footprints swapped to `Library:Kailh_socket_PG1350_reversible`
(pads 1 & 2 on both F.Cu and B.Cu). Existing traces will show DRC errors at old pad
positions — open in KiCad, re-route the switch connections, then export Gerbers.

**Next step:** also swap MCU (Pro Micro) and TRRS footprints to reversible variants
(same approach as Lily58), so one PCB truly serves as either half with no orientation
constraint.

---

## Firmware history

### `qmk-v2/` — for PCB v2 (two-lefts production boards)

Because the physical "right" PCB is a left PCB used upside-down, the column pins read
in reverse order on that half. `MATRIX_COL_PINS` is set to `{ B3, B1, F7, F6, F5, F4 }`
(reversed) to compensate. **Keep this config** — it's the correct firmware for all
existing v2 boards.

Flash the left half:
```sh
cd ~/dev/forks/vial-qmk
QMK_HOME=$PWD qmk flash -kb handwired/aximi -km vial -bl avrdude-split-left
```

Flash the right half (which is physically a second left):
```sh
QMK_HOME=$PWD qmk flash -kb handwired/aximi -km vial -bl avrdude-split-right
```

### `qmk-v3/` — for PCB v3 (corrected boards, not yet printed)

Target firmware for the v3 production run. Should not need the column-reversal
workaround since the PCB is properly mirrored. Verify by testing the right half
once assembled before finalising the keymap.

---

## Hardware

### Controller
- Pro Micro (atmega32u4, caterina bootloader)

### Switches
- Kailh Choc Low Profile 1350 (v1) — Crystal Red

### Split link
- TRRS — single serial data wire (`D1`), other two pins VCC/GND

### Trackball (future)
- PMW3360 sensor via SPI — not yet implemented

---

## KiCad

Arduino nano footprint from: https://github.com/g200kg/kicad-lib-arduino

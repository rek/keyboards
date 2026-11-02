# 06 — Lily58 Pro (ZMK, two firmware variants)

A split 58-key Lily58 **Pro** keyboard running **ZMK** on a **nice!nano v2** (a
"ProMicro nRF52840" clone, see `pro-micro-nice-clone.png`) per half. The same
hardware runs either of two firmware variants:

| Variant | Folder | Halves talk over | PC talks to the left over | Power |
|---|---|---|---|---|
| **06a** — Bluetooth | `zmk-config/06a-ble/` | Bluetooth | USB or Bluetooth | LiPo per half |
| **06b** — TRRS wired (current) | `zmk-config/06b-wired/` | TRRS cable | USB only | Left on USB; right fed through the cable |

The 06b hardware rework (W1 cut + two jumper wires per half) doesn't affect
06a, so you can flash either variant at any time.

> **To build/flash firmware, follow [`BUILDING.md`](BUILDING.md)** — the canonical, journey-free procedure.
> Bring-up history and hard-won learnings: [`HANDOFF.md`](HANDOFF.md). Fault finding: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## At a glance

| | |
|---|---|
| **Board** | Lily58 **Pro** (Pro Micro footprint + Kailh hotswap sockets) |
| **PCB design source** | `~/dev/keyboard-clones/Lily58/Pro/PCB/Lily58_Pro.kicad_pcb` |
| **Fabbed gerbers** | `pcb/production/` (front copper + edge cuts) — board renders in `pcb/` |
| **Controller** | nice!nano v2 (nRF52840) → firmware is **ZMK**, not QMK |
| **Firmware** | `zmk-config/06a-ble/` and `zmk-config/06b-wired/`, shared `zmk-config/build-flash.sh` |
| **Case** | `case/v1/` STLs |
| **Matrix** | 5 rows × 6 cols per half |
| **Status** | ✅ **06b working end-to-end** (2026-11-01): both halves over TRRS, left on USB, **ZMK Studio** for live key editing. 06a verified 2026-07-06 (Bluetooth + batteries). |

## ⚠️ The big gotcha: the controllers sit in the reversed hole-set

The Lily58 Pro controller footprint is **reversible** — two staggered hole-sets
per side. **Both nice!nanos are soldered into the "swapped" set**, which swaps
the controller's two pin rows. Every footprint net therefore lands on a
different nice!nano pin than the PCB intends:

- **Key matrix:** rows and cols swap. Fixed in firmware (no desoldering) by the
  kscan remap in each variant's `config/lily58.keymap`:

  | | row0–4 | col0–5 |
  |---|---|---|
  | stock shield | pro_micro `5,6,7,8,9` (D5–D9) | `19,18,15,14,16,10` |
  | **our left remap** | pro_micro `18,15,14,16,10` (D18,D15,D14,D16,D10) | `4,5,6,7,8,9` (D4–D9) |
  | **our right remap** | same rows | `9,8,7,6,5,4` (mirrored) |

- **TRRS jack (J2):** its power and DATA lines hit the wrong controller pins.
  Harmless for 06a (Bluetooth never uses the jack). 06b needs the hardware
  rework below.

## 06b: wired split (TRRS)

ZMK's wired split is full-duplex UART, so it needs **two** data wires. Because
of the reversed hole-set, J2's lines actually reach:

| J2 pad | PCB net | Really hits on the nice!nano |
|---|---|---|
| 1 | VCC | GND |
| 2 | GND | VCC 3.3V (and RST, P0.08) |
| 3 | DATA | GND, through the W1 jumper — unusable as is |
| 4 | — (P1 pad only) | nothing until hand-wired |

**Rework, on both halves** (picture: [`trrs-rework-guide.png`](trrs-rework-guide.png);
step-by-step: [`BUILDING.md`](BUILDING.md#06b-trrs-hardware-rework-one-time)):

1. Wire **P1** to controller hole **6** (nice!nano **P0.29**).
2. **Cut W1** (top side, next to P1/P2) so DATA is no longer grounded.
3. Wire J2's **DATA leg** to controller hole **5** (nice!nano **P0.31**).

The firmware pins live in
[`zmk-config/06b-wired/config/lily58-wired-pins.h`](zmk-config/06b-wired/config/lily58-wired-pins.h):
left sends on P0.31 and listens on P0.29; the right is the mirror.

- **Use a 4-contact TRRS cable**, not a 3-contact TRS one (its sleeve bridges two jack contacts).
- **Never plug or unplug the TRRS cable while either half has power** (USB or
  battery). ZMK's docs warn it can permanently damage the controllers.
- The right half is powered through the cable (pads 1/2 tie the two halves'
  GND and 3.3V rails). Switch its battery off or remove it.
- Bluetooth is off (`CONFIG_ZMK_BLE=n`), so there are no bonds, no output
  endpoint to get stuck, and no host battery readout.

## Build & flash

Local toolchain lives at `~/dev/zmk-workspace` (west venv + ZMK `main`, uses
system `arm-none-eabi-gcc`, no Zephyr SDK).

```sh
# from this folder; first argument picks the variant:
zmk-config/build-flash.sh 06b left      # build + flash left half (TRRS)
zmk-config/build-flash.sh 06b right     # right half
zmk-config/build-flash.sh 06a left      # same, Bluetooth variant
```

To flash: double-tap RESET on the target nice!nano so the `NICENANO` drive
appears, then run the command. It picks the drive by USB serial, so it never
flashes the wrong half. Full details in [`BUILDING.md`](BUILDING.md).

A cloud build of both variants runs at repo root: `.github/workflows/lilly58.yml`.

## Battery (06a)

The Lily58 Pro has **no battery provision** (it's a wired design). The LiPo wires directly to the nice!nano's **`B+` / `B-`** pads (at the USB end, overhanging the top board edge).

- **Polarity is critical:** red → `B+`, black → `B-`. Reversing kills the nice!nano.
- nice!nano charges the cell over USB at **~100 mA** (no separate charger). Bigger cell = longer charge (750 mAh ≈ 7–8 h).
- Any capacity works electrically (110–1000 mAh+); limited only by **case space** + charge time. ZMK sips power → weeks–months per charge.
- Recommended: a small **slide switch** in series with one battery lead for a true power-off.
- Use thin 30 AWG / magnet wire; secure the cell so it can't be punctured.
- ❌ Do **not** wire the battery to `RAW`/`GND` — that bypasses charging.

To show both halves' charge in a desktop status bar, see
[`HOST-BATTERY.md`](HOST-BATTERY.md) — the right half is proxied as a second BLE
battery service and needs a GATT walk to read, and there is **no** battery
readout over USB at all.

## What the extra PCB holes are

Near the controller: `RESET` (reset button), and the **I²C section** — `R1`/`R2`
(SDA/SCL pull-up resistors), `P1`/`P2` (breakout pads), `W1` (DATA solder
jumper), `J2` (TRRS jack, `MJ-4PP-9`). `J2`, `P1` and `W1` are used by the 06b
rework. `R1`/`R2` are only needed for the I²C **OLED** screen (then also enable
`CONFIG_ZMK_DISPLAY` in `lily58.conf`) — but with the reversed hole-set, SDA/SCL
land on P0.31/P0.29, which 06b now uses for the split link.

## To-do

- [ ] Check the solder joints on the few dead keys.
- [ ] Mirror the ZMK Studio edits (e.g. the right inner key) back into
      `06b-wired/config/lily58.keymap`, so a rebuild or reset doesn't lose them.
- [ ] Verify battery runtime on 06a.
- [ ] Optional: move the kscan overrides into the `lily58_*.overlay` files
      (more idiomatic than in `.keymap`).

## Debugging notes (full detail in [`HANDOFF.md`](HANDOFF.md) and [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md))

- **Label the halves L/R.** Each half's USB serial (left `3A8F02D9AD37EF58`,
  right `EC93E089067872A6`) is the same in bootloader mode, which is how
  `build-flash.sh` tells them apart.
- **Charge-only cables** = board powers (LED on) but nothing enumerates on USB
  (not even the bootloader drive). Use a known data cable, straight to the PC.
- **A peripheral (right) doesn't type over USB alone** — test it with the
  central. The `CONFIG_ZMK_SPLIT=n` standalone trick gives **false negatives**.
- **06b link dead?** `build-flash.sh <variant> <side> --log` builds a USB-logging
  image. The right logs every split message it sends; the left logs anything it
  receives (even garbage). See `BUILDING.md`.
- **06a: output endpoint (USB vs BLE) persists in flash and survives reflashing.**
  Fix with `&out OUT_USB` or the `settings_reset` shield, not reflashing.

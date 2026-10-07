# 06 — Lily58 Pro (wireless)

A split 58-key Lily58 **Pro** keyboard running **wireless ZMK** on a **nice!nano v2** per half.

> 📌 **Bring-up in progress — if you're picking this up, read [`HANDOFF.md`](HANDOFF.md) first.**
> It has the current state, all hard-won learnings, and the exact clean-restart steps.
> **To build/flash firmware, follow [`BUILDING.md`](BUILDING.md)** — the canonical, journey-free procedure.

## At a glance

| | |
|---|---|
| **Board** | Lily58 **Pro** (Pro Micro footprint + Kailh hotswap sockets) |
| **PCB design source** | `~/dev/keyboard-clones/Lily58/Pro/PCB/Lily58_Pro.kicad_pcb` |
| **Fabbed gerbers** | `pcb/production/` (front copper + edge cuts) — board renders in `pcb/` |
| **Controller** | nice!nano v2 (nRF52840, BLE) → firmware is **ZMK**, not QMK (QMK can't do BLE here) |
| **Firmware** | `zmk-config/` (this folder) |
| **Case** | `case/v1/` STLs |
| **Matrix** | 5 rows × 6 cols per half |
| **Status** | ✅ **Working end-to-end** (2026-07-05): both halves remapped, bonded, typing over USB and host Bluetooth, batteries connected. **ZMK Studio enabled** for live key editing (see [`BUILDING.md`](BUILDING.md)). Remaining: install all switches, verify battery runtime, OLEDs. |

## ⚠️ The big gotcha: rows/cols are remapped

The Lily58 Pro controller footprint is **reversible** — two staggered hole-sets per side, and **the two sets swap rows ↔ columns** (outer columns = rows, inner columns = cols). The nice!nano on the left half was soldered into the **rightmost set**, so the stock `lily58` shield drove the wrong pins → *every key dead despite perfect soldering*.

**Fix (no desoldering):** `zmk-config/config/lily58.keymap` overrides `&kscan0`:

| | row0–4 | col0–5 |
|---|---|---|
| stock shield | pro_micro `5,6,7,8,9` (D5–D9) | `19,18,15,14,16,10` |
| **our remap** | pro_micro `18,15,14,16,10` (D18,D15,D14,D16,D10) | `4,5,6,7,8,9` (D4–D9) |

> When building the **right half**: if its nice!nano goes into the same set, it needs the same remap — verify, the mirror may differ.

## Build & flash

Local toolchain lives at `~/dev/zmk-workspace` (west venv + ZMK `main`, uses system `arm-none-eabi-gcc`, no Zephyr SDK).

```sh
# from this folder:
zmk-config/build-flash.sh left      # build + flash left half
zmk-config/build-flash.sh right     # right half
```

To flash: double-tap RESET on the target nice!nano so the `NICENANO` drive appears, then the script copies the `.uf2`. Board id is `nice_nano@2.0.0/nrf52840/zmk` (ZMK main / hardware-model-v2 — **not** the old `nice_nano_v2`). The build stages config to a space-free path because this folder name has spaces.

A cloud-build fallback exists at repo root: `.github/workflows/lilly58.yml`.

## Bluetooth

Halves talk over BLE (no TRRS needed). Pairing controls are on the **raise** layer: `BT_SEL 0–4` to switch profiles, `BT_CLR` to clear a stuck pairing.

## Battery

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

## What the extra PCB holes are (all optional for wireless)

Near the controller: `RESET` (reset button), and the **I²C section** — `R1`/`R2` (SDA/SCL pull-up resistors), `P1`/`P2` (I²C breakout pads), `J2` (TRRS jack, `MJ-4PP-9`). These exist for the **wired QMK** build (halves talk over I²C through the TRRS cable) and the OLED. **For our wireless build none are needed** — only populate `R1`/`R2` if you add the I²C **OLED** screen (then also enable `CONFIG_ZMK_DISPLAY` in `lily58.conf`).

## To-do

**Immediate (see [`HANDOFF.md`](HANDOFF.md) for the exact clean-restart steps):**
- [ ] Verify the **right half** end-to-end: `settings_reset` both halves → reflash normal → pair → press right switch through the central. Right is believed correct on **stock** wiring.
- [ ] Confirm the left outputs to **USB** after `settings_reset` (kills the sticky-Bluetooth-output bug).

**After it works:**
- [ ] Install the remaining switches (both halves).
- [ ] Wire the battery (+ optional power switch) to both nice!nanos.
- [ ] Set output deliberately (`&out OUT_USB` if you want USB by default).
- [ ] Optional: OLED (populate `R1`/`R2`, enable `CONFIG_ZMK_DISPLAY`).
- [ ] Optional: move the left kscan override into a `lily58_left.overlay` (more idiomatic than in `.keymap`).

## Debugging notes (things that wasted time — full detail in [`HANDOFF.md`](HANDOFF.md))

- **Output endpoint (USB vs BLE) persists in flash and survives reflashing** — the #1 time-sink. Fix with `&out OUT_USB` or the `settings_reset` shield, not reflashing. Watch **both** the USB and Bluetooth `event-kbd` devices when testing.
- **Charge-only cables** = board powers (LED on) but nothing enumerates on USB (not even the bootloader drive). Use a known data cable, straight to the PC.
- **A peripheral (right) doesn't type over USB alone** — test it paired with the central. The `CONFIG_ZMK_SPLIT=n` standalone trick gives **false negatives** — don't trust it.
- **USB serial logging builds hang at boot** here (known ZMK bugs) — avoid.
- **Label the halves L/R** — juggling one cable between unlabelled boards scrambled which firmware was where.

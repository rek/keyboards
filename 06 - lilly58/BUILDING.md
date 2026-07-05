# Lily58 Pro (wireless) — Canonical Build & Flash Reference

Procedure only. For history/debugging context see `HANDOFF.md`.

## The build in one paragraph

Lily58 Pro split, one **nice!nano v2** per half, firmware is **ZMK** (tracking
`main`). Left = split **central** with a **custom kscan remap**; right = split
**peripheral** with **stock** wiring. Build locally with
`zmk-config/build-flash.sh <left|right>`, flash by double-tap RESET →
`NICENANO` USB drive → copy the `.uf2`.

## Hardware constants (do not rediscover these)

- The Lily58 Pro controller footprint is **reversible**: two staggered hole-sets
  per side, and the sets **swap rows↔columns** (outer hole-columns = row nets,
  inner = col nets).
- **BOTH nice!nanos are soldered in the "swapped" set** → **both require remaps**
  (in `config/lily58.keymap`, confirmed working 2026-07-05). Same rows; the
  right's columns are reversed because the right half is the same PCB flipped.
- Pin maps (pro_micro numbering):

  | build | rows 0–4 | cols 0–5 |
  |---|---|---|
  | left (remap) | `18 15 14 16 10` | `4 5 6 7 8 9` |
  | right (remap) | `18 15 14 16 10` | `9 8 7 6 5 4` |
  | (stock shield, NOT what this build uses) | `5 6 7 8 9` | left `19 18 15 14 16 10` / right `10 16 14 15 18 19` |

- Reset: double-tap = bootloader (LED pulses **red**, `NICENANO` drive appears).
  Flashing blue = app firmware running. Bootloader always works regardless of
  app state.
- Only use a known **data** USB cable, plugged straight into the PC.

## One-time toolchain setup (new machine)

Arch packages: `arm-none-eabi-gcc arm-none-eabi-newlib cmake ninja dtc python`.
No Zephyr SDK needed.

```sh
mkdir -p ~/dev/zmk-workspace && cd ~/dev/zmk-workspace
python -m venv .venv
.venv/bin/pip install west
git clone https://github.com/zmkfirmware/zmk.git
cd zmk
../.venv/bin/west init -l app
../.venv/bin/west update            # pulls zephyr/ + modules/ (large, one-time)
../.venv/bin/pip install -r zephyr/scripts/requirements.txt
../.venv/bin/pip install protobuf grpcio-tools   # required by ZMK Studio builds (nanopb)
```

Layout after setup: `~/dev/zmk-workspace/{.venv, zmk/{app, zephyr, modules, build}}`.

## Build + flash (the canonical path)

```sh
"06 - lilly58/zmk-config/build-flash.sh" left            # build + flash left
"06 - lilly58/zmk-config/build-flash.sh" right           # build + flash right
"06 - lilly58/zmk-config/build-flash.sh" left --no-flash # build only
```

The script encapsulates three **mandatory** quirks — if building by hand, you
must reproduce all three:

1. **Board id** (ZMK main = Zephyr hardware-model-v2):
   `nice_nano@2.0.0/nrf52840/zmk` — *not* `nice_nano_v2`.
2. **Space-free config staging**: this repo path contains spaces, which break
   the devicetree preprocessor. The script copies `config/` to
   `~/dev/zmk-workspace/lily58-config` and builds from there.
3. **Shield define injection for the keymap guard**: devicetree (including the
   keymap) is preprocessed **before** Kconfig, so `#ifdef
   CONFIG_SHIELD_LILY58_LEFT` in the keymap is invisible unless passed
   explicitly: `-DDTS_EXTRA_CPPFLAGS="-DCONFIG_SHIELD_LILY58_LEFT"` (resp.
   `_RIGHT`). **Omitting this silently builds the left with stock pins → zero
   keystrokes.**

Equivalent manual command:

```sh
cd ~/dev/zmk-workspace/zmk
export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb GNUARMEMB_TOOLCHAIN_PATH=/usr
PATH=~/dev/zmk-workspace/.venv/bin:$PATH west build -s app -d build/left -p \
  -b "nice_nano@2.0.0/nrf52840/zmk" -- \
  -DSHIELD=lily58_left -DZMK_CONFIG=~/dev/zmk-workspace/lily58-config \
  -DDTS_EXTRA_CPPFLAGS="-DCONFIG_SHIELD_LILY58_LEFT"
```

**Always verify the image before flashing** (guards against the silent-stock-pins failure):

```sh
grep -A6 'kscan0: kscan' ~/dev/zmk-workspace/zmk/build/left/zephyr/zephyr.dts
# BOTH halves MUST show rows 0x12 0xf 0xe 0x10 0xa.
# left cols MUST be 0x4 0x5 0x6 0x7 0x8 0x9; right cols 0x9 0x8 0x7 0x6 0x5 0x4.
# If you see rows 0x5–0x9, the remap got dropped — do not flash.
```

Flash: double-tap RESET → mount the `NICENANO` drive → copy
`build/<side>/zephyr/zmk.uf2` onto it → it unmounts and reboots itself.

The settings-reset image is built the same way with `-DSHIELD=settings_reset`
(no define needed); a prebuilt copy lives at `build/reset/zephyr/zmk.uf2`.

## ZMK Studio (live keymap editing, no reflash per change)

The daily-driver **left** image is the Studio-enabled one at `build/left-studio`
(flashed 2026-07-05). Build it with:

```sh
cd ~/dev/zmk-workspace/zmk
export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb GNUARMEMB_TOOLCHAIN_PATH=/usr
PATH=~/dev/zmk-workspace/.venv/bin:$PATH west build -s app -d build/left-studio \
  -b "nice_nano@2.0.0/nrf52840/zmk" -S studio-rpc-usb-uart -- \
  -DSHIELD=lily58_left -DZMK_CONFIG=~/dev/zmk-workspace/lily58-config \
  -DCONFIG_ZMK_STUDIO=y -DDTS_EXTRA_CPPFLAGS="-DCONFIG_SHIELD_LILY58_LEFT"
```

- Needs `protobuf`/`grpcio-tools` in the venv (see toolchain setup). If the build
  fails once right after installing them, just re-run it.
- **Verify the kscan pins in `zephyr.dts` like any other build before flashing.**
- Usage: https://zmk.studio in a Chromium browser → Connect → the Lily58 serial
  port → unlock with **RAISE + top-right key of the right half** (`&studio_unlock`
  in the keymap). Only the left/central talks to Studio. Edits persist on-device.
- Serial-port access is granted by `/etc/udev/rules.d/50-zmk-studio.rules`
  (`uaccess` tag for VID:PID `1d50:615e`).
- Studio edits live in the keyboard's settings storage, NOT in `lily58.keymap` —
  a `settings_reset` wipes them, and the `.keymap` file is what rebuilds use.
  Mirror any layout you want to keep back into the file.
- The plain (non-Studio) left image remains at `build/left`.

## Clean pairing procedure (whenever bonds/output are suspect)

Order matters; one board plugged in at a time.

1. Left: double-tap → flash `settings_reset` → let boot 5 s → double-tap →
   flash `build/left`.
2. Unplug left. Right: same two-step with `build/right`.
3. Power both together (left USB, right battery). They auto-bond in ~10–15 s.
4. All typing (both halves) comes out of the **left/central**. The right never
   types over USB by itself — that is normal, not a fault.

Why the reset step: ZMK persists the chosen output endpoint (USB/BLE) and the
split bond **in flash; both survive reflashing**. A stale BLE endpoint sends
keystrokes into the void; a half-reset bond pair won't re-pair. `settings_reset`
on **both** halves clears both problems.

## Verifying keystrokes on this machine (Arch + keyd + Hyprland)

**keyd grabs all keyboards exclusively** (`/etc/keyd/default.conf` has
`[ids] *`), so the Lily58's raw evdev node shows nothing; events surface on
keyd's virtual device. The reliable check, with device attribution:

```sh
sudo keyd monitor        # press a key; look for lines from "ZMK Project Lily58"
```

Expected on the left half's bring-up switch (closest to MCU): `5`.
A working board also enumerates as `lsusb` → `1d50:615e OpenMoko, Inc. Lily58`.

## Do not

- Do not use the `zmk-usb-logging` left build (`build/left-log`) — hangs at boot.
- Do not use the `CONFIG_ZMK_SPLIT=n` standalone right test — false negatives.
- Do not test with both halves being juggled on one cable — label boards L/R,
  finish one board completely before touching the other.

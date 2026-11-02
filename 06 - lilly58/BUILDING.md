# Lily58 Pro — Canonical Build & Flash Reference (06a Bluetooth / 06b TRRS)

Procedure only. For history/debugging context see `HANDOFF.md`.

## The build in one paragraph

Lily58 Pro split, one **nice!nano v2** per half, firmware is **ZMK** (tracking
`main`). Left = split **central**, right = split **peripheral**, both with a
**custom kscan remap**. Two firmware variants share the hardware:
**06a** (`zmk-config/06a-ble/`, Bluetooth split, batteries) and **06b**
(`zmk-config/06b-wired/`, TRRS wired split, left on USB; needs the one-time
[hardware rework](#06b-trrs-hardware-rework-one-time)). Build locally with
`zmk-config/build-flash.sh <06a|06b> <left|right>`, flash by double-tap RESET →
`NICENANO` USB drive → the script copies the `.uf2`.

## Hardware constants (do not rediscover these)

- The Lily58 Pro controller footprint is **reversible**: two staggered hole-sets
  per side, and the sets **swap rows↔columns** (outer hole-columns = row nets,
  inner = col nets).
- **BOTH nice!nanos are soldered in the "swapped" set** → **both require remaps**
  (in each variant's `config/lily58.keymap`, confirmed working 2026-07-05). Same rows; the
  right's columns are reversed because the right half is the same PCB flipped.
- Pin maps (pro_micro numbering):

  | build | rows 0–4 | cols 0–5 |
  |---|---|---|
  | left (remap) | `18 15 14 16 10` | `4 5 6 7 8 9` |
  | right (remap) | `18 15 14 16 10` | `9 8 7 6 5 4` |
  | (stock shield, NOT what this build uses) | `5 6 7 8 9` | left `19 18 15 14 16 10` / right `10 16 14 15 18 19` |

- The swapped set also moves the TRRS jack's lines onto the wrong controller
  pins (DATA lands on GND). Irrelevant to 06a; 06b needs the rework below.
- USB serials (identical in bootloader mode): left `3A8F02D9AD37EF58`, right
  `EC93E089067872A6`. `build-flash.sh` flashes by serial.
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
"06 - lilly58/zmk-config/build-flash.sh" 06b left            # 06b left: Studio
"06 - lilly58/zmk-config/build-flash.sh" 06b right           # 06b right half (peripheral)
"06 - lilly58/zmk-config/build-flash.sh" 06a left            # 06a left: Studio + battery proxy
"06 - lilly58/zmk-config/build-flash.sh" 06a left --no-batt  # 06a fallback: battery proxy OFF
"06 - lilly58/zmk-config/build-flash.sh" 06a right           # 06a right half
"06 - lilly58/zmk-config/build-flash.sh" 06b left --no-flash # any of the above, build only
"06 - lilly58/zmk-config/build-flash.sh" 06b right --log     # USB-logging image (see below)
```

Images land in `~/dev/zmk-workspace/zmk/build/<variant>-<dir>`, e.g.
`build/06b-left-studio`, `build/06a-right`. **Flash both halves with the same
variant** — a 06a half and a 06b half can't talk to each other.

Flashing picks the `NICENANO` drive by USB serial, so it refuses to flash the
wrong half (2026-11-01: a left image once went onto the right because both
were in bootloader mode). Both halves may be in bootloader mode at once.

Left images, all ZMK-Studio-enabled:

- **`06b left`** → `build/06b-left-studio` — the 06b canonical image.
- **`06a left`** → `build/06a-left-studio` — the 06a canonical image: Studio + per-half
  battery reporting to the host (verified end-to-end 2026-07-06).
- **`06a left --no-batt`** → `build/06a-left-studio-nobat` — identical minus the second
  battery GATT service (disabled via Kconfig CLI overrides, which beat
  `lily58_left.conf`). Diagnostic fallback only: flash it to rule the dual
  battery service out if some host refuses to pair. Not fully re-tested since
  the battery path became canonical — expect to fix it up before relying on it.

The script encapsulates three **mandatory** quirks — if building by hand, you
must reproduce all three:

1. **Board id** (ZMK main = Zephyr hardware-model-v2):
   `nice_nano@2.0.0/nrf52840/zmk` — *not* `nice_nano_v2`.
2. **Space-free config staging**: this repo path contains spaces, which break
   the devicetree preprocessor. The script copies `<variant>/config/` to
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
grep -A6 'kscan0: kscan' ~/dev/zmk-workspace/zmk/build/<dir>/zephyr/zephyr.dts
# <dir> = 06b-left-studio | 06b-right | 06a-left-studio | 06a-left-studio-nobat | 06a-right
# BOTH halves MUST show rows 0x12 0xf 0xe 0x10 0xa.
# left cols MUST be 0x4 0x5 0x6 0x7 0x8 0x9; right cols 0x9 0x8 0x7 0x6 0x5 0x4.
# If you see rows 0x5–0x9, the remap got dropped — do not flash.
```

For 06b the script also prints the UART pins; they must read left `RX
0x100001d TX 0x1f`, right `RX 0x100001f TX 0x1d` (P0.29 / P0.31).
`zmk-config/doctor.sh check` re-runs the kscan check on every built image.

Flash by hand: double-tap RESET → mount the `NICENANO` drive → copy
`build/<dir>/zephyr/zmk.uf2` onto it → it unmounts and reboots itself.

The settings-reset image is built the same way with `-DSHIELD=settings_reset`
(no define needed); a prebuilt copy lives at `build/reset/zephyr/zmk.uf2`.

## ZMK Studio (live keymap editing, no reflash per change)

**Every left image the script produces is Studio-enabled** (except `--log`) —
`build-flash.sh <variant> left` is all you need (it adds `-S studio-rpc-usb-uart` +
`-DCONFIG_ZMK_STUDIO=y` itself). Equivalent manual command:

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
- The only scripted non-Studio left image is `--log` (Studio and USB logging
  both want the USB CDC channel).

## 06b: TRRS hardware rework (one-time)

Done on both halves 2026-11-01. Needed because the reversed hole-set leaves J2
with only one usable line (see `README.md`). Picture with every spot marked:
[`trrs-rework-guide.png`](trrs-rework-guide.png) (left = top side, right =
bottom side, jack at the top). "Hole N" counts the controller holes from the
USB/jack end in the **outer row-net column**: from the bottom it's the left-hand
column; hole 3 beeps against J2's middle leg.

1. **First jumper:** wire the **P1** pad to **hole 6** (nice!nano P0.29).
2. **Cut W1** (top side): the tiny two-pad jumper just past P2, toward the
   controller. Remove the solder blob, or cut the thin copper link between the
   pads with a craft knife.
   Check: J2's **DATA leg** (of the three legs in a row, the one nearest the
   board's top edge, farthest from the lone fourth leg) against **hole 2** must
   **not** beep any more.
3. **Second jumper:** wire the DATA leg to **hole 5** (nice!nano P0.31).
4. Meter checks, unpowered:

   | Probe A | Probe B | Expected |
   |---|---|---|
   | DATA leg | hole 5 | beep |
   | P1 pad | hole 6 | beep |
   | hole 5 | hole 2 (GND) | silent |
   | hole 5 | hole 6 | silent |
   | DATA leg | hole 2 (GND) | silent |

5. With the TRRS cable in and both halves unpowered, hole 5 ↔ hole 5 and
   hole 6 ↔ hole 6 across the two halves should beep.

Meter gotcha: hole 3 (PCB "GND") is really the nice!nano's **3.3V** rail. Use
hole 2 or the jack's lone-side end leg as the voltage reference, or readings
come out inverted.

## 06b: verifying the wired link

Left on USB, TRRS cable in, type on the right half. If nothing arrives:

1. `build-flash.sh 06b right --log` and `build-flash.sh 06b left --log`, flash
   both, then record both serial ports while pressing right-half keys:
   ```sh
   for s in /dev/serial/by-id/usb-ZMK_Project_*; do stty -F "$s" raw -echo; done
   timeout 45 cat /dev/serial/by-id/usb-ZMK_Project_Lily58_* > left.log &
   timeout 45 cat /dev/serial/by-id/usb-ZMK_Project_615e_* > right.log
   ```
   (The right shows up as `615e`, the left as `Lily58`.)
2. Right log shows `split_peripheral_wired_report_event: Payload` per key, so
   the right scans and queues. Left log silent, with not even `Prefix mismatch`
   warnings, means **no signal reaches the left's RX pin**: wiring, wrong
   pin, or DATA still grounded. Garbage or CRC warnings mean a signal arrives
   but is corrupted.
3. Voltages, TRRS cable **unplugged**, both halves running: the left's TX hole
   (hole 5) idles at **3.3V**. A transmit hole reading 0V is not the pin the
   firmware thinks it is.
4. Reflash the normal images afterwards (`--log` drops Studio on the left).

## 06a: clean pairing procedure (whenever bonds/output are suspect)

Order matters; one board plugged in at a time.

1. Left: double-tap → flash `settings_reset` → let boot 5 s → double-tap →
   flash `build/06a-left-studio`.
2. Unplug left. Right: same two-step with `build/06a-right`.
3. Power both together (left USB, right battery). They auto-bond in ~10–15 s.
4. All typing (both halves) comes out of the **left/central**. The right never
   types over USB by itself — that is normal, not a fault.

Why the reset step: ZMK persists the chosen output endpoint (USB/BLE) and the
split bond **in flash; both survive reflashing**. A stale BLE endpoint sends
keystrokes into the void; a half-reset bond pair won't re-pair. `settings_reset`
on **both** halves clears both problems.

## 06a: pairing to a Linux host (bluetoothctl)

A plain `bluetoothctl pair <MAC>` one-shot **fails with
`org.bluez.Error.AuthenticationFailed`** even when everything is healthy —
pairing must run in an interactive session with an agent registered. And if the
keyboard's active BT profile holds a stale bond for this host (after a
`settings_reset`, host reinstall, etc.), it rejects pairing until cleared.
Both fixes, in order (2026-07-06, cost an evening):

1. **Keyboard**: clear the active profile's bond — hold **RAISE** (right-half
   thumb key right of Enter) + tap **ESC** (top-left key) = `&bt BT_CLR`.
   Needs both halves on and linked. RAISE + number-row 1–5 selects profiles
   0–4 if you want to keep other hosts' bonds.
2. **Host** (interactive `bluetoothctl`):

   ```
   remove <MAC>          # drop any half-dead host-side entry first
   agent NoInputNoOutput
   default-agent
   scan on               # wait for "Lily58" to appear
   pair <MAC>
   trust <MAC>           # required for auto-reconnect
   connect <MAC>
   ```

No passkey is configured — pairing is BLE "Just Works". Verify with
`bluetoothctl info <MAC>`: Paired/Bonded/Trusted/Connected all `yes`, and the
device appears in `/proc/bus/input/devices` as `Lily58 Keyboard`.

### Symptom → cause: bonds and the output endpoint (2026-08-15, cost a session)

Two independent faults that both present as "the keyboard doesn't work", and
which mimic each other closely enough to send you chasing cables for hours.

**1. Stale bond — the keyboard's key outlives the host's.**
BLE bonding is symmetric: host and keyboard each store their own LTK, and the
protocol has **no message meaning "I deleted your key"**. Clicking *Forget* /
*Remove* in a desktop Bluetooth UI wipes only the host's copy (a plain
*Disconnect* is harmless — the two sit next to each other in most UIs). The
keyboard then reconnects with an LTK the host can't match. Signatures:

- `LE.Disconnected — org.bluez.Reason.Local, terminated by local host`, on a loop
- `bluetoothctl pair` **hangs with no result**, and the next command returns
  `org.bluez.Error.InProgress` because the first request is still pending
- `Paired: no` / `Bonded: no` while `Connected` flaps yes/no
- **Or the keyboard stops advertising entirely** — ZMK only advertises on an
  *unbonded* profile, so a slot bonded to another host goes silent. A scan that
  sees other devices but never `Lily58` means "bonded elsewhere", not "dead".

The spec's own escape hatch (host replies SMP `0x06` "PIN or Key Missing",
peripheral drops its bond and re-pairs) is **not reliably acted on by ZMK** —
sticky profiles are a deliberate tradeoff. `BT_CLR` is the intended fix, but its
effect is unverifiable from the host, and it spans BOTH halves (RAISE is on the
right, `BT_CLR` on the left) so it silently does nothing if the split link is
down. When in doubt skip it and use `settings_reset` on both halves — that is
the only fix that can be *confirmed*.

**2. Output endpoint stuck on BLE — "types for a few seconds, then stops".**
The classic misdiagnosis. After a reset the board types over USB, then seconds
later goes dead while `lsusb` still shows it and no USB error appears. It has
not crashed: a BLE profile connected, ZMK moved its HID endpoint there, and the
keystrokes now vanish into a half-open link. Distinguish in one command:

```sh
journalctl -k --since "5 min ago" | grep -iE "usb 3-|disconnect"
```

- **`USB disconnect` + re-enumeration** → real USB fault (cable, worn micro-USB
  jack, unpowered hub). Device number climbing across a session is the tell.
- **No USB events at all** → the endpoint moved. Not a hardware problem.

To break the loop while diagnosing, stop the host accepting the link at all:
`bluetoothctl block <MAC>` (reverse with `unblock`). USB then keeps the
endpoint. Since 2026-08-15 the config prevents this by construction —
`CONFIG_ZMK_USB=y` in `lily58.conf` makes USB win whenever a cable is present,
and RAISE + `6`/`7`/`8` = `&out OUT_USB` / `OUT_BLE` / `OUT_TOG` for a manual
override. Before that the keymap had no `&out` bind at all, so a stuck endpoint
could only be cleared by `settings_reset`.

## 06a: battery levels (both halves)

The canonical left image exposes **two** GATT Battery Services (0x180f) to the
host: the primary = left/central, a secondary = right/peripheral, proxied over
the split link (`lily58_left.conf`: `..._BATTERY_LEVEL_FETCHING` + `_PROXY`).

- The peripheral reports every **60 s** once its split link is up; until the
  first report (or while the right is asleep/off) the proxy reads **0** — not a
  fault.
- **`upower` and desktop BT menus only show the FIRST battery instance** (the
  left half). Read both directly (service handles from `gatt.list-attributes`;
  on this machine left = `service0010/char0011`, right = `service0015/char0016`):

  ```sh
  busctl call org.bluez /org/bluez/hci0/dev_<MAC_>/service0015/char0016 \
    org.bluez.GattCharacteristic1 ReadValue 'a{sv}' 0   # right half, e.g. "ay 1 75"
  ```

  (`bluetoothctl`'s gatt output is full of ANSI escapes — busctl is the
  scriptable path.) ZMK Studio also shows both halves.
- A half on USB reads ~100% while charging.
- If a host ever refuses to pair and you suspect the dual battery service,
  `build-flash.sh 06a left --no-batt` produces the same image minus the second
  service. (The one time this was suspected, it was innocent — see the pairing
  section above.)

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

- Do not combine `zmk-usb-logging` with Studio on the left — that combination
  hung at boot. `--log` turns Studio off and works (verified 2026-11-01).
- Do not plug or unplug the TRRS cable while either half has power.
- Do not mix variants: both halves must run 06a, or both 06b.
- Do not use the `CONFIG_ZMK_SPLIT=n` standalone right test — false negatives.
- Do not test with both halves being juggled on one cable — label boards L/R,
  finish one board completely before touching the other.

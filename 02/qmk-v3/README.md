# aximi v3 — QMK / Vial firmware

The **v3** build of keyboard `02` (aximi): target firmware for the **v3 PCB**
(corrected left + right pair). Same hardware as v2 — **split** keyboard, two
**Pro Micro (atmega32u4, caterina bootloader)** halves over TRRS serial, running
**Vial** — but the v3 PCB is properly mirrored so no column-reversal workaround
is needed.

> **Not yet in production** — update and verify this config once the v3 PCBs are
> assembled and tested. In particular, confirm whether `MATRIX_COL_PINS` needs
> adjustment on the right half before finalising the keymap.

> `../qmk-v2` is the firmware for the existing v2 production boards (two-lefts);
> keep that config intact for flashing those.

## Layout of this folder

| File | Purpose |
|------|---------|
| `info.json` | Metadata + the 42-key split `LAYOUT` (rows 0–3 = left, 4–7 = right) |
| `config.h` | Matrix pins, split serial pin, handedness (`EE_HANDS`), Vial entry counts |
| `rules.mk` | Keyboard-level build options |
| `keymaps/vial/` | The real keymap: `keymap.c`, `config.h` (Vial UID), `rules.mk`, `vial.json` |

### Hardware (from build notes)
- Rows: `D4, C6, D7, E6` · Cols: `B3, B1, F7, F6, F5, F4` · diode `COL2ROW`
- Split serial data pin: `D1` (the single TRRS data line; other two pins are VCC/GND)
- Handedness: **`EE_HANDS`** — each half stores L/R in EEPROM, written at flash time
  (see flashing below). With `SPLIT_USB_DETECT` either half can be the USB host.

### Keymap (3 layers)
- `_BASE` — QWERTY + Norwegian (`NO_ARNG` å, `NO_OSTR` ø, `NO_AE` æ)
- `_LOWER` — held via the **outer-left thumb**; numbers + symbols
- `_RAISE` — F-keys; reached by **holding the inner-right thumb**
  (`LT(_RAISE, KC_SPC)` → **tap = Space, hold = RAISE**)

## One-time setup

This board needs **vial-qmk** (mainline QMK can't build Vial — no `quantum/vial.c`).

```sh
# 1. Toolchain (Arch)
sudo pacman -S --needed avr-gcc avr-binutils avr-libc avrdude
yay -S qmk                      # or: uv tool install qmk

# 2. vial-qmk fork
git clone --recurse-submodules https://github.com/vial-kb/vial-qmk.git \
    ~/dev/forks/vial-qmk

# 3. Expose this folder to the tree as a keyboard (symlink — edits stay in this repo)
ln -s ~/dev/keyboards/02/qmk-v3 ~/dev/forks/vial-qmk/keyboards/handwired/aximi
```

### Required patch for avr-gcc 15+

avr-gcc 15 / avr-libc 2.3 stopped pulling `<avr/io.h>` in transitively, so
`quantum/send_string/send_string.c` fails with `TCNT0 undeclared`. Add near the
top includes of that file (in the vial-qmk tree):

```c
#if defined(__AVR__)
#    include <avr/io.h>   // TCNT0/1/3/4 in tap_random_base64()
#endif
```

### Required workarounds for avr-gcc 16.1.0 (Arch, current as of Sep 2026)

Arch's `avr-gcc` package moved to a vanilla-FSF GCC 16 build whose baked-in
search paths (`/usr/avr/{include,sys-include}`) don't match where the
`avr-libc` package actually installs (`/usr/lib/avr/{include,lib}`). Three
symptoms, all from this one mismatch + GCC 16 being generally stricter/bigger:

1. **`fatal error: stdint.h: No such file or directory`** — avr-gcc's own
   `stdint.h` does an `#include_next` that can't find avr-libc's headers.
   Fix: `CPATH=/usr/lib/avr/include` as an env var on the compile/flash command.
2. **`cannot find crtatmega32u4.o` / `-lm` / `-lc` / `-latmega32u4`** at link —
   same path mismatch, this time for the avr5-multilib startfiles/libs. Fix:
   pass `-B/usr/lib/avr/lib/avr5 -L/usr/lib/avr/lib/avr5` (an env `LIBRARY_PATH`
   does **not** reach the startfile search — it has to be `-B` on the command line).
3. **`-Werror=strict-prototypes` / `-Werror=unused-but-set-variable`** in
   `avr/power.h` and the vendored LUFA USB stack — old headers/code, GCC 16's
   default warnings are stricter. Fix: `-Wno-error` to keep them as warnings.
4. **Firmware ~500 bytes over the 28672-byte budget** even with no keymap
   changes — GCC 16's AVR codegen is measurably larger than the older
   avr-gcc this budget was tuned against (confirmed: neither
   `VIAL_TAP_DANCE_ENTRIES` nor `EXTRAKEY_ENABLE` moved the size at all on
   this GCC — don't waste time on those levers first). Fix: AVR call/jump
   relaxation, `-mrelax` (compile) + `-Wl,--relax` (link) — recovered ~500
   bytes with no feature loss.

All four fold into the one compile/flash invocation below. If a future Arch
update reconciles the avr-gcc/avr-libc paths or ships a smaller-codegen
avr-gcc, these may no longer be needed — try a plain `qmk compile` first.

## Compile

```sh
cd ~/dev/forks/vial-qmk
CPATH=/usr/lib/avr/include QMK_HOME=$PWD qmk compile -kb handwired/aximi -km vial \
  -e 'EXTRAFLAGS=-Wno-error -mrelax -B/usr/lib/avr/lib/avr5 -L/usr/lib/avr/lib/avr5' \
  -e 'EXTRALDFLAGS=-Wl,--relax'
```

> **Flash budget is tight** (atmega32u4 caterina = 28672 bytes). The keymap
> `rules.mk` already disables `MOUSEKEY`, `GRAVE_ESC`, `SPACE_CADET`, `MAGIC`,
> and the compile above adds `-mrelax`/`--relax`. Current size on avr-gcc
> 16.1.0 ≈ 28636/28672 (~36 bytes free) — very little headroom left. If a
> future change overflows again, `EXTRAKEY_ENABLE = no` and cutting
> `VIAL_TAP_DANCE_ENTRIES` are already-tried dead ends on this compiler;
> look at `VIAL_COMBO_ENTRIES`/`VIAL_KEY_OVERRIDE_ENTRIES` or trimming the
> keymap itself instead.

## Flash

Each half is flashed separately and gets its handedness written in the **same**
avrdude session (single reset — works around caterina dropping the bootloader
after the flash pass). `qmk flash` recompiles first, so it needs the same
env vars and flags as `qmk compile` above:

```sh
cd ~/dev/forks/vial-qmk
CPATH=/usr/lib/avr/include QMK_HOME=$PWD qmk flash -kb handwired/aximi -km vial -bl avrdude-split-left \
  -e 'EXTRAFLAGS=-Wno-error -mrelax -B/usr/lib/avr/lib/avr5 -L/usr/lib/avr/lib/avr5' \
  -e 'EXTRALDFLAGS=-Wl,--relax'   # left half

CPATH=/usr/lib/avr/include QMK_HOME=$PWD qmk flash -kb handwired/aximi -km vial -bl avrdude-split-right \
  -e 'EXTRAFLAGS=-Wno-error -mrelax -B/usr/lib/avr/lib/avr5 -L/usr/lib/avr/lib/avr5' \
  -e 'EXTRALDFLAGS=-Wl,--relax'   # right half
```

When it prints **“Waiting for USB serial port — reset your controller now”**,
drop the plugged-in half into the caterina bootloader:

- **Double-tap RST** quickly, or **briefly bridge `RST`↔`GND` twice**.
- It re-enumerates as `2341:0036` (`/dev/ttyACM*`) for ~8 s; avrdude grabs it.

No `sudo` needed — the installed `50-qmk.rules` / `70-uaccess.rules` give your
session write access to the bootloader port. Success looks like
`… bytes of flash verified` + `15 bytes of eeprom verified` + `Avrdude done.`
Afterwards the board enumerates as `ID_VENDOR=rek ID_MODEL=aximi` (VID `0x6174`).

## Remap with the Vial app

Open the **Vial** GUI — it auto-detects the board (via the `vial:` serial magic)
and reads the embedded `vial.json`. Layers, tap-dance, combos, and key-overrides
are editable live (no reflash).

### udev rule (required for the GUI to access the board)

Without this, the raw HID node is `root`-only and Vial can't connect. Install the
official rule (matches any Vial board by serial magic, grants your session access):

```sh
sudo tee /etc/udev/rules.d/99-vial.rules >/dev/null <<'EOF'
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{serial}=="*vial:*", TAG+="uaccess", MODE="0660", GROUP="users"
EOF
sudo udevadm control --reload
sudo udevadm trigger --action=add --subsystem-match=hidraw   # or just replug the board
```

> The `uaccess` grant only lands on a device **add** event — `--action=add`
> (or a physical replug) is what writes the `user:<you>` ACL. A plain
> `udevadm trigger` (a "change" event) is not enough.

### Launching the AppImage

The AppImage needs FUSE2, which isn't installed here. Either install it
(`sudo pacman -S fuse2`) and run the `.AppImage` directly, or run the extracted
copy (no FUSE needed):

```sh
cd ~/Documents/Apps
./Vial-v0.7.5-x86_64.AppImage --appimage-extract   # one-time
./squashfs-root/AppRun                             # launch
```

Current app: **Vial v0.7.5** (`~/Documents/Apps/`).

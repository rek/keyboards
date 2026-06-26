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
ln -s ~/dev/keyboards/02/qmk-v2 ~/dev/forks/vial-qmk/keyboards/handwired/aximi
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

## Compile

```sh
cd ~/dev/forks/vial-qmk
QMK_HOME=$PWD qmk compile -kb handwired/aximi -km vial
```

> **Flash budget is tight** (atmega32u4 caterina = 28672 bytes). To fit, the
> keymap `rules.mk` disables `MOUSEKEY`, `GRAVE_ESC`, `SPACE_CADET`, `MAGIC`.
> Current size ≈ 28560/28672 (~112 bytes free). If a future change overflows,
> the next lever is `EXTRAKEY_ENABLE = no` (no media keys are used).

## Flash

Each half is flashed separately and gets its handedness written in the **same**
avrdude session (single reset — works around caterina dropping the bootloader
after the flash pass):

```sh
cd ~/dev/forks/vial-qmk
QMK_HOME=$PWD qmk flash -kb handwired/aximi -km vial -bl avrdude-split-left   # left half
QMK_HOME=$PWD qmk flash -kb handwired/aximi -km vial -bl avrdude-split-right  # right half
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

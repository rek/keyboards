# Lily58 Pro (wireless) — Troubleshooting & Fresh-Arch Setup

Symptom-first guide for the 06 build: a Lily58 Pro with one **nice!nano v2** per
half, running **ZMK**. Written from a working setup on Arch Linux (Omarchy /
Hyprland).

**Start with the script — it does the checking for you:**

```sh
cd "06 - lilly58/zmk-config"
./doctor.sh check            # read-only: finds and explains problems, prints the fix
./doctor.sh setup            # new machine: installs and configures everything (asks first)
./doctor.sh setup --dry-run  # show what setup would do, change nothing
```

`check` covers tools, workspace, built firmware images (including the
silent-wrong-pins bug), USB, Bluetooth bond state and both halves' battery. This
document explains *why* things break and covers what a script can't see (soldering,
cables, which key to press). `check` exits `0` when there are no problems.

Related docs: [`BUILDING.md`](BUILDING.md) is the step-by-step build/flash/pair
procedure. [`HOST-BATTERY.md`](HOST-BATTERY.md) covers battery readout on the
desktop. [`README.md`](README.md) covers the hardware. `HANDOFF.md` is history —
ignore it.

---

## 1. Fresh Arch box: from zero to first keystroke

### Five facts that explain most "bugs"

1. **Left half = the hub (split "central").** Everything you type, from both
   halves, leaves through the left. The right half **never types over USB on its
   own** — that is normal, not a fault.
2. **Two separate links.** Left ↔ right is always Bluetooth Low Energy (BLE).
   Host ↔ left is USB *or* BLE.
3. **Bonds and the USB/BLE output choice are saved in flash and survive
   reflashing.** Reflashing does not clear a stuck state; the `settings_reset`
   image does.
4. **Both halves use a custom pin map**, not ZMK's stock `lily58` one, because the
   nice!nanos sit in the "swapped" hole-set of the Pro's reversible footprint
   (see [dead keys](#c-typing)).
5. **Bootloader mode is always available.** Double-tap RESET quickly (like a
   double-click); the LED pulses **red** and a `NICENANO` USB drive appears. That
   works even when the firmware is broken.

### Pick a build path

| | Cloud build (easiest) | Local build |
|---|---|---|
| Needs | Repo on GitHub with Actions enabled | About 2 GB disk and a few minutes of downloads |
| Steps | Actions → **Build lilly58 (06)** → *Run workflow* → download artifact `lilly58-firmware` | `./doctor.sh setup`, then `./build-flash.sh left\|right` |
| Gives you | `.uf2` for `lily58_left`, `lily58_right`, `settings_reset` | Same three images, and you can edit and rebuild locally |
| Last verified | Green on 2026-08-15 | 2026-09-21: on a pristine Arch container, `doctor.sh setup --yes`, both builds and the pin-map check all passed (no hardware). Keyboard typing last confirmed 2026-07-06 |

The cloud left image already includes ZMK Studio and the battery proxy (both are
switched on by config files in the repo). To flash any `.uf2`: double-tap RESET,
then copy the file onto the `NICENANO` drive. It unmounts and reboots by itself.

### Local build

```sh
cd "06 - lilly58/zmk-config"
./doctor.sh setup        # asks before each step; add --yes to skip the questions
```

`setup` is safe to re-run: it skips whatever is already done. It:

1. installs the Arch packages (`git arm-none-eabi-gcc arm-none-eabi-newlib cmake ninja dtc python udisks2 bluez bluez-utils usbutils`),
2. enables the `bluetooth` service,
3. builds the ZMK workspace at `~/dev/zmk-workspace` (about 1.8 GB; set `ZMK_WS=/other/path` to move it). A **new** clone is pinned to the ZMK commit this build was tested on. `--latest` tracks `main` instead. An existing workspace is never moved,
4. writes the udev rule that lets you open the Studio serial port,
5. builds the `settings_reset` image (`build-flash.sh` only builds left/right).

Then:

1. **Label the halves L and R** before flashing anything.
2. Build with `./build-flash.sh left --no-flash` (and `right`), then run
   `./doctor.sh check` — it verifies the pin map inside each image before you flash.
3. Follow *Clean pairing procedure* in [`BUILDING.md`](BUILDING.md), **one board
   plugged in at a time**: reset image, wait 5 s, real image, for each half.
4. Pair the host — see [Bluetooth](#d-bluetooth-pairing-and-battery).

<details><summary>What setup does by hand (if you'd rather not run it)</summary>

Packages and workspace: *One-time toolchain setup* in [`BUILDING.md`](BUILDING.md),
plus `pip install protobuf grpcio-tools` in the venv. Bluetooth:
`sudo systemctl enable --now bluetooth`. Studio serial access:

```sh
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="615e", TAG+="uaccess"' \
  | sudo tee /etc/udev/rules.d/50-zmk-studio.rules
sudo udevadm control --reload && sudo udevadm trigger   # then replug the left half
```

Reset image:

```sh
cd ~/dev/zmk-workspace/zmk
export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb GNUARMEMB_TOOLCHAIN_PATH=/usr
PATH=~/dev/zmk-workspace/.venv/bin:$PATH west build -s app -d build/reset -p \
  -b "nice_nano@2.0.0/nrf52840/zmk" -- -DSHIELD=settings_reset
```

</details>

---

## 2. Ten-second triage

Run `./doctor.sh check` first. The commands below are what it runs, for when you
want one piece by hand.

| Command | What it tells you |
|---|---|
| `lsusb \| grep 1d50` | `1d50:615e ... Lily58` = firmware running **and** the cable carries data. Nothing = see [flashing](#b-flashing) |
| `lsblk -o NAME,LABEL \| grep NICENANO` | A hit = that half is in bootloader mode |
| `journalctl -k --since "5 min ago" \| grep -iE "usb [0-9]-\|disconnect"` | `USB disconnect` + re-enumeration = real USB fault. **No events** = USB is fine |
| `bluetoothctl info <MAC>` | `Paired`, `Bonded`, `Trusted`, `Connected` should all be `yes` |
| `zmk-kb-status --format json` | Both halves' battery. A non-zero `right` means the left↔right link is up (see [`HOST-BATTERY.md`](HOST-BATTERY.md)) |
| `sudo keyd monitor` (if you run keyd) or `sudo evtest` | Whether keystrokes actually arrive, and from which device |

Find your keyboard's Bluetooth address with `bluetoothctl devices` (the name is
`Lily58`). Find each board's USB serial with
`lsusb -v -d 1d50:615e 2>/dev/null | grep iSerial`. The serial is the **same in
bootloader mode and app mode**, so you can tell which physical half is which even
when it's showing as a `NICENANO` drive.

---

## 3. Symptom guide

### A. Building

| Symptom | Cause | Fix |
|---|---|---|
| Build fails at once, complaining about the board | Old board id `nice_nano_v2`. ZMK `main` uses Zephyr's hardware-model v2 | Use `nice_nano@2.0.0/nrf52840/zmk`. The script and `build.yaml` already do |
| `fatal error: .../06: No such file or directory` | The folder name `06 - lilly58` has spaces, which break the devicetree preprocessor | Build from a space-free copy of `config/`. The script stages one at `~/dev/zmk-workspace/lily58-config`. Hand-built commands must do the same |
| Studio build fails in nanopb, or on protobuf | `protobuf` / `grpcio-tools` missing from the venv | `~/dev/zmk-workspace/.venv/bin/pip install protobuf grpcio-tools`, then **re-run** — the first build after installing can fail once |
| `west` or compiler not found | venv not on `PATH` / toolchain variables unset | Use `build-flash.sh`, which sets `ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb` and `GNUARMEMB_TOOLCHAIN_PATH=/usr` |
| `build-flash.sh` can't find the workspace | Workspace isn't at `~/dev/zmk-workspace` | `export ZMK_WS=/your/path` (both `build-flash.sh` and `doctor.sh` honour it) |
| A build that worked last month now fails | `west.yml` tracks ZMK `main`, which moves | Pin it. `doctor.sh setup` already pins new workspaces to the known-good ZMK `64daf698e073e37b6748ac54f4eb48d8666af0b9` (2026-06-20, Zephyr `v4.1.0+zmk-fixes`). For an older workspace: `git -C ~/dev/zmk-workspace/zmk checkout 64daf698 && (cd ~/dev/zmk-workspace/zmk && ../.venv/bin/west update)`. The cloud build tracks `main` (`config/west.yml`); put the hash in `revision:` there to pin it too |
| **Build is green but the keyboard types nothing** | Pin-map override silently dropped — see below | Verify `zephyr.dts` before flashing |

### B. Flashing

| Symptom | Cause | Fix |
|---|---|---|
| `NICENANO` drive never appears; board LED is on but `lsusb` shows nothing | **Charge-only USB cable** | Use a known data cable, straight into the PC, not a hub |
| Drive doesn't appear, cable is fine | Double-tap too slow | Tap RESET twice quickly, like a double-click. Red pulsing LED = bootloader |
| Script says `NICENANO not found` | Same two causes above | Fix those, then re-run the script |
| Script can't mount the drive | Missing `udisks2`, or the desktop auto-mounted it elsewhere | `sudo pacman -S udisks2`, or copy `zmk.uf2` onto the mounted drive by hand |
| Drive disappears after the copy | **Normal.** The board reboots into the firmware | Nothing to fix |
| Not sure which half is plugged in | Unlabelled boards get swapped | Read the serial (triage section) and label the boards L/R. Never juggle both halves on one cable |

### C. Typing

**Green build, dead keyboard.** The board shows up in `lsusb` but no key
registers. The left/right pin overrides live in `lily58.keymap` under
`#ifdef CONFIG_SHIELD_LILY58_LEFT` / `_RIGHT`. Zephyr reads devicetree **before**
Kconfig, so those macros are invisible unless the build passes
`-DDTS_EXTRA_CPPFLAGS="-DCONFIG_SHIELD_LILY58_<SIDE>"`. Without it the build
succeeds and ships the stock pins. `build-flash.sh` and the cloud workflow both
inject it. If you build by hand, you must too.

`./doctor.sh check` verifies this for every built image. By hand:
```sh
grep -A6 'kscan0: kscan' ~/dev/zmk-workspace/zmk/build/<dir>/zephyr/zephyr.dts
# <dir> = left-studio | right | left-studio-nobat
```

| Half | rows (must be) | cols (must be) |
|---|---|---|
| left | `0x12 0xf 0xe 0x10 0xa` | `0x4 0x5 0x6 0x7 0x8 0x9` |
| right | `0x12 0xf 0xe 0x10 0xa` | `0x9 0x8 0x7 0x6 0x5 0x4` |

Rows `0x5`–`0x9` mean the override was dropped. **Do not flash.**

| Symptom | Cause | Fix |
|---|---|---|
| Enumerates, zero keys, `zephyr.dts` shows the right pins | Your nice!nano is in the *other* hole-set of the reversible footprint. The overrides assume the swapped set | Delete that half's `#ifdef` block in `lily58.keymap` to use ZMK's stock pins (rows `5 6 7 8 9`; left cols `19 18 15 14 16 10`, right cols `10 16 14 15 18 19`). Rebuild and re-verify. If in doubt, trace the pads in `pcb/Lily58_Pro.kicad_pcb` |
| Left types, **right types nothing** | The right is the peripheral: it only works while linked to the left | Power both halves, wait 10–15 s for the link. Check `zmk-kb-status`: right at `0` means no link. Still nothing → `settings_reset` **both** halves and re-pair (below) |
| Only some keys work | Only installed switches register; a missing switch, diode or a cold solder joint is a dead key | Test with a switch bridged by tweezers before blaming firmware |
| Right half types mirrored or scrambled keys | Right column order is wrong | Right cols must be `9 8 7 6 5 4` (mirror of the left) |
| **Types for a few seconds after reset, then stops.** `lsusb` still lists the board | Not a crash. A BLE connection came up and ZMK moved the HID output to Bluetooth, where keystrokes vanish into a half-open link | Press **RAISE + `6`** (`&out OUT_USB`). To break the loop while diagnosing: `bluetoothctl block <MAC>` (undo with `unblock`). `CONFIG_ZMK_USB=y` in `lily58.conf` makes USB win whenever a cable is present |
| `USB disconnect` lines repeat in `journalctl -k`, device number climbs | Real USB fault | Change cable and port, remove hubs, check the micro-USB jack for wear |
| `evtest` / raw device shows nothing while typing works | `keyd` (or a similar remapper) grabs every keyboard | Watch the remapper's own monitor: `sudo keyd monitor` shows a per-device source |
| Keystrokes go somewhere unexpected when USB and BLE are both connected | Output endpoint is stored in flash | RAISE + `6` / `7` / `8` = USB / BLE / toggle |

### D. Bluetooth pairing and battery

Pair the host in an **interactive** `bluetoothctl` session. A one-shot
`bluetoothctl pair <MAC>` fails even when everything is healthy.

```
remove <MAC>          # drop any half-dead host entry first
agent NoInputNoOutput
default-agent
scan on               # wait for "Lily58"
pair <MAC>
trust <MAC>           # required for auto-reconnect
connect <MAC>
```

No passkey is configured — pairing is BLE "Just Works".

| Symptom | Cause | Fix |
|---|---|---|
| `org.bluez.Error.AuthenticationFailed` | Missing agent **and/or** a stale bond in the keyboard's active profile. Both must be fixed | On the keyboard press **RAISE + ESC** (`&bt BT_CLR`, needs both halves linked), then pair in the interactive session above |
| `pair` hangs, next command says `org.bluez.Error.InProgress`; `LE.Disconnected — org.bluez.Reason.Local, terminated by local host` repeats; `Paired: no` while `Connected` flaps | **Stale bond.** The keyboard still holds a key the host deleted. Bluetooth has no message for "I forgot you", and clicking *Forget* in a desktop menu only wipes the host's copy | `bluetoothctl remove <MAC>`, `BT_CLR` on the keyboard, re-pair. If that fails, `settings_reset` on **both** halves |
| `Lily58` never appears in `scan on`, other devices do | ZMK only advertises on an **unbonded** profile. The active profile is bonded to another host | RAISE + `1`…`5` selects profile 0–4. Pick a free one, or `BT_CLR` the current one |
| `BT_CLR` seems to do nothing | RAISE is on the right half, `BT_CLR` on the left, so it needs the split link up. Its effect can't be confirmed from the host | Skip it and use `settings_reset` on both halves — the only fix you can verify |
| Bluetooth won't power on / no adapter | Service stopped or radio blocked | `sudo systemctl enable --now bluetooth`, `rfkill unblock bluetooth`, `bluetoothctl power on` |
| Battery shows only one half | Expected. `upower` and desktop menus show only the first battery service (left) | Use `zmk-kb-status` or ZMK Studio. See [`HOST-BATTERY.md`](HOST-BATTERY.md) |
| Right battery reads `0` | Right half asleep or off, or the link came up less than 60 s ago (it reports every 60 s) | Wait a minute with both halves awake |
| No battery at all, `Paired: no` | Unbonded, so the host never resolved GATT services | Re-pair (`remove`, `BT_CLR`, pair) |
| No battery when only on USB | ZMK reports battery only over Bluetooth | Not a bug. Keep the Bluetooth link connected too (it normally is) |

### E. ZMK Studio (live keymap editing)

| Symptom | Cause | Fix |
|---|---|---|
| No serial port, or permission denied | udev rule missing | `./doctor.sh setup`, then replug the left half. `/dev/ttyACM0` should be group `uucp` with an ACL entry |
| Site can't connect | Studio needs Web Serial, which is Chromium-only | Use Chrome, Chromium or Edge at https://zmk.studio |
| Connects but is read-only | Locked | Unlock with **RAISE + the top-right key of the right half** (`&studio_unlock`) |
| No Studio at all | Left image built without it | Left needs `-S studio-rpc-usb-uart` **and** `CONFIG_ZMK_STUDIO=y`. The script and cloud build do both. The right half never talks to Studio |
| Edits vanished | Studio edits live in the keyboard's flash, not in `lily58.keymap`. `settings_reset` wipes them, and rebuilds use the file | Copy layouts you want to keep back into `lily58.keymap` |

---

## 4. When nothing else works: clean reset

Bonds and output choice can be wrong in ways you can't see. This is the one fix
you can confirm. **One board plugged in at a time:**

1. Left: double-tap → copy `settings_reset` `.uf2` → wait 5 s → double-tap → copy the left image.
2. Unplug the left. Right: repeat the same two steps with the right image.
3. Power both (left on USB, right on battery). They bond by themselves in 10–15 s.
4. Pair the host (section D).

Resetting **only one half** leaves mismatched bonds and they will not re-pair.

---

## 5. Things that are specific to the original setup

Check each of these on a new machine and person:

| Item | Original value | On your setup |
|---|---|---|
| Workspace path | `/home/adam/dev/zmk-workspace` | Default is `~/dev/zmk-workspace`; override with `ZMK_WS` |
| Keyboard Bluetooth address | `E8:0C:B3:F6:66:10` | Different — `bluetoothctl devices` |
| Left-half USB serial | `3A8F02D9AD37EF58` | Different — `lsusb -v -d 1d50:615e \| grep iSerial` |
| Battery GATT handles | left `service0010/char0011`, right `service0015/char0016` | Different — walk `gatt.list-attributes` (see [`HOST-BATTERY.md`](HOST-BATTERY.md)) |
| `keyd` | Installed, grabs all keyboards | Optional. If you don't run it, `sudo evtest` works directly |
| Hole-set / pin overrides | Both nice!nanos in the swapped set | Verify for your own board (section C) |

Known-good versions: ZMK `main` at `64daf698` (2026-06-20), Zephyr
`v4.1.0+zmk-fixes`, west 1.5.0, `arm-none-eabi-gcc` 16.2.0 with newlib 4.6.0,
CMake 4.4.3, protobuf 6.33.6, grpcio-tools 1.81.1, BlueZ 5.87.

## 6. Don't

- Don't use the `zmk-usb-logging` build. It hangs at boot.
- Don't use the `CONFIG_ZMK_SPLIT=n` standalone-right test. It gives false negatives.
- Don't test with both halves juggled on one cable. Finish one board before touching the other.
- Don't rely on reflashing to clear a stuck Bluetooth output or a bad bond. It doesn't.

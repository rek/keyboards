# 06 Lily58 Pro — Handoff / Bring-up State

> Purpose: hand this wireless Lily58 Pro build to a fresh agent. Read this top-to-bottom
> before touching anything. Everything hard has already been figured out; what remains is
> **careful, un-rushed assembly + pairing** (which kept going wrong when tired).
> See also `README.md` (overview), **`BUILDING.md` (canonical build/flash procedure)**,
> and the memory note `zmk-lilly58-flashing`.
>
> **UPDATE 2026-07-05:** Left half re-verified working. Root cause of last session's
> "left types nothing": the keymap's `#ifdef CONFIG_SHIELD_LILY58_LEFT` guard is invisible
> to devicetree preprocessing (DTS runs before Kconfig), so builds after 2026-06-28
> silently dropped the remap. Fixed in `build-flash.sh` via `-DDTS_EXTRA_CPPFLAGS`.
> Learning #11: **always verify the compiled `zephyr.dts` kscan pins before flashing**
> (see BUILDING.md).
>
> **🎉 2026-07-05 (later): THE KEYBOARD WORKS — all phases complete.**
> Left types `5`, right types `J` (position-accurate) through the split link.
> Corrections to earlier beliefs: (1) the right nice!nano is in the **swapped set
> too** — the 06-28 "opposite/stock set" observation was wrong; right needs the
> mirrored remap (rows `18,15,14,16,10`, cols `9,8,7,6,5,4`), now in the keymap
> and confirmed. (2) The right's LiPo delivered no power during the first Phase C
> attempt (board on USB works fine) — battery/switch/wiring still needs checking.
> (3) On this machine **keyd grabs all keyboards** — watch keystrokes with
> `sudo keyd monitor`, not the raw evdev node. (4) The two halves' USB serials:
> left `3A8F02D9AD37EF58`, right `EC93E089067872A6` — and the **bootloader
> reports the same serial**, so you can always identify which board is in DFU.
> Remaining work: §Still open below (switches, battery, output choice, OLED).
>
> **2026-07-05 (evening): ZMK Studio live.** Left runs the Studio-enabled image
> (`build/left-studio`; snippet `studio-rpc-usb-uart` + `CONFIG_ZMK_STUDIO=y`),
> `&studio_unlock` = RAISE + top-right key of the right half. Edit keys at
> https://zmk.studio (Chromium, USB serial; udev rule `50-zmk-studio.rules`
> grants port access). No boot-hang from the CDC channel — that fear was
> logging-specific. Both halves now have batteries connected; keyboard confirmed
> working over host Bluetooth AND USB. See BUILDING.md §ZMK Studio.

---

## TL;DR — where we are

- **Left half: WORKS.** It scans correctly with a custom row/col remap (see below). Confirmed typing earlier.
- **Right half: NOT yet confirmed working**, but very likely fine on **stock** wiring (see "Right half" below).
- **Blocker at pause:** couldn't get a clean end-to-end test because (a) the left kept sending keystrokes to **Bluetooth instead of USB** (root cause found — see §Output endpoint), and (b) **board-juggling scrambled which physical half had which firmware**. Fatigue-driven confusion, not a hardware fault.
- **Next session:** do a **clean, ONE-BOARD-AT-A-TIME pass** (§Clean restart plan). Don't juggle both halves at once.

---

## Hardware facts

- **Keyboard:** Lily58 **Pro** (58-key split), wireless. PCB is the user's own fab.
- **PCB design source:** `~/dev/keyboard-clones/Lily58/Pro/PCB/Lily58_Pro.kicad_pcb` (+ `.net`, `.sch`). It's the classic Lily58 Pro (Pro-Micro footprint + Kailh hotswap). Standard pinout — ZMK's stock `lily58` shield matches it.
- **Controllers:** a **nice!nano v2** (nRF52840, BLE) on each half → firmware is **ZMK** (QMK can't do BLE on nice!nano).
- **Reset:** left has a working reset (double-tap). User wired a reset switch on the right mid-session.
- **Switches installed:** only **ONE per half** during bring-up (fine — empty positions are open circuits and invisible to the scan). Left's is "closest to MCU". Right's is one switch too.
- **Battery:** right half was wired to a LiPo (cold to touch = polarity OK). Left on USB cable.

### The reversible-footprint gotcha (the crux of this whole build)
The Lily58 Pro controller footprint is **reversible: two staggered hole-sets per side, and the two sets SWAP rows↔columns.** From the board file (`Lily58_Pro.kicad_pcb`, footprint `U1`):
- **Outer** hole-columns (X≈−8.82 and X≈+7.72) carry the **row** nets.
- **Inner** hole-columns (X≈−7.52 and X≈+6.42) carry the **col** nets.

So which nets the nice!nano's pins hit depends entirely on which set you soldered into.
- **LEFT nice!nano** → soldered into the **"swapped" set** → needed a **remap** (done, works).
- **RIGHT nice!nano** → user says it's in the **OPPOSITE set** from the left = the **stock/correct** set → should need **NO remap** (stock `lily58_right`). *(Unverified — verify next session.)*

---

## Firmware / config

- **zmk-config:** `06 - lilly58/zmk-config/` (this repo). `config/lily58.keymap`, `lily58.conf`, `build.yaml`, `west.yml`, `build-flash.sh`.
- **Local toolchain:** `~/dev/zmk-workspace` (west venv + ZMK **main** tree; uses system `arm-none-eabi-gcc`, no Zephyr SDK).
- **Board id (ZMK main / hardware-model-v2):** `nice_nano@2.0.0/nrf52840/zmk` — **NOT** the old `nice_nano_v2`.
- **Shields:** `lily58_left` (= **central**, `ZMK_SPLIT_ROLE_CENTRAL` default y), `lily58_right` (= **peripheral**).
- The zmk-config folder name has **spaces**, which break ZMK's devicetree preprocessor — builds stage config to a space-free path (`~/dev/zmk-workspace/lily58-config`). `build-flash.sh` handles this.

### The LEFT remap (in `config/lily58.keymap`, guarded by `#ifdef CONFIG_SHIELD_LILY58_LEFT`)
| | row0–4 | col0–5 |
|---|---|---|
| stock left | pro_micro `5,6,7,8,9` | `19,18,15,14,16,10` |
| **our left remap** | pro_micro `18,15,14,16,10` | `4,5,6,7,8,9` |

The **right** half currently has **no remap** (uses stock `lily58_right`, cols `10,16,14,15,18,19`). The keymap has a comment placeholder for a right remap but it's intentionally empty (right is believed to be in the correct set).

### Pre-built firmware images (in `~/dev/zmk-workspace/zmk/build/*/zephyr/zmk.uf2`)
| dir | what | notes |
|---|---|---|
| `build/left` | normal **left** (remap, central) | the good left image |
| `build/right` | normal **right** (stock, peripheral) | the good right image |
| `build/reset` | `settings_reset` shield | wipes BLE bonds + endpoint pref |
| `build/left-log` | left + `zmk-usb-logging` | **DON'T USE** — hangs at boot (known ZMK bug) |
| `build/right-test` | right with `CONFIG_ZMK_SPLIT=n` | standalone test — **UNRELIABLE**, gives false negatives |

Rebuild any with `build-flash.sh left|right` or the west commands in this repo's git history / `build-flash.sh`.

---

## ⚠️ Hard-won learnings (read these — they cost hours)

1. **Output endpoint (USB vs BLE) is persisted to FLASH and survives re-flashing.** This is THE thing that wasted the most time. ZMK saves the selected output (`endpoints/preferred2`); once the left was on BLE it stayed on BLE **through every reflash**, so keystrokes vanished to a dead Bluetooth link and USB showed nothing. **Fixes:** press `&out OUT_USB` once, OR wipe with the `settings_reset` shield (resets to USB-when-connected default). Reflashing alone does NOT fix it. (ZMK docs: `endpoints.c`, outputs behavior.)

2. **Split re-pairing requires `settings_reset` on BOTH halves**, then reflash both, then power together to re-bond. Resetting one leaves a half-bonded mess. Also "forget" the keyboard on the host and re-pair.

3. **When testing, watch BOTH the USB and Bluetooth input devices.** The central may present two `event-kbd` devices — `[USB]` and `[Bluetooth]`. Keystrokes go to whichever endpoint is selected. Enumerate via `/proc/bus/input/devices` (by-id only lists USB, misses the BT one).

4. **A peripheral does NOT type over USB on its own.** To test the right half you must pair it with the left (central) and read the *central's* output. The `CONFIG_ZMK_SPLIT=n` standalone trick to make it type directly is **unreliable** (ZMK docs warn split-disabled half-shields mis-map — we got repeated false-negative "nothing typed" that were NOT real matrix failures).

5. **USB serial logging builds hang at boot on this setup.** Known ZMK/Zephyr bugs (USB CDC vs HID contention #2372, boot-delay #53000). We abandoned logging. If ever needed: `-S zmk-usb-logging` snippet only, modest log level, don't set `CONFIG_LOG_DEFAULT_LEVEL=4` globally, one half at a time, close the serial monitor to type.

6. **Charge-only USB cables** were a recurring trap. Symptom: board LED lights (powered) but **nothing** appears on USB — no device, no `NICENANO`, no serial. Even the bootloader's `NICENANO` drive won't mount over a charge-only cable. **Always use a known data cable, straight into the PC (not the hub).** The cable that flashed successfully is your known-good one.

7. **LED meanings on the nice!nano:** flashing **blue** = firmware running (normal); **red** (pulsing) = **bootloader** mode. A single flash on battery connect then dark = booted + LED off to save power (normal, not broken).

8. **Bootloader is independent of app firmware** — double-tap RESET always gets you `NICENANO` to reflash, even if the app firmware is hung/wrong. If double-tap yields no `NICENANO` but the board *is* powered, it's the cable (see #6) or a timing miss (tap faster, ~½s apart).

9. **The kscan-remap-in-keymap pattern is idiomatic** (confirmed by ZMK docs): re-declare `row-gpios`/`col-gpios`, keep `diode-direction = col2row`, keep the matrix transform, guard per-side with `#ifdef CONFIG_SHIELD_LILY58_LEFT/RIGHT`. Don't touch diode-direction or the transform.

10. **Label your boards.** The single biggest time-sink at the end was losing track of which physical half had which firmware while swapping the one good cable between them. Put a "L"/"R" sticker on each before the next session.

---

## Clean restart plan (do this next session — ONE board at a time)

Goal: get both halves on correct normal firmware with cleared settings, then verify.

**Phase A — Left, in isolation (nothing else plugged/powered):**
1. Plug **only** the LEFT into the good data cable. Confirm it enumerates (`lsusb` shows `1d50:615e` or `239a` bootloader).
2. Double-tap RESET → flash `build/reset` (settings_reset). Let it boot (~5s).
3. Double-tap RESET → flash `build/left` (normal remap).
4. Verify: watch its `event-kbd` device(s) — **both USB and BT** — and press the left switch. It should type (its "closest to MCU" key = `5` on the default layer). If it types → left is fully good (central + USB output).
   - If it only shows on a BLE device, that's fine too — but easier if USB. If nothing on USB, the settings_reset should have set USB default; re-check you actually reset THIS board.

**Phase B — Right, in isolation:**
5. Unplug left. Plug **only** the RIGHT into the good cable.
6. Double-tap RESET → flash `build/reset`. Boot ~5s.
7. Double-tap RESET → flash `build/right` (normal stock). It's the peripheral — it will NOT type over USB alone. That's expected.

**Phase C — Pair + test:**
8. Power BOTH together: left on USB (central), right on battery (peripheral). Wait ~10–15s to auto-pair (fresh bond after both were reset).
9. Watch the left/central's `event-kbd` device(s) (USB + BT). Press the **left** switch (should type), then the **right** switch.
   - Right types (correct key) → **DONE**, right's stock mapping is correct. Install all switches.
   - Right types the **wrong** key → right needs a remap; derive it (footprint is symmetric — candidate is left remap with cols reversed: rows `18,15,14,16,10`, cols `9,8,7,6,5,4` — but VERIFY, our first guess of that failed via the unreliable standalone test, so re-test properly here).
   - Right types **nothing** (but left works + they're paired) → either not paired (redo §Clean restart both-reset), or a solder issue on the right matrix (multimeter continuity from the switch to the controller pads — diode mode, expect ~0.5–0.7 V through the diode).

**Tip:** keep a text editor focused during Phase C so the user *sees* keys land, and I watch the event device to confirm exactly which keycode.

---

## Still open / to finish after it works
- Install all switches both halves.
- Finalize battery wiring on both (see README §Battery — B+/B- on nice!nano, red→B+, black→B-, ~100 mA charge, optional slide switch).
- Decide USB vs BLE output deliberately (`&out OUT_USB` if daily USB) so the sticky-preference trap doesn't bite again.
- Optional: OLED (populate `R1`/`R2` I²C pull-ups, enable `CONFIG_ZMK_DISPLAY`).
- Consider ZMK Studio for live keymap edits (central only, needs a Studio-compatible physical layout; stock Lily58 uses a matrix-transform so may need layout work).
- Optional cleanup: move the left kscan override from `.keymap` into a `config/boards/…/lily58_left.overlay` (more idiomatic), keeping the `#ifdef` guard.

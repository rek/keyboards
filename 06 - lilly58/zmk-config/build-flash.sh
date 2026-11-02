#!/usr/bin/env bash
# Local build + flash for the 06 lilly58 (ZMK, nice!nano v2).
#
# Two firmware variants for the same keyboard (see ../README.md):
#   06a  06a-ble/config    Bluetooth split + host BLE, runs on batteries
#   06b  06b-wired/config  TRRS wired split, left talks to the PC over USB
#
# Usage:
#   ./build-flash.sh 06b left                 # left (central): Studio enabled
#   ./build-flash.sh 06b right                # right half (peripheral)
#   ./build-flash.sh 06a left --no-batt       # 06a only: Studio, battery proxy OFF
#   ./build-flash.sh <variant> <side> [...] --no-flash   # build only, don't flash
#   ./build-flash.sh <variant> <side> --log   # USB logging (zmk-usb-logging)
#
# Images land in $ZMK_WS/zmk/build/<variant>-<dir>, e.g. build/06b-left-studio.
#
# --log on the left drops Studio: both want the USB CDC channel. Reflash a
# plain `left` afterwards to get Studio back.
# Read the log with `tio /dev/serial/by-id/usb-ZMK_Project_*` (or cat).
#
# Left builds are ALWAYS ZMK-Studio-enabled (needs protobuf/grpcio-tools in the
# venv — see BUILDING.md). Studio only runs on the central, so the right build
# has no studio variant.
#
# --no-batt (06a only) strips the split battery fetch/proxy (the second
# host-visible battery service) via Kconfig CLI overrides, which take precedence
# over lily58_left.conf. Use it to rule the dual battery service out when
# chasing host pairing problems. (2026-07-06: a pairing failure was wrongly
# blamed on it once — real fix was BT_CLR on the keeb + a bluetoothctl agent on
# the host; see BUILDING.md "Pairing to a Linux host".)
#
# To flash: put the target nice!nano in bootloader mode (double-tap RESET) so the
# NICENANO USB drive appears, then run the command. The drive is matched by USB
# serial, so it is safe to have both halves in bootloader mode at once.
#
# Gotchas baked in (learned the hard way on this machine, June 2026):
#  - We track ZMK *main*, which uses Zephyr hardware-model-v2. The board is NOT
#    "nice_nano_v2" anymore; the correct id is "nice_nano@2.0.0/nrf52840/zmk".
#  - The repo folder "06 - lilly58" has SPACES, which break ZMK's devicetree
#    preprocessor (it doesn't quote the keymap path). So we build from a
#    space-free staged copy of config/.
#  - We use the system arm-none-eabi-gcc (gnuarmemb) toolchain, NOT the ~1GB
#    Zephyr SDK.
set -euo pipefail

USAGE="usage: build-flash.sh <06a|06b> <left|right> [--no-batt] [--no-flash] [--log]"
VARIANT="${1:?$USAGE}"; shift
case "$VARIANT" in
  06a) VARIANT_DIR=06a-ble ;;
  06b) VARIANT_DIR=06b-wired ;;
  *) echo "variant must be 06a (Bluetooth) or 06b (TRRS wired)"; echo "$USAGE"; exit 1 ;;
esac
SIDE="${1:?$USAGE}"; shift
case "$SIDE" in left|right) ;; *) echo "side must be left or right"; exit 1;; esac

FLASH=1; BATT=1; LOG=0
for arg in "$@"; do
  case "$arg" in
    --no-flash) FLASH=0 ;;
    --no-batt)  BATT=0 ;;
    --log)      LOG=1 ;;
    *) echo "unknown flag: $arg (known: --no-batt --no-flash --log)"; exit 1 ;;
  esac
done
[[ "$BATT" == "0" && "$VARIANT" != "06a" ]] && { echo "--no-batt only applies to 06a (the BLE battery proxy)"; exit 1; }

WS="${ZMK_WS:-$HOME/dev/zmk-workspace}"   # override with ZMK_WS=/path
CONFIG_SRC="$(cd "$(dirname "$0")/$VARIANT_DIR/config" && pwd)"
STAGE="$WS/lily58-config"            # space-free staging path
BOARD="nice_nano@2.0.0/nrf52840/zmk"
SHIELD="lily58_${SIDE}"

# Pick the build variant.
SNIPPET_ARGS=(); EXTRA_CMAKE=()
if [[ "$SIDE" == "left" ]]; then
  BUILD_DIR="left-studio"
  SNIPPET_ARGS=(-S studio-rpc-usb-uart)
  EXTRA_CMAKE+=(-DCONFIG_ZMK_STUDIO=y)
  if [[ "$BATT" == "0" ]]; then
    BUILD_DIR="left-studio-nobat"
    EXTRA_CMAKE+=(-DCONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=n
                  -DCONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY=n)
  fi
  if [[ "$LOG" == "1" ]]; then
    BUILD_DIR="left-log"
    SNIPPET_ARGS=(-S zmk-usb-logging)
    EXTRA_CMAKE=(-DCONFIG_ZMK_STUDIO=n)
  fi
else
  BUILD_DIR="right"
  [[ "$BATT" == "0" ]] && { echo "--no-batt only applies to the left/central"; exit 1; }
  if [[ "$LOG" == "1" ]]; then
    BUILD_DIR="right-log"
    SNIPPET_ARGS=(-S zmk-usb-logging)
  fi
fi
BUILD_DIR="$VARIANT-$BUILD_DIR"

export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
export GNUARMEMB_TOOLCHAIN_PATH=/usr
export PATH="$WS/.venv/bin:$PATH"

echo ">> staging $VARIANT_DIR/config to space-free path"
rm -rf "$STAGE"; mkdir -p "$STAGE"; cp -R "$CONFIG_SRC/." "$STAGE/"

echo ">> building $VARIANT $SHIELD -> build/$BUILD_DIR"
cd "$WS/zmk"
rm -rf "build/$BUILD_DIR"
# Devicetree (incl. the keymap) is preprocessed BEFORE Kconfig, so the keymap's
# "#ifdef CONFIG_SHIELD_LILY58_LEFT" guard around the kscan remap sees nothing
# unless we inject the define into the DTS preprocessor ourselves. Without this
# the left builds with STOCK pins and types nothing (bit us 2026-06-28..07-05).
SIDE_UPPER=$(echo "$SIDE" | tr '[:lower:]' '[:upper:]')
west build -s app -d "build/$BUILD_DIR" -b "$BOARD" "${SNIPPET_ARGS[@]}" -- \
  -DSHIELD="$SHIELD" -DZMK_CONFIG="$STAGE" \
  "${EXTRA_CMAKE[@]}" \
  -DDTS_EXTRA_CPPFLAGS="-DCONFIG_SHIELD_LILY58_${SIDE_UPPER}"

UF2="$WS/zmk/build/$BUILD_DIR/zephyr/zmk.uf2"
echo ">> built: $UF2 ($(du -h "$UF2" | cut -f1))"

echo ">> kscan sanity check (rows must be 0x12 0xf 0xe 0x10 0xa)"
grep -A3 'row-gpios' "$WS/zmk/build/$BUILD_DIR/zephyr/zephyr.dts" | head -4 || true

if [[ "$VARIANT" == "06b" ]]; then
  # The wired split pins only work after the TRRS rework (BUILDING.md).
  echo ">> wired split UART pins (left: RX 0x100001d TX 0x1f; right: RX 0x100001f TX 0x1d)"
  grep -A8 'uart0_default: uart0_default' "$WS/zmk/build/$BUILD_DIR/zephyr/zephyr.dts" | grep psels || true
fi

if [[ "$FLASH" == "1" ]]; then
  # Each half's bootloader reports the same USB serial as its ZMK firmware, so
  # pick the NICENANO drive by serial: flashing the wrong half bit us 2026-11-01.
  case "$SIDE" in
    left)  WANT_SERIAL=3A8F02D9AD37EF58 ;;
    right) WANT_SERIAL=EC93E089067872A6 ;;
  esac
  DEV=$(lsblk -rno NAME,LABEL,SERIAL | awk -v s="$WANT_SERIAL" '$2=="NICENANO" && $3==s {print "/dev/"$1; exit}')
  if [[ -z "$DEV" ]]; then
    echo "!! $SIDE half's NICENANO (serial $WANT_SERIAL) not found."
    lsblk -rno NAME,LABEL,SERIAL | awk '$2=="NICENANO"{print "   found instead: /dev/"$1" serial "$3}'
    echo "   Double-tap RESET on the $SIDE half, then re-run."
    exit 1
  fi
  udisksctl mount -b "$DEV" >/dev/null 2>&1 || true
  MP=$(findmnt -rno TARGET "$DEV")
  echo ">> flashing $VARIANT $SIDE -> $MP (board reboots automatically)"
  cp -v "$UF2" "$MP"/ || true
  sync || true
  echo ">> done. NICENANO should disconnect as the board reboots into ZMK."
fi

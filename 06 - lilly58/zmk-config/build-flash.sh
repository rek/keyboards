#!/usr/bin/env bash
# Local build + flash for the 06 lilly58 (ZMK, nice!nano v2, wireless).
#
# Usage:
#   ./build-flash.sh left                 # left daily driver: Studio + battery proxy
#   ./build-flash.sh left --no-batt       # left fallback: Studio, battery proxy OFF
#   ./build-flash.sh right                # right half (peripheral)
#   ./build-flash.sh <side> [...] --no-flash   # build only, don't flash
#
# Left builds are ALWAYS ZMK-Studio-enabled (needs protobuf/grpcio-tools in the
# venv — see BUILDING.md). Studio only runs on the central, so the right build
# has no studio variant.
#
# --no-batt strips the split battery fetch/proxy (the second host-visible
# battery service) via Kconfig CLI overrides, which take precedence over
# lily58_left.conf. Use it to rule the dual battery service out when chasing
# host pairing problems. (2026-07-06: a pairing failure was wrongly blamed on
# it once — real fix was BT_CLR on the keeb + a bluetoothctl agent on the host;
# see BUILDING.md "Pairing to a Linux host".)
#
# To flash: put the target nice!nano in bootloader mode (double-tap RESET) so the
# NICENANO USB drive appears, then run the command.
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

SIDE="${1:?usage: build-flash.sh <left|right> [--no-batt] [--no-flash]}"; shift
case "$SIDE" in left|right) ;; *) echo "side must be left or right"; exit 1;; esac

FLASH=1; BATT=1
for arg in "$@"; do
  case "$arg" in
    --no-flash) FLASH=0 ;;
    --no-batt)  BATT=0 ;;
    *) echo "unknown flag: $arg (known: --no-batt --no-flash)"; exit 1 ;;
  esac
done

WS=/home/adam/dev/zmk-workspace
CONFIG_SRC="$(cd "$(dirname "$0")/config" && pwd)"
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
else
  BUILD_DIR="right"
  [[ "$BATT" == "0" ]] && { echo "--no-batt only applies to the left/central"; exit 1; }
fi

export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
export GNUARMEMB_TOOLCHAIN_PATH=/usr
export PATH="$WS/.venv/bin:$PATH"

echo ">> staging config to space-free path"
rm -rf "$STAGE"; mkdir -p "$STAGE"; cp -R "$CONFIG_SRC/." "$STAGE/"

echo ">> building $SHIELD -> build/$BUILD_DIR"
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

if [[ "$FLASH" == "1" ]]; then
  DEV=$(lsblk -rno NAME,LABEL | awk '$2=="NICENANO"{print "/dev/"$1; exit}')
  if [[ -z "$DEV" ]]; then
    echo "!! NICENANO not found. Double-tap RESET on the $SIDE half, then re-run."
    exit 1
  fi
  udisksctl mount -b "$DEV" >/dev/null 2>&1 || true
  MP=$(findmnt -rno TARGET "$DEV")
  echo ">> flashing $SIDE -> $MP (board reboots automatically)"
  cp -v "$UF2" "$MP"/ || true
  sync || true
  echo ">> done. NICENANO should disconnect as the board reboots into ZMK."
fi

#!/usr/bin/env bash
# Local build + flash for the 06 lilly58 (ZMK, nice!nano v2, wireless).
#
# Usage:
#   ./build-flash.sh left            # build left half, then flash if NICENANO is in bootloader
#   ./build-flash.sh right           # build right half
#   ./build-flash.sh left --no-flash # build only, don't flash
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

SIDE="${1:?usage: build-flash.sh <left|right> [--no-flash]}"
FLASH=1; [[ "${2:-}" == "--no-flash" ]] && FLASH=0
case "$SIDE" in left|right) ;; *) echo "side must be left or right"; exit 1;; esac

WS=/home/adam/dev/zmk-workspace
CONFIG_SRC="$(cd "$(dirname "$0")/config" && pwd)"
STAGE="$WS/lily58-config"            # space-free staging path
BOARD="nice_nano@2.0.0/nrf52840/zmk"
SHIELD="lily58_${SIDE}"

export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
export GNUARMEMB_TOOLCHAIN_PATH=/usr
export PATH="$WS/.venv/bin:$PATH"

echo ">> staging config to space-free path"
rm -rf "$STAGE"; mkdir -p "$STAGE"; cp -R "$CONFIG_SRC/." "$STAGE/"

echo ">> building $SHIELD"
cd "$WS/zmk"
rm -rf "build/$SIDE"
west build -s app -d "build/$SIDE" -b "$BOARD" -- \
  -DSHIELD="$SHIELD" -DZMK_CONFIG="$STAGE"

UF2="$WS/zmk/build/$SIDE/zephyr/zmk.uf2"
echo ">> built: $UF2 ($(du -h "$UF2" | cut -f1))"

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

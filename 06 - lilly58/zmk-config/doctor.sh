#!/usr/bin/env bash
# doctor.sh — diagnose and set up the 06 Lily58 Pro (ZMK, nice!nano v2) on an Arch box.
#
#   doctor.sh [check]                        read-only diagnosis; safe to run any time
#   doctor.sh setup [--yes] [--dry-run] [--latest]
#                                            one-time machine setup; every step is
#                                            skipped if it is already done
#
# setup flags:  --yes      don't ask before each step (and pass --noconfirm to pacman)
#               --dry-run  print what would run, change nothing
#               --latest   new workspace tracks ZMK main instead of the known-good commit
#                          (default: pin a NEW clone to the commit this build was tested on;
#                          an existing workspace is never moved)
#
# Env overrides (build-flash.sh honours ZMK_WS too):
#   ZMK_WS      ZMK workspace           (default ~/dev/zmk-workspace)
#   LILY58_MAC  keyboard BLE address    (default: auto-detect a paired "Lily58")
#
# check exits 0 when there are no problems (warnings are fine), 1 otherwise.
# What each finding means and why: see ../TROUBLESHOOTING.md.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SRC="$HERE/config"
WS="${ZMK_WS:-$HOME/dev/zmk-workspace}"
USB_SYSFS="${USB_SYSFS:-/sys/bus/usb/devices}"    # overridable so tests can fake it
VID=1d50 PID=615e
BOARD="nice_nano@2.0.0/nrf52840/zmk"
SELF=$(printf '%q' "$HERE/doctor.sh")          # %q: the repo path has spaces, hints must paste cleanly
BF=$(printf '%q' "$HERE/build-flash.sh")
KNOWN_GOOD_ZMK=64daf698e073e37b6748ac54f4eb48d8666af0b9   # 2026-06-20, builds + runs
ZMK_URL=https://github.com/zmkfirmware/zmk.git
UDEV_RULE=/etc/udev/rules.d/50-zmk-studio.rules
UDEV_LINE='SUBSYSTEM=="tty", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="615e", TAG+="uaccess"'
PKGS=(git arm-none-eabi-gcc arm-none-eabi-newlib cmake ninja dtc python udisks2 bluez bluez-utils usbutils)

# Expected kscan pins in a built image (see BUILDING.md "Verify the image").
ROWS="0x12 0xf 0xe 0x10 0xa"
COLS_LEFT="0x4 0x5 0x6 0x7 0x8 0x9"
COLS_RIGHT="0x9 0x8 0x7 0x6 0x5 0x4"

if [[ -t 1 ]]; then G=$'\e[32m' Y=$'\e[33m' R=$'\e[31m' D=$'\e[2m' N=$'\e[0m'; else G='' Y='' R='' D='' N=''; fi
PASS=0 WARN=0 FAIL=0
ok()      { PASS=$((PASS + 1)); printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
warn()    { WARN=$((WARN + 1)); printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
bad()     { FAIL=$((FAIL + 1)); printf '  %s✗%s %s\n' "$R" "$N" "$*"; }
info()    { printf '  %s·%s %s\n' "$D" "$N" "$*"; }
fix()     { printf '      %sfix:%s %s\n' "$D" "$N" "$*"; }
section() { printf '\n%s%s%s\n' "$D" "$*" "$N"; }
die()     { printf '%s\n' "$*" >&2; exit 2; }

# ----------------------------------------------------------------------------
# check
# ----------------------------------------------------------------------------

check_tools() {
  section "Host tools"
  local missing=() cmd pkg
  while read -r cmd pkg; do
    if command -v "$cmd" >/dev/null 2>&1; then ok "$cmd"; else bad "$cmd not found"; missing+=("$pkg"); fi
  done <<'EOF'
git git
arm-none-eabi-gcc arm-none-eabi-gcc
cmake cmake
ninja ninja
dtc dtc
python python
udisksctl udisks2
bluetoothctl bluez-utils
lsusb usbutils
busctl systemd
EOF
  if command -v pacman >/dev/null 2>&1 && ! pacman -Q arm-none-eabi-newlib >/dev/null 2>&1; then
    bad "arm-none-eabi-newlib not installed (C library for the ARM compiler)"
    missing+=(arm-none-eabi-newlib)
  fi
  ((${#missing[@]})) && fix "sudo pacman -S --needed ${missing[*]}    (or: $SELF setup)"
}

check_workspace() {
  section "ZMK workspace ($WS)"
  if [[ ! -d $WS ]]; then
    bad "workspace not found"; fix "$SELF setup   (or set ZMK_WS to your workspace)"; return
  fi
  local w="$WS/.venv/bin/west"
  if [[ -x $w ]]; then ok "west in venv ($("$w" --version 2>/dev/null | head -1))"; else bad "west missing from $WS/.venv"; fix "$SELF setup"; fi
  if [[ -d $WS/zmk/app && -d $WS/zmk/zephyr && -d $WS/zmk/modules ]]; then
    ok "ZMK tree present (app, zephyr, modules)"
  else
    bad "ZMK tree incomplete (west update not finished?)"; fix "$SELF setup"
  fi
  if [[ -x $WS/.venv/bin/python ]]; then
    if "$WS/.venv/bin/python" -c 'import google.protobuf, grpc_tools' 2>/dev/null; then
      ok "protobuf + grpcio-tools in venv (needed by ZMK Studio builds)"
    else
      bad "protobuf / grpcio-tools missing from venv (Studio build will fail)"
      fix "$WS/.venv/bin/pip install protobuf grpcio-tools"
    fi
  fi
  if [[ -d $WS/zmk/.git ]]; then
    local head; head=$(git -C "$WS/zmk" rev-parse HEAD 2>/dev/null)
    if [[ $head == "$KNOWN_GOOD_ZMK" ]]; then
      ok "ZMK is at the known-good commit"
    else
      info "ZMK at ${head:0:8}; known-good is ${KNOWN_GOOD_ZMK:0:8}. Only matters if a build breaks."
      info "pin: git -C $WS/zmk fetch --depth=1 origin $KNOWN_GOOD_ZMK && git -C $WS/zmk checkout FETCH_HEAD && (cd $WS/zmk && $WS/.venv/bin/west update -n -o=--depth=1)"
    fi
  fi
  if grep -qE '/home/[A-Za-z]' "$HERE/build-flash.sh" 2>/dev/null; then
    bad "build-flash.sh hardcodes a home directory"; fix "use WS=\"\${ZMK_WS:-\$HOME/dev/zmk-workspace}\""
  fi
}

# Verify one built image's key-matrix pins. $1=build dir name, $2=left|right
check_image_pins() {
  local dir=$1 side=$2 b="$WS/zmk/build/$1" dts uf2 rows cols want_cols
  dts="$b/zephyr/zephyr.dts"; uf2="$b/zephyr/zmk.uf2"
  [[ -f $dts && -f $uf2 ]] || return 0
  rows=$(grep -m1 'row-gpios' "$dts" | grep -oE '&pro_micro 0x[0-9a-f]+' | awk '{print $2}' | tr '\n' ' ' | sed 's/ $//')
  cols=$(grep -m1 'col-gpios' "$dts" | grep -oE '&pro_micro 0x[0-9a-f]+' | awk '{print $2}' | tr '\n' ' ' | sed 's/ $//')
  want_cols=$COLS_LEFT; [[ $side == right ]] && want_cols=$COLS_RIGHT
  if [[ $rows == "$ROWS" && $cols == "$want_cols" ]]; then
    ok "build/$dir: pin map correct ($side)"
  else
    bad "build/$dir: WRONG pin map — rows [$rows] cols [$cols]"
    info "expected rows [$ROWS] cols [$want_cols]. Stock pins (rows 0x5-0x9) mean the keymap"
    info "override was dropped: the board would enumerate and type nothing. DO NOT FLASH."
    fix "rebuild with $BF $side --no-flash (it injects the required define)"
  fi
  local other=right newer; [[ $side == right ]] && other=left    # lily58_<other>.conf isn't part of this image
  newer=$(find "$CONFIG_SRC" -type f ! -name "lily58_${other}.conf" -newer "$uf2" -print -quit 2>/dev/null)
  if [[ -n $newer ]]; then
    warn "build/$dir is older than config/$(basename "$newer") — it may be missing your latest edits"
    fix "$BF $side --no-flash    (then flash it)"
  fi
}

check_images() {
  section "Built firmware images"
  local any=0 d
  for d in left-studio left-studio-nobat left; do
    [[ -f $WS/zmk/build/$d/zephyr/zmk.uf2 ]] && { any=1; check_image_pins "$d" left; }
  done
  [[ -f $WS/zmk/build/right/zephyr/zmk.uf2 ]] && { any=1; check_image_pins right right; }
  ((any)) || info "no left/right image built yet — run: $BF left --no-flash"
  if [[ -f $WS/zmk/build/reset/zephyr/zmk.uf2 ]]; then
    ok "settings_reset image present"
  else
    warn "settings_reset image not built (needed to clear bonds / stuck output)"; fix "$SELF setup"
  fi
}

check_studio_access() {
  section "ZMK Studio serial access"
  if [[ -r $UDEV_RULE ]] && grep -q "$VID" "$UDEV_RULE" && grep -q "$PID" "$UDEV_RULE" && grep -q uaccess "$UDEV_RULE"; then
    ok "udev rule installed"
  else
    warn "udev rule for the Studio serial port missing (only matters for live keymap editing)"; fix "$SELF setup"
  fi
  local t ports=0 usb_n
  for t in /dev/ttyACM*; do
    [[ -e $t ]] || continue
    udevadm info -q property -n "$t" 2>/dev/null | grep -q '^ID_MODEL=Lily58$' || continue
    ports=$((ports + 1))
    if [[ -r $t && -w $t ]]; then ok "$t is accessible to you"; else bad "$t exists but you can't open it"; fix "$SELF setup, then replug the left half"; fi
  done
  usb_n=$(lily_usb_list | grep -c .)
  if ((usb_n == 0)); then
    info "no keyboard on USB. Studio only works over the USB cable in this build (not Bluetooth):"
    info "plug the LEFT half in with a data cable, then a serial port (/dev/ttyACM*) appears"
  elif ((ports == 0)); then
    warn "Lily58 is on USB but has no serial port, so ZMK Studio can't connect"
    fix "it's probably the RIGHT half (no Studio there) — plug in the LEFT — or the left image was built without Studio (build-flash.sh left always includes it)"
  fi
  if systemctl is-active --quiet ModemManager 2>/dev/null; then
    warn "ModemManager is running; it can grab USB serial ports and make Studio fail to connect"
    fix "sudo systemctl disable --now ModemManager"
  fi
}

check_bluetooth_stack() {
  section "Bluetooth on this machine"
  if systemctl is-active --quiet bluetooth 2>/dev/null; then ok "bluetooth service running"; else bad "bluetooth service not running"; fix "sudo systemctl enable --now bluetooth"; fi
  if command -v rfkill >/dev/null 2>&1 && rfkill list bluetooth 2>/dev/null | grep -qi 'blocked: yes'; then
    bad "Bluetooth radio is blocked"; fix "rfkill unblock bluetooth"
  fi
  local show; show=$(bluetoothctl show 2>&1)
  if grep -q 'Powered: yes' <<<"$show"; then
    ok "adapter powered"
  elif grep -q 'Powered: no' <<<"$show"; then
    bad "adapter is off"; fix "bluetoothctl power on"
  else
    bad "no Bluetooth adapter found"
  fi
}

# Prints "<port> <serial>" for each Lily58 on USB (reads sysfs; no root needed).
lily_usb_list() {
  local d
  for d in "$USB_SYSFS"/*; do
    [[ -r $d/idVendor && -r $d/idProduct ]] || continue
    [[ $(<"$d/idVendor") == "$VID" && $(<"$d/idProduct") == "$PID" ]] || continue
    echo "$(basename "$d") $(cat "$d/serial" 2>/dev/null)"
  done
}

check_usb() {
  section "USB"
  local found=0 serial port n
  while read -r port serial; do
    [[ -n $port ]] || continue
    found=1; ok "Lily58 on USB at $port (serial ${serial:-unreadable})"
    if journalctl -k -n 1 --no-pager >/dev/null 2>&1; then
      n=$(journalctl -k --since "10 min ago" --no-pager 2>/dev/null | grep -c "usb $port: USB disconnect")
      if ((n >= 3)); then
        bad "USB dropped $n times in 10 min — cable, port or hub fault"; fix "try another data cable, plug straight into the PC (no hub)"
      elif ((n > 0)); then
        info "$n USB disconnect(s) in the last 10 min (a replug or reflash counts)"
      fi
    fi
  done < <(lily_usb_list)
  if lsblk -rno LABEL 2>/dev/null | grep -qx NICENANO; then
    info "a half is in bootloader mode (NICENANO drive mounted/visible)"; found=1
  fi
  if ((!found)); then
    warn "no Lily58 on USB (fine if you're on Bluetooth only)"
    fix "if you expected it: the cable may be charge-only (LED on but nothing here) — use a data cable"
  fi
}

# Print one battery percentage per line, in GATT order (first = left/central, second = right).
read_batteries() {
  local mac=${1^^} p u v
  while read -r p; do
    u=$(busctl get-property org.bluez "$p" org.bluez.GattCharacteristic1 UUID 2>/dev/null | cut -d'"' -f2)
    [[ ${u:4:4} == 2a19 ]] || continue
    v=$(busctl call org.bluez "$p" org.bluez.GattCharacteristic1 ReadValue 'a{sv}' 0 2>/dev/null | awk '{print $3}')
    [[ -n $v ]] && echo "$v"
  done < <(busctl tree org.bluez 2>/dev/null | grep -oE "/org/bluez/hci[0-9]+/dev_${mac//:/_}/service[0-9a-f]+/char[0-9a-f]+\$" | sort -u)
}

check_ble_one() {
  local mac=$1 out paired bonded trusted connected blocked
  out=$(bluetoothctl info "$mac" 2>&1)
  field() { grep -m1 "^[[:space:]]*$1:" <<<"$out" | awk '{print $2}'; }
  paired=$(field Paired); bonded=$(field Bonded); trusted=$(field Trusted); connected=$(field Connected); blocked=$(field Blocked)
  local pair_help="interactive bluetoothctl: remove $mac; agent NoInputNoOutput; default-agent; scan on; pair $mac; trust $mac; connect $mac"

  if [[ $blocked == yes ]]; then
    bad "$mac is BLOCKED on this host"; fix "bluetoothctl unblock $mac"; return
  fi
  if [[ $paired != yes || $bonded != yes ]]; then
    if [[ $connected == yes ]]; then
      bad "$mac connects but is not paired/bonded — a STALE BOND (keyboard remembers a key this host deleted)"
    else
      warn "$mac is known but not paired"
    fi
    fix "on the keyboard: RAISE + ESC (BT_CLR), needs both halves linked — or settings_reset both halves"
    fix "$pair_help"
    return
  fi
  ok "$mac paired and bonded"
  if [[ $trusted == yes ]]; then ok "trusted (auto-reconnects)"; else warn "not trusted — it won't reconnect by itself"; fix "bluetoothctl trust $mac"; fi
  if [[ $connected != yes ]]; then
    warn "not connected right now — the keyboard is asleep, off, or on a different Bluetooth profile"
    fix "press a key; RAISE + 1..5 selects profile 0-4; if it never connects, see the stale-bond fix above"
    return
  fi
  ok "connected"

  local dev="/org/bluez/hci0/dev_${mac^^}"; dev=${dev//:/_}
  if busctl get-property org.bluez "$dev" org.bluez.Device1 ServicesResolved 2>/dev/null | grep -q 'b false'; then
    bad "connected but GATT services never resolved (usually means unbonded)"; fix "re-pair: remove, BT_CLR, pair"; return
  fi
  local bats; mapfile -t bats < <(read_batteries "$mac")
  case ${#bats[@]} in
    0) info "no battery service readable" ;;
    1) warn "only one battery service (left ${bats[0]}%). The right half isn't proxied — left image built with --no-batt?"
       fix "$BF left   (canonical image has battery proxy on)" ;;
    *) if ((bats[0] <= 15)); then warn "left battery low: ${bats[0]}%"; else ok "left battery ${bats[0]}%"; fi
       if ((bats[1] == 0)); then
         warn "right battery reads 0% — right half asleep/off, or its link came up <60 s ago (it reports every 60 s)"
       else
         if ((bats[1] <= 15)); then warn "right battery low: ${bats[1]}%"; else ok "right battery ${bats[1]}% — the left<->right link is up"; fi
       fi ;;
  esac
}

check_ble() {
  section "Bluetooth link to the keyboard"
  local macs=() line
  if [[ -n ${LILY58_MAC:-} ]]; then
    macs=("$LILY58_MAC")
  else
    while read -r line; do macs+=("$(awk '{print $2}' <<<"$line")"); done < <(bluetoothctl devices 2>/dev/null | grep -i 'lily58')
  fi
  if ((${#macs[@]} == 0)); then
    warn "no Lily58 paired to this host (fine if you only use USB)"
    fix "interactive bluetoothctl: agent NoInputNoOutput; default-agent; scan on; pair <MAC>; trust <MAC>; connect <MAC>"
    fix "if it never shows in the scan, it's bonded to another host: BT_CLR (RAISE + ESC) or pick a free profile (RAISE + 1..5)"
    return
  fi
  local m; for m in "${macs[@]}"; do check_ble_one "$m"; done
  info "to see WHICH link delivers keystrokes: sudo keyd monitor   (or: sudo evtest)"
}

main_check() {
  printf 'Lily58 doctor — %s\n' "$(date '+%F %T')"
  check_tools; check_workspace; check_images; check_studio_access
  check_bluetooth_stack; check_usb; check_ble
  printf '\n%s%d ok, %d warnings, %d problems%s\n' "$D" "$PASS" "$WARN" "$FAIL" "$N"
  ((FAIL == 0))
}

# ----------------------------------------------------------------------------
# setup
# ----------------------------------------------------------------------------

YES=0 DRY=0 LATEST=0
run() {
  if ((DRY)); then printf '  %swould run:%s %s\n' "$D" "$N" "$*"; return 0; fi
  printf '  %s$%s %s\n' "$D" "$N" "$*"; "$@"
}
in_dir() { local d=$1; shift; if ((DRY)); then run "$@"; else (cd "$d" && run "$@"); fi; }
confirm() {
  ((YES || DRY)) && return 0
  local a; read -r -p "  $1 [Y/n] " a || { echo; info "no answer (not a terminal) — re-run with --yes"; return 1; }
  [[ ! $a =~ ^[Nn] ]]
}
skip() { info "already done: $*"; }

setup_packages() {
  section "1/6 Packages"
  local missing=() p
  for p in "${PKGS[@]}"; do pacman -Q "$p" >/dev/null 2>&1 || missing+=("$p"); done
  if ((${#missing[@]} == 0)); then skip "all packages installed"; return 0; fi
  info "missing: ${missing[*]}"
  local extra=(); ((YES)) && extra=(--noconfirm)
  confirm "install with pacman (sudo)?" && run sudo pacman -S --needed "${extra[@]}" "${missing[@]}"
}

setup_bluetooth() {
  section "2/6 Bluetooth service"
  if [[ ! -d /run/systemd/system ]]; then info "no systemd running here — skipping"; return 0; fi
  if systemctl is-enabled --quiet bluetooth 2>/dev/null && systemctl is-active --quiet bluetooth 2>/dev/null; then
    skip "bluetooth enabled and running"; return 0
  fi
  confirm "enable and start bluetooth.service (sudo)?" && run sudo systemctl enable --now bluetooth
}

setup_workspace() {
  section "3/6 ZMK workspace ($WS)"
  confirm "create/complete the workspace (about 1.8 GB, several minutes)?" || return 0
  [[ -d $WS ]] || run mkdir -p "$WS" || return 1
  [[ -x $WS/.venv/bin/python ]] && skip "venv" || run python -m venv "$WS/.venv" || return 1
  [[ -x $WS/.venv/bin/west ]] && skip "west" || run "$WS/.venv/bin/pip" install west || return 1
  if [[ -d $WS/zmk/.git ]]; then
    skip "ZMK clone (left where it is: $(git -C "$WS/zmk" rev-parse --short HEAD 2>/dev/null); known-good is ${KNOWN_GOOD_ZMK:0:8})"
  elif ((LATEST)); then
    run git clone --depth=1 "$ZMK_URL" "$WS/zmk" || return 1
  else
    # Shallow, but at the pinned commit: `git clone --depth=1` would fetch main's tip instead.
    # GitHub serves any commit by hash. Only ever done on a fresh clone.
    run git init -q "$WS/zmk" || return 1
    run git -C "$WS/zmk" remote add origin "$ZMK_URL" || return 1
    run git -C "$WS/zmk" fetch -q --depth=1 origin "$KNOWN_GOOD_ZMK" || return 1
    run git -C "$WS/zmk" checkout -q FETCH_HEAD || return 1
  fi
  [[ -d $WS/zmk/.west ]] && skip "west init" || in_dir "$WS/zmk" "$WS/.venv/bin/west" init -l app || return 1
  if [[ -d $WS/zmk/zephyr && -d $WS/zmk/modules ]]; then skip "west update"; else in_dir "$WS/zmk" "$WS/.venv/bin/west" update -n -o=--depth=1 || return 1; fi
  if "$WS/.venv/bin/python" -c 'import elftools, yaml, pykwalify' 2>/dev/null; then skip "Zephyr python requirements"
  else run "$WS/.venv/bin/pip" install -r "$WS/zmk/zephyr/scripts/requirements.txt" || return 1; fi
  if "$WS/.venv/bin/python" -c 'import google.protobuf, grpc_tools' 2>/dev/null; then skip "protobuf + grpcio-tools"
  else run "$WS/.venv/bin/pip" install protobuf grpcio-tools || return 1; fi
}

setup_udev() {
  section "4/6 ZMK Studio serial-port permission (udev rule)"
  if [[ -r $UDEV_RULE ]] && grep -q "$VID" "$UDEV_RULE" && grep -q "$PID" "$UDEV_RULE" && grep -q uaccess "$UDEV_RULE"; then
    skip "$UDEV_RULE"; return 0
  fi
  confirm "write $UDEV_RULE (sudo)?" || return 0
  if ((DRY)); then run sudo tee "$UDEV_RULE" "<<<" "'$UDEV_LINE'"; else printf '%s\n' "$UDEV_LINE" | run sudo tee "$UDEV_RULE" >/dev/null; fi
  run sudo udevadm control --reload || warn "udev not running here — rule will apply on next boot"
  run sudo udevadm trigger || true
  info "replug the left half so the rule applies to it"
}

setup_reset_image() {
  section "5/6 settings_reset image (clears bonds and a stuck USB/BLE output)"
  if [[ -f $WS/zmk/build/reset/zephyr/zmk.uf2 ]]; then skip "build/reset/zephyr/zmk.uf2"; return 0; fi
  if [[ ! -x $WS/.venv/bin/west && $DRY == 0 ]]; then warn "workspace not ready — rerun setup"; return 1; fi
  confirm "build it now (about a minute)?" || return 0
  ( export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb GNUARMEMB_TOOLCHAIN_PATH=/usr PATH="$WS/.venv/bin:$PATH"
    in_dir "$WS/zmk" "$WS/.venv/bin/west" build -s app -d build/reset -p -b "$BOARD" -- -DSHIELD=settings_reset )
}

main_setup() {
  local a
  for a in "$@"; do
    case $a in
      --yes | -y) YES=1 ;;
      --dry-run | -n) DRY=1 ;;
      --latest) LATEST=1 ;;
      *) die "unknown flag: $a (known: --yes --dry-run --latest)" ;;
    esac
  done
  command -v pacman >/dev/null 2>&1 || die "setup automates Arch (pacman) only. Install: ${PKGS[*]}, then follow BUILDING.md; run '$SELF check' after."
  ((EUID == 0)) && die "run setup as your normal user (it calls sudo where needed)"
  ((DRY)) && info "dry run — nothing will change"
  local rc=0
  setup_packages || rc=1
  setup_bluetooth || rc=1
  setup_workspace || rc=1
  setup_udev || rc=1
  setup_reset_image || rc=1
  section "6/6 Next"
  echo "  1. Label the two halves L and R."
  echo "  2. One board at a time — double-tap RESET (red pulse, NICENANO drive appears):"
  echo "       flash build/reset/zephyr/zmk.uf2, wait 5 s, double-tap again, then run"
  echo "       $BF left      (and later: ... right)"
  echo "  3. Pair the host, then run: $SELF check"
  ((rc == 0)) || printf '\n%s%s%s\n' "$R" "setup finished with problems (see above)." "$N"
  return "$rc"
}

usage() { sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

cmd="${1:-check}"; shift || true
case "$cmd" in
  check) main_check ;;
  setup) main_setup "$@" ;;
  -h | --help | help) usage ;;
  *) usage >&2; exit 2 ;;
esac

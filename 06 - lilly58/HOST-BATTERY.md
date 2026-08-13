# Showing the battery on the host

How to get both halves' battery percentage into a desktop status bar, and why
reading it is more awkward than it looks. Hardware side of the battery (wiring,
charging, capacity) is in [`README.md`](README.md#battery); this file is purely
host-side.

## The script

[`zmk-kb-status`](https://github.com/rek/devconfig/blob/main/bin/zmk-kb-status)
lives in the [devconfig](https://github.com/rek/devconfig) repo. It's a single
bash file with no dependencies beyond the `bluetoothctl` / `busctl` that BlueZ
already installs, and it needs no configuration — it autodetects a connected BLE
keyboard advertising the battery service.

```sh
curl -o ~/.local/bin/zmk-kb-status \
  https://raw.githubusercontent.com/rek/devconfig/main/bin/zmk-kb-status
chmod +x ~/.local/bin/zmk-kb-status
zmk-kb-status --format waybar
```

`--format` picks the output shape: `waybar` (JSON for a custom module), `text`
(`󰈷 85 72`, for GNOME panel extensions like Executor, or tmux/polybar), `json`,
or `plain` (`usb|85|72`). Full recipes for each bar, plus the config file
format, are in
[docs/zmk-kb-status.md](https://github.com/rek/devconfig/blob/main/docs/zmk-kb-status.md).

For this board specifically, pin it so `usb` means *the left half* is wired
rather than merely some ZMK board being plugged in:

```sh
zmk-kb-status --mac E8:0C:B3:F6:66:10 --usb-serial 3A8F02D9AD37EF58
```

Those two values are specific to this build — a rebuilt or reflashed board will
have a different BLE address, and the USB serial identifies the left nice!nano.
Omit both to autodetect.

## Why the right half needs special handling

`lily58.conf` sets:

```
CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y
CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY=y
```

The right half never talks to the host — only the left/central does. Fetching
pulls the peripheral's level over the split link; proxying republishes it to the
host as a **second instance of the BLE battery service**.

That second instance is the awkward part. BlueZ exposes the *primary* battery
through a convenience interface, `org.bluez.Battery1`, with a plain `Percentage`
property — that's the left half, and it's easy. It does **not** surface the
second instance there. Reading the right half means walking the device's GATT
tree for characteristics with UUID `2a19` (battery level) and calling `ReadValue`
on the extra one:

```sh
busctl tree org.bluez | grep dev_E8_0C_B3_F6_66_10
# then for each service<N>/char<N>, check its UUID property for 2a19
```

Without the proxy configs above, only one percentage exists and the right half
is simply unknowable from the host.

## Gotcha: there is no battery over USB

ZMK reports battery **only** through the BLE battery service. Plugging in does
not give you a wired readout — dumping the USB HID report descriptor shows only
a keyboard collection (usage page `0x01`) and a consumer-control collection
(`0x0C`), with no battery-strength usage:

```sh
od -An -tx1 /sys/bus/usb/devices/*/*/0003:1D50:615E.*/report_descriptor
```

Because nothing declares a battery, the kernel creates no `power_supply` entry
for the keyboard. So a USB-only session shows the wired icon and no percentage,
and that's correct behaviour, not a bug. To see battery while typing over USB you
need the BLE link *also* connected — which it normally is, since ZMK's endpoint
selection only decides where HID reports go, not whether the BLE connection
lives.

## Gotcha: connected but no battery (unbonded)

The most confusing failure. BlueZ reports the device as connected, yet every
battery read comes back empty, because GATT services never resolved:

```sh
D=/org/bluez/hci0/dev_E8_0C_B3_F6_66_10
busctl get-property org.bluez $D org.bluez.Device1 ServicesResolved   # b false
busctl get-property org.bluez $D org.bluez.Battery1 Percentage
# Failed to get property Percentage: No such interface 'org.bluez.Battery1'
```

`Paired: no` / `Bonded: no` in `bluetoothctl info` confirms it. Without a bond
BlueZ never resolves services, so `org.bluez.Battery1` doesn't exist on the
device object *at all* and `busctl tree` shows zero service paths under it —
both the primary read and the `2a19` proxy walk fail for the same reason.

The fix is re-pairing (clear the profile with `BT_CLR` on the raise layer, then
`bluetoothctl remove <mac>` and pair again), not anything script-side.
`zmk-kb-status` reports this as class `unknown` rather than `off`, precisely so a
blank readout isn't ambiguous between "keyboard is away" and "keyboard is here
but unreadable".

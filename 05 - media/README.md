# Keyboard 05 — Media Macropad

6-key wireless macropad. Built on the viagrid 3.2 PCB template (`/home/adam/dev/keyboards/viagrid`).

## MCU

Nice!Nano V2 (Chinese clone). NRF52840, BLE, built-in LiPo charger.

## Firmware

ZMK (BLE-native, official Nice!Nano V2 board target).

## Components (BOM)

| Part | Qty | Notes |
|---|---|---|
| Nice!Nano V2 (clone) | 1 | NRF52840 module |
| MX or Choc switch | 6 | match viagrid 3.2 footprint |
| Keycap | 6 | 1u |
| 1N4148W diode (SOD-123, SMD) | 6 | matrix wiring |
| LiPo battery 3.7V | 1 | 301230 (~110mAh) or 401230 (~150mAh) |
| Slide switch SS-12D00G4 | 1 | power cutoff |
| Tactile button (SPST momentary) | 1 | reset (optional) |
| Mill-Max sockets / 1.27mm headers | 2× 12-pin | socket the nano (optional) |
| JST-PH 2.0mm 2-pin header | 1 | battery connector (optional, can solder direct) |

Matrix wiring with SMD diodes (1N4148W, SOD-123), per viagrid 3.2 template.

## Battery wiring (Nice!Nano V2)

V2 has dedicated `BAT+` / `BAT-` pads on the underside next to the USB end.

```
Battery (+) ──► Slide switch ──► BAT+ pad
Battery (−) ─────────────────► BAT− pad
```

Notes:
- **Polarity critical** — reversed battery kills the nano.
- Slide switch in series on the **+** line cuts power fully (no idle drain when stored).
- Charging happens automatically over USB-C via the on-board MAX1555/equivalent at ~100mA.
- Single-cell 3.7V LiPo only. No protection circuit needed if battery has built-in PCM (most small LiPos do).

## Schematic blocks

1. **Switch matrix** — 2×3 (or 3×2) matrix. Each switch in series with a 1N4148W (SOD-123) diode, cathode toward the column. Rows/cols on free GPIOs. NRF52840 internal pull-ups.
2. **MCU** — Nice!Nano V2 mounted on sockets, USB-C end facing user-accessible edge.
3. **Power** — battery → slide switch → `BAT+`, battery GND → `BAT−`.
4. **Reset** — momentary button between `RST` pin and `GND` (optional; double-tap reset is built-in).

## GPIO assignment (suggested)

Pick any 6 of: `D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 D10`. Avoid `D15`/`D16`/`D17` if you want to keep SPI/I2C free.

## KiCad setup

Required libs:
- https://kicad.github.io/footprints/Button_Switch_Keyboard.html

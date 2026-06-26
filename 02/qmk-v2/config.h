#pragma once

// Split handedness: each half stores L/R in EEPROM.
// Flash with the avrdude-split-left / avrdude-split-right targets to set it.
#define EE_HANDS

// Split serial link (single data wire on TRRS) — see README "TRRS".
#define SOFT_SERIAL_PIN D1
#define SPLIT_USB_DETECT

#define MATRIX_ROW_PINS { D4, C6, D7, E6 }
// Left half: reversed because the Pro Micro is installed backwards.
#define MATRIX_COL_PINS { B3, B1, F7, F6, F5, F4 }
// Right half: the board is a second left PCB used flipped (B.Cu up, hotswap accessible).
// The board flip reverses columns, and the backwards MCU also reverses columns —
// two reversals cancel out, so the right half needs the original pin order.
#define MATRIX_COL_PINS_RIGHT { F4, F5, F6, F7, B1, B3 }

#define DIODE_DIRECTION COL2ROW

#define DEBOUNCE 5

// Vial features:
#define VIAL_TAP_DANCE_ENTRIES 25
#define DYNAMIC_KEYMAP_LAYER_COUNT 3
#define VIAL_KEY_OVERRIDE_ENTRIES 2
#define VIAL_COMBO_ENTRIES 2

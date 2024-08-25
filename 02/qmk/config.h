#pragma once

// #define MASTER_LEFT
#define MASTER_RIGHT

// key matrix size
// #define MATRIX_ROWS 4
// #define MATRIX_COLS 12

#define USE_SERIAL
#define SOFT_SERIAL_PIN D1
// #define SERIAL_USE_MULTI_TRANSACTION
#define SPLIT_USB_DETECT

#define MATRIX_ROW_PINS { D4, C6, D7, E6 }
#define MATRIX_COL_PINS { F4, F5, F6, F7, B1, B3 }

#define DIODE_DIRECTION COL2ROW

#define DEBOUNCE 5

// Vial features:
#define VIAL_TAP_DANCE_ENTRIES 25
#define DYNAMIC_KEYMAP_LAYER_COUNT 3
#define VIAL_KEY_OVERRIDE_ENTRIES 2
#define VIAL_COMBO_ENTRIES 2

#pragma once

#define MASTER_LEFT

#define USE_SERIAL
#define SOFT_SERIAL_PIN D1
#define SPLIT_USB_DETECT

#define MATRIX_ROW_PINS { F4, F5, F6, F7 }
#define MATRIX_COL_PINS { D0, D4, C6, D7, E6, B4 }

#define DIODE_DIRECTION COL2ROW

#define DEBOUNCE 5

// Vial features:
#define VIAL_TAP_DANCE_ENTRIES 25
#define DYNAMIC_KEYMAP_LAYER_COUNT 3
#define VIAL_KEY_OVERRIDE_ENTRIES 2
#define VIAL_COMBO_ENTRIES 2

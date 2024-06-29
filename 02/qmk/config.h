#pragma once

// #include "config_common.h"

/* key matrix size */
#define MATRIX_ROWS 4
#define MATRIX_COLS 6

#define MATRIX_ROW_PINS { D4, C6, D7, E6 }
#define MATRIX_COL_PINS { F4, F5, F6, F7, B1, B3 }

#define DIODE_DIRECTION COL2ROW

#define DEBOUNCE 5

#define DYNAMIC_KEYMAP_LAYER_COUNT 2
// #define VIAL_KEY_OVERRIDE_ENTRIES x
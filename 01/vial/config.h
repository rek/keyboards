/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

// Plug USB into the LEFT half. No EE_HANDS: handedness stays as the
// old firmware had it, so no extra EEPROM flash step is needed.
#define MASTER_LEFT

// Keep the Vial tables small so the build fits the atmega32u4's 28 KB.
#define VIAL_TAP_DANCE_ENTRIES 4
#define VIAL_COMBO_ENTRIES 4
#define VIAL_KEY_OVERRIDE_ENTRIES 2

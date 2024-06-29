// Copyright 2024 Adam Tombleson (@rekarnar)
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H
#include "keymap_norwegian.h"

// #define RAISE MO(_RAISE)
#define LOWER MO(_LOWER)

enum layer_names {
  _BASE,
  // _RAISE,
  _LOWER
};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
  [_BASE] = LAYOUT(
    KC_TAB   , KC_Q     , KC_W     , KC_E     , KC_R     , KC_T     ,
    KC_LSFT  , KC_A     , KC_S     , KC_D     , KC_F     , KC_G     ,
    KC_LCTL  , KC_Z     , KC_X     , KC_C     , KC_V     , KC_B     ,
                                     LOWER    , KC_ENT   , KC_BSPC
  ),

  [_LOWER] = LAYOUT(
      KC_6     , KC_7     , KC_8     , KC_9     , KC_0     , KC_BSPC  ,
      KC_AMPR  , KC_SLSH  , KC_LPRN  , KC_RPRN  , KC_EQL   , KC_QUES  ,
      _______  , _______  , KC_LBRC  , KC_RBRC  , _______  , KC_ASTR  ,
                                       _______  , _______  , _______
  ),

    // [_RAISE] = LAYOUT(
    //     KC_F7    , KC_F8    , KC_F9    , KC_F10   , KC_F11   , _______  ,
    //     _______  , _______  , _______  , _______  , KC_F11   , _______  ,
    //     _______  , _______  , _______  , _______  , _______  , _______  ,
    //                                      _______  , _______  , _______
    // )
};

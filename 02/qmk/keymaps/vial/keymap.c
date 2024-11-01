// Copyright 2024 Adam Tombleson (@rekarnar)
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H
#include "keymap_norwegian.h"

#define RAISE MO(_RAISE)
#define LOWER MO(_LOWER)

enum layer_names {
  _BASE,
  _RAISE,
  _LOWER
};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
  [_BASE] = LAYOUT(
      KC_TAB   , KC_Q     , KC_W     , KC_E     , KC_R     , KC_T     ,                  KC_Y     , KC_U     , KC_I     , KC_O     , KC_P     , NO_ARNG  ,
      KC_LSFT  , KC_A     , KC_S     , KC_D     , KC_F     , KC_G     ,                  KC_H     , KC_J     , KC_K     , KC_L     , NO_OSTR  , NO_AE    ,
      KC_LCTL  , KC_Z     , KC_X     , KC_C     , KC_V     , KC_B     ,                  KC_N     , KC_M     , KC_COMM  , KC_DOT   , KC_MINUS , KC_QUOTE ,
                                       LOWER    , KC_ENT   , KC_BSPC  ,                  KC_SPC   , KC_ENT   , KC_DEL
  ),

  [_LOWER] = LAYOUT(
      KC_ESC   , KC_1     , KC_2     , KC_3     , KC_4     , KC_5     ,                  KC_6     , KC_7     , KC_8     , KC_9     , KC_0     , KC_BSPC  ,
      _______  , KC_EXLM  , KC_DQUO  , KC_AT    , _______  , KC_PERC  ,                  KC_AMPR  , KC_SLSH  , KC_LPRN  , KC_RPRN  , KC_EQL   , KC_QUES  ,
      _______  , _______  , _______  , _______  , _______  , _______  ,                  _______  , _______  , KC_LBRC  , KC_RBRC  , _______  , KC_ASTR  ,
                                       _______  , KC_LGUI  , _______  ,                  _______  , _______  , _______
  ),

  [_RAISE] = LAYOUT(
      KC_F1    , KC_F2    , KC_F3    , KC_F4    , KC_F5    , KC_F6    ,                  KC_F7    , KC_F8    , KC_F9    , KC_F10   , KC_F11   , _______  ,
      _______  , _______  , _______  , _______  , _______  , _______  ,                  _______  , _______  , _______  , _______  , KC_F11   , _______  ,
      _______  , _______  , _______  , _______  , _______  , _______  ,                  _______  , _______  , _______  , _______  , _______  , _______  ,
                                      _______  , _______  , _______  ,                  _______  , _______  , _______
  )
};

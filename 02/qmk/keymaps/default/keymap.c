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
        KC_Y     , KC_U     , KC_I     , KC_O     , KC_P     , NO_ARNG  ,
        KC_H     , KC_J     , KC_K     , KC_L     , NO_OSTR  , NO_AE    ,
        KC_N     , KC_M     , KC_COMM  , KC_DOT   , KC_MINUS , KC_QUOTE ,
                                         KC_SPC   , KC_ENT   , KC_DEL
    ),

    [_LOWER] = LAYOUT(
        KC_6     , KC_7     , KC_8     , KC_9     , KC_0     , KC_BSPC  ,
        KC_AMPR  , KC_SLSH  , KC_LPRN  , KC_RPRN  , KC_EQL   , KC_QUES  ,
        _______  , _______  , KC_LBRC  , KC_RBRC  , _______  , KC_ASTR  ,
                                         _______  , _______  , _______

    ),

    [_RAISE] = LAYOUT(
        KC_F7    , KC_F8    , KC_F9    , KC_F10   , KC_F11   , _______  ,
        _______  , _______  , _______  , _______  , KC_F11   , _______  ,
        _______  , _______  , _______  , _______  , _______  , _______  ,
                                         _______  , _______  , _______
    )
};

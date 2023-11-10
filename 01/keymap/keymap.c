    // Copyright 2023 Adam Tombleson (@rekarnar)
    // SPDX-License-Identifier: GPL-2.0-or-later

    #include QMK_KEYBOARD_H

    #define RAISE MO(_RAISE)
    #define LOWER MO(_LOWER)

    enum layer_names {
        _BASE,
        _RAISE, 
        _LOWER
    };

    const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
        [_BASE] = LAYOUT(
            KC_ESC  , KC_1   , KC_2   , KC_3   , KC_4   , KC_5   ,                    KC_6   , KC_7    , KC_8    , KC_9    , KC_0    , KC_BSPC,
            KC_TAB  , KC_Q   , KC_W   , KC_E   , KC_R   , KC_T   ,                    KC_Y   , KC_U    , KC_I    , KC_O    , KC_P    , KC_MINS,
            KC_CAPS , KC_A   , KC_S   , KC_D   , KC_F   , KC_G   ,                    KC_H   , KC_J    , KC_K    , KC_L    , KC_SCLN , KC_QUOT,
            KC_LSFT , KC_Z   , KC_X   , KC_C   , KC_V   , KC_B   ,                    KC_N   , KC_M    , KC_COMM , KC_DOT  , KC_SLSH , KC_RSFT,
            KC_LCTL , KC_TAB , KC_LSFT, KC_LALT,                                      KC_LT  , KC_GT   , KC_LPRN , KC_RPRN ,
                                        LOWER  , KC_SPC , KC_BSPC,                    RAISE  , KC_ENT  , KC_DEL
        ),
    
        [_LOWER] = LAYOUT(
            _______   , _______  , _______   , _______   , KC_LT     , KC_GT     ,                    KC_LCBR      , KC_RCBR     , _______      , _______      , _______ , KC_PLUS,
            QK_BOOT   , C(KC_W)  , _______   , _______   , C(KC_R)   , C(KC_T)   ,                    _______      , _______     , C(S(KC_UP))  , C(S(KC_DOWN)), KC_TILD , KC_PIPE,
            A(KC_TAB) , C(KC_A)  , C(KC_S)   , C(S(KC_D)), C(KC_Z)   , C(KC_R)   ,                    _______      , KC_LEFT     , KC_UP        , KC_DOWN      , KC_RGHT , KC_EQL,
            _______   , C(KC_Z)  , C(KC_X)   , C(KC_C)   , C(KC_V)   , C(S(KC_D)),                    _______      , _______     , G(S(KC_PGUP)), G(S(KC_PGDN)), KC_BSLS , KC_EQL,
            _______   , _______  , _______   , C(KC_SLSH),                                            KC_TILD      , _______     , KC_LBRC      , KC_RBRC      ,
                                               _______   , KC_LGUI   , A(KC_PSCR),                    C(S(KC_LEFT)), KC_GRAVE    , C(S(KC_RIGHT))

        ),

        [_RAISE] = LAYOUT(
            KC_F12    , KC_F1    , KC_F2     , KC_F3     , KC_F4     , KC_F5     ,                    KC_F6  , KC_F7   , KC_F8   , KC_F9   , KC_F10  , KC_F11 ,
            _______   , _______  , _______   , _______   , _______   , C(KC_F12) ,                    _______, _______ , _______ , _______ , _______ , _______,
            _______   , KC_LPRN  , KC_RPRN   , KC_EQL    , KC_GT     , KC_LCBR   ,                    _______, KC_HOME , KC_PGUP , KC_PGDN , KC_END  , _______,
            _______   , _______  , _______   , _______   , _______   , _______   ,                    KC_TAB , _______ , _______ , _______ , _______ , _______,
            _______   , _______  , _______   , _______   ,                                            _______, _______ , _______ , LALT(KC_TAB),
                                               KC_VOLD   , KC_MUTE   , KC_VOLU   ,                    _______, _______ , KC_PSCR
        )
    };

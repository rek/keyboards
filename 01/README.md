# Keyboard

**Style**: dactyl manuform 5x6

(but it is really: 4x6 + 4 + 3) 62 Keys!

## Model notes:

I got the base plates from back here: https://github.com/joshreve/dactyl-keyboard/tree/75da53f96e389d837055921bd2eb61b58b7787e2

Note that they seem to be broken in all commits past this one (as on writing, main is [here](https://github.com/joshreve/dactyl-keyboard/commit/dd706f14f9aacfc429160bf5b03b688fdb5ce2f4))

## Build notes:

Used normal amoebas and they were ok, made it pretty quick to solder. Would use again.

Diode to use: **1N4148**

## Firmware notes:
```
python3 -m pip install --user qmk
qmk setup
qmk list-keyboards | grep xxx
```

Then edit the keymap here:
```
~/qmk_firmware/keyboards/handwired/dactyl_manuform/5x6/keymaps/rek
```

flash: `qmk flash`

then just read: https://docs.qmk.fm/#/newbs_building_firmware

To reset for flashing we have 3 options:
* **Bootmagic reset**: Hold down the key at (0,0) in the matrix (usually the top left key or Escape) and plug in the keyboard
* **Physical reset button**: Briefly press the button on the back of the PCB - some may have pads you must short instead
* **Keycode in layout**: Press the key mapped to `QK_BOOT` if it is available
## Next time:

Reaearch: Amoeba Royale **vs** Amoeba King

Purchase: [PCS Kailh Hot-swappable PCB Socket Sip Socket Hot Plug](https://www.amazon.com/gp/product/B096WZ6TJ5?ie=UTF8&psc=1&linkCode=ll1&tag=dlfordio-20&linkId=1c74b975a667dbd57728eb68931f6446&language=en_US&ref_=as_li_ss_tl)

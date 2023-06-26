# Keyboard

Style: dactyl manuform 5x6

(but its really: 4x6 + 4 + 3)

## Build notes:

used normal amoebas and they were ok, made it pretty quick to solder.

diode: 1N4148

## Firmware:
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


## Next time:

Amoeba Royale vs Amoeba King

100 PCS Kailh Hot-swappable PCB Socket Sip Socket Hot Plug
https://www.amazon.com/gp/product/B096WZ6TJ5?ie=UTF8&psc=1&linkCode=ll1&tag=dlfordio-20&linkId=1c74b975a667dbd57728eb68931f6446&language=en_US&ref_=as_li_ss_tl
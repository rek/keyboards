# Keebs

build notes and config for any keyboards i build

## KiCad:

A nice intro: https://youtu.be/8WXpGTIbxlQ?si=IPm6OvvAeKLTbCmh

JLC Fabrication Toolkik Plugin

- Export Gerber

## Firmware notes

Make sure you are running python 3.8+

```sh
python3 -m pip install --user qmk
apt install gcc-arm-none-eabi avrdude dfu-programmer dfu-util
pip install -U Pillow
qmk setup
qmk list-keyboards | grep xxx
```

Then don't forget: https://docs.qmk.fm/faq_build#linux-udev-rules

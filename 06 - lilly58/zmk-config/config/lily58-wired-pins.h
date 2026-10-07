/*
 * TRRS wired split: the two nice!nano pins the halves talk over.
 * Shared by lily58_left.overlay and lily58_right.overlay.
 *
 * ZMK's wired split is full-duplex UART, so it needs TWO data wires. The
 * Lily58 TRRS jack (J2) only routes one to the controller:
 *
 *   J2 pad 1  VCC
 *   J2 pad 2  GND
 *   J2 pad 3  DATA  -> controller pad 2 (stock D2), via the W1 jumper
 *   J2 pad 4  P1 pad only. Hand-wire P1 to a free nice!nano pin (both halves!)
 *
 * Both controllers sit in the SWAPPED hole-set (see lily58.keymap), so DATA
 * is NOT on the stock D2 pin. Find it with a multimeter: continuity from J2
 * pad 3 to the nice!nano pins. Use the nRF names from nrf52840-pinout.webp
 * (P0.xx / P1.xx): PORT is the 0 or 1, PIN is the xx.
 *
 * Both halves use the same PCB in the same hole-set (same kscan rows), so the
 * pins should be the same on both. Check both anyway.
 *
 * Left sends on DATA and listens on P1; the right is the mirror. The
 * overlays handle that. You only fill in the pins below.
 */

/* Delete this line once the four values below are real. */
#error "Fill in the TRRS pins in config/lily58-wired-pins.h (see the comment at the top)"

/* nice!nano pin on J2 pad 3 (DATA) */
#define LILY58_DATA_PORT 0  /* TODO */
#define LILY58_DATA_PIN  0  /* TODO */

/* nice!nano pin you jumpered to P1 (J2 pad 4) */
#define LILY58_P1_PORT   0  /* TODO */
#define LILY58_P1_PIN    0  /* TODO */

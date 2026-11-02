/*
 * TRRS wired split: the two nice!nano pins the halves talk over.
 * Shared by lily58_left.overlay and lily58_right.overlay.
 *
 * ZMK's wired split is full-duplex UART, so it needs TWO data wires.
 *
 * Both controllers sit in the SWAPPED hole-set (see lily58.keymap). That set
 * swaps the controller's two pin rows, so every footprint net lands on a
 * different nice!nano pin than the PCB intends. Worked out 2026-11-01 from the
 * PCB file + meter readings (counting holes from the USB end, footprint pad N
 * = hole N in the row-net column):
 *
 *   footprint pad   PCB net        nice!nano pin it actually hits
 *   1               LED            RAW
 *   2               DATA           GND        <- DATA is grounded via W1!
 *   3, 4            GND            RST, VCC   <- PCB "GND" is really 3.3V
 *   5               SDA            P0.31
 *   6               SCL            P0.29
 *   21              VCC            GND
 *   23              GND            P0.08      <- tied to 3.3V, never use it
 *
 * So the TRRS jack (J2) carries: pad 1 = GND, pad 2 = 3.3V, pad 3 = DATA but
 * grounded, pad 4 = P1 pad only. The fix, on both halves:
 *   - P1 hand-wired to footprint hole 6 (P0.29).
 *   - W1 cut open (separates J2 pad 3 from the grounded DATA net), then
 *     J2 pad 3 hand-wired to footprint hole 5 (P0.31).
 *
 * Left sends on DATA and listens on P1; the right is the mirror. The
 * overlays handle that.
 */

/* J2 pad 3 (DATA), hand-wired to hole 5: P0.31 (W1 must be cut) */
#define LILY58_DATA_PORT 0
#define LILY58_DATA_PIN  31

/* J2 pad 4 via P1, hand-wired to hole 6: P0.29 */
#define LILY58_P1_PORT   0
#define LILY58_P1_PIN    29

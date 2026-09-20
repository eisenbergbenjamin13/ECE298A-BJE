<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->
## How it works

This is an 8-bit binary counter. At its heart is a single 8-bit register that
can be cleared without waiting for the clock. On every rising clock edge, the
counter decides what to do next in this order:

1. If rst_n is low, the count clears to 0 right away. It does not wait for a
   clock edge.
2. If LOAD is high, the value sitting on the uio pins gets written into the
   counter.
3. If EN is high, the count goes up by one. The adder is only 8 bits wide, so
   255 rolls over to 0.
4. If none of those apply, the count stays where it is.

The current count is always visible on uo_out[7:0], no matter what the control
pins are doing.

The uio bus does double duty, and OE picks which job it is doing. When OE is
high, uio_oe goes to all ones and the count is driven out on the uio pins. When
OE is low, uio_oe goes to all zeros, the pins let go and float, and whatever is
applied from outside gets read in as the load value.

That is where the tri-state outputs come from. Tiny Tapeout does not let a
design use z internally, so the actual tri-state buffers sit in the chip's pad
ring and uio_oe tells them when to drive.

One thing worth knowing: since a load reads from the uio pins, OE has to be low
for the load to pick up an outside value. If OE is high, the chip is driving
those pins itself, so it just reads its own count back and the load does nothing.

## How to test

Drive clk, hold rst_n low for a few cycles, then let it go. uo_out should read 0.

To watch it count, set ui_in[1] (EN) high. uo_out goes up by one every clock.

To make it hold, set EN low. The count freezes wherever it was.

To load a value, keep ui_in[2] (OE) low, put a byte on the uio pins, and raise
ui_in[0] (LOAD) for one clock edge. uo_out becomes that byte. If LOAD and EN are
both high, LOAD wins.

To see the rollover, load 0xFE and start counting. You get 0xFE, then 0xFF, then
0x00.

To check that reset really is asynchronous, pull rst_n low partway between two
clock edges while the counter is running. uo_out clears immediately instead of
waiting for the next edge.

To check the tri-state control, read uio_oe. It is 0x00 when OE is low and 0xFF
when OE is high. While the pins are driving, uio_out matches uo_out.

All of this is covered by the cocotb testbench in test/test.py. Run it with
make -B from the test directory.

## External hardware

None.

List external hardware used in your project (e.g. PMOD, LED display, etc), if any

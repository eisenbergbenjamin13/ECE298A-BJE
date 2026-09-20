# SPDX-FileCopyrightText: © 2026 Benjamin J. Eisenberg
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

# ui_in bit masks
LOAD = 0b001
EN   = 0b010
OE   = 0b100


async def step(dut, n=1):
    """Advance n clock edges, then let outputs settle before sampling."""
    await ClockCycles(dut.clk, n)
    await Timer(1, units="ns")


async def start(dut):
    """Start the clock and apply a reset."""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await step(dut, 1)


@cocotb.test()
async def test_reset(dut):
    """Reset clears the count to zero."""
    dut._log.info("reset")
    await start(dut)
    assert dut.uo_out.value == 0


@cocotb.test()
async def test_count(dut):
    """With EN high the count increments once per clock."""
    dut._log.info("count up")
    await start(dut)

    dut.ui_in.value = EN
    for expected in range(1, 11):
        await step(dut, 1)
        assert dut.uo_out.value == expected, \
            f"expected {expected}, got {int(dut.uo_out.value)}"


@cocotb.test()
async def test_hold(dut):
    """With EN low the count holds its value."""
    dut._log.info("hold")
    await start(dut)

    dut.ui_in.value = EN
    await step(dut, 5)
    held = int(dut.uo_out.value)
    assert held == 5, f"expected 5 after 5 enabled edges, got {held}"

    dut.ui_in.value = 0
    await step(dut, 10)
    assert dut.uo_out.value == held, \
        f"count moved while disabled: {held} -> {int(dut.uo_out.value)}"


@cocotb.test()
async def test_load(dut):
    """LOAD writes uio_in into the counter on a clock edge (OE low)."""
    dut._log.info("synchronous load")
    await start(dut)

    # count away from zero first
    dut.ui_in.value = EN
    await step(dut, 7)

    # OE low so the uio pins are inputs, then pulse LOAD for one edge
    dut.uio_in.value = 0xA5
    dut.ui_in.value = LOAD
    await step(dut, 1)
    assert dut.uo_out.value == 0xA5, \
        f"load failed, got {int(dut.uo_out.value):#04x}"

    # LOAD beats EN when both are high
    dut.uio_in.value = 0x3C
    dut.ui_in.value = LOAD | EN
    await step(dut, 1)
    assert dut.uo_out.value == 0x3C, \
        f"load should win over count, got {int(dut.uo_out.value):#04x}"


@cocotb.test()
async def test_wrap(dut):
    """The count wraps from 255 to 0."""
    dut._log.info("wraparound")
    await start(dut)

    dut.uio_in.value = 0xFE
    dut.ui_in.value = LOAD
    await step(dut, 1)
    assert dut.uo_out.value == 0xFE

    dut.ui_in.value = EN
    await step(dut, 1)
    assert dut.uo_out.value == 0xFF

    await step(dut, 1)
    assert dut.uo_out.value == 0x00, \
        f"expected wrap to 0, got {int(dut.uo_out.value)}"


@cocotb.test()
async def test_async_reset(dut):
    """Reset clears the count without waiting for a clock edge."""
    dut._log.info("asynchronous reset")
    await start(dut)

    dut.ui_in.value = EN
    await step(dut, 6)
    assert dut.uo_out.value != 0

    # drop reset between edges and check before the next one arrives
    await Timer(1, units="us")
    dut.rst_n.value = 0
    await Timer(1, units="us")
    assert dut.uo_out.value == 0, \
        "count did not clear before the next clock edge"

    dut.rst_n.value = 1


@cocotb.test()
async def test_output_enable(dut):
    """uio_oe follows OE: all eight pins drive together or go high-Z."""
    dut._log.info("tri-state control")
    await start(dut)

    dut.ui_in.value = 0
    await step(dut, 1)
    assert dut.uio_oe.value == 0x00, \
        f"pins should be inputs with OE low, got {int(dut.uio_oe.value):#04x}"

    dut.ui_in.value = OE
    await step(dut, 1)
    assert dut.uio_oe.value == 0xFF, \
        f"pins should drive with OE high, got {int(dut.uio_oe.value):#04x}"

    # while driving, uio_out carries the count
    dut.ui_in.value = OE | EN
    await step(dut, 3)
    assert dut.uio_out.value == dut.uo_out.value, \
        "uio_out and uo_out disagree while driving"
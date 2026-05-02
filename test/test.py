# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def pulse_sample(dut):
    dut.uio_in.value = int(dut.uio_in.value) | (1 << 2)   # set sample bit
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = int(dut.uio_in.value) & ~(1 << 2)  # clear sample bit


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start RNG test")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # ------------------------------------------------------------
    # CASE 1: Correct key, max = 7 (3-bit range)
    # ------------------------------------------------------------
    dut._log.info("CASE 1: correct key, max=7")
    dut.ui_in.value = 0b00000111   # max = 7
    dut.uio_in.value = 0b00000010  # key = 2'b10, sample = 0

    for i in range(6):
        await ClockCycles(dut.clk, 4 + i)
        await pulse_sample(dut)
        await ClockCycles(dut.clk, 1)

        out_val = int(dut.uo_out.value)
        dut._log.info(f"Correct key sample {i}: output = {out_val}")

        # output should be within 0..7
        assert 0 <= out_val <= 7, f"Output out of range with correct key: {out_val}"

    # ------------------------------------------------------------
    # CASE 2: Correct key, smaller max = 3
    # ------------------------------------------------------------
    dut._log.info("CASE 2: correct key, max=3")
    dut.ui_in.value = 0b00000011   # max = 3
    dut.uio_in.value = 0b00000010  # correct key

    for i in range(6):
        await ClockCycles(dut.clk, 3 + i)
        await pulse_sample(dut)
        await ClockCycles(dut.clk, 1)

        out_val = int(dut.uo_out.value)
        dut._log.info(f"Correct key max=3 sample {i}: output = {out_val}")

        # output should be within 0..3
        assert 0 <= out_val <= 3, f"Output out of range for max=3: {out_val}"

    # ------------------------------------------------------------
    # CASE 3: Wrong key, LFSR should drain toward zero
    # ------------------------------------------------------------
    dut._log.info("CASE 3: wrong key, poisoned behavior")
    dut.ui_in.value = 0b00000111   # max = 7
    dut.uio_in.value = 0b00000000  # wrong key, sample = 0

    observed = []

    for i in range(8):
        await ClockCycles(dut.clk, 2)
        await pulse_sample(dut)
        await ClockCycles(dut.clk, 1)

        out_val = int(dut.uo_out.value)
        observed.append(out_val)
        dut._log.info(f"Wrong key sample {i}: output = {out_val}")

    # Eventually the poisoned LFSR should collapse to zero
    assert observed[-1] == 0, f"Expected poisoned output to drain to 0, got {observed[-1]}"

    # ------------------------------------------------------------
    # CASE 4: Recover after reset with correct key
    # ------------------------------------------------------------
    dut._log.info("CASE 4: reset and recover")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    dut.ui_in.value = 0b00000101   # max = 5
    dut.uio_in.value = 0b00000010  # correct key

    await ClockCycles(dut.clk, 6)
    await pulse_sample(dut)
    await ClockCycles(dut.clk, 1)

    out_val = int(dut.uo_out.value)
    dut._log.info(f"Recovered output = {out_val}")

    assert 0 <= out_val <= 5, f"Recovered output out of range: {out_val}"

    dut._log.info("All tests passed")

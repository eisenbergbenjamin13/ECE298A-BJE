/*
 * Copyright (c) 2026 Benjamin J. Eisenberg
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_eisenbergbenjamin13_counter (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Name the control pins
  wire load = ui_in[0];
  wire en   = ui_in[1];
  wire oe   = ui_in[2];

  // The 8-bit register
  reg [7:0] count;

  // Clocked block: async reset, then sync load, then count, else hold
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      count <= 8'd0;          // asynchronous reset
    else if (load)
      count <= uio_in;        // synchronous load from the uio pins
    else if (en)
      count <= count + 8'd1;  // count up; wraps 255 -> 0
    // no final else: count keeps its value
  end

  // Outputs
  assign uo_out  = count;      // always visible
  assign uio_out = count;      // driven onto uio pins when oe = 1
  assign uio_oe  = {8{oe}};    // tri-state control: 1 = drive, 0 = high-Z (input)

  // Mark unused inputs so the linter doesn't warn
  wire _unused = &{ena, ui_in[7:3], 1'b0};

endmodule
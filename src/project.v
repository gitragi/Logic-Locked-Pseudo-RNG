/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_gitragi_rng (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // =========================
  // Internal signals
  // =========================

  reg  [7:0] lfsr;
  reg  [7:0] sampled;

  wire [7:0] max_val;
  wire [1:0] key;
  wire       sample;

  wire feedback;

  localparam [1:0] CORRECT_KEY = 2'b10;

  assign max_val = ui_in;
  assign key     = uio_in[1:0];
  assign sample  = uio_in[2];

  // =========================
  // LFSR with logic locking
  // =========================

  assign feedback = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      lfsr <= 8'b00000001;  // must not be zero
    else begin
      if (key == CORRECT_KEY)
        // Normal LFSR
        lfsr <= {lfsr[6:0], feedback};
      else
        // Poisoned: drain to zero
        lfsr <= {lfsr[6:0], 1'b0};
    end
  end

  // =========================
  // Sampling
  // =========================

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      sampled <= 8'b00000001;
    else if (sample)
      sampled <= lfsr;
  end

  // =========================
  // Range limiting (modulo)
  // =========================

  wire [7:0] correct_out;
  assign correct_out = (max_val == 0) ? 8'd0 : (sampled % (max_val + 1));

  // =========================
  // Output
  // =========================

  assign uo_out = correct_out;

  // =========================
  // Unused IOs
  // =========================

  assign uio_out = 8'b00000000;
  assign uio_oe  = 8'b00000000;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in[7:3], 1'b0};

endmodule

# Lock-in source audit: the implemented recurrence and its clock matter

6 November 2026. Addendum to [NARROW_STREAM_REVIEW.md](NARROW_STREAM_REVIEW.md). This audit found a material correction to the tempting RePLIA interpretation: **its published ADC rate is not its fractional-IIR update rate in the inspected repository.** Gregorat et al. provide substantially better evidence of a real feedback timing problem, together with an inexpensive implemented solution.

## RePLIA: pin, files and read depth

Repository: [WarwickEPR/RePLIA](https://github.com/WarwickEPR/RePLIA), inspected at commit **`7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561`**, dated 2023-12-28; the commit changes the README. Retrieved the complete recursive tree and source files through the GitHub connector. Read `averaging.v`, `IO_control.v` and `mode_control.v`; inspected the relevant generated-system wiring, block-design Tcl parameters and `settings.c` control sections cited below. The tree contains no `.rpt` timing reports. No synthesis, device measurement, bitstream disassembly or HDL simulation was performed. This is the repository version available now, not a proven reconstruction of the precise 2019 experimental bitstream.

The [Stimpson et al. author preprint, arXiv:1811.10494v2](https://arxiv.org/pdf/1811.10494), corresponding to [DOI 10.1063/1.5083797](https://doi.org/10.1063/1.5083797), describes Zynq-7010/Red-Pitaya hardware, two 125 MS/s 14-bit ADC inputs, mixing followed by a single-pole IIR, and 125 MS/s DAC output. Appendix A/Table II supplies tested time constants from 0.1 to 100 ms; its digital acquisition example requests 20 kSamples/s across eight reported quantities, so one quantity's cadence is one eighth of the setting. These are measurement settings and interfaces, not evidence of a 125-million-update/s rounded IIR. The paper discusses data-transfer/DAC-noise limitations, not a demonstrated fractional-recurrence service deficit.

The [pinned README](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/readme.txt) says the project is no longer maintained and points to [marceluda/rp_lock-in_pid](https://marceluda.github.io/rp_lock-in_pid). That alternative was not source-audited here; neither maintenance status nor the README's preference establishes comparative timing or arithmetic.

## The actual pipeline clocks the IIR after integrate-and-dump

The important source chain is:

| Pinned source | Concrete evidence |
|---|---|
| [Clock constraints](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/LockIn.srcs/constrs_1/imports/cfg/clocks.xdc#L1) | ADC and daisy input clocks have an 8 ns period constraint. This does not prove the filter uses those clocks directly or demonstrate achieved timing. |
| [Generated system, lines 125–144](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/LockIn.srcs/sources_1/bd/system/hdl/system.v#L125) | The ADC/reference multiplier feeds `simple_summation`; its 56-bit accumulated result passes through a normalizing multiplier to the IIR's 24-bit input. `moving_average.clk` connects to `simple_summation.cnt_timer`, **not** the ADC clock. The same structure occurs in four X/Y paths. |
| [Summation module, lines 28–63](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/custom/averaging.v#L28) | The accumulator captures/starts a new sum when the supplied 32-bit counter's MSB wraps high-to-low. `cnt_timer` is the inverse MSB. Thus the IIR receives one rising edge per counter wrap, after integration over many ADC samples. The high-rate addition has retention one. |
| [Block-design Tcl, lines 503–553](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/LockIn.srcs/sources_1/bd/system/hw_handoff/system_bd.tcl#L503) | Each IIR is configured `in_bits=24`, `out_bits=24`, `log2_samples=6`. The mixer selects product bits 28:5 and uses three pipeline stages. The normalizer multiplies signed 56-bit sum by unsigned 32-bit increment, selects bits 55:32, and uses eight pipeline stages. These narrowing operations belong to the original input preparation. |
| [Timing controls, lines 31–34, 71–85, 106–119](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/rp/settings.c#L31) | Software uses `SYS_CLOCK=125000000`, a 32-bit averaging counter and `MOV_AVG_LOG_SAMP=6`. For requested averaging period t, it writes the counter increment computed below. |
| [Averaging phase accumulator, lines 158–174](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/custom/averaging.v#L158) and [system wiring, lines 4460–4465](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/LockIn.srcs/sources_1/bd/system/hdl/system.v#L4460) | The counter adds that increment and exposes its high bits through output registers. Synchronization can restart the timer; timer phase and rounding of window lengths must be preserved. |

Derived from those controls, in normal internal-clock operation and away from initialization/synchronization:

`increment = floor(64 * 2^32 / (125000000 * t))`

`mean_IIR_update_rate = 125000000 * increment / 2^32 ≈ 64/t`.

| Requested t | Written increment | Derived mean IIR updates/s | Mean ADC samples per IIR update |
|---:|---:|---:|---:|
| 0.1 ms | 21,990,232 | 639,999.984 | 195.313 |
| 1 ms | 2,199,023 | 63,999.993 | 1,953.125 |
| 10 ms | 219,902 | 6,399.991 | 19,531.279 |
| 100 ms | 21,990 | 639.993 | 195,314.566 |

These are arithmetic consequences of the source, not scope measurements. Individual integrate-and-dump windows have integer lengths and can differ; the formula is their average. Multiplying 125 MS/s by a millisecond-scale time constant to infer this IIR's retention would miss the preceding rate reduction. Changing t predominantly changes its **update clock**, not its fixed pole.

## The true integer loop is a ceil-decay accumulator

The active [IIR implementation, lines 106–133](https://github.com/WarwickEPR/RePLIA/blob/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561/fpga/custom/averaging.v#L106) follows a commented-out finite moving average; inspect the active module, not its name or the old code.

The live state is a 30-bit register `s`, initialized to zero. A 24-bit two's-complement input is sign-extended into a second initialized register `v`. At each IIR edge the nonblocking assignments implement:

```
v_next = sign_extend_30(input24)
s_next = s + v - arithmetic_floor(s / 64)    # 30-bit assignment
output24 = s[29:6]
```

The concatenations explicitly implement sign extension and arithmetic-shift bit patterns despite unsigned Verilog declarations. The update uses **the previous edge's v**, and there is no explicit filter-reset input in this module. The 30-bit assignment has modular semantics; a replacement must preserve those semantics or establish an invariant excluding overflow.

Interpreted as mathematical signed integers while no overflow occurs:

`s_next = ceil(63*s/64) + v = floor((63*s + 64*v + 63)/64)`.

Consequently a fused floor with rho=0 is wrong. For `s=1,v=0`, this implementation keeps 1, whereas `floor(63/64)` gives zero. The ideal retained fraction is **63/64**, with a deterministic rounding offset corresponding to rho=63 and with high-precision accumulator state. Reading/truncating `output24` is separate from updating that state. `output24` by itself is not the full recurrence state.

A useful algebraic check is available without changing the original arithmetic: take `z=s+2^29` and `V=v+2^23`. Then the signed invariant `-2^29 <= s < 2^29`, with all legal signed 24-bit v, maps to

`z_next = floor((63*z + 64*V + 63)/64)`.

The signed interval is invariant: at the minimum state/minimum input the update stays at the minimum; at the maximum state/maximum input it stays at the maximum, and the map is nondecreasing. Thus this recentering can exclude wraparound for initialized, legal inputs. It is an exact coordinate change, not a new pole or a new quantizer. Any certificate would concern 30-bit z and scaled forcing `64*V`, not merely the 24-bit reported value.

At fixed 63/64 the ideal one-deletion width is 63 under the existing executor's conditions; actual finite-predictor capacities still need their own calculation. The source therefore offers a **well-specified short-certificate control**, but the recovered service rate makes a recurrence-throughput application claim weaker. At the fastest illustrated setting there are about 195 ADC clocks per IIR edge. A direct shift/add implementation, potentially shared among four states, deserves the first synthesis trial. Accelerating the upstream integrate-and-dump would target a different, A=1 problem.

## Gregorat 2024: stronger timing evidence and a stronger opponent

Audited primary article: [Gregorat et al., Sensors 24, 7276, §2.3.1, Figures 8–10 and Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11598244/) ([publisher](https://www.mdpi.com/1424-8220/24/22/7276)). Indexed full-text sections and PDF figure-label extraction were read; complete figure routing/RTL was not recovered.

The paper gives `y[n]=(1−α)y[n−1]+α(u[n]+u[n−1])/2`, 50 MS/s data and Q1.31 output. Its unoptimized feedback implementation struggled at 50 MHz. The implemented C=2 design alternates independent I/Q streams, uses DSP registers/accumulator, reports fmax above 250 MHz, and runs at 100 MHz. Table 1 assigns the 2-slow filter 27 ALMs and one DSP; the complete lock-in uses three DSPs. Outputs are sampled after settling, once per frequency step. The authors identify DSP availability as the remaining scaling bottleneck. Figure-label extraction also contains Q1.25, Q2.25, Q1.26 and Q3.51 formats; exact narrowing/rounding requires RTL or a visual wire audit.

This is a legitimate resource-limited FPGA seed with a real feedback timing obstacle and sparse observations. Its implemented solution is already a demanding baseline. It does not establish demand for a large speculative map engine, original-rounded-state equivalence, or a UP5K fit.

## Falsifiable compatibility questions

For RePLIA, a frozen-source exact replacement is testable now: preserve the prior-input register, ceil semantics, original input preparation, edge schedule, initialization and observed output slice. The first question is whether there is any unmet deadline or equal-throughput area/energy advantage after ordinary direct sharing. A long physical averaging period is not evidence of a long recurrence horizon after the native decimator.

For an accumulator with a narrowed feedback operand, do not infer a single fused-floor contraction from the real-valued pole. As a **conditional diagnostic**, suppose a fine-grid state is updated by

`T(s) = s + floor((B − 64*floor(s/64))/2)`.

With B=0, `T(63)=63` and `T(64)=32`: the map decreases at a quantizer boundary. This independently derived example is not a claim about the authors' RTL or chosen coefficient. It shows why feedback narrowing must be placed precisely before applying an ordered nondecreasing-map proof. Conversely, observing a narrow multiplier port alone does not establish that this hypothetical topology is the implementation. Recover the actual state/feedback wires, coefficient encoding, signed shifts, rounding mode and saturation before classifying it.

The useful experiment is therefore conditional and small: freeze one actual coefficient and output schedule; extract a cycle-accurate integer oracle; compare direct DSP-aware/interleaved execution and exact two/four-step execution with the complete certified engine at the same interface. A source showing a slow naïve loop is motivation to investigate. The decisive result is the comparison against the already implemented cheap fix.

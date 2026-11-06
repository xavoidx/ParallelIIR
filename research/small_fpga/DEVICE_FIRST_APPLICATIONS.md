# Device-first application search: small FPGA streams

6 November 2026. This search starts from actual small-FPGA systems, rather than assuming that a finance or video workload belongs on a small FPGA. It uses the three gates in [THIRD_PASS_VERDICT.md](../direction/THIRD_PASS_VERDICT.md): a real bottleneck in the matching recurrence; a reason to preserve integer results; and a complete advantage over the strongest exact implementation.

**Result: no new confirmed three-gate application.** The useful discovery is a much better collection of grounded controls. A shipping iCE40UP5K radio already performs its DC correction at its required input rate. Compact MAX10 radiation instruments have genuinely fast acquisition and sparse outputs, but their published baseline averaging is a finite-window algorithm. Motor/current sensing often has narrow inputs and decimated outputs, but the fast recurrence is an accumulator/CIC, outside `0<A<D`. These are significant eliminations, not evidence that a block-map engine wins.

Evidence labels below mean:

- **Confirmed:** stated in inspected primary documentation or executable source. A vendor's stated capability is not a new independent board measurement.
- **Derived fit:** arithmetic or scheduling inferred here from that source, with assumptions stated.
- **Open:** an application or implementation claim for which the needed contract, profile or measurement was not found.

## 1. Selection table

| Device/system seed | Confirmed useful work | Matching recurrence and effective rate | Exactness motivation | Decision |
|---|---|---|---|---|
| HackRF Pro, iCE40UP5K | Real RF acquisition, on-device DC removal, decimation; up to 40 Msps with 4-bit output | DC-block input is **8-bit I plus 8-bit Q**, not 4-bit; native implementation has delayed correction, dither and feedback saturation | Reproducing existing gateware is a valid compatibility experiment; no normative integer-output requirement found | Best concrete native negative control; not the current scalar executor's contract |
| ZipCPU gateware radio, iCEBreaker | Open gateware for SX1257 radio and audio | AM carrier average is enabled at the **48 kHz** baseband rate under defaults, despite a 36 MHz fabric clock | Existing integer source defines a reproducibility target | Cheap serial control; no rate bottleneck established |
| Lattice simple sigma-delta ADC, iCE40UP5K | Sensor/power-rail measurement from a 1-bit comparator stream | Accumulate/decimate plus finite box average; not a contracting rounded pole | Preserve ADC transfer function/decimation exactly | Relevant small device success, wrong algebra |
| Motor phase-current sensing | 1-bit sigma-delta streams and low-rate control/protection outputs | Common native filter is multiplier-free sinc³/CIC; control-loop rate differs from modulator clock | Existing filtering/timing contract can matter | Do not replace CIC with an EMA to manufacture a fit |
| I-Spector PSD, MAX10 10M16 | Two 12-bit 125 MS/s ADC channels; spectra, PSD and waveform capture | Published baseline is a finite moving average held during pulses; exact HDL/rounding not inspected | Reproducing pulse classification and spectrum bins is a credible compatibility goal | Strongest new **system/demand lead**, but no matching native pole shown |
| Fermilab PIP-II noise removal | 125 MS/s beam-loss processing | Fast filters change coefficients using tracking state; fixed exponential baseline is low-rate, RAM-interleaved | Reproducible protection thresholds would need a specified implementation contract | High aggregate rate does not establish a hot fixed-pole state |
| TinySDR, ECP5 | Battery-oriented standalone IoT radio, published evaluation | 0.4–4 MHz I/Q interface; no matching pole bottleneck found | No bit-exact filter consumer found | Useful power/device anchor; inadequate demand for block parallelism |

This is a targeted search, not an exhaustive survey or a proof that no suitable workload exists. No device price, whole-system power, achieved timing or method speedup is inferred from a family name.

## 2. HackRF Pro: inspect the registers, not just the “leaky integrator” comment

### Native system and source pin

**Confirmed.** HackRF's official gateware guide identifies the iCE40UP5K, 5,280 LUT4s and eight DSP blocks. It documents standard 8-bit I/Q, optional DC blocking and decimation, and half-precision 4-bit I/Q at up to 40 Msps. Extended precision requires at least 16× decimation and separate RX/TX gateware because of increased logic requirements. This is genuine small-device resource pressure, but it does not identify the DC blocker as the resource or timing limit. [Official gateware guide](https://hackrf.readthedocs.io/en/latest/gateware.html).

**Confirmed source snapshot:** repository `main` resolved through the connected GitHub API to `3a63b29953a3b763f428821e02110def9fb1cade` on this inspection date. The block's last modifying commit was [`fbd529896fd42c45442859fff0a953a5fffcca50`](https://github.com/greatscottgadgets/hackrf/commit/fbd529896fd42c45442859fff0a953a5fffcca50), simplifying its dither generator.

Pinned primary files:

- [DC blocker](https://github.com/greatscottgadgets/hackrf/blob/3a63b29953a3b763f428821e02110def9fb1cade/firmware/fpga/dsp/dc_block.py).
- [Standard receive/transmit integration](https://github.com/greatscottgadgets/hackrf/blob/3a63b29953a3b763f428821e02110def9fb1cade/firmware/fpga/top/standard.py).
- [Half-precision integration](https://github.com/greatscottgadgets/hackrf/blob/3a63b29953a3b763f428821e02110def9fb1cade/firmware/fpga/top/half_precision.py).
- [DDR ADC/DAC interface](https://github.com/greatscottgadgets/hackrf/blob/3a63b29953a3b763f428821e02110def9fb1cade/firmware/fpga/interface/max586x.py).
- [Board and clock constraints](https://github.com/greatscottgadgets/hackrf/blob/3a63b29953a3b763f428821e02110def9fb1cade/firmware/fpga/board.py).

The top levels instantiate `DCBlock(width=8, num_channels=2)` with default `ratio=12`. Half-precision conversion occurs **after** the blocker. The interface captures I and Q on opposite DDR edges of eight pins and supplies an always-valid/always-ready I/Q stream. The board constrains the ADC domain to 40 MHz. Thus the narrow-output mode is not a native four-bit-input filter. The documented sample modes and board constraints should not be conflated with a newly measured sustained service result.

### Exact transition derived from source

For one channel define the registers before an accepted edge as:

| Register | Native width | Role |
|---|---:|---|
| `avg_q` = `A_t` | signed 20 | Extended average accumulator |
| `y_q` = `Y_t` | signed 8 | Previous saturated residual |
| `qavg_q` = `Q_t` | signed 8 | Previous dithered/quantized average |
| `dither` = `d_t` | unsigned 12 | Registered slice of shared PRNG output |

Let `wrap_w` denote the native signed `w`-bit wrap and `sat8` signed eight-bit saturation. Reading the simultaneous assignments gives:

```
Y_(t+1) = sat8(x_t - Q_t)
A_(t+1) = wrap20(A_t + Y_t)
Q_(t+1) = wrap8(floor((A_(t+1) + d_t) / 4096))
output_(t+1) = Y_(t+1) when the synchronized enable is set,
               x_t otherwise.
```

This is an inspection-derived transition description, not an independent RTL equivalence proof. The quantizer equation expresses the signed high-bit extraction with the native finite-width wrap. Initialization, valid cycles and enable synchronization remain part of the contract.

The extra residual register is consequential. Starting with zero filter registers and the same dither history, accepting `x_0=0` versus `x_0=1` leaves the same `A_1=0` and `Q_1`, but different `Y_1`. At the next accepted edge the average changes differently even if the new input is identical. **The average alone is not a sufficient scalar state.** Treating the prior-output delay as an output-only pipeline delay changes the feedback computation.

The source generates dither with a shared 32-bit Galois LFSR, polynomial `0x80200003`, seed 1. It advances on accepted input; each channel's 12-bit dither register is clocked independently of the accepted-input condition. For this top-level always-valid stream, the schedule is straightforward. A generalized stalled stream needs clock/accept history as well as sample data to reproduce dither exactly.

**Derived fit.** Independently generated dither can be known ahead, so random-looking input does not itself defeat a known-`C_t` method. It does not remove the delayed residual state or the saturation **inside** feedback. An otherwise ideal scalar EMA can sometimes be translated from signed to nonnegative coordinates, but translation cannot turn this vector transition into the current scalar floor map. Replacing it with a textbook EMA or moving clipping to output would be a new filter.

For an ideal scalar pole with retention `4095/4096`, the time constant is approximately 4,095.5 accepted samples: about 102.4 µs at 40 Msps, with half-life about 71.0 µs. The usual rounding enclosure scale is approximately 4,096 integer state units, not a 63-boundary mask. These numbers describe the **hypothetical scalar pole**, not an exact reduction or measured settling time of the native delayed/dithered block. The raw eight-bit ADC width does not make its internal 20-bit accumulator an eight-bit state.

**Open.** No inspected source isolates a missed required rate, DC-block LUT count, post-route critical path, or a requirement to preserve particular dithered output words. The existing implementation already has a short saturation/subtraction path and a separate accumulator addition path. It is the exact baseline to beat. A future method must preserve the native transitions or explicitly establish why an alternate filter is acceptable; the latter would weaken the bit-exact application argument.

## 3. Two small-radio controls prevent rate mistakes

**Confirmed.** ZipCPU's SDR targets iCEBreaker, SX1257 and audio peripherals. Its own README distinguishes demonstrated transmitter hardware from receiver simulation limitations; it is not evidence of a production receiver deadline. [Primary project](https://github.com/ZipCPU/sdr).

At pin `f143194d096579168e1c33c02713b0c44260c234`, [AM demodulation](https://github.com/ZipCPU/sdr/blob/f143194d096579168e1c33c02713b0c44260c234/rtl/amdemod.v) defaults to 36 MHz fabric and 48 kHz audio, decimating first by 50 and then by 15. Its carrier average is enabled by the resulting `baseband_ce`, uses eight-bit input/output and `LGALPHA=10`, and consequently has an 18-bit accumulator. [Native average](https://github.com/ZipCPU/sdr/blob/f143194d096579168e1c33c02713b0c44260c234/rtl/iiravg.v) registers the adjustment separately. Reproducing it requires honoring enable and pipeline timing, not just transcribing a transfer function.

**Derived fit.** The fabric clock is not this state's update rate: nominally there are 750 fabric cycles per average update. This is an inexpensive scalar correctness/control workload, not a credible throughput target. The long retention would also make “small input means small certificate” a poor assumption.

**Confirmed.** TinySDR's authors report a battery-oriented standalone IoT platform, an ECP5-class 24K-LUT FPGA with 28 multipliers, and a 13-bit I/Q interface at 0.4–4 MHz. Their 30 µW result is **sleep-mode** power, not active filtering power. [Authors' platform page](https://tinysdr.org/), [primary paper](https://arxiv.org/abs/1907.02063).

**Open.** No inspected native filter/update specification on TinySDR establishes our scalar floor map, an exactness consumer or a hot recurrence rate problem. The system is a useful low-power architecture seed, but an aggregate “radio” label supplies none of those missing requirements.

## 4. One-bit sensing and motor/power control: excellent interfaces, usually the wrong algebra

**Confirmed.** Lattice's small sigma-delta ADC reference design specifically targets sensor and power-rail monitoring. Its performance table lists an iCE40UP5K configuration at 99 LUTs and `>75 MHz`; the page explicitly calls performance and size **estimates** varying with implementation. [Primary reference-design page](https://www.latticesemi.com/Products/DesignSoftwareAndIP/IntellectualProperty/ReferenceDesigns/ReferenceDesign03/SimpleSigmaDeltaADC?ActiveTab=Reference+Design).

The detailed design integrates a one-bit comparator stream, decimates, then takes a finite box average. The documented example uses 62.5 MHz, a 1,024-sample accumulation and an eight-value average, producing about 7.629 kHz. It warns that its simple anti-aliasing response is unsuitable as-is for faithful waveform/audio reconstruction. [Lattice design documentation](https://www.latticesemi.com/view_document?document_id=35762).

**Derived fit.** This is exactly the kind of pin/RAM-friendly physical workload worth checking first. However, the integrator has `A=D`, not `0<A<D`; its comb/finite-window mathematics already supports cheap exact block sums and prefix structures. A contracting EMA is a different transfer function. Block-map overhead must not be credited with replacing an accumulator that needs no such machinery.

**Confirmed.** Gowin's FOC example uses a GW2A-18, a 100 MHz FPGA clock and a 16 kHz current/PWM update rate; the position/speed update is 2 kHz. It says a sigma-delta alternative requires sinc³ filtering, while the supplied demo uses SAR acquisition. [Gowin TN663](https://www.gowinsemi.com/upload/database_doc/1307/document/5ff52100af1d0.pdf). Microchip's LX7720 likewise exposes multiple simultaneous one-bit modulator streams for host-side sinc³ filtering and decimation. [Manufacturer datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/LX7720-Data-Sheet.pdf). Altera's drive example explicitly describes 20 MHz one-bit input and multiplier-free sinc³, with separate control and overcurrent paths. [Primary interface documentation](https://docs.altera.com/r/docs/780361/current/an-994-drive-on-chip-design-example-for-agilextm-7-devices/sigma-delta-adc-interface-for-drive-axes?contentId=fOU9ywoj6b6Ew32filbq_Q).

**Derived fit.** Sparse control outputs can eliminate every-sample replay, but do not make the fast native CIC a contracting pole. In a feedback/protection path, waiting for a future input block also consumes the very latency being optimized; future measurements can depend on earlier actuation. Recorded/offline inputs and independent monitor paths do not have that causal restriction. This must be established for the particular path, not assumed from the modulator bit rate.

**Open.** No inspected primary small-device motor/power source establishes a fixed rounded one-pole stage that misses its required service rate. These examples strongly favor a direct shift/add baseline before any certificate engine.

## 5. Compact pulse instrumentation: the best new system lead, still not a native pole match

**Confirmed.** Nuclear Instruments identifies the I-Spector PSD FPGA as MAX10 `10M16SAU169C8G`. [Manufacturer product/download page](https://downloads.nuclearinstruments.eu/products/i-spector). Its current FPGA documentation describes two 12-bit 125 MS/s ADC channels, summed after inversion, a derivative trigger, delayed integration, baseline correction, energy/PSD accumulation and compact histogram outputs. The baseline is a **moving average between pulses**, frozen during a configured inhibit period. [Manufacturer firmware description](https://downloads.nuclearinstruments.eu/packages/ispector-fpga-psd).

This combination is materially better aligned with small FPGA interfaces than raw video: few ADC channels, local reduction, sparse results. It demonstrates real high-rate processing in a compact instrument. It does **not** show that the averaging stage is an EMA, that it is the timing bottleneck, or that this method beats the already functioning design. No source HDL, exact rounding/state widths or utilization breakdown for this stage was inspected.

The distinction is not semantic pedantry. The same vendor's Sci-Compiler MCA documentation identifies an actual baseline buffer and a finite `2^BL_LEN` averaging window. Its time-multiplexed baseline block supports several samples per cycle, but again describes a finite integration window, shared trigger inhibit and reset. [MCA algorithm documentation](https://docs.sci-compiler.com/docs/blocks/pa/mca/), [parallel baseline block](https://docs.sci-compiler.com/docs/blocks/pa/baseline-restorer-tm/).

**Derived fit.** A native exponential baseline estimator, tail predictor or unipolar RC shaping stage in this device class would be worth investigating if it already exists and has a compatibility consumer. Short physical shaping times at 125 MS/s could have materially shorter sample horizons than radio DC removal. Sparse energy/PSD outputs can reduce drain traffic, but the observable may depend on the entire pulse window, not just the filter endpoint; exact endpoint computation alone need not reproduce exact charge, peak or threshold crossing.

**Open claim / next evidence request:** obtain a native fixed-pole specification and board timing/utilization for an actual compact pulse instrument, along with the decision outputs and allowed extra delay. Do not call a proposed replacement EMA a demonstrated native workload. Do not equate ADC sampling rate with photon event rate, output count rate, or a missed filter deadline.

## 6. High-rate instrumentation counterexamples constrain the search

**Confirmed.** Fermilab's PIP-II noise-processing paper describes 125 MS/s acquisition and one-sample-per-clock pipelined processing. The two fast discharging integrators change their time constants using tracked/untracked state. Its fixed exponential baseline updates distinct phase-indexed RAM words across 60 Hz periods; the paper explicitly permits multicycle RAM updates because their rate is far below the system clock. Integer widths and floor semantics are not specified. [Primary three-page paper](https://arxiv.org/pdf/2602.11415).

**Derived fit.** The attractive ingredients occur in different stages: the high-rate stages have state-dependent coefficients, while the fixed exponential stage has many independent low-rate histories. Neither inherits the current fixed-coefficient executor's demand or proof. An explicitly recorded coefficient schedule could define a different offline problem, but cannot be assumed available ahead in the live adaptive filter.

**Confirmed baseline warning.** A separate many-channel experimental control system reports ten 100 MS/s loops, 155 ns full-loop latency and shift/add IIR PID filters with 30 ns latency. This is not a tiny-device implementation or a scalar-floor equivalence result; it shows that a competent exact/native baseline can be far cheaper than generic multiplication suggests. [Schussheim and Gibble, primary paper](https://arxiv.org/abs/2307.16008).

**Open.** Neither source demonstrates a rate failure that our method repairs, a small-device fitting result, or bit-exact equivalence of a parallel transformed filter.

## 7. What remains plausible after device-first elimination

The unfilled region is fairly specific:

1. A few **hot, narrow or packed streams** arrive faster than a small exact feedback path can serve at its achieved clock. An input fabric/deserializer already exposes several chronological samples together, avoiding a new expensive interface solely for this arithmetic.
2. The native state is a fixed integer contraction with a sufficiently short **sample** horizon, not merely low ADC resolution. Signed translation, state rails, clipping and reset behavior are proved compatible rather than ignored.
3. Inputs can be buffered ahead without changing a live control loop, and extra block latency is acceptable.
4. Required outputs are sparse or block-reducible under an exact observable contract, so every-sample replay and wide output traffic do not consume the benefit.
5. The incumbent has a reproducibility/compatibility reason to retain exact words, or exact final decisions. A permitted approximate filter is also measured as a practical alternative.
6. Serial shift/add, small exact unrolling, independent-channel interleaving, endpoint propagation and shared-base relative-rank construction have all received fair hardware implementations.

For intuition only, at 125 MS/s a 100 ns scalar time constant is about 12.5 samples, while 1 µs is 125 samples and 100 µs is 12,500 samples. The rough accumulated rounding scale `1/(1-a)` changes accordingly. Thus **short pulse shaping/envelope work is a better mathematical search region than slow DC tracking**, conditional on finding a real native integer contract. These are derived illustrations, not measured application settings or claims that an EMA is the appropriate anti-alias filter.

A 32-sample input block alone adds at least 256 ns of acquisition wait at 125 MS/s, before any processing or queueing. That is already longer than the entire 155 ns loop in the cited control system. Buffer latency can be harmless in a monitoring histogram and unacceptable in a servo. The application must choose the latency budget before an accelerator schedule is declared useful.

## 8. Concrete next comparison and stopping rules

The strongest useful next action from this search is a **small, native-contract baseline experiment**, not a claimed new deployment:

- Retain HackRF DC blocking as a register/causality audit and native resource baseline. Its current contract requires a vector/nonlinear extension; do not present a simplified scalar replacement as bit-exact acceleration.
- Seek source or a pinned specification for an actual compact instrument's exponential pulse/baseline stage. I-Spector grounds the device/interface/output class; its current finite moving average is an exclusion/control.
- Reject any target whose matching state advances well below the demonstrated direct baseline's capacity unless an actual area/power bottleneck is measured. A 100 MHz system clock with a 16 kHz state update is not a 100-million-update/s problem.
- For a matching target, freeze coefficient, state width, physical horizon, input grouping, output observable, reset/inhibit schedule and allowed delay. Measure the full direct and 2/4-way exact baselines first. Charge predictor, all ports/RAM, resolution and output work to the proposed engine.

Stop an application speedup claim if the native stage fits and serves the target more cheaply, if bit identity has no consumer and approximation wins, if state-dependent feedback prevents known future inputs, or if the complete design loses to the same-certificate alternatives. The application search has advanced by finding real systems and exposing these boundaries; the third gate remains unmeasured.

## Inspection limits

Sources were inspected on 2026-11-06. GitHub source pins are supplied where code was read; unpinned manufacturer pages are mutable. The HackRF transition and horizon calculations are derived here. No Amaranth simulation, native-board acquisition, synthesis, route, power measurement or comparison RTL was performed for this document. The author's claims and vendor estimates above retain their original scope. Broader ALICE-scale readout and generic vendor IIR IP were screened as demand/background leads but are not evidence for small-FPGA suitability or a matching hot scalar recurrence.

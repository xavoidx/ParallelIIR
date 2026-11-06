# Start with the small FPGA: a wider application and research direction

6 November 2026. This pass starts from deployed resource-constrained hardware, its interfaces and its consumers. It covers compact instrumentation, radios, lock-in amplifiers, one-bit sensing, pulse synthesis, binary monitors, queue management and adaptive compression. It incorporates three parallel reviews, follow-up source audits and an independently checked arithmetic prototype. It contains no synthesis, board timing, power or application-speedup result.

## Recommendation

**Prioritize compact instrumentation with a few fast inputs and sparse measurements. Investigate exact block observations before another full-waveform accelerator.** This is the best new *search direction*, not an application that has passed the complete test. The relevant consumer might need an exact peak, a block-end measurement or a report that at least one filtered sample exceeded a threshold; it need not consume every intermediate filtered word.

Separately, investigate **one shared wide state with narrow residual states across related channels** if a real source supplies a deterministic difference bound. This has a clearer arithmetic-width saving, but changes the workload from one hot recurrence to a bank of related recurrences. It has not identified a production workload or established a service-rate advantage.

The user's three criteria remain the acceptance gate:

1. **Rate bottleneck:** the required update rate for the relevant state or bank exceeds the best affordable exact implementation's delivered service, at a justified latency.
2. **Useful exactness:** a compatibility, reproducibility or decision-stability requirement makes preserving the chosen integer behavior useful. A new application can qualify; a pre-existing standard is not mandatory.
3. **Beats the exact alternative:** the complete proposed design improves the hardware needed to meet that service and latency, against the strongest applicable exact designs.

**No reviewed deployment currently meets all three with evidence.** This pass narrows the missing evidence and adds a testable variant; it does not establish publishability. The broader goal should be *minimum complete hardware at required service*, with throughput, latency, LUTs/registers, DSPs, RAM blocks and energy reported separately. A lower fabric clock alone is not a result: replication can consume more hardware and energy, and the direct baseline must be allowed its own achieved clock.

## What the device-first search found

| System or application | Why it was worth inspecting | Decisive finding | Research role |
|---|---|---|---|
| Compact detector/pulse instrumentation | Few ADC channels, high sample rate, local energy/peak/classification outputs | I-Spector uses a MAX10 and two 12-bit 125 MS/s channels, but its published baseline is a held moving average, not our fixed pole | **First system lead**; acquire a genuine exponential stage and its timing contract |
| Configurable instrumentation IIR IP | A vendor exposes actual EWMA widths and a separate look-ahead implementation | Sci-Compiler IIR Average documents finite formats; original rounding and initiation interval remain unresolved | **First arithmetic/source lead**, not proven demand |
| Lock-in measurement | Real feedback timing and DSP pressure; outputs can be infrequent | Gregorat's implementation already uses I/Q interleaving and DSP-aware retiming; RePLIA decimates before its one-pole stage | Strong exact-baseline and scheduling controls |
| HackRF Pro on iCE40UP5K | A real inexpensive-FPGA radio with high-rate DC removal | Native DC block contains delayed correction, quantized feedback, dither and saturation; not the present scalar machine | Valuable source-level exclusion; do not silently simplify it |
| Wearable lock-in, PDM microphones, isolated current sensing | Narrow inputs and small-device deployment look attractive | Native fast stages commonly use CIC/sinc or accumulation; fractional IIR is often downstream | Controls showing what already works cheaply |
| Nuclear pulse synthesis | Actual exponential waveforms on a small FPGA | The consumer needs every DAC sample; published small-device designs already meet their stated rate | Full-output comparator; sparse observations cannot replace its interface |
| Binary error/duty/PWM monitoring | Narrow fast input, potentially sparse reports | A per-bit EWMA is a proposed statistic; counters, run processing and windows are strong alternatives | Conditional new-design hypothesis |
| Packet-queue RED and lossless probability models | Concrete integer updates and meaningful exact decisions | Updates are cheap; queues/contexts can interleave; live decision and decoder dependencies constrain batching | Native arithmetic controls, weak flagship candidates |

Primary anchors: [I-Spector firmware](https://downloads.nuclearinstruments.eu/packages/ispector-fpga-psd), [IIR Average](https://docs.sci-compiler.com/docs/blocks/dsp/iiraverage/), [tunable IIR/look-ahead](https://docs.sci-compiler.com/docs/blocks/dsp/tunable-i/), [Gregorat et al.](https://www.mdpi.com/1424-8220/24/22/7276), [HackRF source audit](DEVICE_FIRST_APPLICATIONS.md#2-hackrf-pro-inspect-the-registers-not-just-the-leaky-integrator-comment), [Hannigan et al. supplement](https://bretthannigan.ch/assets/pdf/Hannigan2024a-supp.pdf). The detailed reports link each remaining source and identify reading limits. These device classes are not interchangeable resource budgets; a MAX10 or Spartan-6 example does not prove an UP5K fit.

Two source corrections materially change the opportunity:

- **Fast acquisition does not imply a fast exponential recurrence.** In pinned RePLIA source, integrate-and-dump precedes a fixed 63/64-retention integer loop. A requested 1 ms averaging setting gives about 64,000 IIR updates/s despite 125 MS/s acquisition. Its native input register, signed state and output slicing must also be preserved. [Audited clock path and arithmetic](LOCKIN_SOURCE_AUDIT.md).
- **A naïve feedback timing failure does not establish an unsolved bottleneck.** Gregorat et al. report a 50 MHz difficulty that their C=2 I/Q implementation resolves, with one DSP and 27 ALMs for the filter. That implemented remedy belongs in the baseline, not just the slow initial circuit. Exact quantization placement still needs source/figure recovery before applying our scalar-map proof. [Primary article](https://www.mdpi.com/1424-8220/24/22/7276).

## Direction 1: exact observations of a fast stream

The proposed consumer receives an exact block exit plus either the maximum of post-update states or a fixed-threshold any-exceedance flag. Known input blocks allow independent summary construction; the true carry is resolved in order. The consumer accepts the resulting block delay. This excludes immediate protection actions, feedback-triggered reset and unknown future control inputs unless the entire resulting machine is separately modeled.

For a block, write `F_t(s)` for the original integer state after t updates. Then

```
E(s) = F_L(s)
M(s) = max(F_1(s), ..., F_L(s))
Q_T(s) = [M(s) >= T].
```

Both E and M retain the monotone adjacent-increment structure used by the current executor. A fixed-threshold Q needs only one entry cutoff, which is a stronger alternative than storing the whole numeric peak map. A backward inverse pass can also construct that cutoff; its reverse reads and division cost must be compared. “Any sample at or above T” is not an upcrossing count, first-hit time, dwell duration or immediate trigger.

This is more useful than merely retaining the last sample. In the constructed byte rule `s'=floor((3*s+x)/4)`, eight inputs of 255 followed by 56 zeros produce a final state of 0 but an internal peak of 228. A threshold report for 200 must retain that distinction. This is a synthetic illustration of the observation contract, not detector validation.

The second change is a **finite-history certificate**. Before constructing a block map, propagate legal lower/upper state rails through H preceding known inputs. Their endpoints enclose the actual entry without consulting the serial oracle or computing the present wide affine predictor. If the history reaches initialization, use that known initial state. The exact exit summaries still carry the true state forward; no unbounded “repair later” history is hidden.

The cost is substantial. For normalized retention `A/D`, the conservative width recurrence is `w'=ceil(A*w/D)` and its largest positive fixed width is `R=floor((D-1)/(D-A))`. Starting with 32-bit rails takes H=75 steps to reach R=3 for retention 3/4, but H=1,182 to reach R=63 for 63/64. Two endpoint transitions per history sample plus one base transition per new input give counts of about 1.59 and 10.23 transitions/input respectively at L=256, before ranks, observations, memory or interfaces. These are **arithmetic counts, not cycles or throughput**. Endpoint arithmetic can share a base/remainder; give competing implementations that saving too.

This favors short sample horizons and sufficient block length. The horizon must come from the physical measurement: at high sample rates, a short sample horizon can mean a very short physical response. Do not shorten an application's desired smoother just to make the maps small. Longer blocks also increase observation latency.

The complete derivation, finite-history table, forward/backward threshold alternatives and comparison limits are in [OBSERVATION_FIRST_PROTOTYPE.md](OBSERVATION_FIRST_PROTOTYPE.md). Generic state-plus-output composition and restricted-entry lookback are established ideas; the proposed contribution would have to be a measured specialization that enables useful exact observation on smaller hardware. [Cost-register automata](https://www.cis.upenn.edu/~alur/Lics13reg.pdf), [restricted-entry execution](https://arxiv.org/html/1210.5093).

## Direction 2: share precision across related channels

For synchronized channels with identical coefficients and rounding, write `s_c=b+v_c` and `x_c=x_0+delta_c`. One wide reference update supplies remainder r. Each residual then updates exactly as

`v_c' = floor((A*v_c + (D-A)*delta_c + r)/D)`.

If both initial residuals and every input difference lie in `[-K,K]`, the same bound holds forever. The shared remainder preserves the original per-channel rounding. This can replace many wide state updates with one wide update and narrow residual arithmetic, without certificates or replay.

The opportunity is conditional on a **real bound in native integer units**, not statistical correlation. Fractional scaling can make apparently close physical measurements far apart in integer units. Full-width input subtraction, output reconstruction, broadcast routing, RAM allocation and exceptional conditions can erase the saving. Give the direct bank ordinary time sharing, interleaving and range-based width reduction. Identical channels collapse to one state; fixed translated copies may need no evolving residual at all. Do not count redundant high bits as a resource advantage.

This is an elementary arithmetic identity, not a standalone novelty claim. It is a secondary resource investigation until a genuine channel bank and rate deficit are found. See [RESOURCE_EFFICIENT_DIRECTION.md](RESOURCE_EFFICIENT_DIRECTION.md) for the proof, constant-input run alternative, prior art and stop conditions.

## High-level RTL roadmap

1. **Freeze one useful contract.** Obtain the actual integer update, widths/scales, rounding locations, overflow behavior, reset/inhibit rules, coefficient schedule, input packing and requested outputs. Record per-state update rate, physical horizon, acceptable delay and the reason for exactness. Sci-Compiler's generated stage is the most concrete unresolved source lead; compact detector systems anchor the demand search. Four-cycle latency is not evidence of initiation interval four.
2. **Implement and measure the smallest exact reference.** Begin with one direct state and only its required peak register or alarm bit. Use shift/add and constant coefficients where applicable. Measure routed service and resource use on the intended part. Then admit two/four-update exact unrolling, DSP retiming, independent-state interleaving and state-RAM time sharing where the workload permits them. If this meets the target most cheaply, keep it.
3. **Build one bounded comparison.** For a truly hot state, compare two/four-worker exact exit-plus-observation summaries against those baselines. Compare shared-base ranks with bitmaps; compare finite-history and affine certificates where applicable. Test shared endpoint arithmetic. Use the same inputs, coefficients, observable, latency and certificates for competing summary representations. Do not begin with a large replicated design.
4. **Account for the whole device.** Include input capture/deserialization, FIFOs, history storage and ports, constructors, carry resolution, queries, clock crossing and output drain. A fast external interface or bridge is not free. Report actual FPGA resources separately; do not convert payload bits into LUT savings or ALMs into an assumed UP5K fit. Prove worst-case service, startup, partial-block and reset behavior rather than relying on average convergence.
5. **Validate and decide.** Check bit equivalence against a frozen integer oracle, then measure a native workload's rate, latency and system result. For resource sharing, require the channel-bound evidence before implementation. Continue toward a paper only if the complete design wins an agreed service/resource tradeoff and preserves a useful consumer behavior. Otherwise retain the negative result and redirect the application search.

No RTL implementation was added in this pass. The mathematical prototype is deliberately separated from a device claim.

## Evidence produced and reading order

The primary suite checks 4,080 small binary-input blocks, 30,600 exit/peak/alarm entry comparisons, inverse-cutoff sentinels and streamed finite-history certificates. An independent script reproduces its persisted results and adds **499,810 arbitrary-input/domain entry comparisons**, **25,243 inverse-cutoff boundary comparisons**, **32,145 composition comparisons**, and **12,000 history certificates**. No arithmetic mismatch was found. Composition tests evaluate serial query/observable composition; they do not implement a parallel scan or merged-summary circuit. These tests do not establish a hardware or application advantage.

Run from the repository root:

```sh
python3 research/small_fpga/observation_checks.py
python3 research/small_fpga/observation_independent_checks.py
```

Each script refreshes its corresponding JSON result, including source hashes. The model assumes fixed normalized scalar coefficients, sufficient intermediate precision and bounded inputs; native signed/quantized feedback is not automatically equivalent.

For the collaborator, read this report, then the [observation prototype](OBSERVATION_FIRST_PROTOTYPE.md), [source audit of lock-ins](LOCKIN_SOURCE_AUDIT.md), and [resource alternatives](RESOURCE_EFFICIENT_DIRECTION.md). For the surrounding literature, prioritize:

- [Papadantonakis et al., *Pipelining Saturated Accumulation*](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf): prior exact nonlinear transition summaries and FPGA evaluation.
- [Mytkowicz et al., data-parallel FSMs](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf), and [Ko et al., restricted-entry execution](https://arxiv.org/html/1210.5093): state merging, speculation and lookback precedents.
- [Fernandes, order-preserving transformations](https://arxiv.org/pdf/2407.05084): close mathematical structure; read with the existing [third-pass assessment](../direction/THIRD_PASS_VERDICT.md).
- [Alur et al., cost-register automata](https://www.cis.upenn.edu/~alur/Lics13reg.pdf): accumulated observables are broader established machinery.
- [Gregorat et al., FPGA lock-in implementation](https://www.mdpi.com/1424-8220/24/22/7276), [RePLIA source](https://github.com/WarwickEPR/RePLIA/tree/7ca1a65f33a9f9e01a6da9c7c2d8730e3417e561) and [Hannigan et al. supplement](https://bretthannigan.ch/assets/pdf/Hannigan2024a-supp.pdf): strong practical alternatives, actual clock domains and the value of early rate reduction.

Source reading depth and unresolved implementation details are recorded in the supporting reports. Manufacturer documentation is mutable; code audits use commit pins where available. The primary research result of this pass is a better constrained experiment and stronger exact competitors, not a claim that one-pole filtering on small FPGAs is generally unsolved.

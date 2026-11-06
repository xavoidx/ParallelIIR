# ParallelIIR research review and RTL roadmap

Prepared 6 November 2026 from the literature review and software checks completed on 4 November 2026. This document is self-contained so it can be shared as an email attachment. Literature findings retain the reading limits of that review; this is a consolidation, not a new literature search or hardware evaluation.

## Where the project stands

The project asks whether we can process one buffered recursive signal faster while producing exactly the same integer outputs as the original serial filter. The proposed approach summarizes each input block as a compact function of its starting state, uses those summaries to determine the correct block boundaries, and then replays the blocks in parallel.

The mathematical mechanism is sound within its stated arithmetic restrictions, and the independent software checks support it on the tested cases. The open questions are whether the construction is sufficiently distinct from prior work and whether the complete implementation provides a useful advantage after accounting for preparation, memory, boundary resolution and replay.

There are two worthwhile outcomes to pursue:

- **RTL learning:** build and verify an exact arithmetic system, understand its critical paths and memory behavior, and use measurements to choose between architectures. This remains a useful project even if the proposed accelerator loses to a simpler implementation.
- **Research:** establish a specific contribution beyond known exact-map and recursive-filter methods, then demonstrate a meaningful improvement on a native workload at an acceptable resource cost and latency.

The recommendation is to proceed through small, measurable milestones. A strong implementation study could become publishable, but the current evidence does not justify promising that outcome. No FPGA synthesis, placement and routing, board measurements or native application speedups have been established in this review.

## 1. The idea and its exact scope

The supported state update is:

**s_next = clip(floor((A × s + C) / D)), with 0 ≤ A < D and D > 0.**

The state is one integer in a fixed legal interval. The input contribution C and coefficients must be known before the block's entry state is resolved. Intermediate arithmetic must be wide enough to avoid unintended overflow. Floor means rounding toward negative infinity, including for negative values; clipping happens at the specified point in the original machine.

The coefficient may be constant or follow a known schedule. State-dependent adaptation, modular wraparound, general biquads and arbitrary multistate filters are outside the current result. A real-valued filter with the same transfer function is not necessarily the same integer machine.

The execution has three stages:

1. **Construct a block map.** Run the lowest and highest legal entry states through the block. Their final states give its output range. Recover the entry-state thresholds separating those outputs by walking backward through the arithmetic.
2. **Resolve the boundaries.** Apply or compose the maps in time order, starting from the actual initial state. This identifies the correct entry state for each block.
3. **Replay the blocks.** Run each block from its resolved entry state, allowing different blocks to produce their complete output traces in parallel. Deliver those samples in their original order.

Let F be a block map, v its lowest output, and K the difference between its highest and lowest outputs. Increasing an entry state by one can increase the exit state by only zero or one, so the possible outputs are consecutive integers. F can therefore be represented by v and K sorted thresholds. Evaluating it means counting the thresholds at or below the entry state.

For example, if a block has four possible exit values, the map needs a base and three thresholds. It still needs construction, storage and evaluation machinery, and replay is still needed to recover all intermediate outputs. K counts thresholds; the number of possible exit states is K + 1.

For an interior target and A > 0, the backward threshold comes from **ceil((D × target − C) / A)**. Constants, saturation boundaries and unreachable targets need explicit handling. The mathematical inverse is simple; its exact hardware cost remains an implementation question.

## 2. What the literature says about novelty

The strongest finding is that several broad versions of the claim already have close predecessors. This changes how we should describe the project and what we should compare against.

| Ingredient | Prior-work position | What could still matter here |
|---|---|---|
| Turn a sequential recurrence into composed state-transition functions | Established in parallel scans and finite-state execution | A representation and constructor cheap enough for this arithmetic |
| Preserve nonlinear saturation while parallelizing a DSP recurrence | Demonstrated in FPGA work in 2005 | Handling fractional per-step rounding, which produces a more complicated staircase map |
| Reduce work as possible states converge | Established in data-parallel FSMs | Avoiding initial-state enumeration through ordered arithmetic structure |
| Restrict a chunk's possible entry states using earlier inputs | Established in speculative DFA execution | A useful numerical specialization with lower complete-system cost |
| Represent these monotone maps using increment locations | Closely connected to an already studied finite-chain map class | Implementation and compression choices, rather than a new representation principle |
| Compose inverse thresholds backward | Standard generalized-inverse/adjoint reasoning | A useful output-sensitive constructor and efficient physical realization |

The closest hardware paper is **Papadantonakis, Kapre, Chan and DeHon, “Pipelining Saturated Accumulation” (FPT 2005)**. It represents saturating additions by compact functions, composes them associatively and uses a prefix architecture on an FPGA. Its unity-slope updates have a constant-size representation; the proposed fractional floor-rounded updates generally do not retain that representation. We should explain this difference explicitly rather than claim the first exact nonlinear recursive accelerator. [Read the paper][R1].

**Mytkowicz, Musuvathi and Schulte (2014)** already exploit partial convergence of finite-state trajectories. **Ko and coauthors** restrict candidate starting states using preceding symbols. These are important comparators for full tables and restricted forward tables. [Data-parallel FSMs][R2]; [speculative DFA execution][R3].

The mathematical search also found the abstract map class studied as order-preserving contractions of a finite chain, often written OCT_n, and order-preserving maps whose images are intervals, IO_n. “Contraction” in that literature can mean nonexpansive, not strictly contractive. The basic closure, contiguous-image and inverse-composition arguments are unlikely to support a substantial theorem-led contribution by themselves. [Adeshola and Umar][R4]; [Fernandes][R5]; [adjoint composition background][R6].

**What remains open:** the reviewed sources did not reveal the complete proposed backward-ceiling DSP constructor. That is a limited search finding, not proof of novelty. The literal constructor is an elementary specialization of established ideas, so significance would need to come from a stronger algorithm, an effective architecture, or a convincing application result.

Possible research directions include sharing work between inverse walks, choosing between threshold maps and restricted forward tables, or combining arithmetic summaries with thresholds when either alone is wasteful. These are hypotheses to investigate, not established new contributions.

One important comparison remains incomplete: **Parhi's quantizer-loop pipelining work**, along with the roundoff treatment in the classic incremental-block filtering paper. Available author descriptions identify parallel-branch and delayed-decision approaches, but the full methods were inaccessible during the review. We cannot claim that earlier look-ahead methods categorically fail to handle quantization. [Quantizer loops][R7]; [incremental block filtering][R8].

## 3. What has actually been checked

The independent research scripts use exact Python integer arithmetic. They are distinct from the current WIP implementation and from the older experiments described in `internal/`.

| Executed check | Coverage | Result |
|---|---:|---|
| Block-map evaluation against serial execution | 47,352 entry-state comparisons | No differences |
| Composition and associativity | 300 three-block cases | No differences |
| Replay of complete output traces | 4,782 outputs | No differences |
| Proposed AMR-WB arithmetic reduction | 524,288 primitive-model comparisons | No differences |
| True 16-bit endpoint-width sweep | 100 configurations | Strong dependence on coefficient, block length and input scaling |

The map comparisons combine 15,000 comparisons from selected exhaustive short-block families with 32,352 from randomized variable-coefficient cases. They do not cover every input sequence. The codec check covers every 16-bit entry state at eight selected input values; it is not a compiled codec conformance test.

The older internal documents report additional validation, but the underlying archive and raw test records were absent. Those counts were not rerun and should not be combined with the results above as if they were independently reproduced.

### Reference-model issues to fix before using it for RTL

In the version inspected, `GoldenModel.py` accepts a configurable state width but clips every forward update to **[-8, 7]**. Consequently the nominal 16-bit test compares two versions of a four-bit-clipped recurrence. For input [100, 0, 0] at coefficient 1/2, it returns [7, 3, 1]; the intended 16-bit result is [100, 50, 25].

The testbench also omits +7 from its four-bit input alphabet, generates only nonnegative random samples, and can reference an undefined diagnostic variable on the enabled failure path. Coefficients and signed rounding should be made explicit in an integer reference before generalizing beyond the currently tested values.

These are manageable prototype issues. The important lesson for RTL verification is that comparing two implementations is insufficient if both share the same incorrect arithmetic definition. Keep an independently specified oracle and compare complete state/output sequences.

### Compactness has a quantization floor

The logarithmic block-length estimate in `SPEC.md` describes an unrounded contraction envelope. It is not a worst-case capacity guarantee for the integer machine.

For silence and a = (m − 1)/m, every state from −(m − 1) through 0 is fixed, provided those states fit in the legal domain. With a = 255/256, there are 256 such fixed states. Thus a silence block can never have fewer than 255 thresholds, however long it becomes.

Selected new measurements for true 16-bit state:

| Coefficient | Block length L | Silence K | Median K for modestly scaled random input |
|---|---:|---:|---:|
| 3/4 | 64 | 3 | 0 |
| 63/64 | 64 | 23,918 | 23,919.5 |
| 255/256 | 64 | 51,012 | 51,014 |
| 255/256 | 1,024 | 1,199 | 1,196.5 |
| 255/256 | 4,096 | 255 | 0 |

The random columns use 16 blocks per configuration and a fixed seed. Inputs are uniformly sampled from an integer interval with amplitude approximately one quarter of (1 − a) times the positive state limit. These are synthetic characterization cases, not native application measurements. Full-range random input frequently caused clipping and produced much smaller maps. “Random inputs” is therefore not enough to specify a convincing experiment.

A safe width bound begins at w_0 = hi − lo and iterates **w_next = ceil(A × w / D)**; then K ≤ w_L. Use it, or a stronger justified bound, to size fixed-capacity hardware. A favorable average cannot guarantee that a buffer will suffice.

### Operation counts are not hardware timing

The literal two-endpoint, K-inverse-pass, one-replay method performs approximately **(K + 3)L** mixed updates before boundary and memory overhead. An inverse division, a forward multiply/shift and a threshold-memory query may have very different costs.

Under a simple schedule with one engine per block, a better first estimate is **3L × forward-update cost + KL × inverse-update cost**, then add boundary resolution, memory and control. The familiar P/(K + 3) only follows from much stronger equal-cost assumptions. Pipelining or replicating inverse work changes resource usage and must be charged to the comparison.

Keep input sampling period, fabric clock period, recurrence initiation interval and output bandwidth separate. Likewise, distinguish first-output latency, final-output latency and steady-state throughput. A design can improve one and worsen another.

## 4. Applications worth investigating

We need an application whose arithmetic fits, whose exact integer outputs matter, and whose complete implementation benefits. No reviewed candidate currently satisfies all three with measured evidence.

| Candidate | Best reason to investigate | Main obstacle | Appropriate first experiment |
|---|---|---|---|
| AMR-WB de-emphasis | Standardized bit-exact behavior and a native buffered scalar recurrence | Low single-stream rate; inspected source revisions need to be unified | Capture native input/state traces and substitute the exact kernel in a consistent reference codec |
| UKUI exponential blur | Concrete fixed-point arithmetic on an already buffered image | Independent rows/channels may offer cheaper parallelism | Preserve the original image passes and compare whole-image cost with ordinary row parallelism |
| SiPM waveform synthesis | Published fast-stream feedback timing problem and positive one-pole banks | Missing internal integer contract; existing look-ahead solution already works | Obtain native arithmetic and latency/resource requirements before choosing blocks |

### AMR-WB de-emphasis

This is the strongest candidate for explaining **why bit-exactness matters**. ITU describes G.722.2 Annex C as a bit-exact ANSI-C implementation. The inspected `Deemph2` primitives reduce to the supported rule with A = 22282, D = 32768 and C = 16384 × input + 16384, with signed 16-bit state. The rounding offset and saturation order are part of the reduction. [ITU implementation description][A1]; [inspected function][A2]; [primitive header][A3].

A native weighted-speech call operates on 256 samples at an internal 12.8 kHz rate, representing a 20 ms frame. The corresponding input buffer is available before this call. However, existing frame buffering is not permission to add another 20 ms of delay. The function, primitives and caller were inspected at different source revisions; a single consistent release must be obtained and compiled before claiming native equivalence. [Official code constants][A4]; [inspected caller][A5].

The public AMR-WB test specification provides speech, silence, sweep, saturation and mode-switching sequences, with specified homing behavior. Use those to validate the unchanged codec first, then capture the actual recurrence inputs and compare after substitution. [ETSI test sequences][A6].

At 12,800 updates per second, a single stream is unlikely to require a large FPGA accelerator. Many simultaneous calls also provide independent parallelism. Measure the kernel's fraction of codec runtime before making an application-level speedup claim. This is initially an exactness benchmark and learning target, not a proven communications-throughput application.

### Integer image blur

UKUI's inspected blur update has the form z_next = z + floor(alpha × (128 × pixel − z) / 65536). For a valid positive coefficient, it fits the supported scalar form. The interval [0, 32640] is invariant, so clipping can remain inactive without changing the native code. Freeze the actual generated integer alpha and confirm the target platform's signed-shift semantics. [Packaged source][A7].

Images are naturally buffered, but independent rows, columns and channels are a serious competing source of parallelism. A win on one artificially long line is not sufficient if a simpler row-parallel implementation finishes the actual image faster. Preserve the original pass order and initialization; later passes consume already modified pixels.

Use actual byte images plus explicit synthetic ramps, constant images and alternating extremes. The OpenEXR corpus offers public image material, but any conversion to the native byte format must be fixed and separated from filter timing. [Image corpus][A8].

### SiPM detector waveform synthesis

A 2026 paper describes an FPGA emulator using positive one-pole banks, with 0.8 ns subphases on a 156.25 MHz fabric clock. It reports a naive feedback timing failure and a look-ahead implementation with 83.2 ns shaping latency. This is a concrete reason to study recursive hardware. [Carsi and coauthors][A9].

The paper does not specify enough internal state rounding and overflow detail to establish that its native machine matches ours. Final-output saturation cannot simply be moved into each recursive bank. Its existing solution already meets the stated output requirement, so an improvement would need to reduce resources, support another documented operating point, or provide a separately valued exactness guarantee.

Obtain the native HLS types or RTL, integer coefficients, state-reset behavior, golden traces and permitted added delay first. SimSiPM supplies a reproducible event generator, but generated hits alone are not a golden fixed-point model. [SimSiPM][A10].

### Lower-priority leads and exclusions

Automatic radio DC correction has a plausible scalar shape, but UHD documents a very small adaptation parameter; slow contraction makes compact maps difficult, and its exact internal arithmetic was not recovered. Generic DC blockers do not all use the same recurrence. [UHD documentation][A11].

General biquads, detector processing chains with integrators or several states, state-dependent envelope attack/release, and online feedback control should not be treated as supported without another proof. QubiC predistortion supplies a real recursive-hardware example, but the representative integrator/second-order chain is outside the present scope. Financial EWMA has a suitable ideal equation, but the review found no native matching integer implementation with a convincing fast-stream need. [Predistortion example][A12].

Even similarly named image algorithms can differ: the inspected Qt blur puts quantization inside the state feedback differently, and its state map need not be monotone. Algorithm names and transfer functions are insufficient to establish compatibility. [Qt source][A13].

## 5. Reading list for the RTL work

The first group is the recommended reading order. Each item has a specific question to carry into architecture design. “Method read” means the relevant method sections were inspected during the review; it does not mean the implementation or all proofs were reproduced.

### Read first

1. **Papadantonakis, Kapre, Chan and DeHon — Pipelining Saturated Accumulation, FPT 2005.** The closest hardware precedent. Study the compact function representation, what makes composition cheap, and how buffering and prefix logic affect the implementation. **Takeaway:** exact nonlinear arithmetic can be parallelized, but representation cost determines whether it is useful. *Relevant methods and implementation sections read.* [Paper][R1]

2. **Blelloch — Prefix Sums and Their Applications, 1990 report / later chapter.** Read the associative scan and up/down sweep construction. Distinguish function composition from ordinary addition and distinguish tree depth from physical clock cycles. **Takeaway:** learn when a serial boundary chain is worth replacing with a tree. *Relevant sections read; linked PDF is the chapter version.* [Chapter][R9]

3. **Mytkowicz, Musuvathi and Schulte — Data-Parallel Finite-State Machines, ASPLOS 2014.** Focus on chunk execution and partial convergence. **Takeaway:** compare the cost of explicit candidate trajectories with the cost of computing inverse thresholds; give the competing table implementation access to convergence too. *Relevant methods read.* [Paper][R2]

4. **Parhi — Pipelining in Algorithms with Quantizer Loops, 1991.** Prioritize obtaining this paper. **Takeaway:** understand existing branch speculation and delayed-decision approaches before deciding where the proposed constructor differs. *Author descriptions/metadata checked; full method still needs reading.* [DOI][R7]

5. **Parhi and Messerschmitt — Pipeline Interleaving and Parallelism in Recursive Digital Filters, Parts I and II, 1989.** Read look-ahead, decomposition and incremental block filtering, then inspect exactly where rounding occurs. **Takeaway:** transfer-function equality and equality of a rounded state sequence are different claims. *Bibliography and selected indexed material checked; complete arithmetic comparison remains open.* [Author bibliography][R10]; [Part II DOI][R8]

6. **Cox, Sankaranarayanan and Chang — A Bit Too Precise? Verification of Quantized Digital Filters, STTT 2014.** Focus on arithmetic semantics, overflow and limit cycles. **Takeaway:** formulate what the hardware must preserve before trying to optimize it. *Arithmetic and verification framing read; tool not reproduced.* [Paper][R11]

### Read when comparing architectures

- **Chaurasia and coauthors — Compiling High Performance Recursive Filters, HPG 2015.** Local work, boundary reconciliation and recomputation are close scheduling ideas. Its linear transformations do not establish samplewise floor/saturation equivalence. *Relevant transformation sections read.* [Paper][R12]
- **Ko, Jung, Han and Burgstaller — A Speculative Parallel DFA Membership Test for Multicore, SIMD and Cloud Computing Environments, 2012/2013 manuscript.** Read reverse lookahead and reduced entry-state sets. Useful for designing a strong restricted-forward-table comparator. *Relevant methods read.* [Manuscript][R3]
- **Sin'ya, Matsuzaki and Sassa — Simultaneous Finite Automata, ICPP 2013 / 2014 manuscript.** Background on lifting states to whole transition functions, including the cost of precomputation. *Relevant constructions read.* [Manuscript][R13]
- **Maleki and Burtscher — Automatic Hierarchical Parallelization of Linear Recurrences, ASPLOS 2018.** Useful hierarchical scheduling and correction strategies. It includes exact integer-linear experiments; its floating-point filters use a different validation tolerance. *Relevant methods and arithmetic evaluation read.* [Paper][R14]
- **Nehab and coauthors — GPU-Efficient Recursive Filtering and Summed-Area Tables, 2011.** Useful for understanding why memory passes and boundary locality can dominate arithmetic. *Relevant formulation and block decomposition read.* [Paper][R15]
- **Parhi — Finite Word Effects in Pipelined Recursive Filters, 1991.** Helps separate finite-precision error analysis from exact machine equivalence. *Abstract only in this review; full paper still worth obtaining.* [Institutional record][R16]

### Read for the research argument and broader context

- **Adeshola and Umar — Combinatorial Results for Certain Semigroups of Order-Preserving Full Contraction Mappings of a Finite Chain, 2013 preprint / 2018 publication**, and **Fernandes — On the Monoid of Order-Preserving Transformations of a Finite Chain Whose Ranges Are Intervals, 2024.** These explain why the underlying map class and contiguous images are established mathematics. *Definitions and relevant results read.* [First paper][R4]; [second paper][R5]
- **Embrechts and Hofert — A Note on Generalized Inverses**, and **Keimel — Refinement Calculus with Probability or Fuzziness, Appendix B, 2008 report.** Background for threshold conventions and reversal of composition. These are mathematical context, not FPGA accelerator papers. *Selected definitions/results read.* [Generalized inverses][R17]; [adjoints][R6]
- **Wilson — Layered Multishift Coupling for Use in Perfect Sampling Algorithms, 1999 manuscript.** Explains extremal-state tracking and compressed interval images in another field. Useful conceptual context; its sampling objective differs from deterministic DSP replay. *Selected relevant sections read.* [Manuscript][R18]
- **Ma, Adams and Ragan-Kelley — Finding Fast Filters, 2026 preprint**, and **Zhai and Paris — Parallel Cascaded Recursive Filtering on Multi-Core CPUs and GPUs, 2026 preprint.** Modern performance context. Their reviewed numerical contracts do not preserve this prescribed integer machine, but an application may still prefer them if exact compatibility is unnecessary. *Relevant methods/evaluation read; preprint status retained.* [Filter search][R19]; [parallel filtering][R20]

For implementation, read the chosen device's DSP, memory and timing documentation alongside these papers. The review consulted AMD's DSP58 architecture documentation as one example; it does not imply that Versal is the chosen target. CMSIS-DSP is useful for comparing production fixed-point arithmetic contracts, but its variants differ in rounding and overflow. [AMD manual][T1]; [CMSIS-DSP reference][T2].

## 6. RTL roadmap focused on problem solving

This roadmap intentionally leaves microarchitecture and HDL choices open. Each stage should produce an explanation, a working artifact and evidence that the explanation was right or wrong. Advance based on those results rather than a fixed calendar.

### Stage 1 — Define the machine and make the reference trustworthy

Write down state/input/coefficient formats, exact rounding and saturation points, initialization, reset behavior and supported parameter ranges. Decide what constitutes an accepted input and a required output. Start with one fixed coefficient and one state width, then justify any added configurability.

Repair the Python reference issues and retain an independently specified integer oracle. Use hand-checkable cases at both rails, negative rounding cases, silence and nonzero initial states. Exhaustively check small instances and retain failing traces as regressions.

**Learning objective:** turn a mathematical description into an unambiguous hardware contract. **Completion evidence:** two independently structured reference paths agree, and boundary cases have explicit expected results.

### Stage 2 — Build and understand the serial RTL baseline

Implement the original recurrence first. Establish a minimal streaming interface and verify every accepted output against the reference. Synthesize and route it with realistic timing constraints. Inspect the actual feedback path and determine whether arithmetic, selection, fanout or routing limits the recurrence rate.

Distinguish pipeline latency from the interval at which dependent samples can be accepted. Adding registers to a feedback loop is not automatically a valid throughput improvement. Also examine constant-coefficient opportunities before declaring the serial implementation optimized.

**Learning objective:** connect data dependencies to timing reports. **Completion evidence:** a correct baseline with measured initiation interval, achievable clock, latency and resources, plus an explanation of its limiting path.

### Stage 3 — Characterize the work and set a hardware budget

Use software to measure map sizes on honest input distributions and candidate native traces. Sweep block lengths only within a plausible delay budget. Record worst-case K as well as averages, and estimate storage for inputs, maps and pending outputs.

Measure or prototype forward arithmetic, inverse arithmetic and map-query costs separately. Decide which operations can share a datapath and what bandwidth that schedule requires. Predict whether a complete design can plausibly beat the baseline before multiplying the number of engines.

**Learning objective:** derive a resource and service model from the algorithm. **Completion evidence:** a justified choice of initial block length, capacity and engine count, including an unfavorable case the design must handle.

### Stage 4 — Make one block engine exact

Implement endpoint evaluation, threshold construction, map storage and querying, and replay for a single block. Keep construction and replay observable so a mismatch can be localized. Begin with straightforward control and a small supported capacity.

Reason about storage ownership across phases, reverse access to input data, memory read latency and intermediate signed widths. Check constant maps, large maps and unreachable inverse targets. Define what happens if a block exceeds capacity; an exact fallback must preserve the original state and outputs.

**Learning objective:** coordinate arithmetic, storage and control while maintaining invariants. **Completion evidence:** every legal entry state agrees for selected small blocks, complete replay traces agree, and capacity overflow has a tested behavior.

### Stage 5 — Connect two blocks, then a small batch

Resolve boundaries with a simple sequential map chain first. Verify that each block starts from the preceding block's exact exit and that the final batch state is carried into the next batch. Replay concurrently only after the boundaries are correct, and restore the original output order.

Use nonzero initial states, uneven final blocks and consecutive batches. Treat the serial boundary chain as a measurable part of the design. A prefix tree becomes an architectural option when evidence shows this chain matters; it is not required to establish the first complete executor.

**Learning objective:** reason about distributed state and ordering. **Completion evidence:** the complete stream, including transitions between batches, matches the serial machine without missing or duplicated outputs.

### Stage 6 — Make streaming and bounded storage reliable

Add controlled overlap between collection, construction, boundary resolution and replay. Decide when buffers can be reused and what happens when input or output stalls. Exercise reset while work is in flight and specify whether pending work is drained or discarded.

Use randomized stalls and directed long runs of difficult inputs. Count accepted inputs and delivered outputs, check ordering, and track maximum occupancy. If the design relies on backpressure, make that part of the interface contract. If the source cannot pause, prove the selected service rate and buffering can sustain it. A correct serial fallback can still be too slow for a live stream.

**Learning objective:** distinguish arithmetic correctness from system correctness. **Completion evidence:** bounded occupancy and no loss, duplication or reordering under the supported traffic contract, with first-output and sustained-rate measurements.

### Stage 7 — Optimize one measured bottleneck at a time

Compare shared versus replicated arithmetic, sequential versus parallel threshold processing, search versus comparator-based queries, and serial versus tree-based boundary resolution. Change one architectural decision at a time, record the predicted effect, and compare that prediction with synthesis and routed results.

Maintain strong exact competitors: optimized serial execution, exact unrolling that preserves every quantizer, and forward tables restricted to the same justified entry domains. Compare independent-channel replication when the application has independent work. Include preparation, buffering, replay and output interfaces in every result.

**Learning objective:** make architecture choices using evidence rather than nominal operation counts. **Completion evidence:** a throughput/latency/resource comparison showing where each design wins and why. A negative result is useful if it identifies the controlling cost clearly.

### Stage 8 — Integrate one native application and decide the research claim

Freeze one native source/configuration and its output contract. Preserve its coefficients and arithmetic. Verify the unchanged reference first, then substitute the executor and compare the complete application's required outputs. Measure both kernel and application impact.

For AMR-WB, preserve frame state and homing behavior; for blur, preserve pass order and compare ordinary image parallelism; for SiPM, obtain the missing arithmetic and delay requirements before treating it as a supported target. Use matched resource budgets or compare the minimum resources needed to meet a fixed native service target.

**Learning objective:** determine whether a locally faster circuit improves the actual system. **Completion evidence:** either a reproducible application advantage with a clear prior-work distinction, or a well-supported decision to narrow or stop the acceleration claim.

### A useful working habit throughout

Keep a short design notebook for each change: the suspected bottleneck, predicted effect, alternative considered, measurement and explanation of any discrepancy. Distinguish errors in arithmetic, control, interface behavior, memory scheduling, timing constraints and resource estimation. The aim is to get better at diagnosing why a circuit behaves as it does, not simply to accumulate more modules.

Do not add a general compiler, arbitrary filter order or runtime configurability before the simpler contract is understood. Those can become later extensions if the measurements justify them.

## 7. Measurements and research decisions

Every hardware comparison should include:

- Exact agreement of required state and output traces, with the coverage and remaining proof obligations stated.
- Device, tool version, clock constraints and interface assumptions.
- Post-route clock and recurrence/service initiation intervals.
- Sustained accepted and delivered sample rates, first-output latency and batch completion latency.
- LUT, flip-flop, DSP and block-memory usage, including input, map and reorder storage.
- Worst-case K, capacity limits, fallback behavior and service under difficult sustained input.
- Whole-application impact, alongside kernel-level numbers.

Measure power only if the setup supports a defensible whole-system measurement. Resource counts alone do not establish energy savings. For a small codec stage, measure its baseline runtime fraction: even a large kernel speedup can have little effect on the entire encoder.

Continue toward a paper when a distinct method survives the closest-work comparison and a complete exact implementation improves a meaningful native tradeoff. The internal suggestion of 1.5× throughput at matched resources can be an engineering continuation target; it is not a publication rule. Meeting an otherwise-unmet requirement can matter more than an arbitrary speedup factor.

A practical signal-processing implementation paper could fit SiPS; a stronger architecture/tool contribution could fit FPGA. This is audience fit, not an acceptance forecast or a statement about current submission deadlines. A claim based only on the elementary map theorem looks weak. [SiPS scope used in the review][V1]; [FPGA scope used in the review][V2].

If restricted forward tables win, use them and revise the claim. If the application already meets its requirement more cheaply with conventional hardware, keep it as a learning benchmark and look for a better research target. A careful explanation of the tradeoff is more useful than forcing every result to support the initial architecture.

## 8. Suggested division of work and immediate next steps

The literature/application side can close the classic reading gaps, obtain native configurations, establish why exactness is required, prepare reference traces and identify a real rate/delay/resource target. The RTL side can own the serial baseline, arithmetic and storage cost measurements, block engine, streaming schedule and architecture comparisons. Agree together on the arithmetic contract and experimental baselines before measuring speedups.

The next concrete deliverables are:

1. A corrected integer reference and a one-page arithmetic/interface contract.
2. A verified serial RTL baseline with an explained timing report.
3. A small map-size and primitive-cost study that justifies the first block-engine design.
4. A comparison note for the 2005 saturation paper and the unresolved quantizer-loop work.
5. One qualified native benchmark, with its remaining application limitations stated.

These deliverables give the RTL work a clear direction while leaving the central design choices available as problem-solving exercises.

## 9. Existing research artifacts

The repository's `research/` directory contains the detailed assessment, source-by-source literature notes, application audit, technical audit and experiment plan. The files are `README.md`, `PRIOR_ART.md`, `FILTER_LITERATURE.md`, `APPLICATIONS.md`, `TECHNICAL_AUDIT.md` and `EXPERIMENT_PLAN.md`.

`research/audit.py` regenerates `audit_results.json`; `research/codec_arithmetic_check.py` regenerates `codec_arithmetic_results.json`. Run each with Python from the repository. The first script's optional original-model check imports NumPy through `GoldenModel.py`; the independent arithmetic checks otherwise use Python's standard library. Neither script is a hardware performance benchmark. This brief consolidates their recorded findings and does not add new experimental results.

The original project implementation and the documents in `internal/` were left unchanged during the literature review. This handoff provides direction and evidence; the RTL architecture remains to be designed and evaluated.

[R1]: https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf
[R2]: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf
[R3]: https://arxiv.org/html/1210.5093
[R4]: https://arxiv.org/pdf/1303.7428
[R5]: https://arxiv.org/pdf/2407.05084
[R6]: https://www2.mathematik.tu-darmstadt.de/~logik/keimel/Papers/appendixB.pdf
[R7]: https://doi.org/10.1109/31.135746
[R8]: https://doi.org/10.1109/29.32287
[R9]: https://www.cs.cmu.edu/~guyb/papers/Ble93.pdf
[R10]: https://people.eecs.berkeley.edu/~messer/Publications.htm
[R11]: https://arlencox.github.io/papers/filters.pdf
[R12]: https://mit-gfx.github.io/recfilter/recfilter.pdf
[R13]: https://arxiv.org/html/1405.0562
[R14]: https://userweb.cs.txstate.edu/~burtscher/papers/asplos18.pdf
[R15]: https://hhoppe.com/recursive.pdf
[R16]: https://experts.umn.edu/en/publications/finite-word-effects-in-pipelined-recursive-filters/
[R17]: https://people.math.ethz.ch/~embrecht/ftp/generalized_inverse.pdf
[R18]: https://arxiv.org/html/math/9912225
[R19]: https://arxiv.org/html/2607.20634v1
[R20]: https://arxiv.org/html/2607.23763v1
[A1]: https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=13429
[A2]: https://android.googlesource.com/platform/frameworks/av/%2B/dd833ba601e642d72da2200a2fd9c3fa1cb69d2d/media/module/codecs/amrwb/enc/src/deemph.c
[A3]: https://android.1.googlesource.com/platform/frameworks/av/%2B/7aeb9029d26cde995cb6f76748ebe36c7bdc9be3/media/module/codecs/amrwb/enc/inc/basic_op.h
[A4]: https://www.itu.int/epublications/en/publication/itu-t-g-722-2-annex-c-2017-12-fixed-point-c-code/en
[A5]: https://android.googlesource.com/platform/frameworks/av/%2B/1e6a675fccdc37afcfb337f8fa97d1ddab90adf0/media/codecs/amrwb/enc/src/voAMRWBEnc.c
[A6]: https://www.etsi.org/deliver/etsi_ts/126100_126199/126174/18.00.00_60/ts_126174v180000p.pdf
[A7]: https://sources.debian.org/src/ukui-session-manager/1.1.3.1-1/ukui-session/gsm-blur.c
[A8]: https://openexr.com/en/latest/test_images/index.html
[A9]: https://arxiv.org/html/2607.00841v1
[A10]: https://github.com/EdoPro98/SimSiPM
[A11]: https://files.ettus.com/manual/page_calibration.html
[A12]: https://arxiv.org/html/2609.16488v1
[A13]: https://codebrowser.dev/qt6/qtbase/src/gui/painting/qimageeffects.cpp.html
[T1]: https://docs.amd.com/r/en-US/am004-versal-dsp-engine/DSP58-Architecture
[T2]: https://arm-software.github.io/CMSIS-DSP/latest/group__BiquadCascadeDF1.html
[V1]: https://ieee-cas.org/files/ieeecass/2025-12/sips-2026-cfp.pdf
[V2]: https://isfpga.org/past/fpga2026/call-for-papers/

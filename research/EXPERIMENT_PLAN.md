# Experiments that can decide the project

These are proposed experiments, not completed benchmarks. Inputs and coefficients must come from the native implementation; implementation parameters may be tuned, but the target machine must not be changed to favor compact maps. The original application/model requirements and all unfavorable results belong in the artifact.

## 1. Establish a valid reference and recover missing predecessors

Correct the original model's saturation width and failure diagnostics, and specify integer A/D, signed floor, saturation placement, intermediate widths, initialization and continuation. Use a separately specified integer oracle and a compiled native reference where one exists. Add all-state short-block checks, complete traces, zero coefficient, negative numerator, rails, unequal/empty blocks, coefficient changes and consecutive batches. The supplied research checks are a starting point, not exhaustive verification.

In parallel, obtain Parhi's 1991 quantizer-loop paper and 1989 Part II through author/library access. Compare the actual branch/state representation, quantizer placement, all-output production and arithmetic cost with the proposed inverse constructor. Trace citations forward from the 2005 saturated-accumulation paper. Record explicit differences; do not infer them from titles or abstracts. This reading gap must close before claiming priority.

**Decision:** if the current construction is already present, reposition around a genuinely new optimization or a stronger application result. Reimplementation alone is not the proposed contribution.

## 2. Two exactness benchmarks and one physical lead

| Track | Required artifact | Proposed measurement | What would disqualify it as flagship |
|---|---|---|---|
| AMR-WB de-emphasis | One consistent source release, matching conformance vectors, captured native `wsp` arrays and memory state | Per-block K and total cost; every state/output and final encoder code stream; codec-wide time fraction | Tiny baseline time fraction, no exact-compatibility requirement for intended deployment, or channel replication always cheaper |
| UKUI blur | Frozen source/compiler, coefficient/radius, byte images, original pass order and initialization | K by row/column and image class; single-line and whole-image timing; exact state/byte comparison | Independent row/channel scheduling dominates; arithmetic differs on target platform; no system requirement benefits |
| SiPM emulator | Author/native HLS state types and quantizers, integer coefficients, golden traces, maximum delay, device/resource budget | Map width under actual photon events; direct and native look-ahead baseline resources/rate; full waveform comparison | Native recurrence outside the contract, already-sufficient cheaper look-ahead, or permitted buffering shorter than construction schedule |

Sources and publicly available stimuli are in [APPLICATIONS.md](APPLICATIONS.md). Standardized codec sequences are preferable to arbitrary audio samples for testing exactness; SimSiPM gives generated event stimuli, not an actual hardware golden integer model. No author contact was sent in this review.

For the physical lead, a concise information request would seek: the exact recurrence and type declarations; coefficient programming range; input/output rate; allowed added delay; state reset and overflow rules; native look-ahead RTL/HLS or golden outputs; current LUT/FF/DSP/memory use; and a configuration where fewer resources or more throughput is actually needed. These are technical data needs, not presumed deficiencies in the published system.

## 3. Measure width before building the executor

For each native trace, record endpoint K for block lengths 8, 16, 32, 64, 128 and 256, plus larger lengths only when its real delay budget allows. Use several state widths only as separate synthetic sensitivity studies; do not change the native width for the headline application. Include real initialization/entry bounds and, separately, full legal-domain maps.

Report maximum, median and upper quantiles; certified bound; endpoint/actual-state clipping frequency; inverse work; constant-map fraction; and required capacity. Include silence, DC, low amplitude, alternating rails and actual operational traces. Preserve all seeds, exact arrays and coefficients. Test bursty and repeated worst cases, because average K cannot justify a streaming deadline.

Test a nontrivial predictor of runtime, not just K: `sum(K_i*L_i)`, longest lane, constant-divisor cost, map-query depth, memory bandwidth and output serialization. Include the shrinking entry domains available to forward tables. Full-state threshold maps and restricted-entry forward tables must receive equally strong domain information when comparing algorithm quality.

**Decision:** if feasible L never makes either constructor affordable, stop hardware work for that configuration. If forward tables win, keep them and remove threshold-specific superiority claims. A measured mixed strategy can be considered, with all selection costs included.

## 4. Measure primitive costs and implement the strongest comparisons

Synthesize on the same device/tool settings: exact serial update; exact multi-sample unrolling retaining all quantizers; constant/runtime inverse step; threshold query using sorted search and a comparator network; and a restricted forward-table builder. Constant coefficients deserve constant-division optimization in all methods. Runtime-coefficient flexibility must be compared at the same flexibility requirement.

Use small-width exhaustive tables as a correctness/control baseline, not the only performance competitor. Include convergence factoring where it can reduce table work. The unity-slope saturation case should use the 2005 three-parameter map as a control, not a large threshold list. Linear look-ahead and numerical GPU/CPU libraries may be application alternatives, but label their arithmetic contract and compare quality separately if they are not exact.

The full executor must include buffering, endpoint passes, threshold or table construction, boundary resolution, replay, fallback, memory arbitration, output order and batch-to-batch state propagation. Compare a sequential boundary chain with a tree; a tree is not automatically faster at small P once memory and composition are included. Track whether inverse passes and replay reuse the same engine or duplicate resources.

## 5. Evaluate useful service, not an isolated kernel peak

For FPGA hardware, report routed frequency, sustained accepted/delivered samples per second, first and last output delay, worst-case service, LUT/FF/DSP/BRAM, capacity and memory traffic. Specify device, tool version, constraints and interface widths. Report both equal-resource Pareto curves and minimum-resource implementations meeting a fixed native rate/delay. Do not compare a much larger design only by its peak clock.

For CPU experiments, include launch/synchronization cost and memory traffic, use compiled optimized scalar/vectorized references, pin thread/core counts, report distributions over repeated runs and label warm/cold execution. Time whole frames or streams as well as the de-emphasis/blur kernel. For codecs, measure the baseline fraction p: even an infinitely fast replacement has total speedup at most `1/(1-p)`. This can rule out a significant codec-level claim quickly.

Correct fallback must be exercised under sustained worst-case input, not merely counted as “no mismatch.” If backlog grows without bound or the deadline fails, the configuration does not support that input-rate contract. Power/energy claims require actual whole-system measurements and a stated measurement boundary; do not infer them from multiplier counts.

## 6. Decision and paper contents

The internal notes' provisional target of 1.5× throughput at matched resources can be a useful engineering continuation rule, provided native latency and exactness also hold. It is not a publication threshold. A smaller speedup can be significant if it meets a documented otherwise-unmet requirement; a large microbenchmark speedup can be insignificant when it does not affect an application.

Continue toward a paper only when the prior-work distinction survives, the exactness contract is independently checked, and a complete application result improves a meaningful tradeoff. Otherwise narrow to an algorithmic study with a substantially stronger constructor, retain a useful correctness artifact, or stop this direction. Do not resurrect the separate convolution reserve solely because this application search is difficult; it needs its own distinct algorithm and review.

An eventual manuscript should contain a precise arithmetic scope; closest-work comparison; construction/composition pseudocode and cost bounds; proof including sentinels/rounding/overflow; complete implementation architecture; native workload configuration; resource/latency/throughput Pareto plots; adversarial and failure cases; and a reproducibility bundle with exact inputs, golden outputs and build scripts. Publication timing cannot be forecast until the hardware and application gates are met.

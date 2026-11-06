# Certified local execution: architecture and RTL learning roadmap

**Latest audit:** read [THIRD_PASS_VERDICT.md](THIRD_PASS_VERDICT.md) and [FEASIBILITY_RED_TEAM.md](FEASIBILITY_RED_TEAM.md). The mandatory comparator is now a shared-base relative-rank table, not just separately evolved candidate trajectories. Both it and a bitmap can use one input pass. The initial representation choice is an experiment, not a settled advantage.

6 November 2026. This is a proposed research direction, informed by `SPEC.md`, the [financial review](../FINANCIAL_EWMA_REVIEW.md), [device audit](../FINANCIAL_EWMA_FPGA.md) and [prior-art review](../PRIOR_ART.md). It contains analytical schedules and new architectural hypotheses, not measured FPGA results. No RTL is supplied. The objective is exact execution of a specified rounded integer recurrence; whether a newly chosen integer financial feature is accurate enough is a separate application experiment.

## Recommendation and defensible contribution

Investigate **certified local execution**: construct inexpensive enclosures of unresolved block-entry states, then spend exact arithmetic only on the remaining local uncertainty. The strongest proposed mechanism below maintains a local map as a bitmask, deleting at most one surviving threshold per event when the certified domain is narrow enough. Compare it with forward tables, backward thresholds and small unrolling under fixed resource budgets. Start with buffered financial replay and every-event outputs; evaluate threshold decisions separately.

The useful research question is whether a hardware executor can turn cheap, independently computed numerical certificates into enough savings in exact work to beat an excellent shift/add baseline. Replacing the full state domain by tens of candidates could change the design substantially. A real-affine approximation alone cannot eliminate quantization ambiguity, and an impressive events/clock figure can disappear once prediction, memory traffic, fallback and output ordering are included.

Broad ideas already have close predecessors. Exact map prefix hardware appears in [Papadantonakis et al., FPT 2005](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf). Candidate trajectories with convergence factoring appear in [Mytkowicz et al., ASPLOS 2014](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf); preceding-input candidate restriction appears in [Ko et al.](https://arxiv.org/html/1210.5093). These prevent claiming transfer maps, speculation, candidate pruning or merge detection as new principles. Possible contributions are a specialized certified predictor, shared inverse hardware, compact ordered candidate maintenance, or a bounded-service scheduler whose complete measured tradeoff improves on these approaches.

## What the certificate must actually prove

For the unsaturated contract

`s_i = floor((A*s_(i-1) + C_i)/D)`, with `a=A/D`, `0<a<1`,

define the real recurrence `z_i=a*z_(i-1)+C_i/D`, initially `z_0=s_0`. The numerator is integer, so each rounding residual lies in `[-(D-1)/D,0]`. Consequently

`z_h-g_h <= s_h <= z_h`,

`g_h=((D-1)/D)*(1-a^h)/(1-a)`.

An integer entry domain is the integers inside this interval, intersected with the legal state domain. An implemented predictor must add its own outward error allowance: if `z_h` is enclosed by `[zlo,zhi]`, use `[ceil(zlo-g_h), floor(zhi)]`. Bounds and conversions themselves require directed rounding. A rounded numerator offset belongs in `C_i`; using a centered reference can redistribute the one-sided error but does not remove its interval width. Saturation must either be proved inactive, as it often is for a bounded convex EMA, or handled by a separate sound enclosure. The Illinois toward-zero difference update needs its own residual bound; it is not the same formula.

As `h` grows, this rounding-width bound approaches `(D-1)/(D-A)`: 21 for 61/64, 63 for 63/64 and 127 for 127/128. Thus financial coefficients may leave dozens or hundreds of candidates even with perfect prediction. These are certificate limits, not claims about observed candidate counts or actual coalescence. An approximate floating result without an error certificate is not an entry-domain proof.

There are three ways to obtain useful domains:

* **Global affine prediction.** Compute block affine summaries and their prefixes from the known initial state. The summary operation is associative over real arithmetic; fixed-point summary errors must be enclosed. Prediction can be pipelined, reassociated or evaluated with independent weighted input terms because it need not preserve intermediate integer rounding. Its gain, coefficient storage, multiplier widths and summary scan are charged work. A serial predictor with the same feedback bottleneck merely relocates the problem.
* **Preceding-window certificates.** Independently process a known preceding input window, enclosing the unknown state at its beginning by the legal range. Its residual uncertainty includes `a^h*(u-l)` as well as rounding. Longer windows reduce the first term but repeat input work. This can avoid exact full-range endpoint passes, though it need not be cheaper.
* **Exact restricted endpoints.** Given a certified narrow entry domain, run its two endpoints to obtain the exact local exit range. This remains a strong baseline and a tightening option. Global full-range endpoints are retained for comparison, rather than assumed indispensable.

The strongest numerical experiment compares all three on identical tapes. Record both construction cost and resulting domain width. Merely reporting a narrow interval obtained by an uncharged serial pass would not demonstrate parallel acceleration.

The [executable prototype](certified_mask_checks.py) and [results](certified_mask_results.json) test outward affine summaries, an interval-prefix topology, exact masks and replay. Run `python3 research/direction/certified_mask_checks.py`. It passes 80,685 primitive map-entry comparisons, 1,104 boundary checks, 49,820 local-map comparisons, 29,568 replay outputs and 240 exact-rational predictor checks. All inputs are synthetic. Main L=32, P=16 runs use `F=state_bits+12` fractional bits and show at most one deletion/update; coarse F=3 stress reaches 96. Columbia formulas at 17 bits reproduce the audited arithmetic model; their 32-bit widths are proposed extensions. The host executes sequentially: its prefix topology exposes mathematical parallelism, not routed hardware performance. Interval composition is not associative as interval sets; each chosen tree still encloses its exact affine composition.

## Exact local execution choices

**Candidate representation: local masks with bounded deletion.** Set `m=D-A` and `R=floor((D-1)/m)`. The enclosure motivates domains of width near R. For each block, obtain a certified absolute entry interval `[lo,hi]` of width `W=hi-lo<=R`. Initialize its map to the identity: base `b=lo` and a W-bit mask of ones marking the initial adjacent thresholds. No per-event predictor or residual-offset storage is needed: stream the original updates through this map.

The map's current contiguous image has width `k=popcount(mask)<=W`. Because `m*k<=D-1`, one update reduces that width by zero or one. Specifically, set `b_new=floor((A*b+C_i)/D)` and `r=(A*b+C_i) mod D`. At image offset `j`, the update is `b_new+j+floor((r-m*j)/D)`. The only possible deleted rank is `j*=floor(r/m)+1`, when `j*<=k`. Clear the `j*`th set bit of the old mask and update the base. The mask still locates thresholds in the original entry interval. This avoids evolving every candidate or walking inverse thresholds.

The critical physical operation is **selecting a set bit by rank**, followed by clearing it. Compare a small combinational select network, pipelined population-count tree and several-cycle update; charge their feedback latency. For `m=1`, deleted-rank calculation is trivial; for 61/64, it divides by three. Generic coefficients therefore do not automatically give division-free construction. Parallel comparisons with `m*j` are another bounded-size implementation. Wider certified domains admit multiple deletions per event, bounded by `ceil(m*k/D)`; support a small cap or fall back. Initial domain widening from certified predictor rounding must be charged here rather than forcing every block into the one-deletion theorem. Saturation needs an additional case because clipping can delete many levels at once.

The prototype checks this derived mechanism numerically; circuit cost and priority remain open. The underlying bitvector rank/select representation and convergence principle are established. The plausible contribution is a useful bounded-deletion circuit/schedule. Boundary lookup at `s` is `b+popcount(mask & ((1<<(s-lo))-1))`, with the bit convention fixed. It must reject out-of-domain entries. Every-event outputs still require replay or stored histories.

**Stronger comparator: shared-base relative ranks.** Store `F(lo+i)=b+u_i`, omitting constant `u_0=0`. Each sample performs one full-width base/remainder update; ranks update by `u_i+floor((r-(D-A)*u_i)/D)`. With one deletion this is only `u_i-[u_i>=j*]`, using a common threshold. Parallel narrow lanes avoid mask rank/select feedback. Width 63 uses 378 rank payload bits versus 63 mask bits; this is not a physical area/timing result. [representation_checks.py](representation_checks.py) verifies both on identical certificates. This comparator must precede any claimed advantage over tables.

**Generic forward candidate table.** For `M` certified integer entries, evolve sorted candidates, merge equal states and retain entry selectors. This takes `sum_j m_j` separate state updates for active counts `m_j`, plus selector/compaction work. It is a useful generic baseline, but counting these as independent full-width transitions does not describe the stronger shared-base design above.

Store only candidate exit values and selector information initially. After resolving actual block boundaries, replay once to emit every exact output. Storing every candidate's entire trace can remove replay but costs up to `M*L*w` bits and corresponding write bandwidth. Merging shares future evolution; it does not reconstruct the different outputs emitted before the merge. A practical first design should replay rather than invent a large trajectory-history format.

**Local backward thresholds.** Run local endpoints, then construct only thresholds relevant to that domain. For the floor-affine step, a target crossing has predecessor `ceil((D*t-C_i)/A)`, with correct legal-domain and unreachable sentinels. The inverse divides by `A`; power-of-two forward division does not make it a shift. [Granlund and Montgomery](https://gmplib.org/~tege/divcnst-pldi94.pdf) establish exact invariant division via multiplication, including signed conventions. A specialized constant divider is a baseline, not a new contribution. Compare it with a reciprocal estimate followed by an exact remainder check/correction whose correction count is proven for the supported numerator range.

A possible hardware mechanism broadcasts each reverse input to several threshold lanes. Sorted targets may permit shared quotient/remainder updates. Backward walks expand differences: distinct interior thresholds generally do not merge, and later targets can have large gaps. Any cheap range scan therefore needs a proof and gap-handling cost.

**Bounded residual correction** can reduce datapath width, but its exact residual still depends on the preceding residual and quantizer phase. Table, unroll or sequentially execute that dependency; a prediction alone does not remove it.

**Direct execution.** Resource caps select serial or two/four-event exact unrolling when domains or maps are expensive. A first hybrid should have one understandable policy, such as forward execution below an active-state budget, thresholds below a threshold budget, and direct execution otherwise. Do not initially build three sophisticated adaptive engines and attribute their entire combined cost to whichever wins each block.

## A cycle and port model worth implementing

Let `P` blocks of length `L` form a group, `V` exact lanes serve each block, and `q_f` be forward dependent-transition latency. With one-cycle transitions and all active states held in registers, a broadcast forward engine can take approximately `sum_j ceil(m_j/V)` cycles per block, plus load, merge and table-write cycles. For `q_f>1`, require enough independent candidates to fill that pipeline, or insert stalls. A pipelined lane's independent-operation II is not its same-candidate recurrence II.

A concrete **analytical example**, not an implementation estimate: `P=4`, `L=128`, eight candidates and two forward lanes per block, without merges, takes 512 construction cycles at one transition/cycle. Replay adds 128 cycles and two-cycle boundary lookups add eight: `512/648=0.790` events/clock before prediction and interfaces. By contrast, a mask engine with a genuinely one-cycle dependent update takes 128 construction cycles, giving `512/264=1.939` events/clock with the same replay/lookup assumptions. A two-cycle mask update reduces this to `512/392=1.306`. A two-event unroll is therefore a serious competitor. Separate construction/replay engines could overlap groups, but need additional resources and banking; a faster stage interval cannot be inferred from the summed schedule.

Prediction can change those numbers decisively. The prototype computes lower/upper offset recurrences over all L events before scanning summaries. P independent prediction workers take at least L dependent-update slots; one shared worker takes PL, with both endpoints charged. For P=16, Hillis-Steele uses four levels and 49 combines, plus one combine for group carry. One shared engine pays about 50 initiation intervals plus pipeline/barrier overhead, not four clocks. A straightforward combine has four products; fixed gains permit precomputation and constant arithmetic. F=29/44 implies gain widths F+1 and conservative offset widths w+F+1: 47/77 bits, with full products up to 77/122 bits. Retain four endpoints per summary plus scan scratch, certificates and masks. Prediction overlaps input collection only with a demonstrated lane/port schedule; otherwise its pass adds to construction and replay.

The 200 products counted for P=16 describe only 50 interval compositions. Prefix-to-carry applications add 32 products and the final carry application adds two, before constant/identity specialization. These additional 34 products are now recorded. The local-table approach resolves boundaries in P sequential lookups; an unimplemented logarithmic composition tree is optional. Synchronous memory reads, index arithmetic and lookup logic need their own schedule.

Use a phase schedule before overlapping anything:

| Phase | Required accesses and retained state |
|---|---|
| Fill/predict | Write parsed inputs; produce certified summary metadata; retain group initial state |
| Construct | One input read per active block/time step; broadcast to candidate/threshold registers; write compact exit table |
| Resolve | Read tables and pass exact exit to next block; obtain the next group's exact initial state |
| Replay | Independent block input reads and exact forward transitions; write per-block ordered outputs |
| Drain | Read outputs in original order at the promised output lane count |

Overlapping groups needs separate banks or nonconflicting time slots. A predictor reseeded from each exact group-end state waits for that boundary. Instead, the prototype carries a certified interval for the **global unrounded affine trajectory**, independent of exact resolution. Three 4,096-sample tapes pass across sixteen eight-block groups each. Separately, `uniform_capacity_bound()` uses exact rational error bounds: local offset-width propagation, the specified interval-prefix tree and a contracting carry recurrence `E_next<=G_hi*E+delta`. For fixed full groups P=16, L=32, F=w+12, it supplies all-input mask-width caps **15/21/63/127/33**, respectively for retention **15/16, 61/64, 63/64, 127/128 and .97**, at w=17 and 32, hence at most one deletion/update. This is a mathematical capacity bound under unsigned invariant inputs, the tested offsets and sufficient intermediates; partial groups need separate bounds. It establishes no hardware service guarantee. Charge carry feedback latency and do not repeatedly add the integer-rounding budget into the unrounded carry. Replay still consumes arithmetic/ports. The slowest stage determines group interval only with separate resources/buffers; shared phases add occupancy. Include collection, queues, processing, replay and drain in latency.

## Fallback is a service commitment

Cap candidate states, threshold count, construction cycles and queued groups. A failed or wide certificate must produce direct exact execution, backpressure or an explicit rejected-input condition. An approximate answer is not an exact fallback. Never discard original inputs until their exact outputs can be recovered.

Let good groups require `C_g` cycles and fallback groups `C_b`, including abandoned speculative work. With fallback fraction `p`, a nonoverlapped model has mean capacity `P*L/((1-p)*C_g+p*C_b)`. This is not a worst-case guarantee: unfavorable groups can cluster. State the all-fallback capacity and maximum service interruption. If construction is allowed `B` cycles before restart, worst-case work includes `B+C_direct`, unless an independent direct path has already made usable progress.

For online use, replay actual timestamped arrivals through a finite queue with this service model. Report maximum occupancy and output deadline misses. A finite FIFO cannot fix sustained offered load above all-fallback capacity. Buffered offline replay with backpressure is therefore the sensible first target; a live system needs a contractual burst envelope or enough baseline capacity for persistent adverse data.

## Device strategy and financial contracts

Use a moderately larger FPGA with plentiful independently banked RAM and a practical host interface for the first complete mechanism. This is an engineering recommendation, not a claim that a particular untested part will fit. Measure parser-to-feature kernel performance separately from host-to-host performance; preloaded RAM proves only the former. A larger device makes port and predictor experiments easier to observe, but its serial/unrolled baseline must receive the same device and interface.

Use UP5K later as a stress target. The [Lattice datasheet](https://www.latticesemi.com/api/document/download?id=51968) specifies 5,280 logic cells, eight multiplier blocks, 120 Kibit EBR and 1 Mibit SPRAM; package pins and routing matter as much as raw bits. Four [16K×16 SPRAMs](https://www.latticesemi.com/view_document?document_id=51966) are single-port, so their aggregate capacity does not provide arbitrary per-worker bandwidth. A 17-bit native EMA state also crosses the natural 16-bit memory width. Reserve ingress, output and bank counts before selecting worker count. The earlier device note contains the detailed banking audit.

The documented P=16 numerical case is not a straightforward fitting UP5K schedule: 16 simultaneous independently addressed 17–32-bit input words require 32 EBR banks in ordinary 16-bit-wide mapping, before outputs, versus 30 available. A phased/shared arrangement would need a different service model. Numerical validation does not establish device fit.

Two application contracts deserve separate results:

* **Every-event exact feature replay:** reproduce the specified integer state and every output in order. This is the primary comparison, with replay and full output bandwidth charged.
* **Every-event exact threshold decisions:** certify `s_i>=T_i` from enclosures when the whole interval lies on one side; resolve ambiguous events exactly. This may reduce output bandwidth and exact work. It still needs exact boundary state for future groups. A decision based on two correlated EMA states requires a sound bound on their difference; independent intervals may be too loose. Stateful hysteresis and positions add their own recurrence.

Existing FPGA finance makes “EMA trading on hardware” an inadequate headline: [Funie et al., ARC 2017](https://doi.org/10.1007/978-3-319-56258-2_14) already studies trading kernels, while [Asheim et al., CPA 2016, §3.1](https://www.wotug.org/cpa2016/preprints/09-preprint.pdf) includes financial EWMAs. Compare ordinary symbol partitioning, banked state interleaving and multiple independent horizons first. A hot single-symbol replay stream is a valid deliberately accelerated workload; aggregate exchange message rate is not evidence that one unresolved EMA needs that rate.

## Staged RTL learning and decision gates

1. **Arithmetic and verification.** Freeze coefficient, state range, price scale, offset rounding, initialization and output contract. Reproduce the exact serial integer model, exhaustively test small widths, and exercise negative differences, rails, sentinels and ties. Learn feedback latency and valid/backpressure behavior. Gate: every emitted value agrees with the reference.
2. **Fair baseline.** Build constant shift/add serial execution, exact two/four-event unrolling and per-symbol scheduling. Measure achieved routed clock, resources, same-symbol II, stalls and complete throughput. Gate: identify a concrete requirement these simple designs fail, or recast the project as an architectural comparison.
3. **Certificates before hardware scaling.** Measure predictor error, entry candidates, active-state counts, local K, inverse cost and metadata on real tapes plus adversarial constant/ramp/jump runs. Include initialization and price-range changes. Gate: certificate construction plus exact work has a plausible advantage under realistic lane/port caps.
4. **One complete group executor.** Use forward local tables as the reference, then implement the bounded-deletion mask if its proof and predictor budgets survive stage three. Add backward thresholds only when distributions justify them. Gate: cycle-accurate occupancy agrees with measurements, all fallback paths terminate and outputs remain exact.
5. **Sustained interfaces and queues.** Exercise partial groups, output stalls, hot-symbol collisions and long unfavorable runs. Gate: the promised arrival envelope meets capacity and latency with finite measured buffers; otherwise remain an offline accelerator.
6. **Research decision and UP5K port.** Compare equal-area throughput and area/energy at equal required throughput on the same platform. Publish negative regions as well as wins. Port a capped configuration to UP5K only after the mechanism wins elsewhere or the small-device constraint is itself the explicit research question.

The reproducibility bundle should pin source revisions and tool versions, hash tape excerpts, state event filtering/order and integer conversion, preserve seeds, and emit per-group CSV/JSON containing certificate widths, active work, K, chosen mode, wasted construction, service cycles, queue occupancy and output latency. Separate software counts, cycle simulation, synthesis, post-route timing and board measurements. Report p50/p99/max latency, sustained and burst throughput, LUT/FF/DSP/RAM, clock and interface bandwidth. No single ideal events/clock number substitutes for that bundle.

## Additional primary-source context and reading limits

[Strzodka and Göddeke, FCCM 2006](https://wwwold.mathematik.tu-dortmund.de/papers/StrzodkaGoeddeke2006.pdf) and [Sun, Peterson and Storaasli, 2008](https://www.ornl.gov/publication/high-performance-mixed-precision-linear-solver-fpgas) establish FPGA mixed-precision solver precedents, rather than exact recurrence execution. Reading was limited to the indexed author manuscript's introductory discussion for the first and the official abstract for the second; direct reopening of the first failed.

[*Interval arithmetic yields efficient dynamic filters for computational geometry*, 2001](https://doi.org/10.1016/S0166-218X(00)00231-6) explicitly uses interval certificates to accept exact geometric predicate results and otherwise invoke exact arithmetic; the publisher abstract was inspected. This is closer to threshold-decision filtering than numerical solver refinement. The new contribution must therefore be the particular recurrence certificate, representation, physical execution or service guarantee, supported by measurements. This targeted search did not establish priority or rule out a closer predecessor.

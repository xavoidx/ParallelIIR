# Proposed direction: certified local execution for exact financial feature replay

**Latest verdict:** the [third-pass audit](THIRD_PASS_VERDICT.md) found a stronger exact table baseline, closer deletion-generator prior art and prototype interface defects, which are now fixed. Valid-input arithmetic survived independent testing. The recommendation is a bounded comparative RTL study; bitmap superiority, algorithmic priority, financial advantage and publication readiness are not established.

6 November 2026. This is the main collaborator-facing proposal from the deeper literature, application and conceptual review. “Differentiated” here means distinct from existing research. The recommendation is a research hypothesis with a working numerical prototype, not a claim that publication or a hardware speedup has already been secured.

## The decision

**Investigate certified local execution of rounded financial features, comparing arithmetic-shared map representations before selecting an architecture.** Start with historical liquidity/price-feature replay. A possible contribution is a complete implementation with a useful precision/resource/service region. Finance supplies a concrete feature and accuracy criteria; real-tape value remains to be demonstrated.

This changes the original design in a useful way. Instead of starting every block with uncertainty over the entire integer word and walking backward once per surviving threshold, first bound the exact entry state using an independently computed affine prediction. Then maintain the small remaining transition map using shared base arithmetic and either a bitmask or a table of relative ranks. Both can use one forward pass. Resolve exact block entries and replay to recover every output. The bitmap's storage saving must be weighed against its rank/select feedback cost.

The intended paper claim is:

> For a specified class of rounded contractive recurrences, certified boundary intervals and shared arithmetic permit compact exact local execution. A complete implementation improves the throughput/resource/latency tradeoff of feature replay at financially acceptable precision.

The software supports the arithmetic mechanism and, for selected fixed configurations, a uniform mask-capacity bound. **The missing parts are primary-art closure, actual-market fidelity measurements and complete RTL performance.** The independent audit strengthens correctness confidence but weakens the novelty argument: elementary adjacent collapse is explicitly established mathematics, and a stronger relative-rank comparator removes the previous bitmap work-count advantage. This is a hypothesis to test, not yet a publishable result.

Use a larger available FPGA to establish the mechanism first if practical. Treat the iCE40UP5K as a later resource-constrained target, not as a requirement that forces us to ignore predictor or interface costs. A small learning implementation on that device is still useful even if a complete high-throughput financial system does not fit.

## Why the additional literature changes the proposal

The deeper searches found closer competitors, not a clear vacant field:

| Finding | What it changes |
|---|---|
| Exact nonlinear prefix hardware already exists for saturated accumulation | Function summaries and a prefix tree cannot be the headline novelty. |
| Restricted-entry speculation, FSM convergence, sampled maps, path fusion and dependent-bit repair are established | “Predict, reduce the candidate states, then correct” is too broad a contribution. |
| Parhi/Gu describe a pipelined IIR plus a finite-level compensation loop | Moving a wide linear computation outside a small nonlinear dependency is also an old idea. |
| Finite-chain literature supplies boundary encodings AND elementary adjacent-collapse generators with composition relations | Neither the bitmap nor the principle of deleting an ordered boundary is new. |
| FPGA financial EMA and Hawkes likelihood accelerators already exist | Neither “FPGA EWMA for finance” nor “parallel financial intensity evaluation” is enough. |

Key primary sources are [Papadantonakis et al., FPT 2005](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf), [Ko et al.](https://arxiv.org/html/1210.5093), [BoostFSM's primary extended abstract](https://asplos-conference.org/asplos2021/abstracts/asplos21-paper113-extended_abstract.pdf), [Qiu's dissertation, Chapter 5](https://escholarship.org/content/qt5d5997zb/qt5d5997zb_noSplash_e0f7642d800f38a8db085a4d422a733c.pdf), [Parhi/Gu's 2004 presentation](https://www.ieee802.org/3/an/public/sep04/parhi_1_0904.pdf), [Adeshola–Umar](https://arxiv.org/html/1303.7428), and [Guo–Luk's financial Hawkes accelerator](https://www.doc.ic.ac.uk/~swd10/fpl13cg.pdf). The [novelty review](NOVELTY_AND_COMPETITORS.md) records exactly which full methods, abstracts and slides were inspected.

The specific floor-remainder application below was not found in the inspected methods. That is a bounded search finding, and its algebra is simple. The deeper reading of [Fernandes 2024, §§2–3](https://arxiv.org/html/2407.05084) exposes precisely the elementary adjacent-collapse action used here. Significance must come from an effective implemented specialization, not a new deletion principle. The [priority audit](PRIORITY_RED_TEAM.md) also recovers detailed compensation-loop disclosure; the full 1991 quantizer-loop paper and several reconstruction methods remain unresolved comparisons.

## The conceptual mechanism

For a rounded scalar update

`s_next = floor((A*s + C)/D)`, with `0<A<D`,

let a parallelizable affine calculation follow the same recurrence without the floor. The exact integer trajectory stays within a bounded rounding-error distance of that ideal trajectory. With a separately certified implementation error for the affine calculation, we obtain a **guaranteed interval containing each block's exact entry state**.

The accumulated rounding uncertainty is bounded by `(D-1)/(D-A)` state units. For fixed retention this depends on the coefficient, not on whether the original state uses 17 or 32 bits. This matters financially: increasing fractional precision can preserve feature quality without forcing a map over billions of candidate integer states. It still increases arithmetic and predictor cost, and very long memory still produces a large uncertainty interval.

One candidate representation starts with an identity map on the certified interval, storing its minimum output and a bit for each adjacent input pair whose outputs remain different. The map stays monotone with a contiguous image. If the interval is narrow enough, one update merges at most one adjacent pair. Arithmetic identifies its rank; rank/select identifies the bit to clear. This constructs the map in one forward traversal.

The mandatory competing representation stores `F(lo+i)=base+u_i`, with small relative ranks. It shares the same full-width base/remainder calculation. In the one-deletion case each rank becomes `u_i-[u_i>=j*]`, using a common threshold and narrow compare/decrement lanes. It also requires one forward pass and avoids dependent rank/select. At width 63, it needs 378 rank payload bits versus 63 mask bits, omitting its implicit zero entry. This is a storage/timing tradeoff, not a demonstrated bitmap speed advantage. [Executable comparison](representation_checks.py).

For retention `(D-1)/D`, identifying the rank avoids general division. The rank/select network itself is real hardware, however, and its delay may become the new bottleneck. For other coefficients, such as 61/64, there is a small constant division or comparison problem. Wider certificates can require several deletions per sample; our prototype supports this and a hardware design must support or explicitly exclude such configurations.

The complete path is:

1. Prepare affine block summaries and certified boundary intervals.
2. Construct exact local maps with shared base arithmetic using the selected representation.
3. Resolve actual block-entry states using the known initial state and those maps.
4. Replay each block from its exact entry, returning every output in order.

Only boundary estimates are needed; we do not require a predicted value for every event. The predictor can carry an interval for its own global unrounded state across groups without waiting for the previous exact boundary. That carry has its own capacity and service constraints. The [mathematical companion](CONSTRUCTOR_AND_CERTIFICATES.md) proves the stated contract, gives the deletion rule, explains the fixed-group capacity bound and distinguishes it from physical performance.

This approach addresses constant-price cases that defeated the original hope of complete coalescence: a map can retain dozens of possible outputs yet still be maintained with bounded work per input. It does not need the market to supply random inputs that happen to erase all initial-state uncertainty.

## What we have actually demonstrated

The new [Python prototype](certified_mask_checks.py) and [JSON results](certified_mask_results.json) implement finite-precision outward interval prediction, a fixed prefix topology, exact masks, boundary resolution and full replay. They do not obtain certificates from the serial reference. The serial computation is used only to check the answer.

The persisted tests passed **80,685 primitive map-entry comparisons, 1,104 certificate checks, 49,820 local map-entry comparisons and 29,568 replay-output comparisons**, plus 240 checks of the predictor against exact rational affine boundaries. All input tapes are synthetic. Three longer runs exercise certificate carry across 16 groups. A separate analytical bound covers arbitrarily many complete groups for each supported fixed configuration under its stated arithmetic/input assumptions.

For blocks of only 32 samples, the one-tick-walk experiments give:

| Arithmetic | State width | Original full-domain exit width K, maximum | Certified entry width W, maximum |
|---|---:|---:|---:|
| Rounded 61/64 price EMA | 17 | 28,204 | 20 |
| Rounded 63/64 price EMA | 17 | 79,187 | 62 |
| Rounded 127/128 price EMA | 17 | 101,978 | 127 |
| Proposed .97 liquidity EMA | 17 | 49,456 | 32 |
| Same 63/64 rule at extended precision | 32 | 2,594,766,466 | 62 |

K and W are different quantities: original map exit width versus the new certified entry width. The point is the change in domain, not a direct speedup ratio. The 17-bit rounded price formulas follow the inspected Columbia arithmetic; the 32-bit version and integer liquidity port are proposed extensions. For P=16, L=32 and the chosen predictor precision, the uniform capacity calculation gives mask caps **21/63/127/33** for the four corresponding coefficients, all permitting at most one deletion per update. These are mathematical capacity bounds, not routed timing guarantees.

The earlier same-certificate example counted 27,361 updates for independently evolved, convergence-factored candidates versus 512 base updates and 144 rank selections for the mask. **That is not evidence against the strongest table baseline:** shared-base relative ranks also use 512 full-width base updates, with narrow parallel lanes. Their independent comparison passed 386,100 literal-table checks and 7,680 replay outputs. The physical tradeoff is unmeasured.

Common prediction costs in the original example include 1,024 wider offset updates, 200 unspecialized composition products and 34 additional boundary/carry application products. Replay adds 512 original updates. These are unlike operations, not equal-cost clocks. The result files now identify the omitted product category and qualify the generic-table counts.

The predictor is a major risk: the straightforward 32-bit example uses 44 fractional bits, offset quantities around 77 bits and products wider still. Fixed coefficients permit specialization, but a wide predictor can cost more than the simple integer EMA we are trying to accelerate. The winning implementation may use tighter error bounds, fewer guard bits, shared hardware or a different certificate method. These are optimization questions to measure, not assumed savings.

## The financial application to pursue

**Primary application: faithful historical execution of event-driven liquidity features**, with exact reproduction of a deliberately chosen fixed-point specification. The input is a decoded, ordered quote tape; book reconstruction is upstream. The first meaningful feature is an EWMA of displayed best-bid plus best-ask size, anchored by the published .97-retention liquidity example. Preserve duplicate-valued events, initialization, reset boundaries and every requested output. [Original HFT article](https://jamesstuchbery.com.au/assets/pdfs/online_algo.pdf).

The initial service test should be cold replay of a newly specified feature/retention with no reusable exact boundary checkpoints. Repeated unchanged-feature replay must also be compared against cached outputs or exact snapshots. Their original construction cost belongs in a cold-job comparison, while existing snapshots can have zero incremental preparation cost for a warm job.

Jane Street's October 2026 Flex Model article provides stronger production motivation than generic moving-average examples. It distinguishes event handlers that maintain history from evaluation requests, explains why equal-valued events cannot be silently discarded, and describes shared feature code for historical and live use. Its example and most values are floating point; it does not establish an integer-EWMA requirement or an FPGA bottleneck. It supports the relevance of faithful event-state replay. [Firm-authored article](https://blog.janestreet.com/flex-model-an-event-driven-feature-engineering-system/).

Use the native rounded Columbia price EMA as an exact-arithmetic control. Use quote liquidity as the main financial-fidelity experiment. Smoothed canonical order flow is a secondary proposed feature, with signed-arithmetic support added explicitly; the original OFI definition is an additive contribution, not an EWMA. [Columbia report](https://www.cs.columbia.edu/~sedwards/classes/2015/4840/reports/HFT2.pdf), [canonical OFI paper](https://arxiv.org/html/1011.6402v3).

Historical replay is useful without inventing a single live instrument producing hundreds of millions of events per second. It permits backpressure and block buffering. However, multiple instruments, days and horizons give ordinary independent parallelism. A one-state kernel win must be reported alongside the complete multisymbol workload and against that simpler parallelism.

The short-retention examples must also be challenged. At a fixed wall-clock half-life, greater actual selected-event rate requires retention closer to one, enlarging the certificate and mask. A hypothetical 50-million-event/s state with a 1-ms half-life has a rounding-uncertainty scale around 72,000 state units, not dozens. This is a derived stress example, not an observed demand. Faster historical playback preserves the recorded event semantics and does not itself require changing the coefficient.

**Do not lead with Hawkes fitting.** It is a valid later extension, but Guo–Luk already use recurrence-based FPGA likelihood evaluation and candidate interleaving. Time-dependent coefficients, timestamp ties, coefficient generation and logarithms also widen scope. Likewise, do not lead with an UP5K consuming an entire OPRA feed or immediate tick-to-trade decisions. Those require interface and latency evidence that this work does not yet have.

## The application experiment that could earn the claim

Keep three references separate: the high-precision financial estimator, the selected serial integer specification, and the accelerated exact executor. Integer versus high precision measures the numerical port. Executor versus serial integer must match exactly.

Start with official LOBSTER paired message/orderbook samples, then broaden to multiple symbols/days and activity regimes if initial results justify it. The public samples are old and small; they cannot establish modern production rates. The documented format must determine event ordering, price scale, hidden-trade/halt handling and empty-book sentinels. [Sample source](https://php.lobsterdata.com/info/DataSamples.php), [format](https://php.lobsterdata.com/info/DataStructure.php).

Choose the precision sweep and consumer before looking for favorable map results. For example, fit a displayed-depth gate on an earlier segment, freeze its threshold, and evaluate on a later segment. Report feature bias/tail error, gate disagreements and crossing displacement in events/time, stratified by distance from the threshold. A larger dataset can support a predeclared causal forecasting metric. This tests meaningful fidelity without claiming trading profit.

A depth gate establishes decision consistency, not financial usefulness by itself. Choose an independently justified forecasting or operational consumer and a quantitative acceptance tolerance before asserting application value. Also define the replay job that needs fresh computation: a changed recurrence/retention may require a new feature trace, whereas changing only a downstream decision threshold may be served by cached features. Profile the recurrence's share of that job and compare caching/snapshots as well as faster arithmetic.

Compare all of the following under their explicit contracts:

- High-precision/native floating execution and a parallel approximate affine implementation that meets the same financial tolerance.
- Best exact serial shift/add arithmetic and two/four-event exact unrolling.
- Ordinary symbol/horizon interleaving at the same device and memory budget.
- Original backward thresholds, convergence-factored forward tables, and especially shared-base relative-rank tables on the same certified intervals.
- The complete proposed executor, including all predictor work, masks, resolution, replay, transfers and exceptional cases.

The toughest application objection is: **if the approximate predictor already satisfies the consumer, why pay for exact correction?** A useful paper need not claim exactness improves forecasts. It can quantify the cost of preserving a selected deployment/replay contract, provided that contract has been justified independently. If approximate execution is sufficient and much cheaper, report that boundary clearly.

Report one-state and full-workload results; held-out data; constant/quiet periods; precision versus throughput; and total time including input preparation/output. Never tune coefficients or decision thresholds on the test tape to manufacture easy maps or apparent numerical disagreements. [SECOND_PASS_REVIEW.md](SECOND_PASS_REVIEW.md) develops this adversarial experiment and explicit failure conditions.

## Rough RTL roadmap and division of work

| Milestone | Collaborator's RTL work and learning objective | Research/data work in parallel | Gate |
|---|---|---|---|
| 1. Exact baseline | One rounded EMA with valid/stall/reset behavior; then exact small unrolling. Learn feedback timing, widths and quantizer placement. | Freeze the native control and proposed liquidity contract; implement data selection and references. | Every state agrees; baseline routed clock/resources known. |
| 2. Competing map engines | Start with retention 63/64. Compare a shared-base relative-rank table and a bounded bitmap. Learn representation invariants and feedback versus independent-operation II. | Supply identical certified domains; review compensation loops and adjacent-collapse generators. | Exhaustive agreement and measured storage/timing justify a representation; no assumed bitmap win. |
| 3. Certificate engine | Fixed coefficient/block length; directed rounding and documented intermediate widths. Start with a simple scheduled prefix implementation. | Derive configuration-specific capacity bounds and run precision/fidelity sweeps. | Hardware intervals enclose reference values; predictor cost is charged and plausible. |
| 4. Complete group | Combine certificate, construction, exact resolution and replay; include output order and partial groups. Learn memory banking and phase scheduling. | Test all baselines and record per-phase work; repeat on real tapes. | Complete measured throughput, not just constructor speed, beats a relevant exact alternative. |
| 5. Sustained execution | Carry predictor certificates across groups, allocate banks, handle backpressure and resets, verify bounded-capacity paths. | Replay arrivals into the measured service model; report queue/latency tails and unfavorable regions. | No hidden group dependency or port conflict; every output remains exact. |
| 6. Device/resource study | Specialize constants, share or replicate stages, then attempt a capped UP5K implementation if justified. | Compare equal-service resources and equal-budget throughput; document financial and algorithmic limits. | A meaningful Pareto improvement survives complete interfaces and simpler interleaving. |

Do not begin with an exchange parser, full trading strategy, adaptive bar generator or multiple recurrence types. They obscure whether the new constructor works. Do not build a large parallel array before timing one mask engine and one certificate engine. A pipelined multiplier's independent II is not its feedback II, and four SPRAM banks are not an arbitrary number of worker ports.

The [detailed RTL note](RTL_FEASIBILITY.md) supplies phase/port accounting, example schedules, group-carry constraints, fallback obligations and UP5K limits without prescribing VHDL. Reuse whatever suitable board is already available; a device purchase is not required to complete the next software and synthesis gates.

## What would make this publishable—or stop it

A convincing hardware/architecture paper should deliver three things together:

1. **A specific contribution beyond old ingredients:** a useful implemented specialization/schedule, compared with restricted-state, compensation and shared-rank execution. An adjacent-boundary deletion identity alone is insufficient.
2. **A complete implementation improvement:** sustained exact throughput or fewer resources at a specified service level, against strong exact unrolling/interleaving and with predictor, memory and replay included.
3. **An application operating region:** a justified precision/horizon on real financial inputs, with faithful output semantics and approximate alternatives disclosed.

The correction-domain bound and one-pass shared arithmetic are useful foundations, but a small algebraic observation plus synthetic counts is not a finished paper. If wide certification dominates, or neither representation beats exact unrolling/interleaving in the complete schedule, stop or narrow the acceleration claim. If bitmap savings disappear against shared ranks, choose the table rather than protect the original design. Any remaining publication claim must identify a substantive implemented contribution and application value.

This remains a useful RTL problem-solving project under either outcome. It exercises exact arithmetic, alternative representations, certified approximation, memory scheduling, verification and measurement-driven architecture decisions. Those learning outcomes do not depend on a promised paper acceptance.

## Reading order

1. **This proposal, then the mathematical companion:** understand the selected contract and what the new code actually establishes.
2. **Papadantonakis et al. 2005 and Parhi/Gu 2004:** exact-map hardware and the older compensation-loop idea. Obtain Parhi's full [1991 quantizer-loop paper](https://doi.org/10.1109/31.135746) through available institutional access before a novelty claim.
3. **Ko et al.; Mytkowicz et al.; PBS/BoostFSM:** restricted states, convergence and repair. [Mytkowicz primary paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf); other links above.
4. **Adeshola–Umar and Cox et al.:** boundary encoding and conservative quantized-filter analysis, respectively. [Cox primary manuscript](https://arlencox.github.io/papers/filters.pdf).
5. **Loveless–Stoikov–Waeber, Flex Model and LOBSTER format:** financial feature meaning, event semantics and the reproducible input contract.
6. **Funie et al. and Guo–Luk:** existing financial FPGA acceleration and strong application baselines. [Funie DOI](https://doi.org/10.1007/978-3-319-56258-2_14); Guo–Luk above.
7. **Device memory/DSP guides after choosing the first implementation:** the [previous FPGA audit](../FINANCIAL_EWMA_FPGA.md) links the primary UP5K guides and distinguishes component specifications from achieved timing.

Evidence bundle: [novelty review](NOVELTY_AND_COMPETITORS.md), [financial workload review](FINANCIAL_WORKLOADS.md), [adversarial application review](SECOND_PASS_REVIEW.md), [RTL feasibility](RTL_FEASIBILITY.md), [proofs/checks](CONSTRUCTOR_AND_CERTIFICATES.md), [executable prototype](certified_mask_checks.py), [results](certified_mask_results.json).

Actual-market numerical results remain outstanding. A public sample download was attempted, but the environment's network restriction and rejected sandbox escalation prevented it. No synthetic trace is presented as market evidence. The repository contains the complete conceptual proposal and numerical prototype; these files do not claim to implement or measure an FPGA accelerator.

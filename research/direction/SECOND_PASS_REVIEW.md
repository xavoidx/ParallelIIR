# Adversarial finance review of the certified forward-mask direction

2026-11-06. Application review of the proposed boundary-certified, forward deletion-mask executor. Its proofs, arithmetic implementation and measured hardware costs are separate work. This review assumes neither a speedup nor priority over earlier mask/map methods. The proposed pipeline is: affine prefix prediction with directed error bounds; construction on certified boundary intervals; boundary resolution; exact replay of requested states.

**Recommendation:** frame finance as a demanding, reproducible evaluation domain for the *cost of preserving a selected quantized event-state contract*. The plausible contribution is a certified execution method with a measured precision/resource/throughput region and clear failure boundaries. Do not frame the work as satisfying an established industry's demand for bit-exact EWMA or as solving live tick-to-trade latency.

## The hardest objection: why correct the predictor at all?

An efficient affine/float prefix computation is already part of the proposal. If its approximate values preserve every meaningful downstream decision, its exact correction may have no financial benefit. An argument that minute numerical errors *can* alter an arbitrarily positioned threshold is insufficient: nearly any approximation can fail that construction. The consumer, scale and tolerance must be specified independently of the observed disagreements.

There are three distinct contracts:

| Contract | Honest value of exact execution | Main challenge |
|---|---|---|
| Reproduce an existing, documented integer feature | Equivalent outputs enable execution substitutions and regression checks | Find or deliberately qualify a useful feature; weak educational demonstrations do not establish a production rate |
| Deploy a new fixed-point feature and use the same semantics historically | Historical/implementation agreement separates execution bugs from the numerical-port decision | Show the port retains acceptable financial behavior; integer exactness does not make it a better estimator |
| Compute a real-valued estimator within financial tolerance | Exact integer reproduction is optional | A native float recurrence or approximate parallel scan may dominate the complete accuracy/cost frontier |

The second is sufficient for a legitimate research application. The third must remain in the comparisons. If a high-precision float implementation meets the consumer's tolerance and is cheaper, disclose that result rather than imposing bit-exactness after the fact.

Jane Street's Flex Model supplies strong evidence that preserving event history and aligning historical/live feature code matter. Its published worked example and most values are floating point, however. It does not establish that our integer arithmetic or masks are required. [Previously reviewed primary article](https://blog.janestreet.com/flex-model-an-event-driven-feature-engineering-system/).

## What the new design fixes, and what it still owes

Certified narrow intervals could make cost depend on accumulated rounding uncertainty instead of the entire legal state range. That is a substantial improvement in the *hypothesis*. It does not establish that exact correction is cheaper than direct execution: the predictor has already traversed the tape, and certification, mask updates, boundary resolution and full-output replay still consume work and bandwidth.

For finance, the relevant question becomes: **at a precision that preserves a predefined consumer, how much additional resource or time is needed to preserve every intermediate quantizer exactly?** Report the measured complete result against the cheapest adequate approximate method and the fastest exact direct method. A useful exact design need not beat the approximate method; its extra cost must be explicit.

The proposed uncertainty scale of approximately \((D-1)/(D-A)\) still becomes large for long memory. This is especially relevant when a fixed wall-clock horizon is sampled at a high event rate. Do not choose a short horizon merely to obtain one-deletion updates. Conversely, high state precision may enlarge the full legal domain while leaving rounding uncertainty relatively narrow; that is a good reason to sweep precision rather than benchmark only very coarse states. State whether interval “width” means endpoint difference or number of candidate values, and include all endpoint/tie effects in actual capacities.

Every price/quote row, every selected feature update, every output request and every downstream decision are different counts. Duplicate-valued events still update an event-time smoother. Skipping their updates changes the selected contract. Sparse consumer requests can reduce output/replay work only through a proved execution schedule; a boundary-only throughput number cannot represent an all-event feature trace.

## A nontrivial experiment that could establish usefulness

Use a recorded quote tape with original event IDs and timestamps. The official LOBSTER samples provide paired message/orderbook files; they are suitable for a small initial experiment, with the provider's format and distribution terms retained. This session did **not** obtain an actual-market numerical pilot. The samples are old and small, so a later multi-day/multi-symbol study is necessary for broader workload claims. [Sample page](https://php.lobsterdata.com/info/DataSamples.php), [format](https://php.lobsterdata.com/info/DataStructure.php).

Choose the first experiment before inspecting map success:

1. **Feature:** displayed-depth EWMA at retention .97, following the existing application anchor, plus several declared neighboring/longer horizons. Include a price EMA as a low-variation control and a smoothed canonical quote-flow contribution as a proposed extension. The original canonical OFI is an interval sum; smoothing is our choice. [Original OFI definition](https://arxiv.org/html/1011.6402v3).
2. **Consumer:** a depth gate whose threshold is fitted from an earlier training segment using a declared quantile or a fixed, externally meaningful depth threshold. Freeze it for the test segment. Separately fit a small causal next-return model if the dataset is large enough. Do not optimize the gate to create integer/float disagreement or select a horizon to produce easy masks.
3. **Arithmetic:** sweep state LSB and coefficient format. Keep a high-precision causal reference, native float, a genuinely parallel approximate affine scan, serial exact integer execution, exact unrolling, instrument striping and the certified executor. The approximate scan need not reproduce serial floating-point bit patterns: it must meet the same financial tolerance.
4. **Fidelity:** measure feature bias/tail error, saturation, gate disagreement and crossing displacement. Stratify disagreement by distance to the frozen decision threshold and by activity regime. Compare actual decisions to the high-precision reference as well as to the chosen integer reference. Use held-out future observations for any predictive score; keep same-interval price impact separate from forecasting.
5. **Execution:** include prefix construction, directed-bound maintenance, interval/mask construction, boundary resolution, replay, fallback and data movement. Report single-state throughput, original multisymbol mix, all-event output and sparse evaluation modes separately. Show the distribution of certified interval sizes, lost levels/update, mask population, exceptional blocks and buffer occupancy.

A meaningful positive finding would be: at a precision chosen by the declared fidelity criterion, exact execution beats equally exact direct alternatives in a measured operating region while preserving all integer outputs. Financial decision disagreements between integer and higher precision may be zero; that is acceptable if numerical-port fidelity is demonstrated and the claimed contribution remains exact execution. A result in which approximate execution is sufficient is also scientifically useful, but weakens a finance-specific argument for paying the exact-correction cost.

## Independent parallelism must receive its best case

Replay rarely offers just one state. Instruments, days, decay horizons and parameter candidates often provide ordinary parallel work. A narrow one-state kernel win can disappear when many small serial engines fill the machine, or when a CPU vectorizes across feature states. Compare equal total resource/memory budgets and identical output obligations. Report a one-state result as a dependency experiment and the full mix as application relevance.

Hawkes parameter fitting is a particularly severe test of this point. Guo–Luk already interleave parameter candidates and exploit consecutive-iteration parallelism in an FPGA likelihood engine. Fixed-decay exponential sufficient statistics can also be reused across some parameter variations. An intentionally isolated candidate is useful for measuring dependency costs, but is not a demonstrated fitting workload advantage. [Previously reviewed full manuscript, §§3–5](https://www.doc.ic.ac.uk/~swd10/fpl13cg.pdf).

Model selection, changed decision thresholds or new downstream weights do not automatically justify repeating the recurrence: caching an already generated feature trace may be cheaper. If every parameter change alters the retention, maps generally need reconstruction. Measure the actual reuse pattern rather than amortizing construction over hypothetical repetitions.

## Failure conditions that should remain visible

- No adequate precision/horizon region has small enough certified intervals or cheap enough mask maintenance.
- Directed prediction and exact replay cost more than exact unrolling or striping at the achieved clocks and memory schedules.
- The complete workload is limited by decoding, book reconstruction, coefficients, transfers or output volume; recurrence acceleration gives negligible job improvement.
- The consumer accepts approximate prefix values at substantially lower total cost, and no independent reproducibility/deployment requirement motivates exactness.
- Success appears only after selecting favorable blocks, consumer thresholds, symbol subsets or short horizons using the test tape.
- A claimed live use cannot tolerate buffering or fails on an extended unfavorable run. Backpressure makes offline replay valid; it does not create a bounded-delay live service.

The strongest prospective paper claim is therefore conditional and testable: **certified boundary intervals enable an exact forward construction whose measured cost is governed by rounding uncertainty and actual local state-map losses, with financial event-state replay demonstrating where that advantage survives realistic precision and independent-state baselines.** Establish the algorithmic distinction against prior exact-map construction separately. Finance supplies interpretable fidelity tests and realistic correlated inputs; it need not supply an invented 100-million-events/second scalar demand.

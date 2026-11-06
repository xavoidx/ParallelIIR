# Financial EWMA and the small-FPGA opportunity

6 November 2026. Follow-up to the original literature review, prepared on branch `fried`. This is the main shareable financial report; the linked application, arithmetic and device notes supply deeper source audits. New experiments below are exact-integer software checks with synthetic inputs. No exchange capture, financial backtest, synthesis, placement/routing or board measurement was performed.

## Conclusion

**Financial EWMA is a legitimate application family for this project, and the earlier search was too narrow.** There are published tick-level liquidity estimators, trading-framework tick EMAs, FPGA trading papers, and explicit rounded integer financial EMA implementations. The original finance discussion looked principally at daily RiskMetrics and wrongly treated the absence of an audited production integer implementation as grounds to dismiss a new fixed-point application. A useful new implementation need not inherit an existing bit-exact requirement; it needs suitable accuracy and a measurable system advantage.

**Processing more than one financial event per FPGA clock is possible in principle. Whether this exact block-map method enables a useful iCE40UP5K system is still conditional.** The promising setting is buffered feature generation, accelerated replay, reconciliation or a companion processor behind an existing feed handler. A self-contained UP5K receiving a complete high-rate exchange feed and making immediate trading decisions is not supported by the evidence. Input/output bandwidth, same-state event rate, quantization, memory ports, construction work and added delay all matter.

The strongest next experiment is to reproduce one documented integer price EMA, compare against a shift/add implementation and exact small unrolling, and measure complete map execution on recorded inputs. In parallel, evaluate an explicitly specified fixed-point version of the published quote-liquidity EWMA. Finance improves the project's application case; it does not by itself establish algorithmic novelty or an advantage over existing FPGA finance work.

## What finance actually supplies

| Application/source | Concrete evidence | Fit and limitation |
|---|---|---|
| Loveless, Stoikov & Waeber, *Online Algorithms in High-frequency Trading* (2013) | Quote-time smoothing of best-bid plus best-ask size; fitted old-state retention .97; liquidity prediction ten seconds ahead | Useful scalar feature. Integer format is a proposed implementation choice. Forecast horizon does not establish allowable processing delay. |
| Columbia FPGA stock-processing project (2015) | Unsigned 17-bit rounded EMAs with old-state coefficients 61/64, 63/64 and 127/128 | Directly compatible arithmetic reconstructed from report/HDL appendix. Educational project using daily closing-price stimuli, not proof of a live tick-rate bottleneck or compiled RTL equivalence. |
| Illinois FPGA feed-handler project (2026) | Price EMA with input weight 1/16 and correction truncated toward zero | Compatible threshold-map class, but requires the piecewise inverse derived below. State width/init not fully verified. |
| NautilusTrader | EMA handlers for quotes, trades and bars | Native practical tick application; uses floating point/FMA and mean warm-up. An integer port changes arithmetic. |
| Mlfin.py imbalance bars | EWMAs for expected signed imbalance and expected bar length | Known signed inputs can be smoothed, but the actual adjusted floating EWMA and state-dependent bar resets are not one fixed autonomous filter. |
| Funie et al., *Custom Framework for Run-Time Trading Strategies* (2017) | FPGA EMA strategies on buffered market datasets | Relevant existing accelerator and baseline. It uses single precision; generic “FPGA EWMA for trading” is already established. |

Sources: [ACM article](https://queue.acm.org/detail.cfm?id=2534976), [inspected article PDF](https://jamesstuchbery.com.au/assets/pdfs/online_algo.pdf), [Columbia report](https://www.cs.columbia.edu/~sedwards/classes/2015/4840/reports/HFT2.pdf), [Illinois report](https://courses.grainger.illinois.edu/ece445/getfile.asp?id=25819), [Nautilus EMA source](https://docs.rs/nautilus-indicators/latest/src/nautilus_indicators/average/ema.rs.html), [Mlfin.py source](https://github.com/baobach/mlfinpy/blob/main/mlfinpy/util/fast_ewma.py), [ARC paper DOI](https://doi.org/10.1007/978-3-319-56258-2_14). Source-reading limits and precise arithmetic are recorded in [the application audit](FINANCIAL_EWMA_APPLICATIONS.md) and [the native-arithmetic audit](FINANCIAL_EWMA_PRIOR_ART.md).

A useful counterexample is DEBS2022: although its input is a financial tick stream, its challenge computes EMAs from **five-minute-window closing prices**. One inspected solution reports an I/O bottleneck. Raw tick volume therefore does not imply a difficult EMA feedback loop. [Challenge specification](https://vgate.cs.ucy.ac.cy/debs2022/pdfs/debs2022-54.pdf), [solution paper](https://vgate.cs.ucy.ac.cy/debs2022/pdfs/debs2022-26.pdf).

## Are financial streams actually faster than a small FPGA's clock?

Yes, aggregate rates can be. OPRA's March 2026 capacity notice gives July 2026 targets of **16.134 million messages per 100 ms** and **1.824 million per 10 ms**, equivalent to **161.34 and 182.4 million messages/s** over those intervals. Corresponding bandwidth targets are 45.21 and 51.1 Gbit/s. These are projected maximum capacity-test rates for one aggregate stream, not measured sustained traffic or one security's EWMA demand. The same table gives a per-output-line maximum of 625,000 messages/100 ms, or 6.25 million/s. Redundant copies are not additional independent observations. [Official OPRA notice, p.1](https://cdn.opraplan.com/documents/notices/OPRA_Capacity_Test%20Reminder_041126.pdf).

Do not equate network bits/s with state updates/s. For illustration, Nasdaq ITCH's unattributed add-order body is 36 bytes and delete-order body is 19 bytes. A hypothetical 10-Gbit/s payload composed entirely of those messages would have ceilings of about 34.72 or 65.79 million messages/s **before framing and transport overhead**. Neither ceiling is an observed market rate. A feature may update only on selected trades, changed best quotes or completed windows. [Official ITCH specification, §§1.3.1, 1.4.4](https://nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf).

The evidence needed for our architecture is more specific: how many consecutive events update **the same unresolved state**? Thousands of independent symbols can be dispatched to separate states and interleaved. Multiple EMA horizons also provide ordinary independent parallelism. A market-wide statistic or a single hot symbol can retain a dependency, but we have not yet measured such a stream whose required service rate defeats the best simple UP5K implementation.

For a captured tape, replay can deliberately run faster than its original arrival rate. That is a concrete proposed workload, with no need to claim that a single live symbol naturally produces 100 million ticks/s. A replay accelerator must still beat per-symbol partitioning and other existing CPU/FPGA methods on the complete job.

## Exact arithmetic changes the performance assessment

Write retention as `a=A/D` and input weight as `1-a`. For a normalized integer EMA:

`s_next = floor((A*s + (D-A)*x + rounding_offset)/D)`.

Use wide intermediates. With a valid rounding rule and bounded prices/state, convexity keeps this update in range; saturation is not normally doing the work. The original WIP's additive `floor(a*s)+x` is not automatically this normalized financial EMA. Its current `FilterSimulation.py` also uses floating coefficients/inverse arithmetic, so the independent integer script below is the reference for these experiments. The earlier hard-coded four-bit clipping defect was fixed in the fetched checkout; this follow-up does not claim that defect remains.

For native Columbia arithmetic, examples are `(63*s+p+32)//64` and `(127*s+p+64)//128`. These preserve the actual intermediate rounding. With a power-of-two denominator and `A=D-1`, the forward update can become subtraction, shift and addition. The serial baseline may therefore be much cheaper than a generic multiply-based IIR. Conversely, the backward inverse divides by **A**, not D: a cheap forward shift does not imply a cheap inverse circuit.

The Illinois rule is `s+trunc((p-s)/D)`, with D=16 and truncation toward zero. It is floor-affine below p and ceiling-affine above p. Its exact crossing inverse, before domain guards, is:

- target `t <= p`: `ceil((D*t-p)/(D-1))`;
- target `t > p`: `ceil((D*(t-1)+1-p)/(D-1))`.

The branch uses the known price and target, so backward traversal does not require the unresolved forward state. This is a useful extension of the constructor, derived here; it is not a claim that the Illinois project implemented block maps. Small-domain exhaustive checks verified the inverse, adjacent output differences of zero/one, map evaluation and replay.

### New reproducible characterization

[financial_ewma_checks.py](financial_ewma_checks.py) produces [financial_ewma_results.json](financial_ewma_results.json). Run `python3 research/financial_ewma_checks.py` from the repository root. The executed checks passed **10,080 inverse comparisons, 4,960 adjacent-pair checks, 152,064 width-bound checks, 16,384 block/entry comparisons and 2,912 replay-output comparisons**. They validate these Python arithmetic models, not the external RTL or a trading strategy.

For a full legal entry interval of width W, the original convex floor map obeys `W_next <= ceil(A*W/D)`. Iterating this gives a conservative width bound. It can stop shrinking above zero. K is the number of thresholds, one less than the number of possible exit states.

| Contract | State bits | Bound plateau K | First L reaching that bound | Ideal eight-worker throughput / clock at that K |
|---|---:|---:|---:|---:|
| Retention 1/2, favorable control | 16 | 1 | 16 | 2.000 |
| Retention 15/16, proposed normalized mean | 16 | 15 | 139 | .444 |
| Columbia 61/64, native rounding | 17 | 21 | 194 | .333 |
| Columbia 63/64, native rounding | 17 | 63 | 521 | .121 |
| Columbia 127/128, native rounding | 17 | 127 | 958 | .062 |
| Liquidity .97, proposed integer port | 16 | 33 | 268 | .222 |
| Volatility .985, proposed integer port | 16 | 66 | 495 | .116 |
| Span 10,000, proposed unadjusted integer mean | 16 | 5,000 | 15,557 | .00160 |
| Illinois difference rule, chosen 16-bit state | 16 | 30 | 139 | .242 |

The last column assumes literal work `(K+3)L`, P=8 workers, equal one-cycle forward/inverse transitions, and no boundary, memory or output overhead. It is an **analytical schedule example**, not an FPGA throughput bound or result. Eight is not a measured number of fitting workers; shift-based workers need not consume DSPs, and wide/dividing workers may be expensive. For the piecewise Illinois rule we derived and checked the separate bound `W_next <= W-max(0,floor((W-D+1)/D))`, whose plateau is 2D-2 when the domain is wide enough.

Actual K can be substantially lower than the bound. At L=256, the synthetic checks found:

| Contract | Constant midpoint K | One-tick random-walk K | K range in 32 uniform full-range blocks |
|---|---:|---:|---:|
| Normalized 15/16, 16 bits | 15 | 0 | 0–0 |
| Columbia 61/64, 17 bits | 20 | 13 | 0–3 |
| Columbia 63/64, 17 bits | 2,325 | 2,328 | 2,322–2,330 |
| Liquidity .97, 16 bits | 33 | 31 | 24–31 |
| Illinois difference, chosen 16 bits | 30 | 13 | 0–0 |

All four stimulus families in the JSON are synthetic; the uniform-price inputs are particularly unlike ordinary price evolution. At L=4096, uniform inputs coalesced to K=0 for the first three native Columbia formulas, while constant prices retained K=20, 63 and 127. Thus both “finance will always have giant maps” and “random tests prove tiny maps” are unjustified.

For retention `(D-1)/D`, constant integer input in the floor model preserves D distinct fixed states away from the rails, hence K at least D-1 for arbitrarily long blocks. The difference-truncated version preserves 2D-1 fixed states, hence K at least 2D-2. This is an obstruction to guaranteed coalescence, not a claim that every real trace behaves that way. Longer blocks trade better typical contraction for more storage and delay.

### A concrete conditional opportunity

Take the proposed 16-bit normalized 15/16 filter, P=8 and L=256. If K=0, the literal equal-cost model gives `8/3 = 2.67` events/clock before overhead; if K=15, it gives only `8/18 = .444`. At a **hypothetical** 25-MHz implementation these are 66.7 and 11.1 million events/s. An incoming 50-million-event/s stream lies between them. A successful average-case design is conceivable, but a constant-price run can overload that schedule. A FIFO handles bounded bursts, not an indefinitely unfavorable workload.

The 2,048-event group alone takes 40.96 microseconds to collect at that input rate. Its raw 16-bit inputs occupy 4 KiB; double-buffering and complete output storage increase that before maps and bank granularity. This could suit buffered replay with backpressure. It is a poor argument for immediate order decisions unless their delay budget explicitly allows it. The coefficient, clock, rate and worker count here are experimental choices, not an observed financial deployment or mapped UP5K design.

This suggests a more interesting research question: can a hybrid exact executor use cheap direct/unrolled execution for unfavorable blocks and maps when their measured/certified K is small, while meeting a defined service guarantee? Constant-run shortcuts and certified narrow entry domains are also worth comparing. A hybrid's novelty and hardware cost still need checking; fallback must be included in throughput, not treated as free.

## What the iCE40UP5K can and cannot establish

The UP5K provides 5,280 logic cells, eight 16×16 multiplier blocks, 120 Kibit of EBR and 1 Mibit of SPRAM; QFN48 has 39 user I/O. Datasheet example timing, PLL range and global-clock limits are different from the routed clock of an EMA-plus-inverse-plus-memory design. Its listed architecture has no integrated 10G Ethernet transceiver/MAC. See [Lattice datasheet](https://www.latticesemi.com/api/document/download?id=51968) and [the detailed device audit](FINANCIAL_EWMA_FPGA.md).

There are three practical constraints beyond arithmetic:

1. **Delivering and returning events.** Two 16-bit samples/clock consume 32 payload pins on a direct SDR input bus, before control. A separate equally wide output bus would exceed QFN48's I/O. Serialization, DDR, shared buses or an existing external bridge can change this, but their timing and total system cost must be measured. A preloaded on-chip benchmark measures a kernel; it does not establish sustained external ingress and full-output delivery.
2. **Memory access.** Four single-port SPRAMs provide capacity but not arbitrary many-worker access. EBR banking can exhaust blocks before raw bits. Map lookup and ordered replay also consume ports. A cycle/port schedule is required; counting kilobytes is insufficient. [SPRAM guide](https://www.latticesemi.com/view_document?document_id=51966), [EBR guide](https://www.latticesemi.com/view_document?document_id=47775).
3. **The baseline can be excellent.** A shift/add EMA, exact two-event unroll or per-symbol interleaving may already meet the requirement. Artificially slowing the baseline clock demonstrates events/clock, not a cheaper or lower-power deployment. Compare each design's achieved clock, resource count and whole-system service level.

An external feed handler must cover PHY/PCS/MAC, packet sequencing, parsing, order-book reconstruction where needed and symbol dispatch. Moving the EMA behind such a handler is a plausible component experiment. If that handler is already a larger FPGA capable of the tiny serial EMA, explain why a second device provides value. No measured board-cost or power advantage is established here.

## Recommended application and RTL roadmap

**First financial benchmark: exact replay of a qualified rounded price EMA.** Start with Columbia's 61/64 and 63/64 rules. Preserve the 17-bit contract, rounding, initialization and every output. Use actual trade/price data converted with an explicit scale and range policy; applying these formulas to tick replay is our proposed use, not the original report's measured operating point. Public exchange trade archives are available, but raw trades and aggregated trades must not be interchanged because they change update count/order. [Official Binance archive specification](https://github.com/binance/binance-public-data).

**Second benchmark: quote-liquidity EWMA at retention .97.** Reconstruct best-bid plus best-ask size from a suitable capture. Define an integer port and validate numerical error and downstream feature/decision differences against a high-precision reference. This has a strong financial rationale, even though bit-exact integer reproduction is our chosen execution contract. Signed-flow smoothing and historical exponential-intensity evaluation are additional candidates described in the application audit.

For the RTL learning project, use these milestones:

1. **Freeze the contract and workload.** State widths, scales, rounding, warm-up/reset, missing events, timestamps, output cadence, supported coefficient range and allowed delay. Measure per-symbol and burst arrival rates from the selected tape. Report both native arithmetic and any proposed adaptation.
2. **Build the simplest correct baseline.** Serial shift/add or constant arithmetic, then exact two/four-event unrolling and symbol interleaving. Verify every emitted value and explore achieved clock versus events/cycle. Preserve every intermediate quantizer.
3. **Characterize maps before scaling hardware.** On the same real tapes, measure K versus block length and state precision, including constant prices and adverse runs. Compare full-domain and legitimately certified local-domain maps. Choose a capacity and document overflow/fallback behavior.
4. **Build one complete block executor.** Endpoint passes, inverse traversal, boundary evaluation and replay. Then add workers. Draw a cycle and memory-port schedule, including group-to-group dependency and output ordering. Synthesize the inverse rather than assuming it costs a shift.
5. **Integrate a realistic interface.** Reserve pins, buffers and memory banks first. Exercise backpressure, gaps, hot-symbol bursts and worst-case K. Report sustained rate and first/last-output latency, not just an internal loop's initiation interval.
6. **Make the research decision.** Compare equal-resource throughput and equal-required-throughput resources, complete energy/cost where measured, numerical accuracy for proposed integer ports, and bounded-delay/fallback behavior. If simpler RTL wins, the exercise still teaches valuable architecture and verification skills; narrow the research claim accordingly.

A convincing paper could claim a resource-efficient, exact financial feature executor with a measured useful operating region and a new constructor/scheduler/hybrid. It should not claim that EWMA finance, FPGA EMA acceleration, exact transition maps, or all faster-than-clock recurrences are new. The closest generic prior work remains in [PRIOR_ART.md](PRIOR_ART.md); the prior quantizer-loop comparison remains unresolved.

## Prioritized reading for the collaborator

1. **Loveless, Stoikov & Waeber (2013):** financial motivation, event time, fitted retention and the distinction between a useful feature and its execution contract. [Article PDF](https://jamesstuchbery.com.au/assets/pdfs/online_algo.pdf).
2. **Columbia (2015), relevant design and HDL appendix only:** the concrete rounded arithmetic to reproduce; do not treat the whole report as production validation. [Report](https://www.cs.columbia.edu/~sedwards/classes/2015/4840/reports/HFT2.pdf).
3. **Funie et al. (ARC 2017):** existing buffered financial EMA acceleration and a stronger application baseline. [DOI](https://doi.org/10.1007/978-3-319-56258-2_14), [inspected primary manuscript copy](https://scispace.com/pdf/custom-framework-for-run-time-trading-strategies-ltsj6e2dun.pdf).
4. **Papadantonakis et al. (FPT 2005), *Pipelining Saturated Accumulation*:** closest compact exact-map hardware precedent; understand the distinction between saturation-only maps and fractional quantization. [Author paper](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf).
5. **Asheim, Skovhede & Vinter (CPA 2016), §3.1:** a financial EWMA-to-VHDL example, useful for verification and dataflow practice. [Proceedings preprint](https://www.wotug.org/cpa2016/preprints/09-preprint.pdf).
6. **Lattice datasheet plus EBR/SPRAM/DSP usage guides:** resources, feedback paths and access constraints. Links and exact reading sections are in [FINANCIAL_EWMA_FPGA.md](FINANCIAL_EWMA_FPGA.md).
7. **OPRA capacity notice and ITCH specification:** learn to translate feed rates and record semantics into actual feature-update demand; links above.
8. **Headlands' engineering overview:** live strategy, capture, reconciliation and backtesting are distinct workloads with different delay budgets. [Firm-authored overview](https://blog.headlandstech.com/2017/08/03/quantitative-trading-summary/).

The detailed notes also cover Illinois's piecewise integer rule, Nautilus/LEAN arithmetic, adjusted EWMA in imbalance bars, and historical Hawkes intensity. Mutable source URLs should be pinned to a commit/version before claiming reproducibility of a native program. This review supplies stronger applications and a testable hardware hypothesis; it does not yet supply a measured hardware advantage.

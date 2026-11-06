# Financial EWMA: native arithmetic, prior art and reproducible candidates

Review date: 6 November 2026. This review distinguishes an existing financial algorithm, an existing fixed-point implementation, and an existing need for greater single-stream throughput. They are different levels of evidence. Financial usefulness does not require an external demand for bit-exactness: a new fixed-point implementation can be useful if accuracy, latency and cost are competitive. However, changing a floating/decimal program to fixed point is not exact acceleration of that original program.

## Main findings

There are **native fixed-point financial EMA examples**, including one whose rounded arithmetic fits the original floor-affine contract directly. Thus financial EWMA is more than an arbitrary DSP formula given a financial name. The strongest directly compatible source is a 2015 Columbia course project with integer-price EMAs and explicit per-update rounding. An Illinois 2026 course project documents a different integer EMA that retains monotonicity and adjacent increments of zero or one; preserving its arithmetic needs a piecewise inverse. Both are demonstrations, not evidence of an unmet production HFT requirement.

The bounded tick-sign use is mathematically attractive: scale `b_t in {-1,0,1}` to a signed fixed-point state and process a known tick tape. But actual open imbalance-bar generation has endogenous stopping/reset decisions and uses adjusted floating EWMA over trailing arrays. It is not just one autonomous fixed-coefficient scalar recurrence. A standalone quantized tick-sign feature is a reasonable new implementation candidate; claiming an exact drop-in accelerator for the entire existing bar algorithm would be false.

The best initial setting is **buffered replay, historical feature generation, feed catch-up or microbatch analytics**, where future records are already available and delay can be budgeted. Live latency-critical trading is more demanding: input buffering delays decisions, and the serial shift/add EMA baseline can already be exceptionally cheap. A tape with many securities also offers easier per-symbol parallelism. Any performance claim must establish the remaining same-symbol dependence and compare against that baseline.

## Primary sources and what their arithmetic actually does

### F01 — Abrams, Gazman & Guan, Columbia CS/EE4840 final report (2015)

[Institution-hosted full report and HDL appendix](https://www.cs.columbia.edu/~sedwards/classes/2015/4840/reports/HFT2.pdf). Reading: body §§2–3, rounding description, appendix stock-module declarations/update logic, report pp121–123. Student project, not production evidence.

Native states and prices are unsigned 17-bit integers. The documented EMA arithmetic reconstructs as:

- `s4' = floor((61*s4 + 3*p + 32)/64)`.
- `s32' = floor((63*s32 + p + 32)/64)`.
- `s128' = floor((127*s128 + p + 64)/128)`.

The appendix uses 23-bit sums for the first two and 24 bits for the third, then shift/slice and a rounding-bit increment. Full-range weighted sums fit these widths. Convexity keeps outputs within the input/state interval, so saturation is unnecessary. Names are inconsistent: the introduction says 8/32/128 while equations/code say 4/32/128; use coefficients as the reference. The extracted appendix contains malformed/incomplete HDL, so this is an arithmetic reconstruction, not independently compiled RTL equivalence. Incoming `stock_in` must remain stable through its staged computation; overlapping transactions need separate verification.

**Significance:** directly compatible native rounded financial arithmetic; no demonstrated throughput bottleneck.

### F02 — Sehgal, Jairath & Ghoshal, Illinois ECE445 final report (Spring 2026)

[Institution report](https://courses.grainger.illinois.edu/ece445/getfile.asp?id=25819), [project record](https://courses.grainger.illinois.edu/ece445/project.asp?id=12356). Reading: design/EMA equations, verification, limitations, timing/resource and module appendices. No public RTL link located; EMA-register width and exact initialization/reset logic remain unverified.

A custom 100-Mbps feed-handler demonstration uses 32-bit prices and `alpha=1/16`. Its documented update is `s+floor((p-s)/16)` for `p>=s`, otherwise `s-floor((s-p)/16)`. This rounds the correction toward zero, producing a deadband. It is not globally `floor((15*s+p)/16)`.

It is nevertheless monotone with adjacent increments zero/one. With `D=16`, its crossing inverse is `ceil((D*t-p)/(D-1))` for `t<=p`, otherwise `ceil((D*(t-1)+1-p)/(D-1))`, with domain guards. Convexity prevents arithmetic underflow/overflow if unsigned branch subtraction is implemented as documented. This is a derived extension, not verified source RTL. Crossover/cooldown logic adds state beyond EMA. The report describes single-cycle trigger evaluation; it does not establish an EMA bottleneck. Treat measured system claims as author-reported demonstration results, not independently reproduced guarantees.

### F03 — QuantConnect LEAN `ExponentialMovingAverage.cs`

[Native source](https://raw.githubusercontent.com/QuantConnect/Lean/master/Indicators/ExponentialMovingAverage.cs), [official indicator documentation](https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/exponential-moving-average). Reading: entire 120-line class; constructor, initialization and update checked. Mutable `master` URL, inspected on review date; no commit hash captured.

The state/coefficient use C# `decimal`. Default input weight is `k=2.0m/(1+period)`. After initial SMA warm-up, the update is:

`input.Value * _k + Current.Value * (1 - _k)`.

It emits zero before readiness and uses the initial SMA at `Samples==period`. There is no explicit floor or saturation. Decimal multiplication/addition semantics and evaluation order matter; the project does not currently model them. Choosing a fixed-point floor rule would therefore be a replacement numeric implementation, not bit-exact LEAN execution. Inputs become known from the price tape; standard fixed-period coefficients are independent of the unresolved EMA state. Reproduce warm-up separately before comparing complete traces. A public decimal implementation establishes practical EMA use, but neither an HFT update-rate requirement nor a need for FPGA block parallelism.

### F04 — mlfinpy `fast_ewma.py`

[Actual open implementation](https://raw.githubusercontent.com/baobach/mlfinpy/main/mlfinpy/util/fast_ewma.py). Reading: entire 43-line source. Mutable `main`, inspected on review date.

It allocates `float64` output, uses `alpha=2/(window+1)`, initializes the numerator to the first input, and iterates a decayed numerator plus input. A separately accumulated weight normalizes the result. Specifically the denominator adds powers of `1-alpha`; output divides numerator by that weight. This is adjusted EWMA, not the unadjusted scalar `alpha*x+(1-alpha)*y` during startup. No fixed-point rounding or saturation appears. A fixed-point numerator kernel could be implemented, but preserving its float64 outputs is outside the current theorem. Normalization, trailing-window restarts and caller behavior cannot be ignored when comparing to imbalance bars. This source is substantive executable code; the current mlfinlab public counterpart is not.

### F05 — mlfinpy `base_bars.py`

[Native bar/tick source](https://raw.githubusercontent.com/baobach/mlfinpy/main/mlfinpy/data_structure/base_bars.py). Reading: tick rule, imbalance selection, `BaseImbalanceBars._extract_bars`, `_get_expected_imbalance`.

Tick sign uses the price difference's sign, retaining the previous sign on unchanged prices; initial sign is zero. Tick imbalance is that sign, volume imbalance multiplies by volume, dollar imbalance also by price. Only tick imbalance is intrinsically bounded by one.

Bars form when absolute cumulative imbalance exceeds expected ticks times absolute expected imbalance. Formation updates expectations and resets counters. Expected imbalance calls EWMA on a trailing array whose effective window depends on available history. These choices introduce state-dependent sampling and resets; a fixed blocked scalar EMA cannot accelerate the whole algorithm unchanged. On a known tape, tick-rule preprocessing is independent of the downstream EMA; unchanged-price runs can be resolved by last-nonzero-sign propagation. That preprocessing suggestion is an algorithmic inference, not an implementation claimed in this source.

### F06 — mlfinpy `imbalance_bars.py`

[Native configurations](https://raw.githubusercontent.com/baobach/mlfinpy/main/mlfinpy/data_structure/imbalance_bars.py). Reading: `EMAImbalanceBars._get_exp_num_ticks`, default function parameters, constant-entry alternative.

Default EMA-imbalance APIs specify `num_prev_bars=3`, expected-imbalance window `10000`, initial expected ticks `20000`. The expected tick count is recomputed from a short trailing list of completed bar lengths and can be clamped by user constraints. This is **not** saturation after every tick-sign EWMA update. Constant-imbalance variants retain a fixed expected tick count, but bar boundaries and expected-imbalance updates are still endogenous.

These are reproducible native algorithm parameters. For fixed-point experimentation, a 10000-span EWMA has retention `9999/10001` in exact rational arithmetic, but choosing that integer rule does not reproduce the float64 adjusted implementation. Its slow contraction is a deliberately demanding test, not evidence that threshold maps will be compact for short blocks.

### F07 — Current public mlfinlab source: an access limitation

[EWMA stub](https://raw.githubusercontent.com/hudson-and-thames/mlfinlab/master/mlfinlab/util/fast_ewma.py), [bar stubs](https://raw.githubusercontent.com/hudson-and-thames/mlfinlab/master/mlfinlab/data_structures/base_bars.py). Reading: public files inspected directly. Their implementations are currently `pass` stubs despite extensive docstrings. They establish documented API intent, not verified arithmetic. This review uses executable mlfinpy instead. Do not cite present-day mlfinlab as if its private production implementation had been audited.

### F08 — Nasdaq TotalView-ITCH 5.0 specification

[Exchange specification](https://nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf). Reading: data types, order/trade price fields and buy/sell clarification. Retrieved PDF's revision is not independently pinned to the latest exchange release.

Price(4) represents integer prices with four implied decimal places; ordinary integers are unsigned unless specified otherwise. This supports a natural integer **input representation**, not an exchange-mandated integer EMA state or rounding rule. Price quantization and filter-state quantization are separate decisions.

For trade-sign studies, do not interpret every `Buy/Sell Indicator` as aggressor sign: the non-cross trade message's indicator is specified as always `B`, regardless of resting side. Reconstruct direction from suitable feed semantics/order-book state or use a documented tick rule. Feed parsing, order references, filtering, corrections and per-symbol ordering remain required before defining the recurrence input stream.

### F09 — Funie, Guo, Niu, Luk & Salmon, *Custom Framework for Run-Time Trading Strategies* (ARC 2017)

[Publisher DOI](https://doi.org/10.1007/978-3-319-56258-2_14), [full primary manuscript copy](https://scispace.com/pdf/custom-framework-for-run-time-trading-strategies-ltsj6e2dun.pdf). Reading: equations, §§4–6 implementation/evaluation; manuscript copy accessible, DOI fetch unavailable in this session. Primary paper text, not a review summary.

It implements FPGA trend-following strategies with EMA lengths 25, 100 and 200, and `alpha=2/(length+1)`. The evaluated static kernels use single-precision floating point. The paper reports one data point per clock and evaluates large buffered market datasets. Its main contribution concerns static/full/partial reconfiguration, not exact quantized recurrence maps.

This is a relevant stronger baseline/context than only course projects: FPGA financial EMA acceleration and buffered evaluation already exist. The paper does not establish a floor-rounded bit-exact alternative, and its stated pipeline throughput must not be taken as proof of the exact samplewise arithmetic/feedback schedule without implementation inspection. It weakens generic “FPGA EMA for finance” novelty while supporting buffered finance as a real workload class.

### F10 — J.P. Morgan/Reuters, *RiskMetrics Technical Document*, fourth edition (1996)

[Official MSCI-hosted document](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a). Reading: §5 recursive variance equations and daily example only.

The variance update is retained previous variance plus weighted squared return; daily examples use retention `lambda=0.94`. This is native financial EWMA use, but not a per-packet HFT requirement. A research integer variant can choose `A=47,D=50,C=3*q_t`, with `q_t` an explicitly quantized squared return. Computing `q_t` must not depend on unresolved variance, and its scale/bounds need separate definition. Exactness would be to that chosen integer kernel, not automatically to RiskMetrics software. The source does not require floor quantization or saturation. This is a credible broad-use comparison family, not the strongest case for high-rate single-stream acceleration.

## Concrete reproducible benchmark contracts

The following specify **what to implement**, not unmeasured throughput or production requirements. All calculations use sufficiently wide intermediates and mathematical signed floor/ceiling. Inputs are stored before the map construction. Use identical input tapes and initial states for serial and parallel runs.

| Contract | State/input domain | Update | Status |
|---|---|---|---|
| Columbia rounded price EMA32 | unsigned 17-bit `s,p` | `(63*s+p+32)//64` | Native arithmetic reconstructed from F01 |
| Columbia rounded price EMA128 | unsigned 17-bit `s,p` | `(127*s+p+64)//128` | Native arithmetic reconstructed from F01 |
| Illinois difference EMA16 | unsigned price domain with explicit chosen state width | `s + sign(p-s)*(abs(p-s)//16)` | Native documented recurrence F02; RTL widths unverified |
| Normalized tick-sign EMA | `s in [-Q,Q]`, `b in {-1,0,1}`, e.g. `Q=32767` | `floor((A*s+(D-A)*Q*b)/D)` | Proposed implementation of native feature idea F05 |
| RiskMetrics-style quantized variance | define nonnegative `q_t` and state bound explicitly | `(47*s+3*q_t)//50` | Proposed integer option inspired by F10 |

For tick-sign sweep choose input weights `1/16`, `1/64`, `1/128`, and `2/10001`. The last corresponds to the native 10000-span setting, not a rounded power-of-two approximation. Use initial states `-Q,0,Q` and actual tick-sign tapes plus transparent stress tapes: constant buy, constant sell, alternating signs, long sign runs and randomized signs. These stress tapes are synthetic, not claimed market distributions.

The normalized state interval is invariant without clipping: each update is a rounded convex combination of `s` and `Q*b`, so it stays in `[-Q,Q]`. This gives a small natural state domain independent of the absolute stock price. If fractional precision is increased, `Q` and the possible threshold count increase too; bounded inputs do not imply a tiny map. At slow forgetting factors, large maps or long block delays may remain necessary.

A subtle alternative is `floor(A*s/D)+b`. It has bounded integer inputs but is an **unnormalized leaky accumulator**, not the same scaled EMA as above. With slow retention and no fractional state bits it can exhibit severe deadbands/fixed-point effects. Do not use the smaller state range of one recurrence and the financial meaning of the other interchangeably.

For unsigned price EMAs, exploit convex invariance to avoid hypothetical saturation. Real input traces often occupy a much narrower price interval than the entire type; test both full-domain maps and legitimately certified local domains. A domain inferred from the tape must include every possible entry state actually admitted by the benchmark. Report local-domain construction cost and assumptions explicitly.

## Are affine-floor summaries a simpler exact alternative?

Real EWMA has a two-parameter affine block map and standard affine prefix scans. Replacing per-step rounded updates by the real block formula and one final rounding generally changes the integer machine. A fixed coefficient and bounded binary input alphabet do not restore closure under a single `floor((P*s+Q)/R)` summary. Their plateau placements can carry phase information from each intermediate rounding.

However, special cases can be much simpler: coefficient zero, complete coalescence, repeated identical inputs, tiny naturally reachable state domains, or recognized arithmetic orbits. The previously reviewed saturating-accumulator prefix construction remains relevant when the update reduces to a saturating translation. Check these shortcuts, small forward tables, exact unrolling and endpoint replay before treating thresholds as the winning representation. Exact bounded-input recurrences can also admit state-space enumeration much smaller than a full word-domain table.

The documented Illinois rule illustrates why widening scope by arithmetic proof can be useful. Its map can be rewritten as floor on `s<=p` and ceiling on `s>=p`. The inverse's branch condition uses the **target and known price**, not unresolved forward state; therefore each backward step remains direct. The generic threshold-map/replay framework survives while the one-step inverse changes. This is an extension derived for this review, not a claim that another finance project used threshold maps.

## What would make the finance application persuasive?

Measure throughput, first-decision delay, storage and resource cost on a known per-symbol tape. Include parser/sign preprocessing, any symbol demultiplexing, map construction, boundary resolution, replay and output order. Compare the whole workload against a tight shift/add integer serial loop/circuit, exact unrolling, forward tables, and ordinary affine scans when numerical tolerances allow them. Use a quantization-accuracy comparison against a higher-precision EMA if fixed point is a design option.

For a replay/backtest study, every feature value may be consumed later, so buffered latency can be acceptable; prove that this is the chosen use contract. For live triggering, document a real permissible delay and arrival envelope. Multiplying market-wide message rate by a serial feedback latency can be misleading when events are distributed across many independent securities. Conversely, one heavily traded symbol or a post-merge feature can retain a real scalar bottleneck; establish it with the tape rather than assume it.

No source inspected here establishes that a new threshold executor improves P&L, that exact integer semantics are an industry requirement, or that production HFT systems need this extra buffering. Those claims are unnecessary for an honest first paper. A credible claim is narrower: a useful, accurate quantized financial feature or native rounded kernel, evaluated on known data with complete execution costs and relevant latency constraints.

## Search log and limits

Queries included `FPGA finance exponential moving average fixed point high frequency trading paper`, `FPGA order flow imbalance exponential moving average fixed point`, `FPGA EWMA trading`, `trade sign EWMA`, `order flow imbalance exponential moving average`, `FPGA exponential moving averages financial`, `parallel EWMA exact`, `Custom Framework for Run-Time Trading Strategies`, and repository-specific LEAN/mlfinlab/mlfinpy searches. Further searches for the Illinois authors and `trigger_engine ema COOLDOWN_CYCLES` found the institution project/report but no public RTL. Network access from shell was unavailable; source inspection used the web tool.

The result is a targeted source audit, not a complete finance literature or patent search. Native source snippets were checked directly where accessible. Current mutable branch URLs should be pinned to commits before reproducible experiments or publication. No additional broad statistical use case was accepted as evidence of a high-rate bottleneck. No direct earlier publication of the proposed exact threshold-map EMA executor was located; that search result is not proof of novelty. The earlier mathematical/FSM/saturation precedents in `PRIOR_ART.md` continue to constrain all broad novelty claims.

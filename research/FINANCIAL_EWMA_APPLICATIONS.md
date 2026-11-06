# Financial EWMA applications: a deeper application audit

Evidence date: 2026-11-06. This supersedes the *breadth of the financial search* in `APPLICATIONS.md`; it does not change the scalar arithmetic theorem. Financial EWMA is much broader than daily RiskMetrics. Quote-time liquidity, tick-price smoothing, signed-flow expectations, and exponentially decaying event intensities are concrete applications. The question is which implementation benefits from exact block maps, rather than whether finance uses recurrences.

**Assessment:** there are credible mathematically compatible financial kernels and native educational FPGA integer implementations. The best near-term financial experiment is buffered replay/reconciliation of an explicitly specified integer feature, followed by quote-liquidity smoothing. Evidence does not yet establish that one live financial state must accept events faster than an iCE40UP5K's available implementation can process them, or that threshold maps would fit that device better than exact unrolling. Absence of an audited production implementation is an evidence gap, not proof that no compatible production use exists.

## Keep three claims separate

1. **Application relevance:** a published strategy, estimator, or real source code uses exponential recurrence.
2. **Arithmetic compatibility:** its particular state update is `clip(floor((A*s+C)/D))`, `0<=A<D`, or another proved monotone adjacent-step-0/1 map; all block inputs/coefficient choices are known before resolving the state.
3. **System advantage:** the same state has a measured rate bottleneck, tolerates the entire buffer/build/resolve/replay delay, and a complete map executor beats simpler exact alternatives within device resources.

A floating-point implementation establishes the first claim, not the second. A new integer port can nevertheless be useful: call it a proposed fixed-point financial specification and validate its financial fidelity separately. Bit-identical reproduction of that specification is then an honest engineering objective; it is not retrospectively a mandated exchange or production requirement.

## Concrete applications and native dataflow

### Quote-time liquidity and short-term risk

Loveless, Stoikov and Waeber's primary HFT article evaluates a quote-time EWMA of best-bid size plus best-ask size to predict liquidity ten seconds ahead. Its fitted retention is **.97**. Their volatility example instead samples in seconds and predicts next-minute realized volatility, with fitted retention **.985**. The worked online variance estimator carries a mean and a variance, and their pairs-regression example carries additional state; neither is one scalar filter as a whole. [F1: original ACM article](https://queue.acm.org/detail.cfm?id=2534976), [inspected PDF copy](https://jamesstuchbery.com.au/assets/pdfs/online_algo.pdf)

This directly corrects the earlier daily-only framing. For liquidity, `x_n=bid_size_n+ask_size_n` is available after book reconstruction and a scalar smoother is natural. In an integer implementation with retention `A/D`, choose a widened numerator `A*s+(D-A)*x`, its specified rounding offset, and explicit output range. Published .97 is a calibration result, not a native rational coefficient or fixed-point format. Do not silently substitute .9375 merely because it is cheap.

For volatility, an EWMA of **known squared returns** is a compatible scalar stage after return formation. A variance whose innovation is `(x-current_mean)^2` first needs the exact mean outputs; mapping both unresolved states with the one-scalar theorem is invalid. Materializing the mean stage, then constructing the variance stage is legitimate but adds work and buffering. Price differences and log returns also have different precision/preprocessing costs.

### Trade and quote price EMA in a real trading framework

NautilusTrader's inspected Rust EMA accepts `QuoteTick`, `TradeTick`, and bars. It uses `alpha=2/(period+1)` for the new input, seeds from an initial period's mean, and subsequently updates with `alpha.mul_add(input,(1-alpha)*old)`. State is `f64`, not an integer floor-and-clip machine. Non-finite inputs are skipped. [F2: EMA source](https://docs.rs/nautilus-indicators/latest/src/nautilus_indicators/average/ema.rs.html)

The hot recurrence fits mathematically with retention `1-alpha`, but warm-up, skipped events, resets and exact floating-point FMA behavior must be preserved for native compatibility. Period is measured in **calls**, hence trades for `handle_trade`, quotes for `handle_quote`, or bars for `handle_bar`; it is not intrinsically seconds. Feed and instrument subscriptions determine which events reach each state. An aggregate market-data rate cannot be assigned to every per-instrument EMA.

### Signed-trade imbalance, expected bar size, and toxicity-related sampling

Mlfin.py's EMA imbalance bars consume raw `(timestamp,price,volume)` ticks, with default expected-imbalance window **10,000**, initial expected bar length **20,000 ticks**, and **3 previous bars** for expected tick-count estimation. The expected bar size is clamped to configurable bounds. Tick, volume and dollar imbalance variants exist. These are financial data structures intended for subsequent feature generation. [F3: imbalance-bar source](https://mlfinpy.readthedocs.io/en/stable/_modules/mlfinpy/data_structure/imbalance_bars.html)

Its EWMA helper uses a decaying **unnormalized numerator** plus a changing normalization weight: `alpha=2/(window+1)`, `u_i=(1-alpha)*u_(i-1)+x_i`, output `u_i/weight_i`. Arrays/output are floating point. This is the adjusted finite-history average, not simply the usual constant-gain mean. [F4: helper source](https://github.com/baobach/mlfinpy/blob/main/mlfinpy/util/fast_ewma.py)

Signed ticks (`+1/-1`), signed volume and signed notional are candidate **known innovations**, once trade signing is resolved. The numerator is a compatible mathematical leaky accumulator; normalization can be generated from position/window independently. However, adaptively ending a bar changes the subsequent history/window/reset schedule. It depends on previous statistics, so the whole sampler is not automatically a known-coefficient scalar block. Isolate fixed-history EWMA calculation or replay a separately recorded boundary schedule, and disclose that separation. Also distinguish the helper's history initialization from a perpetually streaming recursive mean.

Toxicity, order-flow imbalance, and trade-sign imbalance are not synonyms. A raw OFI sum, finite-window VPIN statistic, or depth-weighted imbalance is not an EWMA merely because it is a microstructure signal. Adding exponential smoothing is a proposed feature transformation requiring evaluation, not evidence that the cited indicator already contains the desired recurrence.

### Arrival intensity and time-decaying activity

Carreira derives and implements the exponential-kernel Hawkes statistic `R_i=exp(-beta*(t_i-t_(i-1)))*(1+R_(i-1))`, including extensions with a fixed latency and known delayed-event contributions. The real-data section uses four BUND event streams and April-2014 data; its per-stream median gaps range from approximately **13 ms to 183 ms**, despite short-gap clusters. This is primarily historical model estimation, not evidence of a deployed order-path accelerator. [F5: methods and real-data section](https://arxiv.org/html/2101.06348v1)

At fixed parameters and recorded timestamps, one kernel component is mathematically scalar with known varying retention. A quantized implementation can map it exactly after specifying coefficient generation and rounding. Exponential evaluation/LUT error is separate from preserving the ensuing integer recurrence. Timestamp ties give retention one; rounding can also produce `A=D`. Handle identity-plus-known-input transitions explicitly rather than assuming strict contraction. A multikernel/multivariate model has several scalar states and independent candidate parallelism. State-dependent estimated parameters and generating the next event from the unresolved intensity are additional dependencies; historical likelihood replay avoids the latter.

The simpler interarrival-mean recurrence `m_i=lambda*m_(i-1)+(1-lambda)*(t_i-t_(i-1))` would fit too. No audited finance-specific implementation or coefficient was obtained for that exact feature. Likewise, acknowledgement-latency smoothing is plausible infrastructure telemetry, but this audit supplies no native financial configuration for it. Do not present these two suggested kernels as observed proprietary HFT internals.

## Native integer finance evidence: useful, with limits

**Columbia 2015 course project: first native replay choice.** The companion audit in `FINANCIAL_EWMA_PRIOR_ART.md` reconstructs unsigned 17-bit rounded price updates from the report/HDL appendix: `(61*s+3*p+32)//64`, `(63*s+p+32)//64`, and `(127*s+p+64)//128`. They directly fit the original floor-affine contract; convex invariance makes saturation inactive. The appendix contains malformed/incomplete HDL, so these are reconstructed arithmetic contracts, not compiled RTL equivalence. The report's actual stimulus is historical **daily closing prices** regarded as a simulated live stream, not an exchange tick feed. Preserve staged input stability and use coefficients rather than inconsistent filter names. [F12: institutional report](https://www.cs.columbia.edu/~sedwards/classes/2015/4840/reports/HFT2.pdf)

**Illinois 2026 feed-handler course project.** The report specifies per-symbol price EMA with gain **1/16**, implemented as `s+=floor((p-s)/16)` for `p>=s` and `s-=floor((s-p)/16)` otherwise. It reports eight tested symbols, 100 Mbps ingress, 100 MHz processing, mean receive-to-trigger latency 2.34 microseconds and a 50-microsecond per-symbol cooldown. This is a native integer design example, not production HFT validation or evidence of ingress events exceeding clock rate. [F6: report §§2.1.3, 2.2.8](https://courses.grainger.illinois.edu/ece445/getfile.asp?id=25819)

The correction is truncated toward zero, leaving the result toward the old state. This is not one global floor-affine expression. Nevertheless each branch and the join preserve order with adjacent output increments zero or one, so threshold-map representation is a credible narrow extension, with its own inverse and width proof. Preserve branch semantics; replacing it with `floor((15*s+p)/16)` changes outputs. The parent investigation separately audits this extension. No full HDL equivalence or resource claim is made here.

**Cornell 2024 course project.** The report proposes EMA/variance-based decisions, uses one-second aggregated delayed stock data, and explicitly says end-to-end testing failed. Its advertised .94 retention is approximated by shift arithmetic. [F7a: report](https://people.ece.cornell.edu/land/courses/ece5760/FinalProjects/s2024/wb273_sal267_rak277/docs/index.html)

The published `ema` module uses 27-bit signed state with `avg <= (x >> k)+avg-(avg >> k)` and updates each clock without an input-valid condition. The adjacent variance module truncates a product; it is not covered as a single scalar mean. [F7b: actual RTL, module near line 1522](https://people.ece.cornell.edu/land/courses/ece5760/FinalProjects/s2024/wb273_sal267_rak277/docs/code/DE1_SoC_Computer.v)

Independent arithmetic observation: on nonnegative bounded price/state domains, `k=4` gives

`s'=floor((15*s + 15 + 16*floor(x/16))/16)`.

This follows from `s-floor(s/16)=ceil(15*s/16)` and avoids overflow on an invariant nonnegative range. Clipping is inactive. The real RTL uses logical `>>`, so this reduction is not a claim for negative prices/state. Nor may repeated-clock updates be relabeled as one update per market tick. It is a concrete integer finance kernel to reproduce, with qualification of valid clocking and domain before execution.

**Open-source market-making motivation.** Krypto-trading-bot documents EWMA periods in minutes, crosses between horizons for position management, and EWMA protection of quotes. This shows application use beyond generic charting but gives no reason to demand tens of millions of updates per second for those particular smoothed states. No integer implementation or verified performance was audited. [F8: project manual](https://github.com/ctubio/Krypto-trading-bot/blob/master/doc/MANUAL.md)

## Buffer tolerance, exactness, and the small-FPGA hypothesis

Headlands' own engineering overview distinguishes the live strategy from market-data capture, production reconciliation and historical backtesting. It describes reconciliation as checking internal strategy state against captured data; it also explains a trade-impulse example valid for only one packet. This supports both a credible replay use and a sharp exclusion for delayed, immediate-action signals. It does **not** specify integer EWMA or require every arithmetic bit to agree. [F9: firm-authored overview](https://blog.headlandstech.com/2017/08/03/quantitative-trading-summary/)

Exact integer replay can make differences attributable to code changes rather than execution order, including threshold-crossing disagreements. That is an engineering motivation, not a financial requirement established by F9. Preserve historical input availability: computing later samples in parallel is not statistical look-ahead if each emitted feature equals its causal reference and is delivered at the modeled availability time. Delivering it later in live trading, or letting a backtest consume it earlier than available, changes the strategy.

For live use, prediction horizon, smoothing horizon, decision cadence and processing-delay budget are four different quantities. A ten-second forecast can still drive an immediate order. Conversely, a public `hftbacktest` imbalance example processes full market data while deciding at **one-second** intervals, with a one-hour standardization window; another uses 500 ms. Its actual example is rolling standardization, not EWMA. It demonstrates why raw feed event rate and downstream feature update rate must be measured separately. [F10: executable tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)

DEBS2022 provides another explicit cadence counterexample. Its challenge groups by symbol and computes EMA38/EMA100 from each **five-minute tumbling window's closing price**, evaluated when the next window starts, with input weights `2/39` and `2/101`. Its 59-million-event evaluation subset is not 59 million EMA steps per symbol. [F13: challenge §4](https://vgate.cs.ucy.ac.cy/debs2022/pdfs/debs2022-54.pdf) The UT Austin solution partitions consumers by symbol and reports profiling as **I/O bound**, with EMA/crossover arithmetic a small part of the work. This supports batching/replay as a financial systems setting while arguing against using that specific workload as an EMA-compute bottleneck. [F14: solution §§2,5](https://vgate.cs.ucy.ac.cy/debs2022/pdfs/debs2022-26.pdf)

The proposed small/slow-FPGA advantage is **possible in principle, unestablished here**. Let `r` be the arrival rate *to one state*, and `f_clk` the routed clock; a serial loop taking `q` cycles sustains `f_clk/q`. A map executor must sustain `r` including endpoint runs, threshold work, resolution, replay and memory traffic. Its first block's oldest event waits approximately `(L-1)/r` just to fill, before computation. Greater aggregate event rate is relevant only if the state truly aggregates them, or same-symbol bursts defeat interleaving. Independent symbols and independent EWMA horizons are simpler parallelism to benchmark first.

Calculated examples, not workload measurements: with `L=256`, fill alone is 255 microseconds at one million events/s and 25.5 microseconds at ten million. A slowly varying signal does not make those delays free. For retention `a`, half-life is `ln(.5)/ln(a)` **updates**: .97 gives 22.76, .99 gives 68.97; a 10,000-span conventional EMA gives about 3,466 updates. High event rate can mean very slow contraction per event for a fixed wall-clock horizon, leading to large maps or long buffers. Mathematical width bounds and worst-case threshold capacities must replace intuition from smooth price traces.

No reviewed source establishes iCE40UP5K end-to-end suitability. This report makes no unverified clock, network-interface, memory or power assertion about that part. Board fit must include ingress adaptation, buffers, output, same-symbol bursts and threshold storage, compared with the tiny shift/add serial kernels above. “Cheaper device” requires complete routed designs and total board/interface cost; kernel speedup alone cannot establish it.

## Best three experiments and clear stop conditions

1. **Exact financial feature replay/reconciliation.** Start with Columbia's directly compatible 17-bit rounded EMA32/EMA128 contracts; retain Illinois's branch rule as an extension and Cornell's bounded positive-domain rule as a secondary clocking-sensitive case. On recorded price updates, preserve the actual update schedule and output every state. First demonstrate exactness and complete throughput; then measure whether a buffered executor permits the same replay rate on a smaller/slower device. Native coarse ingress is not evidence of a large required rate: accelerated replay is the proposed requirement.
2. **Quote-liquidity feature at F1's .97 calibration.** Reconstruct a per-instrument top-of-book stream; freeze an explicit integer port, compare its financial outputs with the published real-valued estimator, then compare exact execution methods within that integer contract. This has the cleanest useful scalar input. Treat buffering as acceptable only for documented off-path analytics or a measured live decision budget.
3. **Historical exponential-intensity evaluation.** At fixed candidate model parameters, precompute timestamp-derived coefficients and contributions, evaluate exact scalar kernel traces, and preserve the likelihood's downstream calculations separately. Historical data remove the online waiting constraint. Baselines must include parallel parameter candidates/kernels, native optimized float code when approximation is permitted, and simpler exact forward tables. This tests financial modelling throughput, not live tick-to-trade latency.

Common stop conditions: no one-state bottleneck; ingress/output throughput below the alleged rate; byte-identical arithmetic not valuable to the chosen consumer; map construction or buffering dominates; forward tables/unrolling/interleaved states win. Do not promote adaptive bar creation, complete variance/regression, order-book reconstruction, or a closed-loop agent simulator as one scalar known-input recurrence.

Public stimuli: Binance's official archive provides symbol-specific daily/monthly **trades** and **aggregate trades**, with timestamps and maker flags; spot timestamps from January 2025 use microseconds. Prefer raw trades for trade-event EWMA and explicitly document signing conventions. Aggregated trade records change the number/order of recursive updates and are not interchangeable. These archives do not by themselves provide quote-size inputs for F1. [F11: official archive specification](https://github.com/binance/binance-public-data)

Use the public BUND event dataset linked by F5 for intensity replay, retaining its event definitions and ties. Obtain a licensed or public top-of-book capture for liquidity; LOBSTER's sample pages were attempted but returned no readable content, so no dataset format or event rate is asserted from them. No market data were downloaded, no financial backtest was run, and no new throughput experiment was executed in this audit.

## Source and reading-depth registry

All accessed 2026-11-06. Source claims are limited to what was read; mutable code needs a commit/version pin before reproduction.

| Key | Primary evidence read | Limitation |
|---|---|---|
| F1 Loveless/Stoikov/Waeber, ACM Queue 2013 | Full article PDF, pp.1–12: estimator methods, horizons, fitted retention | Original publisher returned 403; inspected original article via mirror; no integer format |
| F2 NautilusTrader EMA | Complete relevant Rust definition, warm-up and tick handlers, update | Current docs.rs source; not compiled; version may change |
| F3 Mlfin.py imbalance bars | Constructor, expected-count estimator and public defaults | Whole adaptive sampler not proved compatible |
| F4 Mlfin.py fast_ewma.py | Complete 46-line helper | Float64 adjusted mean; no integer semantics |
| F5 Carreira 2021 | HTML methods equations 7–20, algorithms, real-data §4 and gap statistics | Historical estimation; no live deployment claim |
| F6 Illinois ECE445 Spring2026 report | EMA equations, ingress/clocks, trigger and cooldown descriptions | Course project; report evidence, no independent full RTL validation |
| F7 Cornell ECE5760 Spring2024 | Report including failures; actual RTL `ema` and product extraction | Logical shifts, clock-valid issue, incomplete system validation |
| F8 Krypto-trading-bot | Manual's EWMA strategy/quote-protection configuration | No source-level arithmetic/throughput audit |
| F9 Headlands 2017 overview | Capture/reconciliation/backtesting and one-packet signal sections | Public educational description; no hidden-firm arithmetic inferred |
| F10 hftbacktest | Tutorial code, interval/window configuration, feature calculation | Useful cadence comparator; not an EWMA example |
| F11 Binance | Official public-data README: types and timestamps | No capture counts or rates measured |
| F12 Columbia CS/EE4840 2015 | Companion primary-source audit read; institutional PDF opened; appendix arithmetic reconstruction inherited explicitly | Malformed/incomplete HDL; no compiled equivalence |
| F13 DEBS2022 challenge | Full PDF text, specifically §§3–4 dataset and window/cadence definitions | Five-minute window EMA, not per-tick recurrence |
| F14 DEBS2022 UT Austin solution | Full PDF text, specifically §§2,5 symbol partitioning and profiling | Author-reported I/O bottleneck, not independently reproduced |

Search log: targeted primary-source queries included `high frequency trading exponentially weighted moving average trade imbalance`, `mlfinlab expected imbalance bars ewma expected ticks`, `Hawkes high frequency finance exponential kernel recursive intensity`, `FPGA EWMA financial integer`, `Online Algorithms in High-frequency Trading`, and source searches for NautilusTrader, Krypto-trading-bot and latency smoothing. The current mlfinlab helper found on GitHub was a `pass` stub; the functioning Mlfin.py source was inspected instead. QUB's 2014 technical-indicator PDF returned 403, so no detailed performance claims were taken from it. The CPA2016 slides were readable but showed a different toy example; a search snippet about an EWMA demonstration was not treated as full-method evidence. Fresh low-star “HFT” repositories with broad performance claims were not used as proof of production demand.

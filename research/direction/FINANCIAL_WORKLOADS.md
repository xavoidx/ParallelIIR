# Financial workloads: faithful event-state replay, with a measured precision/service frontier

Research pass: 2026-11-06. This is a new application and source audit, building on `../FINANCIAL_EWMA_APPLICATIONS.md`, `../FINANCIAL_EWMA_PRIOR_ART.md`, and `../../SPEC.md`. Proposed contracts and experiments below are research choices, not reported production requirements. No new financial performance or hardware result is claimed here.

The strongest financial direction is **accelerated historical execution of explicitly quantized, event-driven liquidity/flow features**, with exact reproduction of that chosen arithmetic and empirical validation against a higher-precision financial reference. The second direction is **historical exponential-kernel intensity evaluation**, where timestamps generate varying coefficients. Both are credible workloads. Neither supplies an established single-state rate requirement that already defeats a simple serial FPGA. A publishable application argument must establish the useful region between precision, state-map complexity, replay throughput and end-to-end delay.

## 1. New evidence changes the motivation

Jane Street's October 2026 description of **Flex Model** is unusually direct production evidence for stateful feature computation. It separates event handlers, which maintain history, from evaluations requested by model consumers. It describes hundreds or thousands of features, many updated on every event, and explains why duplicate-valued trades cannot simply be coalesced. The same feature code runs in live and historical modes. Most values are floats; its worked example is a ten-trade rolling trade-price-minus-mid average. Thus it supports preserving the event schedule and matching historical/live behavior, but supplies neither native integer EWMA nor an FPGA bottleneck. [Primary engineering description](https://blog.janestreet.com/flex-model-an-event-driven-feature-engineering-system/).

This gives a better systems interface than “a trading moving average”: a **feature handler** consumes a known ordered event tape, while downstream consumers request values at separately specified observation points. Our proposed accelerator can target a compatible subgraph after book reconstruction. The whole feature graph is not necessarily scalar, monotone or known-input.

Nigito's Jane Street exchange talk describes replaying ordered transactions to reconstruct deterministic application state and replaying past weeks for testing. It also identifies state snapshots as an alternative to full replay and discusses commodity hardware. This establishes a real replay/recovery setting, not that its matching engine fits our map theorem or needs our accelerator. [Primary talk and transcript](https://www.janestreet.com/tech-talks/building-an-exchange/).

The important hypothesis is consequently modest: **when a financial feature has been deliberately specified in fixed point, can its entire causal state trajectory be reproduced faster per unit hardware than direct exact execution?** Production does not have to demand bit-for-bit integer arithmetic for that research question to be legitimate. Precision must earn its place through measured financial fidelity; exactness then prevents the execution optimization from adding a second source of disagreement.

## 2. Formulation A: liquidity and order-flow feature replay

Take one instrument's ordered best-quote observations

\[
(t_n,p^b_n,q^b_n,p^a_n,q^a_n).
\]

The cleanest scalar input is displayed liquidity, \(x_n=q^b_n+q^a_n\). The earlier audit already established the published quote-time liquidity EWMA with retention .97. Retain that as the initial application anchor; the new work is a qualified integer implementation and complete execution comparison, rather than another demonstration that finance uses EWMA. [Previously audited original article](https://queue.acm.org/detail.cfm?id=2534976).

A stronger extension is the canonical top-of-book event contribution

\[
e_n=\mathbf1_{p^b_n\ge p^b_{n-1}}q^b_n
-\mathbf1_{p^b_n\le p^b_{n-1}}q^b_{n-1}
-\mathbf1_{p^a_n\le p^a_{n-1}}q^a_n
+\mathbf1_{p^a_n\ge p^a_{n-1}}q^a_{n-1}.
\]

Cont, Kukanov and Stoikov define interval OFI by **summing** these contributions. Its inclusion of quote additions/removals makes it different from trade-only signed flow. Their estimator is not an EWMA. We propose smoothing \(e_n\) as a decaying flow feature, to be tested against the unsmoothed/interval-sum alternatives; the citation supports the underlying input, not our transformation or its predictive superiority. [Author paper, §2.1](https://arxiv.org/html/1011.6402v3).

For either integer innovation \(x_n\), freeze the following normalized contract:

\[
s_n=\operatorname{clip}_{[s_-,s_+]}
\left\lfloor\frac{A s_{n-1}+(D-A)x_n+\rho}{D}\right\rfloor,
\qquad 0<A<D.
\]

Here an integer state represents physical value \(s_n/S\), with the input converted using the same scale \(S\). Use \(\rho=\lfloor D/2\rfloor\) for the chosen nearest-rounding convention, including explicit tie behavior. Signed division means mathematical floor, not language-dependent truncation toward zero. Widen products and additions before quantization; clipping must be explicit. The update is monotone with adjacent output differences zero or one, including for signed states. Therefore a block map can use the scalar threshold construction. No approximation of intermediate rounding is permitted in the exact comparison.

Begin with liquidity at exact retention \(97/100\), then include a nearby dyadic implementation and the previously audited native price kernels as controls. Choosing \(15/16\) solely because shifts are cheap changes the financial time scale. For signed OFI, select scale and rails using training data plus a stated overflow policy; testing observations outside those rails must remain visible in the results. Preserve daily reset, warm-up, session gaps and repeated observations. A declared changed-best-quote schedule differs from an every-message schedule even if most inputs repeat.

Useful downstream consumers are a depth alarm or a small causal regression relating the feature to subsequent mid-price changes. A depth alarm is easy to make exact and interpretable: emit \(d_n=\mathbf1_{s_n<T}\) at selected events. For a fitted predictor, keep training chronology and coefficients fixed while comparing arithmetic formats. First ask whether the quantized feature preserves the reference decisions; establishing new trading alpha is a separate and considerably harder claim.

Risk features are an additional control rather than the strongest rate argument. An EWMA of precomputed squared mid-price returns has known scalar innovations and can drive a specified volatility gate. Computing returns, choosing event versus clock sampling, handling overnight jumps and evaluating the gate remain separate work. A variance update using the unresolved current mean is a coupled dependency and needs materialized mean outputs or a different proof. The prior application audit documents financial variance use; no new evidence here establishes that a single live risk state is throughput-limited.

Modern OFI evidence reinforces relevance while constraining the story. Cont, Cucuringu and Zhang's 2023 study integrates multiple levels, evaluates forecasting with chronological fits, and uses one-minute observations and previous-30-minute fitting windows in its forecasting experiment. It therefore motivates feature fidelity and suitable downstream metrics, but not a per-tick EWMA throughput demand. [Full methods, §§2, 3.2.2, 4.2](https://arxiv.org/html/2112.13213v4).

Kolm, Turiel and Westray's 2023 abstract reports order-flow-based predictors and a forecast horizon around two average price changes. Only its abstract and data-availability statement were reviewed here. This is a reason to measure added delay against the event process, not a verified deadline for our proposed smoother. [Publisher abstract](https://doi.org/10.1111/mafi.12413).

**Proposed service contract.** Supply an already decoded, ordered feature-input tape with instrument IDs, event IDs and resets. Return every requested \((\text{event ID},s_n)\) in order, plus exact final states. Historical mode permits backpressure and block buffering; it must report complete job time including preparation and transfer. A consumer may request every output or just recorded evaluation points. Benchmark these modes separately: sparse output does not authorize skipping intervening state updates. Exclude adaptive event generation and decisions that alter later inputs from the initial benchmark.

For live catch-up, additionally define a maximum backlog and a deadline to regain the current tape position. Given backlog \(B\), incoming selected-event rate \(r\), and demonstrated service rate \(\mu>r\), an idealized catch-up time is \(B/(\mu-r)\), before fixed overhead. This calculation belongs to the proposed contract; no reviewed firm supplies its required \(B,r,\mu\). Ordinary on-path trading needs its own measured event-to-decision delay budget.

## 3. Formulation B: recorded exponential-intensity evaluation

For known timestamps and fixed decay \(\beta\), an exponential event-history state before event \(i\) is

\[
R_1=0,\qquad
R_i=\exp[-\beta(t_i-t_{i-1})](R_{i-1}+1),\qquad
\lambda_i=\mu+\alpha R_i.
\]

A candidate quantized contract, with \(z_i\) representing \(S R_i\), is

\[
A_i=Q_D(\exp[-\beta\Delta t_i]),\qquad
z_i=\operatorname{clip}_{[0,Z]}
\left\lfloor\frac{A_i(z_{i-1}+S)+\rho}{D}\right\rfloor.
\]

Timestamp-to-coefficient conversion is independent of the unresolved state. It may be precomputed for a kernel-only benchmark, but its cost and approximation must appear in the complete workload. Identity-retention coefficients \(A_i=D\), from ties or coefficient rounding, need support; forcing strict contraction changes the model. Coefficients rounded to zero give a constant transition and need explicit handling rather than an inverse division by zero. In a marked/multivariate extension, known event types provide known impulses. Several decay kernels are several states, not one magically scalar coupled system. State-dependent excitation or parameters require separate analysis.

This workload has especially important omitted prior art. **Guo and Luk, FPL 2013**, derive the same recurrence, use c-slow interleaving across parameter candidates and parallelism across consecutive iterations, and implement a 100-MHz Virtex-6 engine with 12-iteration hardware and 1,024 parameter candidates. Their arithmetic is primarily single precision, with double-precision log inputs; they report likelihood differences below .1%. Their reported 72×/10× CPU speedups concern recorded likelihood queries, excluding the optimizer but including host/device communication. Thus FPGA Hawkes evaluation and buffered iteration parallelism are established; our possible contribution would be exact quantized-state execution with a demonstrably better resource/service region. [Author manuscript, §§3–5](https://www.doc.ic.ac.uk/~swd10/fpl13cg.pdf), [publication DOI](https://doi.org/10.1109/FPL.2013.6645502).

Anantha and Jain's 2024 preprint fits bid/sell trade-arrival Hawkes models and compares OFI forecasts, including sum-of-exponential kernels, on NSE futures data. The reviewed methods include likelihood fitting and event simulation; its trade-based OFI is not identical to the canonical quote-flow contribution above. Simulation chooses future times from evolving intensity, so it does not directly provide a known-input block workload. Recorded-intensity evaluation does. [Full preprint methods](https://arxiv.org/html/2408.03594v1).

**Proposed service contract.** Accept timestamp gaps, fixed parameter candidates and initialization; produce intensity traces or objective contributions. Report one-candidate and many-candidate throughput separately. Candidate interleaving, independent days, independent kernels and a modern optimized CPU implementation are mandatory baselines. The `tick` project's official documentation explicitly exploits exponential recurrence for efficient estimation and provides exponential/sum-exponential likelihood and least-squares models. Its presence makes comparison with a naive quadratic history sum inappropriate. [Official module documentation](https://github.com/X-DataInitiative/tick/blob/master/doc/modules/hawkes.rst).

Returning only block-exit states is insufficient for a likelihood that needs intensity at every event. The replay stage, logarithms, reductions and coefficient generation may dominate. Also, exact \(z_i\) does not imply exact agreement of an independently rounded log-likelihood reduction. Freeze and measure that output contract separately.

## 4. Actual data and what each tape can establish

**First choice: LOBSTER's official samples.** The current readable sample page offers paired orderbook/message CSV archives for AMZN, AAPL, GOOG, INTC and MSFT, with one-level archives advertised at .5–3.3 MB, derived from the official Nasdaq Historical TotalView-ITCH sample. These support a small, auditable liquidity/OFI characterization without collecting a feed or downloading huge data. [Official sample page](https://php.lobsterdata.com/info/DataSamples.php).

The official structure specifies ask-price/size then bid-price/size, integer prices scaled by 10,000, share quantities, event kinds and timestamps. Row \(k\)'s message explains the transition from book row \(k-1\) to row \(k\). Hidden trades and halt markers need explicit treatment; limit-order direction is not aggressor trade direction. Empty-level sentinel prices must not become ordinary price observations. [Official format](https://php.lobsterdata.com/info/DataStructure.php).

Use all five symbols and preserve the original sample ordering. Keep every raw row's identity while deriving several named selection schedules. Report zero input changes, repeated input runs, timestamp ties, selected events/second, and burst counts over 10 µs, 100 µs, 1 ms and 100 ms. The old, small sample can establish arithmetic behavior on an actual tape; it cannot establish contemporary production capacity, crisis robustness or profitable alpha. Reproducibility should publish checksums, extraction code and derived statistics while respecting the provider's distribution terms.

**Second choice: the official `tick-datasets` Bund tape.** Its README specifies April 2014 Eurex Bund futures, 20 realizations, microsecond timestamp resolution and four event series: up/down mid-price changes and buyer/seller trades that do not move the mid. It states the session-time adjustment. This is useful for varying-coefficient recurrence tests and tie/rate analysis, not for reconstructing best-quote depth. [Provider repository and README](https://github.com/X-DataInitiative/tick-datasets/tree/master/hawkes/bund).

Trade-only exchange archives remain useful price/signed-trade controls, as previously documented, but cannot manufacture quote depth. Pre-normalized ML benchmarks should not be the first exact-integer microstructure tape: verify raw units, event selection and timestamps before assigning a state contract.

## 5. Experiments that make the application claim meaningful

Keep three references: high precision financial recurrence, serial integer specification, and proposed executor. Integer-vs-high-precision differences evaluate the port. Executor-vs-serial differences must be zero. Do not collapse these into a single “accuracy” figure.

1. **Precision and financial behavior.** Sweep physical state LSB, coefficient representation and rails. Report absolute/relative feature error, bias, saturation frequency, alarm disagreement and crossing-time displacement in events and microseconds. Relative error near zero needs a denominator floor. For prediction, report chronological out-of-sample loss, direction decisions and stability of conclusions across formats. Show disagreement concentrated near decision margins; an average numerical error alone can hide materially different decisions.
2. **Map statistics.** Sweep block length, retention, full legal entry range and separately justified entry intervals. Record threshold count \(K\), its percentiles/maxima, constant-block frequency, capacity overflow and constructor work. Relate \(K\) to actual event inputs rather than fitting a random-input distribution after seeing the result. Keep quiet periods and large unchanged-depth runs. For Hawkes, analyze \(A_i=D\) runs and long gaps separately.
3. **Complete execution.** Compare serial exact arithmetic, 2/4-step exact unrolling, interleaved instruments/candidates, a CPU implementation, and the complete map constructor/resolver/replayer. Each preserves intermediate quantizers. Measure routed clock, accepted events/cycle, events/second, bytes transferred, output bandwidth and resources. Full-domain tables are a baseline at small state widths. A high-precision approximate scan is an accuracy/performance alternative when exact integer agreement is optional.
4. **Service and workload decomposition.** Report one state, the actual multisymbol mix and one aggregate state only if that aggregate has a defined financial meaning. Separate book/input preparation, coefficient generation, state kernel, output and consumer work. Include block fill, fallback and ordering. Test cold start, resets, backpressure and partial final blocks. Speedup from symbols or parameter candidates must not be described as overcoming a single feedback dependency.

An elementary port-error bound helps select the sweep. With identical exact coefficient \(a\), no clipping and per-step physical rounding error bounded by \(\delta\), the error obeys

\[
|E_n|\le a^n|E_0|+\delta\frac{1-a^n}{1-a}.
\]

For nearest rounding, \(\delta\le1/(2S)\); innovation quantization and coefficient error add separate terms. This is a derived worst-case bound, not an observed market error. Long memory may require more fractional bits. **Third-pass clarification:** more bits enlarge the full legal domain and may hurt the original full-domain constructor, but do not directly enlarge the certified rounding-domain width at fixed retention and adequate predictor precision. They increase base/predictor datapath cost. A fixed wall-clock horizon at greater actual event rate instead increases retention and can enlarge the certified domain substantially; sweep both dimensions separately.

## 6. Counterarguments and decision gates

The strongest objection is that compatible financial filters are cheap and independent-state parallelism is plentiful. An application result must survive that comparison. A second objection is that a block can be almost constant on tested inputs yet have expensive legal worst cases. Average \(K\) is useful for backpressured replay; a bounded-delay live service needs capacity/fallback behavior under adverse runs. A third is that disk, parsing, book reconstruction or feature consumers dominate. In that case optimize or scope the complete job honestly; a faster EMA is not a faster trading system.

Do not claim that preserving integer output improves trading quality by itself. It improves reproducibility of a deliberately chosen implementation. Nor does a successful tiny sample establish a production requirement for exactness. Conversely, absence of a native fixed-point production example does not disqualify a validated integer port.

Proceed toward RTL if actual-data maps show a useful region at financially acceptable precision and a complete schedule plausibly beats exact unrolling/interleaving. Prefer formulation A first: readily inspectable integer inputs, interpretable decisions and fewer expensive surrounding operators. Use formulation B as a varying-coefficient stress case and as a guarded application extension. If neither survives, the financial conclusion is a negative boundary result; it should not be rescued by attributing an aggregate feed's rate to one scalar state.

## Source depth and next reading

All links accessed 2026-11-06. Mutable code/data links need a revision pin before reproduction.

| Source | Reading depth in this pass | Next use / limit |
|---|---|---|
| Flex Model (2026) | Full engineering article, including handler/eval mechanism and performance discussion | Production event-state motivation; float rolling example, no EWMA audit |
| Nigito exchange talk | Architecture/replay/testing transcript sections | Recovery/replay motivation; complete exchange state is outside scalar scope |
| Cont–Kukanov–Stoikov | Full §2.1 input definition; surrounding empirical motivation | Implement canonical quote-flow innovation; no EWMA in that definition |
| Cont–Cucuringu–Zhang (2023) | Methods for features, chronological evaluation and forecasting cadence | Strong evaluation design; no native quantized recurrence |
| Kolm–Turiel–Westray (2023) | Abstract and data-availability only | Read full methods before using model details or performance claims |
| Guo–Luk (FPL 2013) | Full six-page manuscript, especially §§3–5 | Closest new finance accelerator baseline; reproduce scope before comparison |
| Anantha–Jain (2024) | Full model/fitting/simulation methods and results framing | Modern finance use; not a native exact implementation or latency requirement |
| LOBSTER sample/format pages | Full provider documentation | Small actual-data pilot; retain schedule and event semantics |
| `tick` docs and Bund README | Official algorithm/API overview and full dataset README | Optimized software baseline and second tape; C++ arithmetic not audited |

First further reading should be Guo–Luk's architecture alongside the existing Funie EMA accelerator audit; then full Kolm methods, the exact `tick` C++ kernel and reproducible live/historical feature configurations. These are targeted evidence gaps, not prerequisites for executing the initial liquidity-map pilot.

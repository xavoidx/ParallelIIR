# A differentiated research direction and its strongest competitors

**Third-pass correction:** [PRIORITY_RED_TEAM.md](PRIORITY_RED_TEAM.md) finds explicit adjacent-collapse generators and rank-shift composition in Fernandes 2024, beyond the earlier boundary encoding. [THIRD_PASS_VERDICT.md](THIRD_PASS_VERDICT.md) also adds a stronger shared-base relative-rank competitor. The direction is now a bounded implementation comparison; a standalone deletion-principle or bitmap-work advantage is not established.

Review date: 6 November 2026. This is a conceptual and primary-source review of exact scalar, floor-rounded EWMA execution. It builds on [PRIOR_ART.md](../PRIOR_ART.md), [FILTER_LITERATURE.md](../FILTER_LITERATURE.md), [FINANCIAL_EWMA_REVIEW.md](../FINANCIAL_EWMA_REVIEW.md), and `SPEC.md`. Proposed mechanisms below are hypotheses and derivations, not published priority claims or measured hardware results. No RTL was implemented for this note.

## Recommendation

The strongest direction is **certified affine boundary enclosures followed by exact block maps that update by deleting boundaries**. The research question changes from “can inverse thresholds parallelize a quantized EWMA?” to “can numerical certificates reduce the unresolved entry state to a small interval, and can its ordered structure eliminate most speculative work?” This directly targets the original constructor's `K` reverse passes, expensive division by `A`, and dependence on long blocks for image contraction.

This is a stronger candidate than adding a predictor or fallback alone. Prediction, state speculation, convergence, sampled transfer functions, parallel merging, and recovery already have extensive predecessors. Even the bitmap of adjacent state boundaries is an elementary representation with a direct mathematical predecessor. What might be useful is the **specific arithmetic deletion constructor, practical boundary certificates, and their complete execution schedule**. The combination being absent from the inspected sources would be insufficient: its reduced work must translate into a meaningful latency/resource advantage over strong exact alternatives.

The financial application remains rounded feature replay. This review does not establish that a trading decision requires bitwise reproduction, that live single-symbol traffic exceeds a good serial implementation, or that approximate filtering is unacceptable. Those are separate workload questions.

## Comparison matrix

“Exact” concerns every output of the specified integer program, not its ideal transfer function. Reading codes are: **M**, relevant full-text method inspected; **E**, primary extended abstract/slides inspected; **A**, primary abstract/metadata only; **R**, inherited detailed review, with selected passages checked again here.

| Predecessor | What is already established | Consequence for the proposed direction | Depth / primary source |
|---|---|---|---|
| Papadantonakis et al., FPT 2005 | Exact saturating accumulation through compact unary maps and parallel prefix hardware | Kills architecture-level novelty for exact nonlinear DSP summaries and scans; its constant-size clamp/shift closure is stronger on its own domain | R: [author paper](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf), §§2–3 checked |
| Mytkowicz et al., ASPLOS 2014 | Enumerative transition maps, composition, and factoring partially converged trajectories | Residual execution must beat convergence-aware enumeration; “process only surviving states” is not a contribution | R: [primary paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf), see companion review |
| Ko et al., 2012/2013 | Known preceding symbols restrict a chunk's possible entry states before exact speculative execution | A certified numerical entry interval is a specialized restriction mechanism; reduced candidate domains alone are old | M: [author manuscript](https://arxiv.org/html/1210.5093), §§4.2–4.3 |
| Parhi, TCAS 1991 | Pipelining feedback containing finite-level quantizers; parallel-branch/delayed-decision lineage | Generic precompute-and-select around quantization is old; full paper remains an unresolved priority comparison | A: [DOI](https://doi.org/10.1109/31.135746), [author bibliography](https://parhi.umn.edu/publications/journal-publications) |
| Parhi & Gu, IEEE 802.3an, 2004 | Reformulate a nonlinear precoder as a pipelined IIR plus finite-level compensation and precomputation | Especially close conceptual threat to moving wide-state nonlinear dependence into a narrow compensation loop | E: [author presentation](https://www.ieee802.org/3/an/public/sep04/parhi_1_0904.pdf), all 14 slides |
| Cox et al., STTT 2014 | Bit-precise verification and conservative real/affine error encodings of quantized filters | Certified rounding-error envelopes are established analysis machinery; possible contribution is using them to accelerate exact execution | M: [author manuscript](https://arlencox.github.io/papers/filters.pdf), §5, related-work discussion |
| Adeshola & Umar, 2013 | Semigroup of order-preserving nonexpansive finite-chain maps; convex image and kernel blocks; boundaries represented as bars between adjacent states | The exact map class, closure, and boundary bitmap are established mathematics | M: [author manuscript](https://arxiv.org/html/1303.7428), §1 and §2 |
| Fernandes, 2024; Fernandes–Paulista, 2021/2023 | Explicit elementary adjacent-collapse generators, products and rank-shift relations | Even the action of deleting an ordered image boundary is established; the floor-remainder choice and implementation are the remaining specialization | M: [2024 §§2–3](https://arxiv.org/html/2407.05084), [predecessor pp.6–8](https://arxiv.org/pdf/2112.13427); independently read in third pass |
| Jiang/Chen/Agrawal, PACT 2018; Xia/Jiang/Agrawal, CC 2019 | Function sampling/reconstruction; subsequent parallel merging | Another mandatory predecessor to sampled/reconstructed or hybrid maps; detailed quantization coverage not audited | A: [author publication list](https://homepage.cs.uiowa.edu/~penjiang/pubs.html), [PACT DOI](https://doi.org/10.1145/3243176.3243204), [CC DOI](https://doi.org/10.1145/3302516.3307354) |
| Qiu et al., ASPLOS 2021 / BoostFSM | Path fusion, iterative higher-order speculation, selection among execution schemes | Hybrid enumeration/prediction and improving speculative boundaries iteratively are old | E: [primary extended abstract](https://asplos-conference.org/asplos2021/abstracts/asplos21-paper113-extended_abstract.pdf), complete |
| Qiu/Jiang/Zhao, ASPLOS 2020 / PBS | Identify dependent bits, model their combinations as FSM states, exploit convergence, and repair outputs using proved bit relations | “Narrow dependency state plus fast repair” is insufficiently distinctive; ordered arithmetic construction must do the work | M: [Qiu dissertation](https://escholarship.org/content/qt5d5997zb/qt5d5997zb_noSplash_e0f7642d800f38a8db085a4d422a733c.pdf), Ch.5 §§5.5–5.6 |
| Parhi 1991 finite-word analysis; current super-sample-rate IIR work | Look-ahead can be sized under finite-precision error criteria and achieve high throughput | Useful quality/throughput competitors, but equal ideal transfer functions or error bounds do not establish identical per-step integer results | A/M: [Parhi institutional abstract](https://experts.umn.edu/en/publications/finite-word-effects-in-pipelined-recursive-filters/); [2026 primary preprint](https://arxiv.org/html/2609.16488), §§IV–V |

The last source is a newly identified current comparator: *Error-Bounded Fixed-Point Design of Super-Sample-Rate IIR Filters for Real-Time Superconducting Qubit Flux Predistortion*, arXiv:2609.16488. It specifies convergent rounding/saturation and scattered look-ahead; its accuracy assessment includes coefficient sensitivity, imperfect cancellation, and bit-accurate simulation of the transformed datapath. That is serious finite-precision engineering. The inspected sections do not claim reproduction of the original, untransformed quantizer at every sample. Calling all previous pipelines “real arithmetic only” would mischaracterize this literature.

## Ranked route 1: certified narrow entry domains and one-pass boundary deletion

Consider the unsaturated integer recurrence

`s[n+1] = floor((A*s[n] + C[n])/D)`, `0 < A < D`.

Use an ideal affine trajectory `z[n+1]=(A*z[n]+C[n])/D`, initialized at `z[0]=s[0]`. Because the integer numerator's floor error is at most `(D-1)/D`, the accumulated discrepancy satisfies

`0 <= z[n]-s[n] <= ((D-1)/(D-A))*(1-(A/D)^n)`.

Consequently, knowing `floor(z[n])` gives a conservative interval of exact states of width `R=floor((D-1)/(D-A))`. This means `R+1` candidates, not recovery of the correct state merely by rounding `z`. Constant-price trajectories can retain distinct integer states indefinitely. A valid rounding offset is absorbed into `C`; other rounding rules require their own discrepancy proof.

An affine scan can produce boundary estimates in parallel, but it must also certify its own numerical error. An outward interval for `z` plus the quantization discrepancy supplies a legal absolute entry interval `[lo,hi]` for each block. The important simplification is that **only block boundaries need prediction**. No per-event predictor value or exact floor of an approximate real trajectory is needed by the block constructor.

Initialize a block map over that certified entry interval as the identity: base `b=lo` and one set bit for each adjacent input pair. For any current monotone adjacent-0/1 map, its image is contiguous. Store its minimum `b` and a bitmap `M` of surviving input-adjacent jumps, so evaluation is

`F(lo+i) = b + popcount(M[0:i])`.

Appending one ORIGINAL integer transition transforms the current contiguous image. Write `B=D-A` and observe

`floor((A*s+C)/D) = s + floor((C-B*s)/D)`.

If the current image width is at most `R`, then `B*R <= D-1`, so the second floor can drop at most once across that image. Thus the sample preserves every surviving boundary except possibly one. Set

`r = (A*b+C) mod D`,

`j_star = floor(r/B)+1`.

If `j_star` is no greater than the number of currently surviving boundaries, clear the `j_star`-th set bit of `M`. Update `b` to the original transition applied to `b`. The map now exactly represents the enlarged block. Domain width cannot increase, so the narrow-domain condition persists. The input stream is read once to construct the map; there is no separate reverse traversal for each final threshold.

This is an arithmetic specialization of ordered convergence. Generic path factoring updates all distinct candidate states; here the floor contraction identifies the single pair of adjacent image values that merge and translates its output rank back to an original entry boundary with `select`. Deletion arithmetic divides by `B`, potentially much cheaper than reverse construction's division by `A`. Normalized retention `(D-1)/D` has `B=1`, making it the clean first implementation. A larger certified interval may require multiple deletions per sample; this must be implemented or handled explicitly, not hidden by reporting ideal-predictor widths.

After independent map construction, resolve exact block boundaries using these maps and the known initial state. Query a map only within its certified domain. Replay each block from its resolved entry to produce every original sample. A final-state summary does not itself supply the internal output trace, and replay remains real work.

For comparison, a per-event integer predictor `p[n]` gives the equivalent exact residual recurrence

`e[n+1] = floor((A*e[n]+A*p[n]+C[n]-D*p[n+1])/D)`.

That identity is useful for understanding and reference models. The boundary-only constructor avoids generating or storing every `p[n]` and keeps the full-width base arithmetic. Its gain comes from sharing the candidate trajectories' structure, not from making every arithmetic operation narrow.

**What remains worth investigating?** The bitmap, rank/select, finite-state lifting, error bounds, compensation loops and elementary adjacent-collapse actions all have precedents. The specific remainder-to-generator selection was not located, but is elementary. A plausible contribution would be an efficient complete specialization with a measured service/resource advantage. A shared-base rank table also provides one-pass construction, so bitmap compression must win on physical cost rather than a count of avoided full-width candidate operations.

**Primary threat:** the 2004 Parhi/Gu presentation already separates an IIR from a finite-level compensation loop and precomputes the latter. Its modulo precoder and compensation alphabet differ from the floor contraction and ordered deletion here, but the conceptual bridge is close. Full quantizer-loop and precoder papers must be checked before asserting a new decomposition principle. The constructor could still be useful even if that broader principle is fully anticipated.

This was also a published research line: Gu/Parhi's ISCAS 2005 paper, [DOI 10.1109/ISCAS.2005.1464611](https://experts.umn.edu/en/publications/pipelining-tomlinson-harashima-precoders/), and their 2007 TCAS-I paper, [DOI 10.1109/TCSI.2007.904688](https://experts.umn.edu/en/publications/high-speed-architecture-design-of-tomlinson-harashima-precoders/), explicitly describe the finite-compensation reformulation in their institutional abstracts. Those abstracts were checked; neither full article is claimed as read. The boundary-only constructor's claim should therefore concern its specific floor-arithmetic update rather than inventing a wide-linear/narrow-nonlinear decomposition.

**Hard gate:** exact rational affine scanning can grow numerator/denominator precision with the horizon. Assuming that a floating estimate's floor is correct fails near integer boundaries. A practical predictor must deliver outward enclosures; a wider certified domain can be accepted, or ambiguous boundaries refined. Certificate arithmetic, precision, refinement, buffering and scan fill all belong in the cost. The right comparison is against the best exact serial/short-unrolled filter, not an ideal unit-cost inverse model.

Saturation requires separate reasoning. Clipping can remove several adjacent image values at a rail, invalidating the one-deletion assertion even on a narrow interval. The bitmap representation remains valid, but its update must remove those additional boundaries. A normalized bounded price EMA with convex arithmetic can often prove inactive rails. Claim that restricted contract first; add clipping only with explicit invariants and cost.

## Ranked route 2: certified entry intervals with adaptive exact construction

This is the lower-risk implementation path. Generate a certified interval `I_j` for each block entry, then choose the cheapest exact representation on that interval: forward trajectories with convergence factoring, inverse thresholds, residual boundary masks, or direct execution. Block summaries must be valid for every entry in their certificate, and their selected exact boundary must lie inside the certificate. This preserves all output samples after exact replay.

The potential benefit is latency. Full-domain maps need long blocks to reduce an initial width such as `2^17-1`; an affine predictor's rounding enclosure can give a domain on the order of tens or hundreds of integer states at short boundaries. However, it cannot generally shrink uncertainty below the accumulated quantization band. At retention `63/64`, a rounding-only envelope has roughly 64 candidates; at `127/128`, roughly 128. Those are manageable compared with a full table, but are not a proof that eight workers amortize all work. The values depend on the exact rounding and any extra predictor error.

The closest predecessor is Ko's restricted-entry speculation; Cox supplies conservative arithmetic enclosures, and BoostFSM supplies multi-scheme selection. Therefore “use bounds, then run fewer candidates” is probably an engineering combination. A publishable result needs something further: a sharper useful certificate, a provable service bound under adaptive construction, or an implementation that changes the feasible resource/delay region substantially. Dispatching on observed `K` and reporting average speedup is weaker.

If certificates are deterministic and cover every case, call the scheme certified execution rather than probabilistic value prediction. If a heuristic predicts one state, validate it and charge repair. A constant-price run can defeat a typical-case coalescence argument forever; a FIFO does not fix an indefinitely inadequate service rate. Measure deadlines under unfavorable inputs and compare a serial or unrolled fallback with the full pipeline overhead included.

This route is suitable as the first executable comparison harness, even if route 1 becomes the paper's core. It separates the value of a narrower domain from the value of a new constructor.

## Ranked route 3: grouped inverse thresholds or selective checkpoint repair

Batching sorted inverse thresholds can share input reads and constant arithmetic. Adjacent targets can sometimes update quotients/residues incrementally, and common prefixes or checkpoints can avoid repeated traversal. Conversely, a speculative run can retain already correct tails after certified convergence and repair only an unresolved prefix. These are useful ablations and possible hardware optimizations.

Neither is currently a strong independent conceptual claim. Backward ceiling maps with slope `D/A>1` are strictly increasing before domain clipping, so distinct reachable thresholds do **not** naturally merge when traced backward. Claiming trajectory convergence to amortize these inverse walks would use convergence in the wrong direction. Shared constant division and SIMD execution are ordinary arithmetic optimizations unless a new complexity bound is established.

For repair, PBS already proves relations allowing direct output correction instead of full reprocessing; general speculative FSM execution already stops repair after convergence. A scalar quantized EWMA cannot usually correct every output by adding an ideal homogeneous term because the intervening floors change decisions. One must retain enough transition information or prove a concrete correction relation. Checkpointing alone trades storage for recomputation and is not a new way to remove recurrence dependence.

Financial predicate certification is a separate possible project: if only a threshold decision is required, an interval entirely on one side certifies it and only ambiguous cases need refinement. It changes the requested output contract and needs its own genuine financial workload. It should not be silently substituted for exact all-output EWMA replay.

## Search passes, unresolved access, and rejection tests

The first pass followed classic quantizer-loop, exact IIR, finite-word and compensation-loop citations. IEEE full-text/stamp access for Parhi 1991 again failed; the primary IEEE record produced a robot-verification page. The author-linked 1988 thesis on Drive was unavailable through the research fetcher, and Berkeley's thesis PDF returned 403. No full reading of those sources is claimed. Newly recovered primary 2004 slides provide a substantial comparison, but do not close the 1991 obligation. A newly located Chang/Bliss 1994 PDF on finite-wordlength pipelined filters also returned 403; it is a reading lead, not evidence of an audited exact algorithm.

The second pass followed compiler reconstruction, FSM speculation, path fusion and bit-level correction. It recovered BoostFSM's complete extended abstract and Qiu's thesis method for dependent bits, virtual FSMs, lookback and fast recovery. PACT2018/CC2019 authorship and titles were verified against the author's page; unavailable full methods must not be inferred from third-party summaries. The third pass searched finite-chain monotone contractions and found the explicit convex-kernel boundary encoding in Adeshola/Umar. Searches combining residual quantization, rank/select, bitmaps, monotone maps and composition did not identify a prior implementation of the proposed arithmetic deletion engine. That is a limited negative search result, not a priority finding.

A skeptical reviewer can reasonably reject the project for any of these reasons:

1. The proposed contribution reduces to established quantizer compensation plus an elementary encoding, with no meaningful reduction in implemented work.
2. Predictor certification/refinement costs more than the saved construction, particularly for cheap shift/add EWMA baselines.
3. Rank/select feedback or map merging becomes the new timing bottleneck; an `R`-bit mask is small storage but not constant physical logic.
4. Only favorable synthetic inputs show speedup; constant prices, weak contraction, larger fractional precision or hot-symbol latency defeat it.
5. Exactness is asserted for an integer contract without demonstrating why that contract matters for the selected financial task.

The decisive experiment compares, on identical arithmetic and tape order: best serial and small exact unroll; independent-symbol interleaving; full/restricted forward maps with convergence factoring; original reverse thresholds; certified residual tables; and the proposed deletion engine. Report certificate width and ambiguity, constructor work, routed clock, buffers/ports, every-output throughput, and worst delay. For route 1, the essential ablation is **same predictor and certificate, different exact residual constructor**. Otherwise an apparent gain could come entirely from old restricted-entry speculation.

The narrow claim worth trying to earn is: “For a specified class of rounded contractive recurrences, certified residual coordinates permit an ordered boundary-deletion constructor with proved storage/update bounds, and an implementation improves exact replay throughput at a stated delay and resource budget.” It leaves established ideas credited and makes the remaining contribution falsifiable.

## Second-pass verdict on the executable proposal

Reviewed [certified_mask_checks.py](certified_mask_checks.py) and its [results](certified_mask_results.json). The prototype does not obtain certificates from the exact serial oracle: local affine interval summaries, their fixed prefix topology, and the geometric quantization bound generate the domains independently. The serial path validates map entries and replay afterward. Outward parameter multiplication/composition is sound for the implemented nonnegative coefficients and contributions. Rounded interval composition need not be associative; the explicitly selected Hillis–Steele evaluation tree still encloses the corresponding exact affine prefix. Simultaneous deletion uses ranks in the old bitmap correctly. No conceptual exactness defect was found within the stated scope.

The scope requires `0<A<D`, bounded unsigned inputs/initial state, and an offset that preserves the unsigned state interval; `0<=offset<D` suffices for these normalized rules. The low-level signed mask tests do not establish signed predictor certificates. Python's unlimited intermediates do not establish an RTL word-width or overflow contract. Exact powers used to form gain bounds are reasonable offline constants for a fixed coefficient/block length, but are not a runtime implementation for arbitrary changing lengths.

The reported checks support the arithmetic construction: 11,475 mask cases, 80,685 primitive entry comparisons, 1,104 boundary certificates, 49,820 block-entry comparisons, 29,568 replay outputs, and 240 rational-predictor enclosures. They cover synthetic finite traces, including three 4,096-sample runs using eight 32-sample blocks per group across 16 groups. The prototype carries a certified interval for the global unrounded affine trajectory between groups independently of the resolved exact state. Coarse precision caused as many as 96 deletions in one update, demonstrating why a universal single-deletion promise is invalid without a width certificate. Total deletions per block cannot exceed its initial bitmap width, but `select` cost and mask capacity still matter.

The immediate rejection risk is cost displacement. A 17-bit state with 29 fractional predictor bits implies roughly 46-bit intercept arithmetic; the 32-bit/44-fractional-bit case implies roughly 76 bits, before wide products and conservative extra range bits. Local interval summaries precede the exact constructor, and serial boundary resolution precedes replay in this implementation. Its four-level, 16-block prefix performs 49 interval combines, plus one for group carry. None of those operations is a demonstrated clock cycle. The carry is implemented and tested. The later `uniform_capacity_bound()` addition also supplies a conservative all-input capacity calculation for fixed complete groups, using exact rational error bounds and a contractive predictor carry; see [the derivation](CONSTRUCTOR_AND_CERTIFICATES.md). It yields one-deletion caps for the main configurations. That analytical result is distinct from the finite tests, and still establishes no physical-width implementation, service guarantee, or bound for arbitrary partial groups/coefficient changes.

The narrowly defensible result today is **an executable, exact restricted-domain floor-contraction map constructor, supplied by independently computed outward affine certificates and followed by exact boundary queries and all-output replay**. A new algorithm/hardware contribution remains plausible, with the arithmetic collision deletion as its center. Before a priority claim, resolve Parhi's quantizer-loop/precoder methods and PACT2018/CC2019 reconstruction details. Before a performance claim, synthesize certificate arithmetic and rank/select, freeze capacity/fallback and group scheduling, and compare against the same-certificate forward/threshold baselines plus best serial/unrolled RTL. The present evidence justifies that investigation, not a publishability verdict.

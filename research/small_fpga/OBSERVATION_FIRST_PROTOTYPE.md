# Exact block observations without reconstructing every sample

6 November 2026. **A constructed research variant, not a discovered application win.** This changes the executor's observable contract, retains the exact original scalar state machine, and replaces the current wide affine certificate with a competing certificate made from finite input history. It is motivated by small devices that can accept a narrow fast stream but only need occasional measurements or alarm reports.

The useful question is whether a complete implementation can meet a real fast-stream deadline on a smaller device than the best direct exact design. Neither the arithmetic below nor the software tests establishes that result.

## 1. Preserve the right observations

For a known nonempty block of L inputs, let `F_t(s)` be the exact state after t original updates from entry s. Define

```
E(s) = F_L(s)
M(s) = max(F_1(s), ..., F_L(s))
Q_T(s) = [M(s) >= T].
```

The outputs are the exact exit state and either the numeric peak or one fixed-threshold Boolean. No numeric replay is required once the actual entry is resolved. Crucially, `M` excludes the entry state: the maximum is over post-update samples only. `Q_T` reports **at least one sample at or above T**. It does not report an upcrossing edge, first-hit time, count, duration, or a reset caused by the condition. Those are different observables and may need more state or a different construction.

This addresses a real semantic weakness of endpoint-only sampling. In the synthetic byte rule `s'=floor((3*s+x)/4)`, start at zero, send eight inputs of 255 then 56 zeros. The final state is zero, but the within-block maximum is 228. A threshold of 200 was exceeded even though the endpoint is below it. Reducing output rate by discarding that maximum changes an alarm requirement.

## 2. Exact compact state/peak pairs

Every prefix `F_t` is monotone with adjacent output increments in `{0,1}`. Their pointwise maximum M has the same property: monotonicity is preserved, and no function can rise by more than one when the entry rises by one. Thus the exit and peak can each use the existing base-plus-ranks or base-plus-increment-bitmap representation on a domain of width W.

For consecutive blocks 1 then 2:

```
E_12 = E_2 composed with E_1
M_12(s) = max(M_1(s), M_2(E_1(s))).
```

This is an ordinary state-transition summary with an accumulated maximum. **Generic state-plus-output composition is not claimed as novel.** Cost-register/transducer literature is relevant prior art; the possible contribution would have to be a useful, measured specialization of bounded integer maps. [Alur et al., *Regular Functions and Cost Register Automata*](https://www.cis.upenn.edu/~alur/Lics13reg.pdf).

Here is the arithmetic-sharing version tested in the prototype. Store current exit values as `b+u_i` and current peak values as `h+v_i`. One wide update gives

```
b_new, r = divmod(A*b + C, D)
u_i_new = u_i + floor((r-(D-A)*u_i)/D).
```

For the peak, set `d=b_new-h`:

```
h_new = max(h, b_new)
v_i_new = max(v_i, d+u_i_new) - max(0,d).
```

Because both relative vectors lie in `[0,W]`, d can be clamped to `[-W,W]` for the narrow expression: sufficiently positive d selects the new exit map; sufficiently negative d retains the old peak map. Wide base comparison/range detection still costs hardware. Initialize the peak from the first updated map, not the identity map. Storing a second peak map is justified when the consumer needs a numeric maximum or will choose thresholds later.

## 3. The stronger fixed-threshold alternative

For one known T, `Q_T` is a monotone Boolean map, so it needs only a **single entry cutoff**, not a full peak map. While updating the exit map, find the first rank i with `b+u_i>=T` and retain the smallest such original-entry index over the block. An entry at or above this cutoff triggers the Boolean. Include always/never sentinels.

A rank table supports this with lower-bound logic. A bitmap can use rank/select after checking whether `T-b` lies outside the current image. Neither lookup nor its sharing with the constructor is free. The comparison must include this much smaller observable, not assume every alarm requires a second numeric map.

There is also a direct backward competitor. For the normalized invariant rule and state range `[0,Smax]`, initialize `cut=Smax+1`, then process the block in reverse:

```
target = min(T, cut)
cut = clamp(ceil((D*target-C_t)/A), 0, Smax+1).
```

This gives the exact entry cutoff in one backward pass. Division by A may be much more expensive than the forward rule's power-of-two shift; it remains a serious alternative, particularly if inverse hardware is already present. Charge the reverse input reads/storage and division, but do not charge unrelated numeric-peak machinery to this Boolean-only rival. This computes the alarm cutoff, not the exact exit state, which is still needed for subsequent blocks. The prototype tests forward rank cutoffs, backward cutoffs and literal every-sample maxima against each other.

## 4. A competing certificate without the wide affine predictor

Instead of predicting an unrounded global trajectory, take H known inputs immediately preceding a block. Apply those H original integer updates to the legal lower and upper state rails. Their endpoints enclose the true block entry by monotonicity. If the history reaches the actual stream initialization, use the known initial state instead of the rails.

This certificate is independent of unresolved exact preceding block exits. It does **not** obtain its bounds from the serial golden trace. It also avoids the wide affine gains, offsets, prefix products and global affine carry of the current predictor. The price is repeated native computation over overlapping history, storage/access to that history, and possibly much longer blocks to amortize the cost. Restricted-entry lookback is established speculation prior art, not a new general principle. [Ko et al., restricted entry-state execution](https://arxiv.org/html/1210.5093).

For `w_0=Smax`, an input-independent width bound is

`w_(j+1) = ceil(A*w_j/D)`.

The largest positive fixed width is `R=floor((D-1)/(D-A))`. Consequently, this bound cannot promise coalescence below R. It reaches R after a finite number of steps when starting above it; the tests compute the integer recurrence rather than a logarithmic approximation.

For 32-bit unsigned state, the calculated history lengths are:

| Retention | Guaranteed width R | H to reach R | Native updates/input at L=256 |
|---|---:|---:|---:|
| 3/4 | 3 | 75 | 1.586 |
| 15/16 | 15 | 311 | 3.430 |
| 63/64 | 63 | 1,182 | 10.234 |
| 127/128 | 127 | 2,284 | 18.844 |
| 97/100 | 33 | 632 | 5.938 |

The last column counts `1+2H/L`: two history endpoint transitions plus one shared-base constructor transition per input. It omits the narrow ranks, observable, lookup, memory and interfaces. It is **not clocks, throughput or energy**. These L=256 figures extrapolate arithmetic counts; the streamed prototype tests use L=64. Removing the affine predictor can be attractive for short-memory rules and very unattractive for long-memory rules. Two endpoint transitions need not require two independent full-width datapaths: after updating the lower endpoint with remainder r, the exact width updates as `floor((A*w+r)/D)`. Credit this arithmetic sharing and any proved narrowing schedule to all alternatives.

With P workers, an illustrative nonoverlapped schedule that serializes both endpoint transitions on one update datapath per worker uses at least `2H+L+P` issue slots per group if every update and boundary query can issue in one slot. A shared lower-endpoint/width implementation could reduce this history schedule, at a resource and timing cost that must be measured. Longer feedback latency, peak/select logic, history collection, partial blocks and bank conflicts add costs. Overlapping groups requires separate resources and a valid memory schedule. This expression is specific to the stated schedule, not a universal lower bound or achieved speedup.

Short retention at a high physical sampling rate also means a short physical memory. A useful fast-transient consumer must justify that response; changing a desired millisecond smoother into a nanosecond smoother merely to reduce H/R would change the problem.

## 5. Keep exact carry; do not hide an unbounded repair history

The tested executor constructs exact exit summaries, resolves their actual entries in original block order, and queries the corresponding exact peak/alarm. It maintains the true state at every boundary. There is no discarded ambiguity, guessed carry or probability-of-success argument.

Only certifying an alarm from a loose interval is insufficient for future numeric state. If ambiguity never coalesces, a later ambiguous alarm can require information from arbitrarily far back. A bounded FIFO plus an unproved “rare repair” path is not an exact real-time design. The exact exit maps prevent that problem, at a hardware cost that remains in the comparison.

Nor is an immediate trigger equivalent to a block report. Block collection and processing delay must fit the observer's actual deadline. If the alarm resets the filter, gates acquisition, or changes subsequent inputs/coefficients inside the block, the present open-loop map is not the correct machine.

## 6. Executed evidence and limits

[observation_checks.py](observation_checks.py) and [results](observation_results.json) contain:

- 4,080 small binary-input blocks and 30,600 entry comparisons of exit, numeric peak and fixed-threshold alarm;
- 91,800 backward-cutoff sentinel comparisons;
- 6,400 entry comparisons of serial query/observable composition, not a materialized merged-summary circuit or parallel scan;
- 171 exact boundary/peak/alarm triples from finite-history-certified streams across 15 configurations, including 32-bit state, non-dyadic coefficients and partial final blocks;
- the concrete endpoint-misses-peak example above.

The comparisons use literal sequential updates as an oracle after independently generating the certificates and maps. The main suite initially generated one threshold outside its declared test range; its input generator was corrected before the persisted successful run. No arithmetic mismatch was found in the admitted test domain. This is finite software evidence, not a formal RTL proof or a production interface implementation.

The current reference uses rank vectors and constructs both numeric peak and Boolean outputs to cross-check them. A real fixed-threshold design should omit the unused numeric peak machinery. The prototype does not supply a bitmap peak-update circuit, synthesis estimate or scheduling proof. Those are comparison subjects, not implicit results.

An [independent audit](observation_independent_checks.py), with [persisted results](observation_independent_results.json), reproduced the main results and added 499,810 arbitrary-input/domain entry comparisons, 25,243 inverse-cutoff boundary comparisons, 32,145 restricted-image composition comparisons and 12,000 history certificates. It also checked peak-clamp branches, post-update-only semantics and out-of-domain rejection. No mismatch or use of the serial oracle to generate certificates was found. See the [audit discussion](RESOURCE_EFFICIENT_DIRECTION.md#9-independent-review-of-the-observation-prototype) for scope and accounting limits.

For a first RTL test, use only a small exact direct baseline and a two/four-worker endpoint-plus-alarm design with the same coefficient, widths, input packing, delay and device. Compare the existing affine certificate against finite-history endpoints where relevant. Continue only if a real consumer needs the exact observer and the complete design improves the minimum resource cost of meeting its input rate. No inspected deployment yet supplies that full result.

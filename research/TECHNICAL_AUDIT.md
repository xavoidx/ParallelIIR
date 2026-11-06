# Technical audit and reproducible checks

4 November 2026. This is an independent assessment of the supplied WIP, not a modification of the implementation or a hardware benchmark. Run `python research/audit.py` from the repository root to regenerate [audit_results.json](audit_results.json). The script's mathematical oracle uses Python integers; the optional original-model check imports NumPy through `GoldenModel.py`.

## What the current repository demonstrates

The supplied Python code illustrates endpoint evaluation, backward threshold construction, sequential boundary resolution and replay. It does not implement concurrent workers, a tree of composed maps, RTL, bounded-capacity storage or sustained streaming. Comments marking loops `PARALLEL` identify potential parallelism; Python still executes them sequentially. This is appropriate for an early functional prototype, but it supplies no speedup evidence.

The October internal documents report independent earlier experiments. Their underlying archive, scripts and JSON files are absent from this repository. Those counts are historical claims from the supplied documents, not results reproduced here. The new check below is separate and deliberately smaller.

| Issue | Evidence in supplied source | Consequence |
|---|---|---|
| Configurable width does not control saturation | `GoldenModel.py:16` hardcodes `max(-8,min(7,...))` | The nominal 16-bit test compares two implementations of a four-bit-clipped transition |
| Serial and parallel tests share this arithmetic | `Testbench.py:64–65` calls the same model | Equality cannot detect a shared wrong reference contract |
| Incomplete four-bit alphabet | `Testbench.py:13,25–26` uses radix 15 and subtracts 8 | Enumerates -8 through 6, omitting +7; four-bit tests are disabled by default |
| Biased random stimulus | `Testbench.py:58` draws nonnegative inputs only | Particularly likely to drive this four-bit-clipped model into saturation |
| Failure diagnostic can raise another exception | `Testbench.py:71` uses `iteration`, assigned only in disabled four-bit branch | A mismatch in the enabled path may be obscured by `NameError` |
| Reference arithmetic not fully explicit | Floating `a`, `math.floor`, floating division and `math.ceil` | Current tested dyadic coefficients can be safe at small widths; arbitrary rationals/large states need exact integer arithmetic and explicit widths |
| Boundary state fixed at zero | `GoldenModel.py:41` | Full-trace tests should also cover nonzero initialization and continuation across batches |
| No runtime domain validation | Constructor accepts arbitrary coefficient, width and P | Document/enforce the supported contract before treating it as a reusable exact executor |

Minimal reproduced counterexample: `ParallelFilter(0.5,1,16).serialPass([100,0,0])` emits `[7,3,1]`. A genuinely 16-bit floor-and-clip implementation emits `[100,50,25]`. The SHA-256 of the inspected source is recorded in the results file. Original project files were left intact.

## The exact contract is coherent

For integer state `s ∈ [lo,hi]`, define

```
f_n(s) = clip_[lo,hi]((A_n*s + C_n) // D_n)
0 <= A_n < D_n, D_n > 0
```

Here `//` denotes mathematical floor, including negative numerators. Inputs and coefficient schedules are known before resolving the block's entry. Multiplication/addition use sufficient width; overflow is not silently modular. A final output conversion may be applied after each state update if it preserves the original program's semantics.

One-state monotonicity and adjacent differences of zero or one survive composition. Therefore a block map has a contiguous image; store `v=F(lo)` and crossings `t_j=min{s:F(s)>=v+j}` for `j=1..K`, `K=F(hi)-F(lo)`. Evaluation is `v + upper_bound(thresholds,s)`.

The guarded inverse threshold is `lo` for targets at/below `lo`, `hi+1` for targets above `hi`, and otherwise, when `A>0`, `clamp(ceil((D*t-C)/A),lo,hi+1)`. A zero coefficient is a constant transition and needs its own branch. Integer ceiling is `-((-numerator)//denominator)` for positive denominator. Pull thresholds backward through the entire block. Although in-image targets can make some guards unnecessary in a tightly scoped constructor, a reusable composition/preimage routine needs explicit semantics for impossible targets.

These are correctness arguments, not strong standalone novelty claims; see the finite-chain contraction and adjoint literature in [PRIOR_ART.md](PRIOR_ART.md).

## The logarithmic estimate is not a capacity guarantee

Let `R=hi-lo`. A deterministic integer bound is

```
w_0 = R
w_(n+1) = ceil(A_n*w_n / D_n)
K <= w_L
```

It follows by comparing two floored affine values and using the nonexpansiveness of clipping. For constant `a`, a looser explanatory envelope is `K <= a^L R + (1-a^L)/(1-a)`, as well as `K<=R`. Unlike the unrounded `a^L R`, it retains a quantization term. The exact integer recurrence is preferable for capacity planning.

There is also a constructive obstruction, stronger than merely a loose bound. With zero input and `a=(m-1)/m`, every integer in `[-(m-1),0]` is fixed, provided that interval lies inside the state domain. Thus `K>=m-1` for every block length. For 16-bit states and this repository's coefficients 63/64, 127/128, 255/256 and 511/512, silence can retain at least 63, 127, 255 and 511 thresholds respectively. No choice of L reaches K=3 on these silence cases. The fixed-point claim follows directly from `floor(-k+k/m)=-k` for `0<=k<m`.

The approximation `L≈ln(R/K)/(-ln(a))`, then `-ln(a)≈1-a`, describes an unrounded envelope. It can guide exploration when K is far above the rounding scale, but it cannot justify universal compactness, finite buffer capacity or a service guarantee. At `a=0`, the logarithmic form is inapplicable and every nonempty block is constant.

## New software results

The independent exact implementation passed:

| Check | Coverage | Mismatches |
|---|---:|---:|
| All entry states for selected exhaustive input families | 1,250 blocks; 15,000 state comparisons | 0 |
| Variable-coefficient/input random blocks, all states | 32,352 state comparisons | 0 |
| Composition and associativity | 300 three-block cases | 0 |
| Complete replay outputs with random initial state | 4,782 outputs | 0 |

Exhaustive families cover 3/4-bit states, all length-three sequences over five selected input values, and five coefficients including zero and non-dyadic 2/3. Random cases use 4/6/8-bit states, variable denominators and signed input contributions, including saturation. They do not exhaust all sequences or validate hardware widths. Composition is checked against direct full-block execution. These results support the stated finite cases only.

Endpoint-width sweeps cover 100 configurations with true 16-bit state. The random generator seed is 20261104. Each random configuration uses 16 blocks; deterministic configurations use one. “Scaled random” selects integer inputs uniformly from `[-q,q]`, where `q=max(1,floor((1-a)*32767/4))`; this is a declared synthetic workload, not an application dataset.

| a | L | Silence K | Scaled-random median K | Full-range-random median K | Certified K bound |
|---|---:|---:|---:|---:|---:|
| 1/2 | 64 | 1 | 0 | 0 | 1 |
| 3/4 | 64 | 3 | 0 | 0 | 3 |
| 63/64 | 64 | 23,918 | 23,919.5 | 0 | 23,939 |
| 255/256 | 64 | 51,012 | 51,014 | 0 | 51,039 |
| 511/512 | 64 | 57,830 | 57,828 | 0 | 57,857 |
| 63/64 | 1,024 | 63 | 0 | 0 | 63 |
| 255/256 | 1,024 | 1,199 | 1,196.5 | 0 | 1,317 |
| 255/256 | 4,096 | 255 | 0 | 0 | 255 |
| 511/512 | 4,096 | 511 | 31.5 | 0 | 511 |

Full-range random input has frequent clipping: around 30–32% of samples from zero state in these near-unit-pole examples. Scaled random does not clip on those traces. Both have the same state width and coefficient, yet very different K. Endpoint trajectories can also merge through rounding without clipping. Consequently report actual input scaling, distributions, saturation and worst-case widths; the label “random inputs” is insufficient. The old appendix's random distribution is not recoverable from the available files, so this is not a reproduction or contradiction of its numerical result.

## A usable performance model

Separate input period `T_in`, fabric clock period `T_clk`, direct recurrence time, and inverse-step time. They need not be equal. Let `c_f` and `c_i` be measured effective dependent-update costs in clock cycles for forward and inverse walks. Under a simple architecture with one engine per block doing its passes sequentially,

```
C_lane ≈ 3*L*c_f + K*L*c_i
C_compute ≈ max_lane(C_lane) + C_boundary + C_memory/control
```

The three forward passes are two endpoints plus replay. A rough comparison to a serial same-clock implementation for P blocks is `P*L*c_serial/C_compute`. Only after assuming equal-cost one-cycle updates and ignoring everything else does this reduce to `P/(K+3)`. That quantity is an optimistic model for a particular resource schedule, not measured speedup. Inverse steps for constant coefficients can sometimes be lowered to exact multiply/shift or arithmetic identities, so their cost should be measured rather than automatically assumed large. Their own feedback chains still constrain scheduling.

For a batch that waits for all `N=P*L` inputs, collection takes approximately `(N-1)*T_in` from the first arriving sample. Add the actual schedule's map preparation, boundary resolution, replay and output ordering delays. If phases overlap, use a cycle schedule, not a sum that double-counts overlaps. `L*(P+c+K+1)*T_s` in `SPEC.md` mixes collection and compute periods unless an additional equal-clock assumption is made; it also omits boundary/memory/output costs and does not distinguish first from last output.

Across repeated batches, the next batch's first state depends on the previous exit. Map preparation can start early because it is state-independent, but resolved outputs still need that state. Sufficient double buffering, memory ports and output bandwidth must be included. A serial output interface may cap useful throughput regardless of internal lane count. A serial fallback can be bit-exact and still miss arrivals; evaluate the worst sustained legal input pattern as well as averages.

At K=3 with 16 identical one-pass engines, the idealized factor is only `16/6≈2.67` before omitted overhead. At K=255 it is `16/258≈0.062`, using that same sequential-pass architecture. Parallelizing thresholds can reduce latency, but allocates additional engines and bandwidth, so it changes the equal-resource comparison. K also does not lower-bound all possible descriptions: an identity interval contains many thresholds but has a simple arithmetic representation. Hybrid summaries deserve investigation.

## Immediate implementation priorities

1. Freeze native arithmetic, replace floating reference coefficients with exact A/D, and make saturation use the intended width. Keep a separately specified serial oracle.
2. Repair test coverage and failure diagnostics; add mixed signs, nonzero starts, consecutive batches, short/empty blocks and out-of-contract rejection. These are required future changes, not edits made in this review.
3. Record K and inverse work using actual native signals before writing hardware. Never silently discard large-K cases.
4. Synthesize forward, inverse, map-query and storage primitives on the actual device. Compare constant-coefficient specializations and restricted forward tables before committing to an architecture.
5. Build a complete schedule and strongest exact comparator; measure sustained rate, delay and resources after routing. The current repository has no evidence for that stage.

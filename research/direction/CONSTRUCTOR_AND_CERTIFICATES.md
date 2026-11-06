# Mathematical contract and executed checks

6 November 2026. Companion to [RESEARCH_DIRECTION.md](RESEARCH_DIRECTION.md). These are derivations and a software reference model for the proposed constructor. They are not a priority claim, a formal machine-checked proof, or a hardware result. Ordered finite-chain maps, numerical enclosures and rank/select already have precedents; see [NOVELTY_AND_COMPETITORS.md](NOVELTY_AND_COMPETITORS.md).

**Third-pass status:** independent literal-table/rational checks found no valid-contract counterexample. The [audit](INDEPENDENT_MATH_AUDIT.md) records the exact scope and repaired interface defects. The [overall verdict](THIRD_PASS_VERDICT.md) withdraws any inference of bitmap superiority from generic trajectory counts and identifies explicit prior adjacent-collapse generators.

## Supported contract

Let `0<A<D`, `m=D-A`, and

`s[n+1] = floor((A*s[n] + C[n])/D)`.

The current prototype uses `C[n]=m*x[n]+rho`, integer `0<=rho<D`, and unsigned state/input in `[0,H]`. This interval is invariant: the numerator lies between zero and `D*H+rho`, whose floor-divided maximum is H. There is no saturation or modular overflow. Initial state is known. Constant coefficients and known, ordered inputs permit independent block preparation. Absorbing rho into C preserves the actual rounded integer machine.

Signed innovations, active clipping, variable/time-derived coefficients and the Illinois difference-truncation rule require extensions. The generic mask primitive is tested with signed base/C, but the predictor's nonnegative interval-product implementation does not support arbitrary signed financial inputs. Do not infer broader pipeline coverage from the primitive tests.

## 1. Bound unresolved states using an independent linear calculation

Define the unrounded recurrence `z[n+1]=(A*z[n]+C[n])/D`, with `z[0]=s[0]`. Each original integer rounding error is between zero and `(D-1)/D`. By induction:

`0 <= z[n]-s[n] <= ((D-1)/m)*(1-(A/D)^n) <= G`,

where `G=(D-1)/m`. If a separate calculation certifies `z[n] in [zlo,zhi]`, then the legal exact boundary interval is

`I[n] = [ceil(zlo-G), floor(zhi)] intersect [0,H]`.

This interval contains the actual state without executing its exact serial history. Its width is at most `floor(G + zhi-zlo)`. The perfect-predictor bound is `R=floor(G)`. R is independent of state word length for a fixed coefficient; its physical width is in state LSBs. Increasing fractional precision does not increase R, but it does increase predictor/base arithmetic widths. Retention approaching one still makes R large.

For each block, the unrounded map is affine: `z_out=g*z_in+h`. The software computes enclosing fixed-point intervals for g and h. The gain is a precomputed bound on `(A/D)^L`; the offset is constructed by two directed-rounding recurrences starting from zero. A Hillis–Steele prefix topology composes those interval maps. For nonnegative parameters, each product/add is rounded outward. Rounded interval composition is not associative as an interval-valued operation; nevertheless each fixed tree encloses the corresponding exact affine composition. No exact serial-state oracle supplies certificates.

The reference uses `F=w+12` fractional bits in the main experiments. It computes exact rational powers only to generate fixed configuration constants. An RTL implementation should precompute these constants or charge their runtime construction if L/A/D change. The code uses arbitrary-precision intermediates; hardware widths must be established separately.

## 2. Construct the exact map by deleting increment positions

For a block-entry interval `[lo,hi]` of width W, initialize a W-bit all-ones mask M and base `b=lo`. At any point the exact map has the form

`F(lo+i) = b + popcount(M & (2^i-1))`, for `0<=i<=W`.

The image is a contiguous interval of width `k=popcount(M)`. Append one original update. Write

`b_new, r = divmod(A*b+C, D)`.

At image offset j, elementary integer algebra gives

`f(b+j) = b_new + j + floor((r-m*j)/D)`.

If `m*k<=D-1`, the last floor changes from zero to minus one at most once. The lost adjacent boundary has **output rank**

`j* = floor(r/m)+1`.

If `j*<=k`, clear the j*-th set bit of the OLD mask. Set `b=b_new`. This preserves the exact map for every entry, including entries different from the eventual actual state. Since k never increases, a width cap `W<=floor((D-1)/m)` remains sufficient throughout the block.

For larger W, all deleted ranks are

`j_t = floor((r+t*D)/m)+1`, for `t=0,1,...` while `j_t<=k`.

Clear these ranks simultaneously with respect to the old mask. Sequentially looking up unchanged rank numbers in an already shortened mask is wrong. The number of deletions is at most `ceil(m*k/D)`. The prototype supports this general case; an RTL design can instead admit only configurations with a proved small deletion cap.

For retention `(D-1)/D`, m=1 and collision-rank arithmetic needs no general divider. The rank-to-bit-position operation still needs actual hardware. The number of bits in M is small storage, not a claim that selecting a set bit has constant circuit delay. For 61/64, m=3; a constant divider or bounded comparison network is needed. Base arithmetic remains full width.

Each block constructor streams its inputs once, updating one base and the mask. This avoids enumerating all candidate values and avoids separate reverse passes for every final threshold. It does not remove predictor construction, boundary queries, or output replay.

## 3. Resolve boundaries and emit every output

After independent construction, query each block map with its actual entry state, starting from the known initial state and propagating exits in order. Immutable summary metadata now stores the original inclusive domain; evaluation rejects entries outside it and supplied bounds that disagree with it. The prototype uses a serial sequence of P queries; it does not implement a logarithmic tree of mask compositions.

Replay each block with the original integer update and its resolved entry. Concatenating these replay traces is identical to serial execution by induction over block boundaries. A summary provides only a block-exit function; replay is what supplies all intermediate outputs. The current code retains inputs and pays this additional pass.

## 4. Keep certificates valid across groups

Waiting for the previous group's exact exit to restart prediction can introduce an unwanted group-level dependency. Instead carry an interval enclosing the **global unrounded z** across groups, independently of exact-state resolution. Apply the same global rounding bound G to each resulting boundary. Do not repeatedly add G to the carried predictor interval.

There is a conservative uniform capacity calculation for fixed complete groups. Let `S=H+rho/m`, so the unrounded trajectory and every zero-initialized block offset lie in `[0,S]`. Let a group gain be enclosed by `[glo,ghi]`, its offset width be `E_h`, and fixed-point scale be Q. If carried interval width is E, outward arithmetic implies

`E_next <= ghi*E + (ghi-glo)*S + E_h + 2/Q`.

If `ghi<1`, define `delta=(ghi-glo)*S+E_h+2/Q`. Starting from a point interval, `E<=delta/(1-ghi)` is an invariant upper bound. For a prefix within the next group, apply the same expression with that prefix's gain/offset error. Combine this with G to obtain an integer mask capacity.

The prototype's `uniform_capacity_bound()` constructs a sufficient E_h without looking at a particular tape. For the local offset recurrence, bound its integer interval width by `w_h_next=ceil(A*w_h/D)+1`, starting at zero. For composition of an after-map and before-map, a sufficient offset-error bound is

`E_h_composed <= g_after_hi*E_h_before + (g_after_hi-g_after_lo)*S + E_h_after + 2/Q`.

Propagate these bounds through the same prefix tree and the group carry. Calculations, returned proof fields and verification comparisons use exact rational arithmetic. Display-only float fields can be null on overflow without invalidating the exact bound. If the upper group gain rounds to one, this test returns no finite carry certificate. It is a sufficient test, not an optimal bound or a proof that another configuration cannot work.

For P=16, L=32, F=w+12, both w=17 and w=32, the checked fixed configurations give **uniform mask-width caps 15, 21, 63, 127 and 33** for retentions 15/16, 61/64, 63/64, 127/128 and 97/100 respectively. Each implies at most one deletion/update, for every bounded input sequence under these arithmetic assumptions. This is an analytical capacity result, not a timing, port, queue or physical-overflow guarantee. Partial groups, resets and changed coefficients require their own constants/bounds or an exact direct path.

## Executed checks and comparison counts

Run `python3 research/direction/certified_mask_checks.py`. It writes [certified_mask_results.json](certified_mask_results.json). The persisted test suite passes:

| Check | Count |
|---|---:|
| Primitive mask updates, including signed bases/C and multiple deletions | 11,475 |
| Primitive entry comparisons | 80,685 |
| Exact-state membership in independently generated certificates | 1,104 |
| Complete local map/entry comparisons | 49,820 |
| Every-output replay comparisons | 29,568 |
| Predictor enclosures checked against exact rational affine boundaries | 240 |

The suite includes 30 main configurations, coarse-precision stress, and three 4,096-event runs with independently carried certificates over 16 groups. All inputs are synthetic. Deliberately coarse F=3 caused as many as 96 deletions/update, showing why a one-deletion circuit needs a proved configuration bound rather than an observed typical width.

For the 512-event, 17-bit, retention-63/64 one-tick random-walk case, the same certified domains produce these constructor counts:

| Exact constructor | Count, excluding common prediction/resolution/replay |
|---|---|
| Forward trajectories with ideal convergence factoring | 27,361 state updates, plus selector maintenance |
| Restricted inverse thresholds | 25,152 inverse steps plus 1,024 endpoint steps |
| Forward deletion mask | 512 base updates plus 144 rank selections/bit clears |

The chosen predictor additionally performs 1,024 wide offset-endpoint updates, 200 unspecialized interval-composition products and 34 boundary/carry application products; replay needs 512 original updates and resolution needs 16 queries. These are unlike operations and must not be added as equal-cost clocks.

**Baseline correction:** the table above evolves distinct full-width candidate states. A stronger relative-rank table shares one full-width base/remainder update per sample and updates only small ranks, also in one pass. Thus it too needs 512 full-width base updates in this example. Bitmap versus ranks is a physical storage/feedback tradeoff requiring RTL measurement; the old counts do not establish a win. See [representation_checks.py](representation_checks.py) and [the audit verdict](THIRD_PASS_VERDICT.md).

The reference now rejects noninteger configuration, invalid query domains and malformed public dimensions. Its default 65,536-bit software mask allocation guard prevents accidental huge masks; this is not FPGA admission or an implemented fallback. The verification runner refuses `python -O`. The independent audit separately verifies that runtime input rejections remain active with assertions disabled.

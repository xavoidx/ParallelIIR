# Independent feasibility challenge: certify the architecture, not just the mask

6 November 2026. This is an adversarial review of `RESEARCH_DIRECTION.md`, `RTL_FEASIBILITY.md`, `certified_mask_checks.py` and `FINANCIAL_WORKLOADS.md`. It supplies derived necessary conditions and proposed experiments, not RTL or a measured device result. New external facts below use primary sources inspected in this pass.

## Decision

The arithmetic direction remains credible, but **the central hardware hypothesis should be certified, arithmetic-shared local execution, with the bitmap as one representation to compare**. A stronger exact baseline has the same one-pass construction and one full-width state update per input, without the bitmap's rank/select feedback. The existing comparison against thousands of independently evaluated candidate states does not establish that the bitmap is the essential improvement.

The most serious application objection is unchanged: one rounded EMA is cheap, many financial states are independent, and tape preparation or output can dominate. Exact execution is useful for a specified reproducible feature without being a production bottleneck. No inspected source supplies the missing per-state rate/deadline requirement. A sound research result can be a measured architecture tradeoff; it should not inherit a demand from aggregate feed bandwidth.

## 1. A mandatory stronger baseline: shared base plus small residual ranks

Let the current block map on its certified domain be

`F(lo+i) = b + v_i`, where `v_0=0` and `0 <= v_i <= W`.

The `v_i` are ordered integer ranks, including duplicates. They need only `ceil(log2(W+1))` bits each. For an incoming update, compute **once**

`A*b + C = D*b_new + r`, with `0 <= r < D`, and `m=D-A`.

Then every table entry obeys the exact identity

`v_i_new = floor((A*v_i+r)/D) = v_i + floor((r-m*v_i)/D)`.

When `m*W <= D-1`, set `j_star=floor(r/m)+1`. The update simplifies to

`v_i_new = v_i - [v_i >= j_star]`.

Thus a parallel residual-rank table uses one full-width base/remainder update, broadcast `j_star`, and many **small** compare/decrement units. It does not need one full-width multiply/add/divide for every candidate. Initial ranks are `v_i=i`; lookup after boundary resolution returns `b+v_(entry-lo)`. No sorting or compaction is required. For wider domains the general identity remains exact; small residual constant arithmetic can replace the one-decrement case.

The bitmap and residual-rank table encode the same monotone map. Their practical difference is state compression and feedback/lookup circuitry:

| Representation at width W | Variable map payload, excluding base/metadata | Dependent update | Boundary lookup |
|---|---:|---|---|
| Bitmap | W bits | Find the original position of rank `j_star`, clear it | Prefix population count |
| Direct residual-rank vector | `(W+1)*ceil(log2(W+1))` bits, with `v_0` omittable | Broadcast small compare/decrement | Select one small rank |
| Ordered surviving boundary positions | Up to `W*ceil(log2(W+1))` bits | Remove one entry and shift/rename suffix | Ordered threshold lookup |

At W=63, the straightforward rank vector uses 384 bits versus 63 mask bits; at W=127, 896 versus 127. These are storage counts, not LUT/clock estimates. The bitmap may win resource efficiency, while the larger rank vector may win clock or simplify control. An all-bit bitmap update based on prefix counts and comparisons is another circuit to compare with a centralized select network. It is equivalent arithmetic, but routing can differ.

**Required correction to the interpretation of software counts:** `factored_updates += popcount(mask)+1` counts active-state transitions for one candidate execution method. It does not lower-bound the cost of all forward tables. The 27,361-versus-512 comparison must not be described as a 53-fold hardware work reduction relative to the strongest exact alternative. Both mask and residual-rank constructions use 512 shared full-width base updates; their small-state logic differs. The broad arithmetic-sharing insight may matter more than bitmap deletion itself.

Independent arithmetic check in this review exhaustively evaluated the single-decrement identity for D=2..17, every A=1..D-1, bases -7..7, C=-D..D and every legal residual v. All **193,560 comparisons passed**, including negative base/numerator cases using mathematical floor. This confirms the algebra, not signed predictor support or any timing claim.

## 2. Same-certificate alternatives must receive the whole benefit

Use the identical independently generated certificate for every constructor. Compare mask, residual ranks, ordinary candidates with convergence factoring, local inverse thresholds and exact endpoint propagation. Charge shared arithmetic wherever it can actually be shared. A restricted full-width candidate table is useful as a correctness reference but is too weak as the sole performance opponent.

A restricted endpoint pair is particularly cheap and can certify suffixes after coalescence. A speculative chosen-entry trajectory can retain its outputs; after resolving the entry, replay only the still-unresolved prefix when coalescence makes that valid. This can save replay or storage on convergent blocks. It cannot invent correct pre-merge outputs, and quiet persistent-ambiguity blocks can force full replay. It is a hybrid worth costing before committing to a full map engine.

Also separate **map construction** from **every-output execution**. At every-event output the mask still needs a second exact pass. At block-final-state output it may avoid that pass, but a serial baseline also produces only the requested outputs. At threshold decisions, certify directly from enclosures before constructing every exact state. These are three distinct workloads.

## 3. Necessary cycle, resource and port conditions

Write N=PL events per group, q_p dependent latency per predictor endpoint update, q_c per constructor update, q_r per replay update, q_b per boundary lookup, and C_s scan/carry/certificate cost. With P simultaneous block workers and paired predictor endpoint lanes, a simple nonoverlapped schedule has

`C_group >= L*q_p + L*q_c + P*q_b + L*q_r + C_s`.

With one shared endpoint lane per block, the first term is at least `2L*q_p`. With fewer workers, account for the corresponding batches. Input collection and output drain add latency; interface/memory limits can add occupancy too. This is a schedule lower bound under stated lane allocation, not an implementation estimate.

For P=16, L=32, all q=1 and a single scan engine idealized at 50 total initiation slots, the bound is 162 cycles, or **3.16 events/cycle**. Sequential endpoint use gives 194 cycles, or **2.64 events/cycle**. Omitting predictor updates entirely still gives 130 cycles, or 3.94 events/cycle. These examples omit scan pipeline/barrier delay and certificate arithmetic, and require sixteen constructor/replay workers. A four-event exact unroll is a serious competitor; clocks and resources must be measured separately, so these numbers establish neither victory nor defeat.

The prototype's P=16 Hillis–Steele scan performs 49 combines plus a group combine. Four general products per combine give 200 composition products. Applying prefix maps to the global carry additionally entails up to two products per block and two for the new carry in the straightforward formulas. Fixed gains and known topology allow constant specialization and sharing. Count the implemented arithmetic; do not treat 200 as a complete multiplier-operation bill or four scan levels as four physical clocks.

Overlapping groups changes a sum into a maximum only with separately allocated engines and nonconflicting ports. If a stage uses R engines, its group interval is at least its operation demand divided by R's delivered service rate, with recurrence feedback constraints retained. In particular:

* The global affine carry is itself a recurrence. Its feedback latency bounds the interval between groups using that carry; adding groups does not hide one carry's unresolved dependency.
* A serial exact boundary resolver needs P dependent lookups per group; its throughput is at most `PL/(P*q_b)=L/q_b` events/cycle before other stages.
* Constructor plus replay need at least 2N input reads after fill unless a proven residency/broadcast schedule removes a read. Concurrent construction and replay on different groups require banks for both.
* Every-output service with output width b_o and port capacity B_o bits/cycle is at most `B_o/b_o` events/cycle, regardless of the number of workers. Input capacity similarly bounds service by `B_i/b_i`.
* Output from P replay workers is naturally block-interleaved. Original tape order needs storage or a drain schedule. Tags alone do not provide original-order outputs.

To beat an exact U-event unroll at its own routed clock f_U, a group engine at f_M must satisfy

`f_M * PL / C_group > f_U * U`,

with equivalent resource and output budgets, or demonstrate lower resource/energy at equal required throughput. Same events/cycle at a lower clock is a loss in throughput. Equal-area comparisons should also allow independent-state replication of the direct baseline. A masked engine's saved state bits do not pay for a wide predictor automatically.

At complete-job level, if the accelerated kernel consumes fraction p of baseline job time and gets speedup S, the ideal total speedup is at most `1/((1-p)+p/S)` when other work is unchanged. This derived accounting bound is the reason to measure decoding, transfer, book reconstruction and output consumers independently.

## 4. Snapshots, repeated replay and natural batching can erase the need

An existing exact snapshot at each block boundary makes blocks independently replayable immediately. With unchanged feature definition, coefficient, initialization and tape, a snapshot is a stronger certificate: a singleton. It removes the map constructor, global predictor and resolver for subsequent replays. The initial snapshot-production pass must be charged on a cold job and amortized explicitly over repeated jobs. A new parameter or arithmetic format generally invalidates old feature-state snapshots.

For R repeated jobs, snapshot generation time T_p and subsequent replay time T_s, compare `T_p/R + T_s` with the map executor's recurring job time. Already available snapshots deserve a zero *incremental* production cost, together with a clear statement of their origin. Frequent short range queries can make indexing/snapshots better than accelerating full-tape replay. Conversely, one never-before-evaluated coefficient and a cold tape is a legitimate snapshot-unavailable test.

Independent instruments, days with real reset states, horizons, parameter candidates and scenarios are natural batch dimensions. Give serial and two/four-event exact unroll implementations the same batch. Interleaving at least q independent states can hide a q-cycle arithmetic feedback path if the access schedule and state memory permit it. Hot-symbol or hot-candidate contention must be measured. A daily reset can create an exact start; arbitrarily splitting a continuous tape cannot.

The scientifically strongest remaining case is a **cold, long, single dependent tape with no usable exact checkpoints, financially acceptable fixed arithmetic, sufficient surrounding bandwidth and a throughput requirement above the best small unroll**. It is narrower than general historical financial replay, but well defined.

## 5. Horizons, units and precision need an explicit application matrix

Distinguish retention a from the innovation coefficient alpha=1-a. The official pandas recursive EW definition (`adjust=False`) uses innovation `alpha=2/(span+1)`; its default adjusted mean has a different startup contract. This is a useful parameter translation, not evidence that pandas floating output implements the proposed integer feature. [Official pandas EW documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html).

| Retention a in current proposal | Equivalent span | Half-life in selected events | Ideal rounding-certificate width `(D-1)/(D-A)` |
|---|---:|---:|---:|
| 61/64 | 41.67 | 14.44 | 21 |
| .97=97/100 | 65.67 | 22.76 | 33 |
| 63/64 | 127 | 44.01 | 63 |
| 127/128 | 255 | 88.38 | 127 |

Values are derived, with `half_life=ln(.5)/ln(a)`. The uniform finite-predictor caps can be wider, as the prototype already reports. At one thousand selected events/s, 63/64 has a 44 ms half-life; at one million/s, it has a 44 microsecond half-life. These rates illustrate units and are **not measured typical market rates**. For bursty event time, a fixed event half-life has no single physical half-life. Timestamp-based decay is a separate contract.

Include an explicit span sweep, for example 12, 26, 64, 128, 256, 1,024 and 4,096. With exact reduced `a=(span-1)/(span+1)`, the corresponding sufficient one-deletion widths `floor((D-1)/(D-A))` are **6, 13, 32, 64, 128, 512 and 2,048**. This exposes the scaling that the four short-memory configurations hide. The first two spans have a recognizable financial reference: TA-Lib's MACD implementation defaults to fast/slow periods 12/26 and signal period 9. That supports an illustrative price-indicator control, not a production event-rate requirement or an optimal liquidity horizon. [Maintainer MACD source](https://github.com/TA-Lib/ta-lib/blob/main/src/ta_func/ta_MACD.c).

Choose each horizon for the feature/consumer first. Report input unit, selected-event schedule, mean and burst event rates for the *same state*, physical horizon and observation cadence. Several horizons are separate independent states that strengthen the direct batch baseline. An exponentially decayed state with very long memory has uncertainty of order `1/(1-a)`; for half-life H events it is approximately `H/ln(2)`, so tens-of-candidates is not a general finance guarantee. Timestamp ties or rounding can produce a=1; the constant strictly contractive capacity proof then does not apply. A zero-decay event is a useful reset, while a long a=1 run can preserve all unresolved ranks.

For nearest physical quantization step Delta and no other approximation, the elementary steady error bound is `Delta/(2*(1-a))`. If an application elects a worst-case rounding-error budget of 0.01 physical units, binary fractional bits f must satisfy `2^-f <= 0.02*(1-a)`. This gives f at least 11/.97, 12/(63/64), 13/(127/128), and 16/.999. These are **conditional numerical illustrations**, excluding coefficient/input error, clipping and finite warm-up; they do not prescribe appropriate price/share resolution. Actual decision disagreement may be much less than a worst-case bound and needs measurement.

Increasing fractional precision widens the full legal integer domain and full-width arithmetic, but **does not by itself widen the certified interval in integer state units at fixed a** when predictor accuracy is maintained. It raises base/predictor/resource costs. This distinction should replace any implication that extra precision necessarily requires longer local blocks in the new certified-domain method. Changing the coefficient to preserve a physical time horizon at a higher event rate is different: that does increase a and therefore the certificate width.

The firm-authored Flex Model article establishes an event-state feature framework with many features, frequent event updates and separate evaluation behavior. Its examples and performance discussion do not identify a rounded integer EMA as the bottleneck. Treat this as workload motivation while measuring whether a compatible subgraph is large enough to matter. [Jane Street engineering article](https://blog.janestreet.com/flex-model-an-event-driven-feature-engineering-system/).

## 6. UP5K is a constrained experiment, not the P=16 implied target

The official device inventory is 5,280 logic cells, 30 EBRs totaling 120 Kibit, four SPRAMs totaling 1 Mibit and eight multiplier blocks. These resources do not imply sixteen independent wide workers. [Lattice family datasheet](https://www.latticesemi.com/api/document/download?id=51968).

The straightforward P=16 banked input schedule cannot use one independent 17–32-bit EBR read per worker per cycle: it requires `16*ceil(w/16)=32` EBR banks before output buffering. P=8 requires sixteen input EBRs; a separate equally banked output set requires another sixteen, exceeding thirty. This conclusion is conditional on that simple mapping, not an impossibility result for packing, staged reuse, distributed registers or reduced lane counts. A 32-bit word and a 17-bit word both cross the native 16-bit EBR width. [Official EBR organizations and synchronous ports](https://www.latticesemi.com/view_document?document_id=47775).

Four 16K×16 **single-port** SPRAMs cannot supply sixteen independently addressed reads per cycle. Wide cascading changes word width rather than adding addresses. Capacity is not bandwidth. [Official SPRAM primitives](https://www.latticesemi.com/view_document?document_id=51966).

A direct register residual-rank design at P=16, W=63 needs 6,144 map bits before bases/predictor/control, exceeding the device's 5,280 logic-cell flip-flops. The mask payload is 1,008 bits; this is a real possible advantage of compression, but the rest of the design still has to fit. This comparison concerns the straightforward fully parallel registered rank vector, not every possible compressed or time-multiplexed implementation. Constant gains can remove general multipliers; sufficient width and feedback timing remain mandatory.

Therefore P=16, L=32 in the Python certificate proof is a **mathematical configuration**, not an UP5K implementation claim. Start any UP5K investigation with a capped P, fixed coefficient, parsed/preloaded tape, stated output width and a cycle/port budget; report that interface scope. Nothing here proves the full predictor plus map plus ordered replay fits or wins on that device. The larger-device recommendation remains sensible, provided the direct baseline receives the same device and interfaces.

## 7. Non-negotiable go/no-go experiments before major RTL investment

1. **Representation challenge.** Extend a conceptual/software cost model with shared-base residual ranks using the exact same certificates. Verify every rank against map enumeration, signed arithmetic where supported, rails and multi-deletion cases. Compare stored bits, small operation widths, lookup/feedback depth and realistic lane counts. Go only with a contribution stated broadly enough to survive a simpler representation winning. A bitmap-only novelty claim fails this gate without measured advantage.
2. **Requirement challenge.** On an actual decoded tape, freeze selected-event schedule, physical horizon, precision, resets and output cadence. Measure per-state rate/bursts and fidelity against a high precision reference. Compare a single hot state with the naturally batched mix. Go toward an application speedup claim only if a concrete job/service target survives cheap exact baselines and surrounding-cost decomposition. Exactness alone does not pass this gate.
3. **Cold-versus-warm challenge.** Compare cold replay, repeated same-parameter replay with checkpoint amortization, and replay with already available snapshots. Include CPU serial/batched kernels and exact two/four-event unroll. Do not count all speedup from independent states as a single-feedback result.
4. **Complete schedule challenge.** Before implementation, provide one fully enumerated group schedule including predictor endpoints, all certificate applications, carry feedback, constructor, boundary lookup, replay, partial groups, ordered drain and every bank access. Apply the inequality against each baseline's own clock. Reject configurations whose optimistic bound already loses at the stated resource/port budget.
5. **Worst-case challenge.** Analyze long spans, constant/unchanged inputs, jumps, timestamp ties, resets, partial final groups, out-of-range events and sustained output stalls. Bound all-fallback service and abandoned work. An average-rate queue experiment is not a maximum-delay guarantee.

Proceed to a small RTL comparison only after these gates identify a plausible region. If the residual-rank vector wins, use it and describe certified arithmetic sharing as the core executor. If exact snapshots or ordinary batching win, report that application boundary and change the target. If the predictor dominates, improve or replace certificate generation before optimizing bitmap select. None of these outcomes is rescued by ideal events/clock or a deliberately slowed baseline.

## Evidence limits

No RTL, synthesis, post-route timing, board test or actual-market-rate measurement was performed in this review. The 193,560 local identity checks and all tables above are arithmetic checks/derivations. Hardware documentation, pandas EW semantics, TA-Lib defaults and the Flex Model article were inspected on 2026-11-06; mutable code/docs require revision pins in the eventual reproduction bundle. The source claims above stay within those sources' scope. Production precision, useful horizons and service requirements remain experiments, not inferred industry constants.

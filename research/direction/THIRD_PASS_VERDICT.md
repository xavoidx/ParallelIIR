# Third-pass verdict: arithmetic survives; the research claim needs narrowing

6 November 2026. This pass was an attempt to falsify the proposed direction, using independent literal-table/rational oracles, deeper primary-art reading and a hardware/application challenge. It found **real omissions and implementation defects**. The fixes below are incorporated into the prototype and current proposal.

**Recommendation:** continue with a small comparison of certified local execution methods. Treat the bitmap and a shared-base relative-rank table as competing representations. Do not assume bitmap superiority, a new boundary-deletion principle, a financial throughput bottleneck, or UP5K suitability. The next commitment should be measured baseline/certificate/representation RTL, not a large accelerator array or a novelty-led paper.

## What survived—and what did not

| Question | Current answer | Evidence / remaining obligation |
|---|---|---|
| Is the specified mathematical executor exact? | No counterexample found; independent derivations support it within its precise contract | Integer unsigned floor recurrence, fixed coefficients, nonnegative interval arithmetic, sufficient intermediates, correct domains |
| Do the fixed-group capacity bounds hold indefinitely? | Supported by an independent induction review; small closed carry graphs also checked | Only the stated full-group/precision/tree configurations with upper group gain below one; partial/reset/changed-coefficient cases need their own handling |
| Was the prototype safe at its interfaces? | Not initially; three defects were repaired | Bound query domains, integer-only configuration and exact bound serialization; explicit software allocation guard added |
| Is deletion of an ordered boundary a new principle? | No | Fernandes explicitly defines adjacent-collapse generators and their composition relations |
| Did the earlier work counts establish bitmap superiority? | No | A stronger shared-base rank-table constructor also needs only one full-width update and one forward pass per sample |
| Is the complete design faster or smaller? | Unknown | Predictor, rank/select or narrow rank lanes, resolution, replay, ports and interfaces must be synthesized and scheduled |
| Is the financial application useful at these precision/horizon choices? | Still an empirical question | A justified consumer, real tape, approximate alternative, caching and independent-state baselines are required |

“Ironclad” would conflate these different questions. Passing exactness checks cannot establish novelty, speedup, application value or publication readiness.

## Correction 1: a much stronger exact table baseline

The earlier comparison counted independently evolving full-width candidate states. That is a valid generic baseline, but not the strongest arithmetic-aware alternative.

Store a block map as `F(lo+i)=b+u_i`, where `u_0=0` is implicit and the remaining ranks are small integers. Compute `b_new,r=divmod(A*b+C,D)` **once** per sample. With `m=D-A`, every relative rank updates exactly as

`u_i_next = u_i + floor((r-m*u_i)/D)`.

Under the one-deletion condition, this becomes `u_i-[u_i>=j*]`, where `j*=floor(r/m)+1`. All ranks use the same threshold. The circuit can therefore use one full-width base/remainder datapath plus parallel small compare/decrement lanes. It avoids the bitmap's dependent rank/select operation.

Both representations are exact and use one input pass. At domain width 63, a straightforward rank table needs **378 rank bits**, omitting the constant zero entry, versus 63 mask bits. These are representation payloads, not LUT counts or timing results. A bitmap may win on storage or area; the table may win on feedback timing. Both pay for certification, boundary resolution and replay. A bitsliced rank implementation is a further optimization to consider.

[representation_checks.py](representation_checks.py) now implements this competitor on exactly the same certified domains. It passed 50,266 primitive entry checks, 386,100 literal-table comparisons and 7,680 replay outputs. These are synthetic correctness checks. The [results](representation_results.json) explicitly reject interpreting logical lane operations as clock cycles.

The old “27,361 candidate updates versus 512 base updates” example is retained as a generic-constructor comparison only. It does not demonstrate superiority over shared arithmetic. The main research gate now compares **mask versus relative ranks versus exact serial/unrolled execution**, all with complete costs.

## Correction 2: closer prior art than the previous reading exposed

Fernandes's 2024 paper defines an elementary transformation that leaves a prefix unchanged and shifts the remaining suffix down by one, collapsing one adjacent pair. It also gives product/rank-shift relations and ordered normal forms. After subtracting the updated base, our one-deletion step is such an action; the bitmap translates its rank into original-entry coordinates. This overlap is deeper than merely studying the same map class. [Primary paper, §§2–3](https://arxiv.org/html/2407.05084).

The specific floor-remainder formula and its use with independently certified domains were not located in the inspected methods. Their derivation is elementary, however. Treat them as a potentially useful specialization, not an established new algorithmic principle. The newly recovered Gu–Parhi technical disclosure also makes the older linear-IIR/finite-compensation decomposition concrete. [Inventor-authored disclosure](https://patents.google.com/patent/US20070014345A1/en).

[PRIORITY_RED_TEAM.md](PRIORITY_RED_TEAM.md) records the exact overlap, full versus partial reading, and remaining inaccessible 1991/reconstruction methods. A defensible future paper needs an implemented contribution and meaningful improvement beyond this existing structure. This pass is not a proof of priority or a guarantee that no closer implementation exists.

## Correction 3: prototype interfaces needed hardening

The audit found three initial defects:

- An out-of-domain query could silently return a plausible wrong result. For a map built on `[2,3]`, querying entry 4 returned 1 when the true exit was 2. The map now stores its original inclusive domain in immutable summary metadata. Queries outside it, or supplied bounds that disagree with it, raise an error.
- A noninteger coefficient such as `A=.5` was accepted despite the integer proof contract. Rule parameters and exposed configuration/input boundaries now reject such values explicitly.
- A finite exact bound could fail while being converted to a display float, and a rational enclosure check used display floats. Bounds now retain exact numerator/denominator fields; verification uses rational arithmetic. An overflowing optional display becomes null without destroying the exact result.

Explicit checks remain active under `python -O`; the original assertion-based test runner refuses optimized mode rather than reporting a false pass. A default 65,536-bit allocation guard rejects oversized reference masks before shifting/allocating. This is a software guard, not FPGA capacity admission or an implemented hardware fallback.

The independent regression suite includes all these cases. The immutable domain prevents accidental domain substitution; it does not authenticate deliberately fabricated summary contents. Internal helpers and mathematical operations still have documented preconditions. This remains a research model, not a production library.

## The independent correctness evidence

[independent_audit_checks.py](independent_audit_checks.py) reconstructs expected maps from literal execution of every candidate state. It does not use the deletion formula to generate expected masks. It uses exact rational trajectories to check predictor intervals and exercises extreme values, offsets, high retention, coarse precision, non-power-of-two groups and partial final groups.

The final persisted run passed:

| Check | Count |
|---|---:|
| Independent primitive entry comparisons | 107,660 |
| Input traces | 15,962 |
| Complete local-map candidate comparisons | 319,974 |
| Exact-rational boundary checks | 44,906 |
| Every-output replay comparisons | 58,766 |
| Closed finite carry graphs | 24 |
| Reachable intervals / transitions in those graphs | 971 / 10,090 |

The closed graphs exhaust every possible next complete input group in selected small configurations and reach closure. Thus they verify arbitrary future group counts **for those configurations**, rather than simply extending a sampled tape. The general statement still rests on the separately reviewed induction and its assumptions, not on extrapolation from these graphs. Seven invalid-input regressions pass with assertions disabled. Results include the tested source hash in [independent_audit_results.json](independent_audit_results.json).

The proof contract is intentionally narrow: constant integer `0<A<D`, integer rounding offset in `[0,D)`, unsigned invariant inputs/state, known initialization, floor semantics, and sufficient intermediate widths. Signed flow, clipping, toward-zero correction, variable decay, resets and changed group shapes cannot inherit every proof or capacity constant automatically. A formal RTL equivalence result has not been produced.

## Correction 4: hardware accounting must include the remaining operations

The P=16, L=32 prototype's 50 interval-composition operations require 200 unspecialized products, but that is not the entire predictor. Applying the prefix intervals to the carry requires another 32 products, and advancing the group carry requires two more. These **34 application products** are now separately recorded. Fixed gains and identities can specialize some operations; they still need an explicit schedule and implementation.

The width and bank costs remain serious. A straightforward P=16 design with independent 17–32-bit input reads needs 32 EBR banks on a device whose UP5K inventory has 30, before separate output storage. This rules out that particular direct banking arrangement, not every possible phased design. The 32-bit numerical example also uses roughly 77-bit predictor offset endpoints and wider products. It is an arithmetic configuration, not a demonstrated fitting UP5K design. [Primary memory guide](https://www.latticesemi.com/view_document?document_id=47775), [device datasheet](https://www.latticesemi.com/api/document/download?id=51968).

[FEASIBILITY_RED_TEAM.md](FEASIBILITY_RED_TEAM.md) derives an optimistic phased schedule, break-even conditions and memory obligations. Even its favorable P=16/L=32 schedule gives only about 3.16 events/clock before further overhead, assuming paired predictor endpoints, one-cycle exact/mask stages and one-cycle combines/lookups. Exact four-event unrolling at its own achieved clock is therefore a serious competitor. None of these abstract cycles establishes routed timing.

## Correction 5: the financial horizon matters as much as word width

At a fixed retention, increasing state precision grows the base/predictor datapaths but not the ideal certificate width. The older application note's wording about precision forcing longer blocks has been corrected for this new method.

Conversely, at a fixed **wall-clock half-life**, increasing the actual selected-event rate brings retention closer to one. For roughly regular arrivals at rate r and half-life T, `a=2^(-1/(r*T))`, so the rounding interval scale is approximately `r*T/ln(2)`. A hypothetical 50-million-event/s state with a 1-ms half-life would need roughly 72,000 candidate-boundary units, far beyond the small-mask examples. This is a derived illustration, not an observed financial configuration. Accelerating a recorded tape does not change its event semantics or require changing its coefficient; the example constrains live-time interpretations, not offline replay speed.

The published .97 example and native 63/64 control remain useful anchors. They cannot establish that all financially useful horizons produce small masks. Test longer event horizons, a stated real-time consumer and relevant precision. Separate exact integer execution from financial fidelity. Also compare snapshots, cached feature traces and ordinary parallelism across instruments/days/parameter candidates: a job that can avoid recomputing the recurrence is a stronger baseline than a faster recurrence engine.

One reference distinction is easy to miss: with nonzero rounding offset rho, the certificate predictor includes `rho/D` at every unrounded step. It is not the usual offset-free financial EMA. With identical initialization its difference from that real EMA is `(rho/(D-A))*(1-(A/D)^n)`. Use an explicitly defined high-precision financial reference or remove this deterministic shift when comparing financial accuracy. Exact reproduction of the integer implementation remains a separate check.

## The next commitment

1. Freeze one native rounded control and one independently justified liquidity-feature specification, including precision, reset and output schedule.
2. Measure exact serial and small-unrolled RTL, a shared-base rank engine and a bitmap engine on the same device. At this stage, supplied certified intervals can isolate representation cost; do not call this complete throughput.
3. Implement and charge one fixed-configuration certificate engine, memory schedule and full replay path. Compare complete sustained service and resources.
4. Obtain the actual tape and predefined financial acceptance metric. Compare approximate execution, caching and the actual independent-state mix.
5. Continue the research claim only if a meaningful complete improvement survives. Otherwise retain the exactness work and RTL learning results, and narrow or stop the accelerator claim.

The result of this pass is **greater confidence in the specified arithmetic, lower confidence in a standalone novelty claim, and a better-controlled experiment**. That is the appropriate basis for proceeding.

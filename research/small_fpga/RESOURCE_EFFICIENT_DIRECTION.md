# Resource-efficient exact one-pole filtering: a wider direction review

6 November 2026. Conceptual and primary-source review; no RTL, place-and-route, device fit, application bottleneck, priority, or performance result is claimed. Read alongside [the third-pass verdict](../direction/THIRD_PASS_VERDICT.md), [the feasibility challenge](../direction/FEASIBILITY_RED_TEAM.md), and [the certificate contract](../direction/CONSTRUCTOR_AND_CERTIFICATES.md).

## Verdict

**Changing the output contract is necessary in some useful applications, but sparse outputs alone do not establish a small-FPGA resource advantage.** A native dyadic one-pole can already be one state register and shift/add/subtract logic. Removing replay from a parallel summary machine does not make its predictor, constructors, resolver, input banks, and carry machinery cheaper than that baseline.

The strongest falsifiable resource hypothesis found here is **exact common-base filtering of a bank of synchronized, provably close channels**, with one wide base state and narrow channel differences. It avoids the affine predictor completely and has a simple all-time integer width invariant. It is a different workload from speeding up one independent hot state. If no real workload supplies bounded differences in the required integer units, reject it; do not manufacture channel similarity or exclude ordinary time sharing to make it win.

For a **single** hot state, keep sparse block-final output as a legitimate experiment, with a strong prior that the direct implementation wins area at modest required rates. A more specialized single-state alternative is exact constant-input run processing, relevant to PWM observation. Neither alternative currently satisfies “real rate bottleneck + bit-exact wanted + beats the strongest exact method.” The inspected application sources establish plausible settings and native arithmetic, not that conjunction.

## 1. Fix the observable behavior before choosing hardware

The current arithmetic is

`s[t+1] = floor((A*s[t] + m*x[t] + rho)/D)`, `m=D-A`,

with fixed integer `0<A<D`, `0<=rho<D`, unsigned bounded inputs/state, and sufficient intermediates. Three distinct output contracts matter:

| Required observable | Work that can disappear | Work that remains |
|---|---|---|
| Every numeric state | None of the original replay obligation | Exact entries, all intermediate states, ordered output |
| Exact state only at prescribed block ends | Intermediate replay and its output storage | Reading all arbitrary inputs, constructing an exact block function or another exact evaluator, resolving actual state |
| Exact threshold/category decisions | Numeric materialization when a sound enclosure decides the predicate | Correct future state/information, ambiguous decisions, any repair and its retained history |

These are application changes, not interchangeable evaluations of the same accelerator. Output sparsity helps a direct implementation too: it retains one current state and emits only requested outputs. It does not require a full output trace buffer.

For `A=D-1`, the direct recurrence is exactly

`s_next = s + floor((x-s+rho)/D)`.

With `D=2^k`, division is a properly defined arithmetic shift of a sufficiently wide signed difference. Compare both this form and constant-coefficient implementations of the original numerator; synthesis and signed semantics decide which is best. A generic multiplier/divider is not a fair mandatory direct baseline.

## 2. Candidate A: one wide reference channel, exact narrow residual channels

This is the clearest route to reducing **total state and arithmetic width**, rather than replicating wide engines to buy throughput.

### Exact identity and an all-time width bound

Let channel 0 be the reference. Channels have the same `A,D,rho` and synchronous update times, but may have different inputs:

`x_c = x_0 + delta_c`, `s_c = b + v_c`, with `b=s_0`.

Perform one full-width update:

`b_next, r = divmod(A*b + m*x_0 + rho, D)`, `0<=r<D`.

Every other channel then updates **exactly** by

`v_c_next = floor((A*v_c + m*delta_c + r)/D)`.

This follows by substituting `s_c=b+v_c` into the original numerator. The shared remainder is essential: rounding a separately filtered difference generally does not reproduce the original channel.

Suppose integer `K>=0` bounds both the initial state differences and every future input difference:

`-K <= v_c[0] <= K`, and `-K <= delta_c[t] <= K`.

Then `-K <= v_c[t] <= K` forever. Indeed, the residual numerator lies between `-D*K` and `D*K+D-1`, so its floored quotient lies in `[-K,K]`. Equivalently, the original update is monotone and obeys integer translation equivariance:

`f(s+K,x+K)=f(s,x)+K`.

**There is no additional `1/(1-a)` spread penalty in this bound.** It uses the correlation of the exact channels and the common remainder; it is not the independent-unrounded certificate bound. Unsigned original states may have signed differences. This algebra does not automatically extend to differing coefficients, differing rounding offsets, asynchronous updates, clipping, or overflow.

Store `v_c+K` in `ceil(log2(2*K+1))` bits, treating `K=0` specially. A sufficient signed residual-numerator width is `1+ceil(log2(D*(K+1)))`; a physical design must check actual arithmetic structure and boundary cases. Power-of-two `D` is attractive, but the broadcast remainder and residue-lane timing still require implementation.

For an illustrative `M=16`, 32-bit state bank and `K=127`, the variable state payload falls from `16*32=512` bits to `32+15*8=152` bits. This is a derived storage comparison, **not a LUT, clock, or power result**. If all states are already RAM-backed, fewer bits may not save a single physical RAM block.

### What would make it a real resource win

At equal required service, compare

`C_wide + (M-1)*C_residual + C_input_differences + C_outputs + C_control`

with the **best** direct bank, including time sharing and its state RAM. The candidate wins only if the complete left side is smaller under the same clock, deadlines, interface, and device constraints. LUTs, registers, DSPs, RAM blocks, and power must be reported separately; a RAM/LUT trade is not automatically lower total hardware.

Necessary favorable conditions are:

1. A real source supplies a narrow, deterministic difference bound in **native integer state units**, including startup and transients.
2. The input representation already supplies reference plus differences, or generating those differences costs substantially less than the removed wide updates. An array of full-width subtractors can consume the apparent arithmetic saving.
3. Outputs are sparse, serially reconstructed, or consumed as shared-base predicates. Reconstructing every full-width channel value simultaneously costs wide adders and output bandwidth. For a common threshold `T`, compute `T-b` once and compare narrow residuals, with correct treatment outside `[-K,K]`; arbitrary distinct thresholds may require more wide work.
4. The direct bank cannot satisfy the target with one shared shift/add datapath. Multichannel independence is an advantage for that baseline and must not be forbidden.

A possible workload is a synchronized bank of closely related calibrated measurements, or multiple initial-condition hypotheses observing exactly the same innovation sequence. **No inspected source establishes a production need for this precise exact integer bank.** Ordinary independent radio antennas, motor phases, queues, or probability contexts do not imply bounded narrow differences. Their worst-case spread can be full scale.

Credit ordinary range analysis to the direct baseline as well. A wide declared state that can only occupy a small integer interval may already be narrowed without cross-channel sharing. Fractional input/state scaling must be included when asserting K; physical closeness does not imply a small residual in native state units.

The cheap special cases must be admitted. Identical initial states and identical inputs require only one state. If `x_c=x_0+d_c` and `s_c[0]=b[0]+d_c` for constant integer offsets, translation equivariance gives `s_c[t]=b[t]+d_c` forever: no evolving residual lane is needed. If channels differ in gain/decay, this shared-coefficient invariant does not apply.

### Relationship to the existing work and novelty limits

This generalizes the already mandatory shared-base rank arithmetic to channel-dependent innovations. It is an elementary exact identity and a monotonicity invariant, not evidence of a new algorithmic principle. In the identical-input ordered case, relative ranks and deletion masks remain competitors; with varying per-channel innovations, order may change, so an unchanged ordered bitmap is not a valid replacement for independent residuals.

Sharing coefficients or fixed gain powers alone is much weaker: channels with unrelated inputs still need their own affine offsets, carry enclosures, exact maps, and state information. A shared coefficient ROM cannot be counted as sharing the entire certificate engine. Conversely, normal multichannel hardware time sharing is longstanding; NXP's EFCOP application note explicitly supports multichannel FIR/IIR filtering. That is a baseline capability, not a prior demonstration of this residual formula. [NXP AN2108](https://www.nxp.com.cn/docs/en/application-note/AN2108.pdf).

## 3. Candidate B: exact sparse-output execution of one hot recurrence

Block-final outputs eliminate the exact replay pass. They also remove the need to store every intermediate output or repair the prefix merely to emit it. This is a substantial change from the present every-output executor, but it leaves a full-rate exact constructor and a full-rate predictor in the current design.

For `N=P*L` and the existing nonoverlapped stage allocation, removing replay changes the optimistic bound to

`C_group >= L*q_predict + L*q_construct + P*q_lookup + C_certificate`.

All scan/carry/application work belongs in the final term. With the earlier favorable `P=16,L=32`, all `q=1`, paired predictor lanes, and the same idealized 50-slot scan charge, this is at least 130 clocks for 512 events, or 3.94 events/clock. It is not a routed result or an UP5K fit claim; it still requires many workers and adequate memory ports. A four-event exact unroll at its own clock remains a serious competitor. A serial direct engine is cheaper when its achieved clock already exceeds the required event rate.

Use the same independently generated intervals for masks, shared-base ranks, exact endpoint propagation, convergence factoring, and any restricted inverse method. A rank-vector constructor uses one full-width base update per sample, just as the bitmap does. The 63-versus-378 payload-bit distinction is interesting, but cannot stand in for the complete hardware cost.

### Why high state precision and narrow inputs are not sufficient

Increasing state precision at fixed retention need not enlarge the ideal certificate's width in integer units. It does enlarge the base and the predictor. A gain error `epsilon_g` applied to a possible state of magnitude `H` contributes up to `H*epsilon_g` absolute error. Keeping this below one state unit can require gain accuracy of order `1/H`, even if the incoming symbol is one bit. Low input entropy does not make a high-precision accumulated offset cheap automatically.

The current `F=w+12` interval construction, wide products, and outward endpoint arithmetic cannot be replaced with a low-precision predictor merely because its inputs are narrow. Precomputed fixed gains, shift/add constants, analytic error propagation, and shared schedules may reduce cost; charge the actual specialized implementation. Tiny state formats, meanwhile, invite ordinary full transition tables and direct exact unrolling.

### Sparse IIR decimation prior art is relevant but does not settle bit identity

The 2002 Krukowski–Morling–Kale paper analyzes several polyphase N-path IIR implementations, internal growth, and rounding noise, with fixed-point simulation and an equivalent bit-true VHDL implementation. Here “bit-true” links a chosen fixed-point model to its hardware; the inspected abstract does **not** establish equality to a separately specified original per-input floor recurrence after arbitrary multirate rearrangement. Full structural comparison is still required. [Author-repository paper](https://westminsterresearch.westminster.ac.uk/download/3455d7dd605b198d8e2ab7348fbc93379db62ed6377d87566ff192990c3dadc8/2325722/Krukowski%2C_Morling_%26_Kale_2002_final.pdf).

Saramäki's author-hosted multirate text explains why ordinary recursive loops do not inherit FIR's full decimation-factor saving, and describes efficient polyphase alternatives. This is supporting background, not a lower-bound proof for exact nonlinear integer execution. [Author-hosted text, Chapter V](https://homepages.tuni.fi/tapio.saramaki/multirate_copy.pdf). The primary EUSIPCO 2000 decimator paper uses polyphase decomposition and examines coefficient sensitivity; it is a genuine redesign rival if the application accepts a filter specification instead of a fixed old integer trajectory. [Primary proceedings paper](https://www.eurasip.org/Proceedings/Eusipco/Eusipco2000/SESSIONS/TUEPM/PO2/CR1712.PDF).

No inspected source established a general low-cost, sparse-output evaluator preserving this exact arbitrary-input, per-step floor contract. That limited negative search is not novelty evidence. The unresolved quantizer-loop literature remains an obligation from the earlier review.

## 4. Candidate C: certified predicates and exact hybrid repair

If `s` lies in a sound integer enclosure `[lo,hi]`, `lo>=T` certifies true and `hi<T` certifies false for `s>=T`. This can eliminate numeric outputs and many exact **queries**. Exact predicate filters using an approximate enclosure followed by exact fallback are established: Brönnimann–Burnikel–Pion use interval arithmetic for exact geometric predicates. Their application has no persistent filter state, so its fallback strategy cannot be copied without analyzing the recurrence's hidden carry. [Primary publisher abstract](https://www.sciencedirect.com/science/article/pii/S0166218X00002316).

The hidden-state trap is decisive. Accepting a predicate does not identify the exact numeric state needed by future ambiguous predicates. A coarse enclosure that remains narrow forever still does not identify the actual member of that enclosure. A bounded replay FIFO cannot safely discard unresolved history merely because the last thousand decisions were easy.

At least one of the following must be true:

* The exact carry is maintained continuously. Then exact state-update work has not disappeared; compare the extra predicate predictor against simply comparing the exact state.
* A sound exact summary retains all information needed to select the carry later. Charge its construction, metadata, lookup, and storage.
* Exact endpoints coalesce, or an application reset supplies a singleton. Only then can the unresolved earlier numeric state be forgotten for future execution.
* A proved behavioral equivalence quotient merges states that no possible future admissible input/decision can distinguish. Equal recent decisions are insufficient.
* History remains available until repair. Charge its potentially unbounded extent, or prove a finite recovery bound under the admitted workload.

The established coalescence hybrid remains useful: evolve certified endpoints, retain a speculative trajectory, and accept its suffix after the endpoints have become equal. Replay only outputs whose correctness is unresolved. For block-final output, equality of exact endpoints already gives the exit, so a full mask may be unnecessary. For every-output execution, equality at the end does not validate earlier speculative outputs. Constant/quiet inputs can preserve ambiguity indefinitely; a typical merging-time histogram is not a finite buffer or deadline proof.

Ko et al. restrict speculative chunk-entry states using preceding input symbols; their exact enumeration method is a direct predecessor for restricted-entry execution. [Primary manuscript, §§4.2–4.3](https://arxiv.org/html/1210.5093). Zhao–Wu–Shen's principled FSM speculation explicitly studies lookback, merging length, and partial reexecution; endpoint/speculative-tail repair cannot be presented as a new general speculation idea. The primary indexed PDF was located, but its current URL redirects to a group page; this pass relies on the indexed primary excerpt rather than claiming full-method reading. [Primary paper URL](https://research.csc.ncsu.edu/picture/publications/papers/asplos14FSM.pdf).

For a nonoverlapped hybrid, with fallback fraction `p`, use `C_avg=(1-p)*C_good+p*C_bad`, where `C_bad` includes abandoned speculation and repair. Worst-case clustered fallbacks govern a hard real-time claim. Keeping a full direct path capable of all events can provide the guarantee, but its area remains in the total. Energy savings from fewer toggles can be valuable without being area savings.

## 5. Candidate D: exact constant-input run processing

PWM is a structured exception to arbitrary inputs. If only the state at edges or period boundaries is required, the source may provide a value and run length directly. There is then no need to buffer or process a bit for every timer tick merely to recover the same run information. This is a legitimate single-state workload change.

For one constant-input run, let `C=m*x+rho`. Write the exact update as

`s_next = s + q(s)`, `q(s)=floor((C-m*s)/D)`.

While `q` is constant, the trajectory is an exact arithmetic progression. For current `q>0`, define `upper=floor((C-q*D)/m)`. The number of consecutive valid updates with this increment is

`h=floor((upper-s)/q)+1`.

For `q<0`, define `lower=floor((C-(q+1)*D)/m)+1`, giving

`h=floor((s-lower)/(-q))+1`.

Clamp `h` to the remaining run length, advance `s` by `h*q`, and repeat. If `q=0`, the remaining constant run leaves the state fixed. Each batch is exact because every pre-update state lies in the same quotient band. This also preserves the native rounding offset; replacing the run by an ideal exponential and one final rounding generally does not.

This is an elementary skip method, not a novelty claim. It introduces variable division by `|q|`, a multiply by `h`, run counters, and control. When `|q|` is large, bands can last one update and the method adds overhead. A crude bound on nonzero-increment batches is `min(T,|q_initial|)` because the increment moves monotonically toward zero and each completed band changes it; this bound can be large and is not a logarithmic-time guarantee. A budgeted direct path should prevent run processing from losing unbounded service.

The strongest rivals are direct clock-enabled shift/add updates, stopping after a detected fixed point, precomputed jump tables where state/run ranges are small, constant-input-specific arithmetic, and simply counting PWM duty if the consumer only needs an average. Duty counting is not equal to the specified one-pole state; if that distinction is irrelevant to the consumer, it can be the correct cheaper design.

Lattice's UltraPlus PWM reference uses a 12 MHz system clock and illustrates 120 timer counts for 100 kHz PWM, with programmable frequency and duty. This establishes a realistic source of known high/low run lengths, **not a need for an exact one-pole observer**. Those illustrated runs are short enough that jump overhead could easily lose. [Primary reference design, §3](https://www.latticesemi.com/view_document?document_id=52512). A promising run-skip case needs a stated observer, much longer admitted runs or many channels, sparse requested outputs, and a budget comparison against a shared direct engine.

## 6. Application triage outside video and finance

| Setting | Concrete supporting evidence | Principal obstacle / strongest rival | Present disposition |
|---|---|---|---|
| Small-FPGA AM/FM/QPSK receiver; RSSI, DC tracking, squelch, or block AGC detector | ZipCPU's SDR project explicitly targets iCEBreaker/SX1257 and documents AM/FM/QPSK designs | Native source must identify the actual one-pole, state precision and event rate. A cheap direct recurrence and existing decimation may suffice. Tracking/control feedback may require each output before later inputs exist. | Best source to inspect for a real complete small-FPGA system, not an established bottleneck |
| Synchronized delta-sigma current sensors feeding a PWM/control system | TI AMC1306 supplies synchronous one-bit streams at 5–21 MHz and supports synchronization of current-sensing channels | Sinc/CIC and application-approved multirate filters are strong rivals. Independent one-bit streams can differ by full scale even when analog currents are close, so Candidate A's narrow *per-tick integer* difference bound does not follow. | Useful rate anchor; no bit-exact one-pole requirement established |
| PWM state observer or exact digital reference model, state read at edges/period ends | Lattice has a native UltraPlus PWM design with known run counts | Run jumping, duty counting, direct shift/add, and shared bit/digit-serial arithmetic | Specialized Candidate D test; no generic summary-array case |
| Packet queue EWMA / RED decisions | Linux supplies an explicit fixed-point on-arrival update and threshold/action logic | One shift and two add/subtract operations; many queues permit interleaving; idle behavior and random marking must also match. Batch delay may violate enqueue decisions. | Strong native arithmetic control, weak reason for a complex predictor |
| LZMA adaptive probabilities for general-purpose lossless compression | Maintainer decoder source supplies native 11-bit probability arithmetic and shift-by-5 updates | Tiny exact state, cheap direct updates, context RAM, and entropy-decoder dependence. Future decoded bits and model addresses are not available as a free input tape. | Genuine bit-exact nonlinear state example; poor standalone one-pole accelerator target |

Primary application sources: [ZipCPU SDR README](https://github.com/ZipCPU/sdr), [TI AMC1306 datasheet, §8.1](https://www.ti.com/lit/ds/symlink/amc1306m25.pdf), [Linux RED implementation](https://github.com/torvalds/linux/blob/master/include/net/red.h), and [Igor Pavlov's LZMA decoder](https://raw.githubusercontent.com/ip7z/7zip/main/C/LzmaDec.c). These support the evidence column; the opportunities and objections are this review's inferences.

Two native arithmetic details prevent misleading application matching:

* Linux's non-idle update is `qavg_next=qavg+backlog-(qavg>>Wlog)`, with `qavg` scaled by `D=2^Wlog`. In the current floor form it is `A=D-1`, `x=D*backlog`, `rho=D-1`. Units and rounding matter. Its idle-time path and random marking are additional behaviors; matching the non-idle scalar recurrence alone does not reproduce RED.
* LZMA uses `p += (2048-p)>>5` for one bit outcome and `p -= p>>5` for the other. They correspond to `floor((31*p+2048)/32)` and `floor((31*p+31)/32)`. Thus the effective offset depends on the outcome. The current fixed-`rho` certificate theorem cannot simply be cited unchanged. The decoder uses the current probability to determine the bit and subsequent context; preloading already decoded model updates would remove part of the very dependence being claimed as accelerated. An encoder with known decisions is a different test, and its whole range-coder work still belongs in the baseline.

Communications also has close existing nonlinear-feedback work: Parhi–Gu's 2004 10GBASE-T presentation reformulates a Tomlinson–Harashima precoder into a pipelined IIR and finite-level compensation loop, with precomputation. It explicitly notes increased complexity at greater pipelining. That is both a real nonlinear communications precedent and a warning that pipelining does not imply resource reduction. Its modulo precoder is not the current scalar floor contraction. [Primary IEEE 802.3an presentation](https://www.ieee802.org/3/an/public/sep04/parhi_1_0904.pdf).

## 7. Falsifiable next experiment and stop conditions

Do not start another P=16 accelerator or a broad application claim. First freeze one source-level, exact integer contract and its actual per-state rate, output cadence, reset behavior, latency allowance, and reason for requiring bit identity. No source inspected here supplies all of these.

For a **resource-efficiency investigation**, prioritize Candidate A only if the source provides a legitimate narrow bound. Suggested arithmetic controls are `M=2,4,8,16`, state widths 24/32/48/64, and residual widths 4/8/12/16, with the same fixed retention and source-native input units. These are experiment axes, not application recommendations. Compare:

1. Best direct shift/add/constant-multiply implementation, serial or small unroll as needed, with state RAM, independent-channel interleaving, and bit/digit-serial scheduling where deadlines permit.
2. The exact common-base residual bank, charging input difference formation, fanout, reconstruction, thresholding, and overflow/escape handling.
3. Identical-channel collapse and constant-offset collapse whenever applicable.
4. If block summaries are included, masks, shared-base ranks, endpoint/coalescence hybrids and exact direct execution supplied the same certificates, charging the complete predictor and schedule.

At equal service and deadlines, a useful advance must improve a reported hardware or energy objective against **all applicable** rivals. Set the desired improvement before synthesis; for example, at least a 20% LUT reduction without more RAM/DSP blocks and without losing the target service is a falsifiable optional gate, not a prediction. If reduced LUTs consume extra scarce RAM, report the Pareto trade instead of claiming unqualified “smaller.”

For a single-state sparse-output claim, the initial gate is harsher: demonstrate a needed rate above the best direct design's delivered service, and show a complete summary implementation that meets it with fewer resources than the best exact direct/unrolled alternative. Sparse output, high precision, small input bit width, or perfect certificates alone do not pass that gate.

Reject or narrow the direction if any of these occur:

* Real inputs have no deterministic narrow residual bound, or input differencing/reconstruction erases the saved arithmetic.
* One ordinary shared direct engine already meets all deadlines with lower hardware.
* The application accepts a cheaper CIC/polyphase/approximate filter and has no independent need for the old integer trajectory.
* Ambiguity can persist longer than available history and there is no proved exact fallback/carry mechanism.
* Known future update symbols or free checkpoints are obtained by solving the original dependent decoder/control computation first.
* Only payload bits, constructor operations, optimistic cycles, or an excluded weak baseline show a win.

## 8. Follow-up challenge: observation-first peak summaries and finite-history certificates

The root investigation proposed a further single-state variant during this review; its separate experimental write-up is [the observation-first prototype](OBSERVATION_FIRST_PROTOTYPE.md) (forthcoming when this review was written). The following is an independent algebra/scope challenge, not a claim that its complete executor is implemented or advantageous.

### Finite-history endpoint certificates

At a block entry, process the preceding `H` actual known inputs from the legal-state rails. Monotonicity gives a valid entry interval without the wide affine prefix scan. If `w` is its width, each step obeys

`w_next <= ceil(A*w/D)`.

This can replace wide predictor products with native exact updates, but costs two endpoint trajectories over `H` inputs per independently certified block, plus history reads/storage. It is numerical reverse lookahead, closely related to the restricted-entry DFA predecessor already cited above. Existing exact checkpoints receive their full singleton advantage.

The width recurrence has positive fixed values whenever `m*w<D`; it cannot guarantee a singleton. For `A/D=63/64`, starting with width `2^b-1`, the conservative recurrence first reaches width 63 after these exact derived iteration counts:

| State bits `b` | History updates `H` per endpoint | Endpoint work `2H/L` per new event, `L=32` | Same ratio, `L=1024` |
|---:|---:|---:|---:|
| 16 | 477 | 29.81 | 0.93 |
| 24 | 830 | 51.88 | 1.62 |
| 32 | 1,182 | 73.88 | 2.31 |
| 64 | 2,590 | 161.88 | 5.06 |

These are endpoint update counts, not clocks or area. Actual input-dependent endpoints can be narrower earlier. Long blocks amortize the conservative certificate work but increase observation delay; removing the affine predictor is not automatically reducing total work. Online streams cannot use the preceding `H` samples until those samples exist, and independent windows need a concrete bandwidth schedule. Near startup, the known initialization must be used when `H` preceding samples do not exist. Resets and changed update semantics need explicit treatment.

### Exact block peak as the requested output

Let `F_t(s)` be the exact state after the first `t` updates of a block, `E(s)=F_L(s)`, and define **post-update** peak `M(s)=max_{1<=t<=L} F_t(s)`. Every `F_t` is monotone with adjacent increments zero or one; therefore `M` has the same properties. It can be represented by a base and adjacent-increment mask or shared-base ranks on the certified entry domain.

Composition of consecutive nonempty blocks is exact:

`E = E_2 o E_1`,

`M(s) = max(M_1(s), M_2(E_1(s)))`.

Thus `M(actual_entry)>=T` answers whether **any post-update state reached/exceeded** a fixed threshold, including an interior transient that a block-exit comparison misses. This does not report when, how many times, duration above threshold, or every-event decisions. It is not an upward-crossing detector unless entry-below-threshold or another suitable condition is part of the contract. An empty-block identity needs a peak sentinel or a separate flag. Initializing the peak to the block-entry state silently changes the definition to include `t=0`.

For peak base `h=M(lo)` and peak ranks `v_i=M(lo+i)-h`, append an exact state update whose new base/ranks are `b_next,u_i_next`. Then

`h_next=max(h,b_next)`,

`v_i_next=max(h+v_i,b_next+u_i_next)-h_next`.

With `d=b_next-h`, this becomes `max(v_i,d+u_i_next)-max(0,d)`. Both rank vectors lie in `[0,W]`. If `d>=W`, the result is `u_i_next`; if `d<=-W`, it is `v_i`; in between, bounded signed arithmetic suffices. Clamping `d` to `[-W,W]` is therefore valid. **Determining the clamp still requires full-width base comparison/range detection.** A second mask is not automatically updated by the original exit-map deletion rule: peak ranks can gain a boundary that the exit map has lost, and need their own update implementation.

This is a better-defined sparse observer than throwing away state history after easy threshold decisions: the pair retains the exact exit map and the exact maximum function on the certificate. It avoids replay for this observer while preserving the carry needed by later blocks. Its direct baseline is also stronger than an every-output filter: update one exact state and a single peak register/comparator, resetting the peak at each output block. Charge both maps, the peak comparison, certificate construction, and exact resolution against that baseline.

**Mandatory cheaper rival for a fixed threshold:** the full peak function is unnecessary when `T` is known during construction. The Boolean map `Q_T(s)=[M(s)>=T]` is monotone, hence is described by one entry threshold `kappa`, with all/none sentinels. At each step, obtain the first entry whose current exit reaches `T`, and retain the smallest such entry over time. A rank vector gives a lower-bound query; a bitmap gives a select query at rank `T-b` when that rank lies in the image. This uses roughly `log2(W+2)` alarm metadata bits rather than a complete second peak map, although query logic and any contention with deletion select still cost hardware. Composition is `kappa=min(kappa_1,preimage_E1(kappa_2))`, with correct domain/sentinel handling. Give this exact observer the same certificates and arithmetic sharing. A full peak map needs a reason such as a threshold chosen after construction, many queried thresholds, or a requested numeric peak.

The general state-transition-plus-accumulated-output construction is not a new principle. Cost-register automata already formalize combining register values with operations such as scaling and minimum; this is a broad conceptual predecessor, not an inspected exact integer one-pole peak implementation. [Alur et al., primary author paper](https://www.cis.upenn.edu/~alur/Lics13reg.pdf). The plausible contribution to investigate is the particular bounded arithmetic representation and complete resource/deadline tradeoff. No priority or hardware result follows from the composition identity.

This follow-up deserves a bounded experiment if a real detector needs only a delayed block alarm, the innovation sequence is independently available, and a native direct filter is an actual bottleneck. A control loop that needs an earlier alarm to determine later inputs cannot accept block-delayed observation by assumption. A narrow one-bit input with a short pole is plausible test structure, but is not evidence of an application requiring the exact old state trajectory or of superiority to a direct exact state-plus-peak engine.

### Limited arithmetic checks performed in this pass

An inline Python falsification check compared the common-base identity and invariant on **408,000** cases (`D=2..17`, every `A`, endpoint rounding offsets, `K=0..4`, seeded signed differences). A separate **100,000** seeded test compared the quotient-band constant-run jump with literal per-tick execution over varying coefficients, offsets, states, run inputs and lengths. Both passed. No test script or result artifact was added; these checks support the algebra only and are not hardware validation or an exhaustive proof. The derivations above state the general arguments.

**Current decision:** investigate exact residual sharing only after obtaining a real bounded-difference workload; test the observation-first exit/peak variant under an explicit delayed-alarm contract; retain sparse-output and run-structured single-state methods as tightly scoped alternatives. The original single-hot-state, complete-speedup objective remains unproven, and moving to multichannel area reduction must be stated openly as a change of research objective.

## 9. Independent review of the observation prototype

Reviewed and executed the new [observation checks](observation_checks.py), preserving the root files. The independent [audit script](observation_independent_checks.py) and [persisted results](observation_independent_results.json) reproduce the root JSON's source/core hashes, all exhaustive counts, composition count, and streamed rows, then add a separate literal recurrence oracle. No mathematical defect was found within the valid-input arithmetic contract.

| Independent additional check | Passed comparisons |
|---|---:|
| Arbitrary-input, restricted-domain exit/peak/forward-alarm versus literal recurrence | 499,810 |
| Backward inverse cut and its neighboring legal-state boundaries | 25,243 |
| Two-block composition with the second domain restricted to the first exact image | 32,145 |
| General-input finite-history membership and conservative width bounds | 12,000 |

The 12,000 seeded cases vary state widths 1–16, denominators 2–257, coefficients, all sampled rounding offsets, singleton and nonsingleton domains of width at most 127, block lengths 1–39, arbitrary inputs, and supported thresholds including 0 and `high+1`. Peak-clamp coverage includes 14,685 `d>W`, 120,913 `d<-W`, and 91,038 interior/boundary cases. A separate entry-15/update-to-7 fixture with threshold 15 confirms that entry state is excluded from the peak. Out-of-domain queries reject. These checks are falsification evidence, not exhaustive proof or formal RTL equivalence.

The certificate has no observed oracle leak: history rails use only preceding input samples, legal state bounds, and the known initialization when the window reaches tape start. Exact literal state is used to validate membership/output after constructing summaries. Streamed resolution propagates the exact exit from each summary to the next; numeric peak and alarm need no output replay. The earlier corrected test threshold above the supported `high+1` sentinel was a test-domain issue, not an arithmetic counterexample.

The forward alarm correctly retains the minimum entry index found by lower-bound search of current ordered ranks. The inverse alarm's backward update uses `min(T,cut_after)`, exact ceiling division, and legal-domain sentinels; state invariance makes the sentinel clipping valid. The clamped numeric peak update and initialization after the first actual update implement the post-update peak contract. Composition checks exercise serial query/observable composition; there is no materialized merged-summary circuit or demonstrated parallel scan in these tests.

Hardware conclusions still require these corrections to any accounting interpretation:

* `build()` constructs numeric peak and fixed-threshold alarm together for validation. A fixed-threshold-only rival must omit the numeric peak map; an inverse-alarm rival must omit unrelated peak construction and pay its reverse input pass, storage, and division by `A`.
* `1+2H/L` counts endpoint/base native transitions in a steady full-block model. It excludes ranks, peak/alarm operations, queries, memories, control, and interfaces. The L=256 numbers are arithmetic extrapolations, not a separately implemented or measured L=256 schedule. Startup and partial blocks have their own work.
* Two endpoint transitions do not require independent full-width arithmetic. If the lower endpoint's exact update supplies remainder `r`, the endpoint width updates as `floor((A*w+r)/D)`. Arithmetic sharing, dynamic width schedules where valid, and ordinary direct engines must receive their full benefit.
* The smallest observable-specific direct baseline maintains one exact state plus a peak comparator/register or an alarm bit. Every-event output storage is unnecessary. No replay saving establishes superiority over this baseline.

The audit therefore supports the exactness of the constructed observation model while leaving native workload necessity, complete scheduling, device fit, throughput, resource advantage, and novelty unestablished.

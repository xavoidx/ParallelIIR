# A less obvious video candidate: exact adaptive probability updates

6 November 2026. **This is a new arithmetic/application lead, not a demonstrated accelerator win.** VVC and AV1 contain integer exponential probability estimators inside entropy coding. Here exactness serves bitstream compatibility, a stronger motivation than preserving the appearance of a blur. However, a bottleneck in an entropy coder does not establish that its probability update is the limiting stage. The decoder also lacks the known future symbols required by our block method.

## 1. VVC: a native match, including its stored-state representation

The standard's designers describe two exponentially weighted estimates per context, with different adaptation rates and an averaged probability for coding. They specify shift-based integer updates and distinguish probability estimation from interval subdivision. The paper reports measured software entropy-engine throughput; that number is neither an FPGA result nor a probability-update profile. §IV was read through indexed primary full-text passages; direct PDF retrieval failed. [Schwarz et al., *Quantization and Entropy Coding in the Versatile Video Coding (VVC) Standard*, DOI 10.1109/TCSVT.2021.3072202](https://refubium.fu-berlin.de/handle/fub188/33130).

The implementation audited here is **VVenC commit `6441f64f9997e9ab8a12d4ac600998a104aa5ddf`**, not a hypothetical rounded version of a real equation. Its two estimates carry 10 and 14 significant state bits, aligned in nominal 15-bit storage. The update subtracts a shifted/masked state and conditionally adds a precomputed constant. The rate setter gives first-estimate shifts 2–5 and valid second-estimate shifts 5–9; not every pair in the Cartesian product is a valid configured pair. [Pinned header](https://github.com/fraunhoferhhi/vvenc/blob/6441f64f9997e9ab8a12d4ac600998a104aa5ddf/source/Lib/CommonLib/Contexts.h), [pinned constant tables and initialization](https://github.com/fraunhoferhhi/vvenc/blob/6441f64f9997e9ab8a12d4ac600998a104aa5ddf/source/Lib/CommonLib/Contexts.cpp).

**Our reduction:** remove the invariant low zero bits from one estimate, call its integer state `s`, significant width `b`, shift `k`, denominator `D=2^k`, and known coded bit `v`:

```
s_next = s - floor(s/D) + v*floor((2^b-1)/D)
       = floor(((D-1)*s + (D-1) + v*(2^b-D))/D).
```

This is precisely the existing normalized rule with `A=D-1`, `rho=D-1`, input `x=v*(2^b-D)`, and state range `[0,2^b-1]`. Both inputs are inside that range. No change to the native rounding is needed. The two scalar hypotheses can be executed independently given their common bin sequence, then combined in the native order. They are **not** one scalar state after averaging.

The ideal certificate width is `D-1`: 3–31 for the first estimate and 31–511 for the second. Finite predictor precision and the full schedule still need charging. The slow estimate is not always a convenient 31/63-bit mask. This scope assumes initialized/configured contexts: the class constructor's default rate byte includes a zero shift for one estimate, outside the strictly contractive `0<A<D` prototype. Preserve real initialization rather than feeding that default to the theorem.

A stronger exact baseline follows from our own algebra. Define `H=2^b-1` and `G(s)=s-(s>>k)`. The zero-bit branch is `G(s)`; the one-bit branch is `H-G(H-s)`, equivalently `s+((H-s)>>k)`. Since complementing a `b`-bit value computes `H-s`, conditional complements around one shift/subtract datapath implement both branches. Thus even the conditional constant adder need not be a separate serial adder. This optimization and its unrolled versions must be compared before assuming summary construction is competitive.

The [executable audit](entropy_arithmetic_checks.py) reconstructed the masked storage expression independently of the floor-rule constructor. It passed 172,032 primitive comparisons over all states, both input bits, and these individual rates; 33,424 local-map entry comparisons; and 4,644 every-output replay checks over 36 synthetic traces. Certificate domains came from the existing independent predictor, not serial exact entries. See [results and source/blob hashes](entropy_arithmetic_results.json). These checks support the reduction and executor behavior. They do **not** compile VVenC, test a real encoded sequence, certify the complete codec, or measure speed.

## 2. AV1: matching transition maps, but a different certification obligation

Libaom stores inverse CDF values. For each nonterminal element it either moves toward 32768 or toward zero; the update rate depends on alphabet size and a per-context count that saturates at 32. The count is determined by the number of updates, independently of the CDF's numerical state. [Pinned libaom update, indexed source body inspected](https://aomedia.googlesource.com/aom.git/+/52de8996066ff8b3130aa53ae4ce1527254b930b/aom_dsp/prob.h).

For `D=2^rate`, our independent reductions are:

```
up(s)   = s + floor((32768-s)/D)
        = floor(((D-1)*s + 32768)/D)
down(s) = s - floor(s/D)
        = floor(((D-1)*s + D-1)/D).
```

Both maps are monotone with adjacent increments zero or one, including the endpoint 32768. That endpoint needs storage capable of representing 32768; describing the probability scale as Q15 is not a reason to truncate it to a maximum of 32767. The nonterminal CDF states are only a subset of this conservative test domain.

These maps fit the general `advance_mask` transition primitive. **They do not directly fit the fixed-offset, fixed-coefficient certificate configuration:** the two branches have different residues and the rate changes during startup. It is possible to derive a separate bound or split rate phases, but this audit does not claim that extension is already implemented.

The audit passed 262,152 primitive comparisons, 262,144 adjacent-difference checks, all 495 tested alphabet-size/count rate cases, and 7,680 entry comparisons for 120 variable-rate/offset block maps. Those latter maps use explicitly supplied domains, **not certified AV1 domains**.

The AOM parsing description updates the CDF after determining the current symbol. Its HTML page explicitly calls itself a working document; the approved PDF link was located but could not be fetched in this pass. A normative conformance experiment must obtain the approved revision and matching vectors. [AOM parsing process, `read_symbol`](https://aomediacodec.github.io/av1-spec/#symbol-decoding-process), [approved PDF location](https://aomediacodec.github.io/av1-spec/av1-spec.pdf). The official tool description independently explains the per-symbol adaptive CDF and separate precision used for interval coding. [AOM AV1 tool description, §3.6](https://aomedia.org/docs/AV1_ToolDescription_v11-clean.pdf).

## 3. Why this still does not pass all three gates

**Exactness: strong.** For a fixed syntax stream and initialization, reproducing the probability state preserves the model used by the standard-compatible entropy process. Altering the recurrence is not merely a small image-quality perturbation: it can change the coder's intervals and desynchronize decoding. Conversely, the standard does not require every encoder to select identical syntax or emit the same valid bitstream. Define our target as a drop-in implementation of a pinned encoder's fixed token stream, and check the final bytes as well as internal states.

**Rate: real at the entropy-engine level, unproved at this stage.** CABAC hardware literature explicitly addresses serial dependencies and context-update hazards. The 2023 multi-result context-update design reports a complete high-throughput encoder, while its conclusion leaves VVC support to future work. It uses the earlier table-based context state machine. Treat it as an important exact hardware alternative and architectural precedent, not evidence of a beaten VVC EWMA implementation. [Fu et al., *A Highly Pipelined and Highly Parallel VLSI Architecture of CABAC Encoder for UHDTV Applications*, Sensors 23:4293](https://www.mdpi.com/1424-8220/23/9/4293).

**Superiority: entirely open.** Probability adaptation, context RAM hazards, interval/range update, renormalization, and output carry propagation are separate costs. Faster CDF production does not speed a range coder that still consumes one symbol per clock. Public AV1 hardware already pipelines range, low and carry processing; it is a relevant integration/baseline resource, not proof that our probability executor helps. Do not use the repository README's ambiguous throughput units as a validated number. [Bortoli's AV1 arithmetic-encoder RTL and trace-generation instructions](https://github.com/tuliopereirab/arithmetic-encoder-av1).

**Causality restricts the application.** On a normal decoder, the next symbol depends on the current entropy state and compressed input. The future symbol sequence cannot be handed to a block-map constructor without first decoding it or adding a separate speculative architecture. A predecoded trace is not evidence of decoder acceleration.

On an encoder, a **frozen token/bin stream** can make symbols and context IDs available ahead of probability execution. This is the legitimate opening. But live mode decisions, rate-distortion search, context selection, checkpoint/rollback and context inheritance can be state-dependent. Instrument the actual pipeline to identify a valid decoupling point; don't assume that all future tokens are available merely because the uncompressed picture is known.

Rate estimation without a range coder is a second, weaker lead: supplied candidates might need exact probability trajectories and fractional-bit sums. Yet many candidates already start from known context snapshots and can be processed independently. It must beat that ordinary parallelism. Encoder RDO is not a normative decoder process, so matching its existing decisions is an implementation-compatibility goal rather than a universal standard requirement.

## 4. The useful next experiment

Use **VVC first for arithmetic qualification**, since its valid constant-rate scalar hypotheses fit the existing certificate code. This preference is based on implementation fit, not measured throughput value.

1. Record actual `(context ID, bin, configured shifts, reset/checkpoint events)` and the native states before/after updates from one pinned encoder. Also record range-coder consumption and upstream availability times. Preserve the original tile/slice structure.
2. Measure hot-context run lengths, revisit distances, per-context bin rate, probability-stage stalls, memory hazards and the fraction of time spent elsewhere. A UHD frame rate does not determine bins per pixel or the hottest context's update rate.
3. Establish exact one-bin and 2/4-bin shift/add implementations with forwarding for context hazards. Include independent-context scheduling, finite-state/precomputed short compositions and the actual downstream coder.
4. Only if those miss the required service under a stated small-FPGA budget, compare certified rank tables and bitmaps, including token buffering, per-context metadata, certificate arithmetic, replay and reordered output delivery.
5. Require zero final-byte differences for fixed tokens and a useful improvement in complete throughput or resources. If the range coder or context-memory ports still limit the system, stop this application claim.

A conditional paper direction would be **exact probability-state preparation for a measured multi-bin video encoder on a constrained FPGA**. The arithmetic match is now supported; the bottleneck and complete advantage are not. This is a better question to test than claiming that integer EWMA automatically accelerates 4K video compression.

The [independent audit](ENTROPY_INDEPENDENT_AUDIT.md) additionally checked all 13 configured rate pairs, both packed hypotheses and their pre-update combined index. It found and prompted a correction to the main check: block replay now starts from boundaries resolved entirely through maps. Fraction-bit cost tables, full encoder decisions, final bitstreams and physical performance remain untested.

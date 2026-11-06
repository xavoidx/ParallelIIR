# Independent priority red-team review

6 November 2026. This pass tried to disprove the specificity of the certified-boundary, forward deletion-mask proposal. It inspected the current direction, constructor and competitor notes and searched primary literature beyond the previously inspected abstracts/slides. This is a technical priority assessment, not patent clearance. No hardware result or finance benefit is inferred.

## Verdict

**There is still a narrow algorithm/architecture hypothesis worth testing, but substantially less mathematical novelty than “a map evolves by deleting boundaries” suggests.** The strongest new finding is that the ordered-map literature explicitly supplies elementary adjacent-collapse generators and their multiplication/rank-shift relations. The specific floor-arithmetic rule for locating their ranks, its use on independently certified entry intervals, and a competitive complete executor were not located in the sources inspected here. That limited negative finding is not evidence of first invention.

The appropriate next commitment is a bounded comparison experiment, not an assumption that the direction already supports a paper. The proposal should survive only if its constructor and certificate costs beat good exact direct execution under the intended output contract. A pleasing elementary identity and a large improvement over state enumeration are insufficient: state enumeration can be a very weak baseline for a cheap scalar recurrence.

## The strongest newly sharpened overlap: elementary deletion is old

[Fernandes, 2024, §2 and §3](https://arxiv.org/html/2407.05084) defines generators

`a_i: (1,...,i,i+1,...,n) -> (1,...,i,i,...,n-1)`.

These collapse one adjacent image pair and translate all later image values down by one. The paper gives their products explicitly and the relation `a_i a_j = a_(j+1) a_i` for its stated index range. Lemma 3.5 reduces products to ordered generator words; the associated normal forms correspond to subsets of boundary positions. Reading here covered these actual constructions and relations, beyond the class definition/cardinality checked previously.

**Inference for this project:** after subtracting the updated base, a one-deletion floor update on its current contiguous image is precisely an elementary adjacent-collapse action. Clearing the selected old increment bit implements that action in original-entry coordinates. The rank/select coordinate conversion is useful engineering, but does not introduce a new map-composition principle. The paper does not supply our floor-rank calculation, numerical entry certificates, or executor.

The earlier [Fernandes–Paulista preprint, 2021, pp. 6–8](https://arxiv.org/pdf/2112.13427), published in 2023, independently confirms the generator lineage. Its `alpha_i`/`beta_i` generators have exactly one adjacent repeated output; Lemma 2.1 characterizes all maps of image cardinality `n-1` this way. Lemma 2.2 factors smaller-image maps through larger-image maps. This pass read those method proofs and the image/ordered-partition representation on pp. 3–4. It is a semigroup generation result, rather than an efficient floor-rounded DSP construction, but makes a general “one merge at a time” theorem particularly weak as a contribution.

The project can still explain this mathematics to readers. It should attribute the class and elementary generators, and identify its own contribution as choosing and implementing the needed generator directly from the rounded arithmetic, under a useful independently certified domain bound.

## Compensation-loop detail recovered beyond the old presentation

[Gu and Parhi, US20070014345A1, published 2007](https://patents.google.com/patent/US20070014345A1/en) supplies a complete inventor-authored technical disclosure. Read: detailed background, “Background on Pipelined Tomlinson-Harashima Precoders,” “The Proposed Low Complexity Precomputation Approach for FIR Filters,” and its application to the precoder. It walks through IIR conversion, look-ahead, removal of the current compensation input through a modulo device, and a remaining finite-level nonlinear loop. It also replaces whole-FIR enumeration of `S^L` possibilities by per-tap precomputation using `L` multiplexers plus an adder tree. This establishes more than a slide-level slogan. It does not expose certified floor-map domains, increment masks, or the deleted-rank formula. No legal scope/status conclusion is drawn.

[Chen and Wu, 2010](https://access.ee.ntu.edu.tw/files/journals/J34_2010.pdf), DOI [10.1109/TSP.2009.2037351](https://doi.org/10.1109/TSP.2009.2037351), extends this lineage with two stages of IIR pipelining and compensation precomputation. **Reading limitation:** direct PDF retrieval repeatedly timed out. Search returned actual indexed passages from §§II–III, including the equivalent IIR/finite-compensation construction, rather than merely an abstract. This is a partial-method inspection; do not label the full paper read or claim verified finite-word output equivalence. Its architecture trades dynamic range and hardware overhead, and is a useful implementation lead.

**Consequence:** wide linear calculation plus narrow nonlinear compensation is unavailable as a new decomposition claim. The floor-mask constructor must earn its distinction through ordered arithmetic and measured implementation cost. TH modulo compensation has different semantics; its output-level finiteness alone does not prove that an implementation reproduces every quantizer in the project's original recurrence.

## Strong finite-word and software comparators

[Potkonjak and Rabaey, TCAD 2000, author manuscript](https://web.cs.ucla.edu/~miodrag/papers/J_Potkonjak_TCAD_00.pdf) was recovered in full. Read: §I computational class and finite-precision discussion, §II, introductory construction, and experimental conclusions. Its feedback-linear class permits coefficients depending on inputs, but requires feedback-cycle operations to be additions/subtractions and suitable multiplications. A state-dependent floor does not satisfy that test. Finite precision is assessed through fixed-point versus double-precision simulation; this is not a proof of preserving every original rounded intermediate. Consequently the paper blocks broad claims about arbitrary recurrence speedup, but is not a demonstrated exact substitute for this floor loop. Its hardware/wordlength accounting remains relevant.

[Vigna, *Broadword Implementation of Rank/Select Queries*, author manuscript revised 31 January 2023](https://vigna.di.unimi.it/ftp/papers/Broadword.pdf) was inspected through §5/Algorithm 2 and the relevant experimental discussion; the underlying conference work is from 2008. The select-in-a-word method computes packed cumulative population counts, locates the byte using parallel comparisons, then selects inside that byte. This provides a concrete established implementation primitive. A CPU comparison should use competent broadword/BMI implementations where available, rather than a loop that scans individual set bits. This source is not an ordered floor-map constructor or an FPGA feedback-timing result. Its static-array indexing structures should not be charged to a single changing machine-word mask unnecessarily.

The current review already identifies saturated-accumulator prefix hardware, restricted-entry FSM speculation, convergence factoring, dependent-bit recovery and function reconstruction. Those are serious competitors. This pass did **not** obtain the full PACT 2018/CC 2019 sampling-and-reconstruction papers from a lawful author/institutional source. The author's publication page and primary conference program confirm the works; indexed secondary descriptions do not close the method comparison. Do not convert their unavailable full methods into an assertion that they lack ordered arithmetic or quantized examples.

## Precisely what remains candidate-specific

For `f(s)=floor((A*s+C)/D)`, set `m=D-A`, and write `A*b+C = D*b_new+r`, `0<=r<D`. Elementary algebra gives

`f(b+j)-b_new = j + floor((r-m*j)/D)`.

The removed image ranks are therefore `j_t=floor((r+t*D)/m)+1`. On `m*k<=D-1`, there is at most one within image width `k`. This pass found no earlier source applying exactly that rank rule to update a certified-domain increment mask. However, solving the discontinuity inequality is elementary; its novelty weight should be modest. The potentially substantial result is eliminating repeated state updates/inverse walks **with complete numerical certification and an implementation that remains competitive**.

Claim overlap should be stated at this granularity:

| Claim | Red-team position |
|---|---|
| Exact recurrences can be summarized and scanned | Established |
| Known information can restrict speculative entry states | Established |
| Conservative numerical analysis bounds rounded state error | Established |
| Ordered adjacent-0/1 maps admit boundary encodings | Established |
| Composing an elementary collapse deletes one ordered image boundary | Explicit old generator calculus |
| Rank/select evaluates or updates those boundary coordinates | Established primitive/elementary identification |
| The floor remainder directly determines all deletion ranks | Specific rule not located here; simple derivation |
| Certified domains make this rule useful independent of full state range | Plausible specialization, significance unproved |
| Complete certificate/construction/resolution/replay wins | Open empirical claim |

## Attacks that can still kill the direction without finding an identical paper

1. **The certificate is more expensive than the work saved.** The exact reference can be a subtraction/shift/add loop. Wider directed affine bounds and prefix products need to be compared to that circuit, including feedback initiation interval. A constructor-only operation-count improvement cannot establish this.
2. **Selection is the new recurrence bottleneck.** One arithmetic update and one small stored mask do not imply one cheap clock. Even an infrequent deletion requires a worst-case schedule, and a long combinational select path can dominate the base update.
3. **Ordinary independent parallelism wins.** Symbols, horizons, days and parameter sets may fill the machine with simpler exact serial engines. The proposed dependency technique must be compared under equal resources and real output/memory obligations.
4. **The approximate computation already meets the consumer.** Exact correction needs an independently chosen reproducibility/deployment contract or an explicit quantified cost, not thresholds chosen after observing disagreements. This is a workload objection, distinct from mathematical exactness.
5. **Replay or interfaces erase the kernel improvement.** Every-output replay is an additional pass. Block exits per second, all-event outputs per second, and complete job throughput are separate measures.
6. **Priority remains unresolved.** Missing 1991 and compiler full methods prevent a strong novelty conclusion. An exact match in either would require reframing the contribution as specialization/implementation or stopping if no performance advantage remains.

These objections do not show the arithmetic prototype is wrong. They show why a researcher can rationally reject the project even after every prototype comparison passes.

## Access log and stopping gate

The Berkeley-hosted 1988 thesis [ERL-88-61](https://digicoll.lib.berkeley.edu/record/136130/files/ERL-88-61.pdf) was located again; both record and PDF returned 403. The original 1991 quantizer-loop paper and Gu's 2005 thesis were not recovered in full. No access controls were bypassed. General searches combined floor/quantized recurrences, exact parallel execution, ordered contractions, bitvectors, rank/select, PDEP, function reconstruction, TH compensation and finite-word recursion; no direct matching deletion constructor was located. Negative searches have weak evidentiary value.

**Recommendation to the main direction:** preserve the narrow hypothesis, add elementary generator calculus and the full compensation disclosure to the comparison, and make the immediate research gate a small exact baseline/mask/certificate implementation comparison. Do not invest in a large array or write a novelty-led paper before that gate. A positive result should claim a useful specialized exact executor with a measured operating region. A negative result should be allowed to end the direction rather than trigger progressively weaker baselines.

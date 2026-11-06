# Critical prior-art review: compact exact scalar transfer maps

Review date: 4 November 2026. Scope: exact execution of `clip(floor((A*s+C)/D))`, with `0 <= A < D`, known block inputs, integer state on a finite chain, and no intermediate overflow. Local materials inspected: `SPEC.md`, `GoldenModel.py`, and the two extracted internal decision/appendix texts in `/tmp`. This is a targeted scholarly review, not a patent search or a proof of priority. Classic recursive-filter papers and application suitability are covered separately.

## Assessment

**Broad novelty is untenable.** Exact transfer-function composition, parallel chunk execution with unknown entry states, exploiting partial convergence, and prefix hardware for a nonlinear saturating DSP recurrence all have direct precedents. The most consequential additional source is Papadantonakis et al. (2005): compact exact transfer maps and a prefix architecture already remove the single-stream dependence of a saturating accumulator on an FPGA.

**The narrow candidate remains plausible but unestablished:** an output-sensitive construction for the particular floor-rounded strict contraction, obtaining a base plus one inverse threshold per reachable output increment by backward integer-ceiling propagation, followed by exact boundary resolution and replay. None of the inspected sources was found to present that complete construction. This negative observation is limited to the sources and sections actually read. Its components are mathematically elementary, so a systems result must carry substantial weight even if the exact combination has no predecessor.

The method should be described as a specialized compressed transition-function algorithm, not as discovery that nonlinear recursion can be parallelized. Required comparison families are exact unrolling; compact saturation-map prefix circuits where applicable; generic enumeration with convergence factoring; forward-only tables restricted by preceding-block images; and the proposed inverse-threshold maps. A large exhaustive lookup table alone is not a credible baseline.

## What precisely needs a priority claim

For a monotone integer function with adjacent increments in `{0,1}`, the image is contiguous. Writing `v=F(l)` and `K=F(u)-F(l)`, the project represents it as `F(s)=v+sum_j [s>=t_j]`, where `t_j=min{s:F(s)>=v+j}`. This is a run-boundary / generalized-inverse representation, not an unfamiliar mathematical object.

For an interior target and `A>0`, the one-step inverse inequality reduces exactly to `s>=ceil((D*t-C)/A)`, with legal-domain clipping and an unreachable sentinel. Upper-set preimages remain upper sets under monotone maps, so propagating this threshold backward is standard predicate preimage calculation specialized to cheap arithmetic. The potentially useful distinction is computing only the `K` final output levels rather than enumerating the state domain, and showing the cost beats strong alternatives.

The composition-width result also has a general interpretation: composition cannot increase image cardinality beyond either factor. For these contiguous images, this becomes `K_(G∘F)<=min(K_F,K_G)`. Generic FSM convergence literature already exploits the cardinality fact; the project supplies an ordered, arithmetic realization.

`GoldenModel.py` is illustrative rather than the full arithmetic contract: its serial path clips to hardcoded `[-8,7]` despite configurable `bits`, uses floating `a`, and its inverse loop lacks explicit constant-coefficient and unreachable-target guards. Literature comparisons should target the integer contract in the appendix, not infer implementation completeness from that file. The logarithmic width estimate in `SPEC.md` is not a worst-case coalescence theorem: floor quantization can preserve several fixed states.

## Closest primary sources

Each entry records actual reading depth. “Full-text sections” means the relevant method sections were inspected, not that every proof, experimental appendix, or implementation was reproduced. Comparisons below are this review's analysis.

### P01 — Papadantonakis, Kapre, Chan & DeHon, *Pipelining Saturated Accumulation* (FPT 2005)

[Author-hosted full paper](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf). **Reading:** full-text §§2–5, composition derivation, width discussion, implementation and result table; extended author version identifies the FPT venue.

The recurrence repeatedly adds and saturates, preserving each saturation's semantics. Each update becomes a unary function; composites remain in the same three-parameter shift/lower-clamp/upper-clamp family. The paper derives composition hardware and uses a prefix tree with input/output serialization. It reports VHDL simulation and routed FPGA comparisons.

**Overlap:** exact nonlinear DSP recurrence; compact closed transfer representation; associative function composition; buffering and throughput/latency tradeoff; concrete FPGA realization. This is a very strong threat to architecture-level novelty.

**Difference:** its update has unit unsaturated slope, corresponding to `A=D`, outside the project's strict contraction. No repeated floor division creates a staircase with many separated plateaus. It therefore needs neither `K` inverse-threshold passes nor contraction-induced image compression. Its constant-size representation can be substantially stronger on its own domain. A sensible paper must acknowledge this precedent explicitly and explain why fractional floor rounding breaks its three-parameter closure.

### P02 — Mytkowicz, Musuvathi & Schulte, *Data-Parallel Finite-State Machines* (ASPLOS 2014)

[Microsoft Research paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf). **Reading:** §§3–5, chunk/gather algorithms, convergence factoring and invariant; benchmark discussion inspected selectively.

The method composes transition arrays using gathers and supports both within-core and across-core execution. Section 5 factors the accumulated mapping into a selector and unique active states; later transitions process only those distinct states. Active-state count cannot increase. It explicitly handles partial convergence rather than requiring all trajectories to merge.

**Overlap:** generic transition-function lifting, chunk independence, composition, reducing redundant candidate trajectories as images shrink. Claims that partial convergence or retaining only surviving states is new are contradicted by this source.

**Difference:** the algorithm starts with enumerative maps and dynamically factors duplicate values. It does not use the ordered adjacent-increment property to reconstruct preimage boundaries via signed ceiling division. The project's possible benefit is avoiding initial-state enumeration, not inventing image reduction. Comparison should include a convergence-aware baseline rather than only an unfactored table.

### P03 — Sin’ya, Matsuzaki & Sassa, *Simultaneous Finite Automata: An Efficient Data-Parallel Model for Regular Expression Matching* (ICPP 2013; arXiv 2014)

[Author manuscript and full HTML](https://arxiv.org/html/1405.0562). **Reading:** §§III–V, algorithms 3–5, monoid discussion and complexity table.

An SFA state encodes a mapping from all original automaton states. Correspondence construction precomputes reachable maps. Chunks then evolve independently from the identity map, and their results combine by an associative operator, either sequentially or in parallel. This shifts work into automaton construction and can enlarge the state space greatly.

**Overlap:** exact chunk transfer functions and associative combination are explicit, including a sequential final resolution option.

**Difference:** precomputing a transition monoid for a fixed alphabet is distinct from computing arithmetic threshold maps for each numeric input block. SFA evaluates automaton acceptance/final states; a DSP executor must additionally deliver every internal sample, motivating replay. Replay is an implementation obligation, not by itself evidence of a new parallelism principle. An offline SFA construction could in principle represent this finite machine, but that does not imply comparable storage or runtime cost.

### P04 — Ko, Jung, Han & Burgstaller, *A Speculative Parallel DFA Membership Test for Multicore, SIMD and Cloud Computing Environments* (arXiv 2012, revised 2013)

[Full manuscript](https://arxiv.org/html/1210.5093). **Reading:** §§3–4, especially reverse lookahead §§4.2–4.3, definitions and algorithms for reduced entry sets; implementation inspected selectively.

Chunk workers process possible starting states. Reverse lookahead determines possible chunk-entry states from the image of preceding symbols. Multiple preceding symbols can shrink this set further; construction overhead and load balancing matter.

**Overlap:** the forward-only restricted-table competitor is closely related. So is the broad idea of using known preceding inputs to certify a smaller boundary domain before exact speculative execution. This source should accompany any boundary-enclosure variant.

**Difference:** candidate sets are obtained from automaton structure and finite-alphabet paths, rather than a numerical rounding-error enclosure or contiguous monotone image. It does not provide output-sensitive backward threshold construction. Its error-state omission is specific to membership recognition and must not be copied into a DSP system that must preserve all outputs. The manuscript's performance guarantees refer to its own cost model and do not transfer to hardware inverse operations.

### P05 — Propp & Wilson, *Exact Sampling with Coupled Markov Chains and Applications to Statistical Mechanics* (1996)

[Publisher primary article](https://doi.org/10.1002/(SICI)1098-2418(199608/09)9:1/2%3C223::AID-RSA14%3E3.0.CO;2-O). **Reading:** publisher abstract/metadata only; detailed monotone mechanics cross-checked in Wilson's full texts P06–P07. Do not report this as an independent full-paper reading.

Coupling from the past composes common random updates until initial-state uncertainty disappears, producing exact stationary samples. Order-preserving chains admit efficient coupling.

**Overlap:** monotonicity and coalescence eliminate dependence on unknown starts; exactness is certified rather than justified by asymptotic contraction alone.

**Difference:** the goal is sampling a stationary distribution, not executing a fixed finite input sequence from a known initial state. DSP maps may retain multiple states forever; the proposed executor retains that exact residual dependence instead of waiting for singleton coalescence. The project's two endpoint passes are established monotone-coupling reasoning, while its `K>0` map recovery is a distinct construction question. No stochastic-independence assumption is needed for the deterministic DSP correctness argument.

### P06 — D. B. Wilson, *How to Couple from the Past Using a Read-Once Source of Randomness* (1999 preprint)

[Author manuscript](https://arxiv.org/abs/math/9910050). **Reading:** full-text introduction, §2 random-map formulation and coalescence tests, read-once method overview; not all point-process extensions.

The paper explicitly describes finite compositions of random maps, tests whether their image is a singleton, and distinguishes composing forward from extending the past. It discusses computing images efficiently in the monotone setting. Read-once CFTP avoids replaying the random source under specified conditions.

**Overlap:** block map image tracking and eliminating initial-state uncertainty are well established. The source makes the map-composition abstraction especially explicit.

**Difference:** singleton detection and stationary-sampling bias control determine the algorithm. DSP replay instead produces an already specified deterministic output trace. “Read-once” here must not be confused with a DSP single-pass output executor: the purposes and permitted state/source reuse differ. This is conceptual prior art, not evidence that the project's exact arithmetic construction or FPGA performance is already published.

### P07 — D. B. Wilson, *Layered Multishift Coupling for Use in Perfect Sampling Algorithms (with a Primer on CFTP)* (1999 preprint)

[Full author manuscript](https://arxiv.org/html/math/9912225). **Reading:** monotone-coupling primer §1.6.1; multishift setup, layered construction and image-size discussion in §2 selectively.

This work constructs random maps that send intervals to finitely many image points and analyzes image size. It also explains tracking extremal states in monotone systems.

**Overlap:** compact interval images and explicit image-cardinality savings predate this project; merely observing that an interval can collapse to few outputs is weak novelty. The link is closer than an unrestricted generic Markov-chain reference.

**Difference:** the maps are deliberately designed couplers for specified probability distributions, rather than fixed quantized DSP transitions that must remain unchanged. The method is not a backward-ceiling construction for `clip(floor((As+C)/D))`, nor a parallel deterministic all-output executor. It is useful conceptual context and a search lead into storage/queueing systems, not a demonstrated anticipation of the complete project.

### P08 — Embrechts & Hofert, *A Note on Generalized Inverses* (author manuscript dated 2014)

[ETH author manuscript](https://people.math.ethz.ch/~embrecht/ftp/generalized_inverse.pdf). **Reading:** definition 2.1, proposition 2.3 and associated examples; composition-specific claims were not located.

The generalized inverse of a nondecreasing function uses an infimum crossing convention. The paper carefully distinguishes weak/strict inequalities and continuity assumptions.

**Overlap:** the project's first-entry thresholds are finite-chain generalized inverses. Calling the representation or inverse concept itself new would be inappropriate.

**Difference:** no DSP executor, output-sensitive block constructor, or FPGA cost model is supplied. The project must prove its finite-domain sentinel conventions directly; continuous-domain inverse identities cannot be copied without checking attainability. On a finite chain, upper-set preimages give the backward composition law directly. That finite-chain observation is this review's derivation, not a theorem claimed to have been read in this paper.

### P09 — Blelloch, *Prefix Sums and Their Applications* (CMU-CS-90-190, 1990; linked chapter version)

[CMU record](https://www.cs.cmu.edu/afs/cs.cmu.edu/project/scandal/public/papers/CMU-CS-90-190.html), [linked author PDF](https://www.cs.cmu.edu/~guyb/papers/Ble93.pdf). **Reading:** scan definition, up/down sweep and recurrence-related passages; source-version distinction preserved.

Associative operators support efficient all-prefix computation even when the apparent recurrence is sequential. The algorithm separates reduction and distribution down the tree.

**Overlap:** the proposed tree for block boundaries is a standard scan instantiated with transfer maps. Tree topology and associativity cannot bear the novelty claim.

**Difference:** practical tractability still depends on representing and composing each operator cheaply. A general function object may grow exponentially or require full enumeration; the project's arithmetic structure aims to avoid that. The relevant result is therefore a specialized representation/construction and measured total cost, not merely logarithmic tree depth.

### P10 — Blelloch, *Scans as Primitive Parallel Operations* (IEEE Transactions on Computers 38(11), 1989)

[Primary article full-text copy](https://people.eecs.berkeley.edu/~culler/cs262b/papers/scan89.pdf). **Reading:** definition and §III-A tree scan; implementation/history passages selectively.

The paper explicitly describes a balanced binary tree with an up sweep and a down sweep, storing left results for prefix propagation. It also distinguishes program steps from real machine cycles.

**Overlap:** a nearly exact architectural template for the appendix's boundary-resolution tree. It supports the warning that abstract tree depth does not determine hardware latency.

**Difference:** it does not exploit floor-rounded contractions or inverse thresholds. P09–P10 are two distinct publications but the same scan lineage, not two independent validations of the proposed arithmetic contribution.

### P11 — Ladner & Fischer, *Parallel Prefix Computation* (JACM 27(4), 1980)

[DOI](https://doi.org/10.1145/322217.322232), [full-text lead](https://www.cse.chalmers.se/~ms/PP/ladner.pdf). **Reading:** bibliographic record and subsequent primary-source attribution in P10 only. Direct PDF fetch returned HTTP 403; DOI fetch failed. No detailed theorem verification claimed.

This is foundational prefix-circuit prior art. Its presence prevents presenting a balanced associative boundary tree as a new circuit principle. It does not settle the specialized arithmetic novelty. Full text should be obtained before giving precise size/depth bounds or attributing a particular tree to this paper. This entry counts as a meaningful priority lead, not as a completed method comparison.

### P12 — Veanes, Hooimeijer, Molnar, Bjørner & Livshits, *Symbolic Finite State Transducers: Algorithms and Applications* (POPL 2012)

[Microsoft primary record](https://www.microsoft.com/en-us/research/publication/symbolic-finite-state-transducers-algorithms-applications/), [full paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2012/01/popl171.pdf). **Reading:** official abstract and full-text definitions/composition overview selectively; detailed solver proofs not audited.

The work uses symbolic predicates and functions over large alphabets and supports effective composition and equivalence operations, including register extensions.

**Overlap:** replacing enumeration by symbolic arithmetic, composing exact transition behavior and computing preimages belong to a mature lineage.

**Difference:** symbolic alphabets are not automatically compact representations of an exponentially large DSP state space. General decision procedures do not imply this project's output-sensitive `K` bound or a cheap physical datapath. This is weaker prior art than P01–P04, but it limits claims that arithmetic-symbolic transition compression itself is new. The proper unresolved claim concerns the concrete restricted class and cost.

## Claim-by-claim position

| Proposed claim | Assessment | Most relevant prior art |
|---|---|---|
| Recursion becomes parallel by composing exact state maps | Established | P01–P04, P09 |
| Nonlinear saturation prevents all exact parallelization | False | P01 |
| Exact nonlinear DSP prefix hardware is new | Contradicted broadly | P01 |
| Partial convergence makes maps smaller | Established | P02, P07 |
| Two endpoint trajectories certify monotone range | Established reasoning | P05–P07 |
| Prior inputs restrict chunk-entry candidates | Established broadly | P04 |
| Thresholds are generalized inverses | Established concept | P08 |
| Signed backward ceiling construction avoids state enumeration for this strict floor contraction | Not located in reviewed methods; narrow candidate | Compare especially P01–P04 and P08 |
| Complete threshold-map/replay hardware improves native single-stream requirements | Open empirical contribution | Requires new implementation/evidence |

The representation has a useful separation from P01: saturation-only maps retain a contiguous slope-one interval; fractional per-step rounding can make many separated plateaus, so a constant-size clipped-affine summary generally fails. However, “the old summary is not closed” is only the beginning of a contribution. Show that the new summary and its construction actually improve total resource/service cost.

Likewise, the ceiling rule follows from a single linear inequality. Its mathematical novelty in isolation is unlikely to support a strong paper. A credible claim combines exact semantics, provable output-sensitive construction/composition bounds, a tractable physical implementation and an application where the total executor wins.

## Search log and remaining uncertainty

Queries executed on 4 November 2026 (grouped; search snippets used only to locate primary materials):

- `Mytkowicz Data Parallel Finite State Machines 2014 pdf`; `Siny a simultaneous finite automata 2013 pdf`.
- `monotone maps coupling from the past Propp Wilson 1996 pdf`; `Wilson layered multishift coupling 2000 arxiv`.
- `parallel prefix saturating arithmetic function composition clamp addition` — located P01, the strongest new close precedent.
- `generalized inverses monotone functions composition Embrechts Hofert 2013 pdf`.
- `parallel prefix nonlinear recurrences compact function representation 1986 scan`; `Blelloch scans primitive parallel operations 1990 pdf`; `parallel simulation finite state automata Ladner Fischer 1980 associative`.
- `Hillis Steele 1986 data parallel algorithms finite state machines pdf`; `Ladner Fischer Parallel Prefix Computation 1980 pdf`; `parallelizing finite state machine computations speculative execution 2003 2004`; `Kogge Stone general class recurrence equations 1973 pdf`.
- `Cousot Cousot 1977 abstract interpretation pdf`; `symbolic finite state transducers Veanes 2012 pdf`; `parallel scan nonlinear recurrences piecewise linear functions ReLU prefix`.

The last group yielded symbolic-transition background but no stronger direct threshold constructor. Hillis–Steele and Kogge–Stone are follow-up leads; no detailed findings from unverified full methods are attributed here. The Cousot PDF was located but browser text extraction was empty, so it is not included as an audited source. P11 remains access-limited. P05's original full method was checked through later author papers, not independently reread.

There are twelve primary works in the registry above and three mathematical sources below, but only P01–P04 are close algorithm/architecture comparators; a source count must not conceal that distinction. Before a paper submission, search citation descendants of P01 and arithmetic recurrence acceleration / ordered transformation semigroups / queueing perfect simulation for a direct staircase-map implementation; check patents separately if commercial priority matters. No unsuccessful search proves absence. Hardware superiority and application suitability remain completely separate questions from bibliographic novelty.

## Second targeted pass: the constructor's mathematical foundations

This pass searched beyond DSP/FSM vocabulary. It substantially weakens any claim that the supporting representation/closure/inverse-composition theorems are new. It did **not** locate a publication implementing the full output-sensitive backward-ceiling DSP constructor.

**M01: Adeshola & Umar, *Combinatorial Results for Certain Semigroups of Order-Preserving Full Contraction Mappings of a Finite Chain*.** [Author preprint, 2013](https://arxiv.org/pdf/1303.7428); [institutional publication record, 2018](https://kwasuspace.kwasu.edu.ng/items/b0d217b4-e882-4777-9b12-08dcc399316f). Reading: definitions, Lemmas 1.1–1.2, and opening of §2. Their `OCT_n` is exactly the class of order-preserving nonexpansive full maps of a finite integer chain, the abstract class containing the project block maps. “Contraction” there means Lipschitz constant at most one, not strictly less than one. Lemma 1.2 proves that the image of a contraction on the full chain is an interval. The paper counts maps using image height and extremal image values. It does not present the proposed DSP constructor in the inspected sections. **Consequence:** integer nonexpansive closure and contiguous-image facts are established semigroup foundations, not project-specific new theorems.

**M02: Fernandes, *On the Monoid of Order-Preserving Transformations of a Finite Chain Whose Ranges Are Intervals* (2024).** [Author preprint](https://arxiv.org/pdf/2407.05084). Reading: introduction, §2 definitions/generators, and stated cardinality. It studies `IO_n`, also identified as weak endomorphisms of a directed path, and gives a monoid presentation. For a full monotone integer-chain map, contiguous range is equivalent to all adjacent differences being zero or one; consequently this is the same abstract class as `OCT_n`. That equivalence is this review's elementary identification, not wording attributed to the paper. Its count `sum_k (n-k+1)*binom(n-1,k-1)` fits choosing an image base and the `k-1` positions where the output increments. **Consequence:** a base plus increment-position representation is inherent in a previously studied class. No arithmetic backward construction or DSP speed result was found in the inspected sections.

**M03: Keimel, *Refinement Calculus with Probability or Fuzziness*, preliminary report, 8 July 2008, Appendix B.** [Author-hosted full report](https://www2.mathematik.tu-darmstadt.de/~logik/keimel/Papers/appendixB.pdf). Reading: §2, adjoint definitions, extremal formulas, Lemma 2.1. This is an author report rather than a final archival priority source. It explicitly states the reversed-composition identity for adjoints and gives least/greatest preimage formulas. Terminology for “upper” and “lower” differs across conventions, so the inequality below is preferable to relying on names. The report provides a verified primary exposition; it is not claimed as the original discovery of the general theorem.

The project's complete backward-threshold identity follows directly. Add a greatest sentinel `top=u+1` to both chains, extend every map by `F(top)=top`, and define

`L_F(t) = min{s in [l,top] : t <= F(s)}`.

Then `L_F(t) <= s` if and only if `t <= F(s)`. Thus `L_F` is a left adjoint of `F` under standard terminology, including unreachable legal targets through the sentinel. For `H=G∘F`,

`L_H(t) <= s <=> t <= G(F(s)) <=> L_G(t) <= F(s) <=> L_F(L_G(t)) <= s`,

so `L_(G∘F)=L_F∘L_G`. For an interior target of the specified update, solving `t<=floor((A*s+C)/D)` yields exactly `ceil((D*t-C)/A)` when `A>0`. Saturation, constants and sentinels supply the remaining cases. Enumerating only `t=v+1,...,v+K` then gives the constructor's `K` backward walks. This derivation needs no new composition theorem.

The threshold representation also has a standard rank/select interpretation. Set `b_i=F(l+i)-F(l+i-1)`; this is a bitvector. Evaluating `F` is a base plus a prefix rank of that vector. The thresholds are its select positions. This is a mathematical identification, not an assertion that a particular succinct-data-structure publication already constructed these DSP blocks. Compressed threshold storage and fast rank queries could improve implementation, but the rank/select correspondence itself is elementary.

**Revised narrow verdict:** the supporting theorem package is too elementary and too directly covered by established ordered-transformation/adjoint machinery to be presented as a substantial new mathematical result. A possibly unpublished specialized algorithm can still arise by using the cheap affine inverse and enumerating final output levels, but the literal `O(KL)` algorithm is an immediate output-sensitive application of those facts. A paper would need evidence that this application creates a useful algorithmic/physical tradeoff, or a stronger construction/composition algorithm, rather than relying on a new theorem claim. This is an assessment of technical substance, not a formal legal opinion on obviousness or proof that the exact algorithm has a predecessor.

Additional queries: `residuated maps composition left adjoint integer floor ceiling affine maps`; `quantized affine contraction inverse iteration staircase function algorithm`; `order preserving contraction monoid integer chain rank select transformation`; `parallel evaluation floor linear recurrence integer quantization`; `integer floor recurrence parallel algorithm`; `quantized affine inverse contraction`; `monotone map rank select compression function composition`; `order-preserving contractions kernel image finite chain`; `floor linear recurrence acceleration`; `integer affine preimage threshold recurrence`; `succinct monotone functions composition rank select`; `Combinatorial results order-preserving full contraction pdf`. Many affine-quantization hits concerned neural-model or quantum quantization and were irrelevant. These negative search results establish no priority. Useful vocabulary for subsequent citation searches is now `OCT_n`, `IO_n`, weak endomorphisms of a directed path, adjoint/residual composition, and rank/select on increment bitvectors.

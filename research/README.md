# Research assessment of exact parallel quantized filtering

**Latest independent audit:** [THIRD_PASS_VERDICT.md](direction/THIRD_PASS_VERDICT.md) records a stronger exact baseline, closer deletion-generator prior art and repaired prototype interfaces. The specified arithmetic survived independent oracle and closed-state checks; novelty and complete performance remain unestablished. The next step is a bounded comparison of shared-base relative ranks, bitmaps, certification and exact unrolling.

**Latest conceptual follow-up:** [Recommended research direction](direction/RESEARCH_DIRECTION.md) proposes certified boundary intervals and a one-pass forward deletion-mask constructor for exact financial feature replay. It includes a deeper primary-art/application review, adversarial second pass, a new working numerical prototype, fixed-configuration capacity bounds and a rough RTL roadmap. Start there for the current recommendation; the dated reviews below document how it developed. No hardware speedup or actual-market numerical result is claimed.

Review date: **4 November 2026**. Project: buffered, bit-exact execution of the scalar recurrence `s'=clip(floor((A*s+C)/D))`, with `0<=A<D`, using compact block maps, exact boundary resolution and replay.

**6 November follow-up:** [Financial EWMA and the small-FPGA opportunity](FINANCIAL_EWMA_REVIEW.md) corrects the original finance search's narrow scope. Native rounded financial FPGA EMAs exist, and tick-level liquidity smoothing supplies a useful proposed integer application. The follow-up includes an iCE40UP5K resource/interface audit, actual exchange capacity targets, new exact-integer checks, and a financial RTL roadmap. Buffered replay is a credible starting point; a complete faster-than-clock UP5K advantage remains unmeasured. The fetched `FilterSimulation.py` also fixes the old four-bit clipping defect described below; those original audit findings are historical.

**Recommendation: continue only as a bounded feasibility investigation. The current evidence does not establish a novel, significant, publication-ready result.** There is a plausible specialized implementation question, but much of the original conceptual territory is already occupied. No reviewed application yet demonstrates both matching integer semantics and a system requirement that this approach beats the strongest simpler alternatives on.

The most promising research claim is: *an efficient exact executor for specified quantized contractive recurrences, whose summary construction and scheduling improve a measured throughput, latency or resource tradeoff on a native workload*. Whether that claim is true remains to be tested. The representation alone is unlikely to carry a strong paper.

## Contents and evidence status

| File | Purpose |
|---|---|
| [direction/RESEARCH_DIRECTION.md](direction/RESEARCH_DIRECTION.md) and [supporting index](direction/README.md) | Latest differentiated conceptual proposal, deeper finance/prior-art reviews, proof/checks, source reading list and RTL direction |
| [FINANCIAL_EWMA_REVIEW.md](FINANCIAL_EWMA_REVIEW.md) | Main shareable follow-up: concrete finance applications, faster-than-clock feasibility, new results, reading list and RTL milestones |
| [FINANCIAL_EWMA_APPLICATIONS.md](FINANCIAL_EWMA_APPLICATIONS.md) | Tick liquidity, price/flow indicators, intensity, datasets and precise workload limitations |
| [FINANCIAL_EWMA_PRIOR_ART.md](FINANCIAL_EWMA_PRIOR_ART.md) | Native rounded financial arithmetic, piecewise extension, existing FPGA finance and implementation contracts |
| [FINANCIAL_EWMA_FPGA.md](FINANCIAL_EWMA_FPGA.md) | Verified UP5K resources, timing distinctions, interfaces, memory banking and fair baselines |
| [financial_ewma_checks.py](financial_ewma_checks.py) and [results](financial_ewma_results.json) | Reproducible integer inverse/map/replay checks and synthetic normalized-EWMA width characterization |
| [COLLABORATOR_BRIEF.md](COLLABORATOR_BRIEF.md) | Self-contained email attachment consolidating the review, prioritized reading and an RTL learning roadmap |
| [PRIOR_ART.md](PRIOR_ART.md) | Closest exact-map, FSM, saturation, coupling, ordered-map and inverse-composition precedents; claim-by-claim novelty assessment |
| [FILTER_LITERATURE.md](FILTER_LITERATURE.md) | Classic and current recursive filtering, compiler and finite-precision comparisons; necessary baselines and venue fit |
| [APPLICATIONS.md](APPLICATIONS.md) | Native source/configuration evidence, ranked application leads, exclusions, public stimuli and source-reading limits |
| [TECHNICAL_AUDIT.md](TECHNICAL_AUDIT.md) | WIP defects, exactness checks, quantization obstruction, width measurements and corrected cost model |
| [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | Concrete experiments, required measurements and decisions that would justify continuing or narrowing the project |
| [audit.py](audit.py) and [results](audit_results.json) | Reproducible exact-map/composition/replay checks and 100 width-sweep configurations |
| [codec_arithmetic_check.py](codec_arithmetic_check.py) and [results](codec_arithmetic_results.json) | Reproducible check of the proposed reduction of inspected AMR-WB arithmetic; not compiled codec conformance |

The review separates **published evidence**, **our derivations**, **new executed software checks**, and **unvalidated hypotheses**. Each literature entry records reading depth. Some important classic full texts were inaccessible, and some application code was accessible only as indexed source bodies. Those gaps remain explicit. The internal October reports' earlier test archives were not present and were not reproduced. No FPGA synthesis, routing, power measurement or native application benchmark was performed. Original project files were left unchanged.

## What the literature changes

**The strongest architectural predecessor is older and closer than the internal notes suggest.** Papadantonakis, Kapre, Chan and DeHon's *Pipelining Saturated Accumulation* already builds compact exact nonlinear transition summaries, composes them with a prefix architecture and evaluates an FPGA implementation. It addresses unity-slope saturating accumulation, whereas this project adds fractional per-step rounding. That is a meaningful difference, but the broad “exact nonlinear recursion through compact maps” claim is already established. [Author paper, FPT 2005](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf)

**Partial convergence and restricted starting-state execution are also established.** Data-parallel FSM work avoids continuing redundant trajectories after states merge; speculative DFA work restricts chunk entry candidates using preceding input symbols. Accordingly, neither “only retain remaining states” nor “use previous blocks to shrink entry uncertainty” is a new contribution by itself. [Mytkowicz et al., 2014](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/asplos302-mytkowicz.pdf), [Ko et al., manuscript](https://arxiv.org/html/1210.5093)

**The basic mathematical structure is established too.** Order-preserving nonexpansive maps of a finite integer chain have been studied as `OCT_n` and `IO_n`. The base-plus-threshold representation is the increment-position representation of this map class. Backward threshold composition is a generalized-inverse/adjoint composition identity; the one-step ceiling follows by solving a linear inequality. These observations weaken a theorem-led publication claim considerably. They do not prove the exact DSP construction has been published. [Adeshola–Umar](https://arxiv.org/pdf/1303.7428), [Fernandes](https://arxiv.org/pdf/2407.05084), [Keimel, Appendix B](https://www2.mathematik.tu-darmstadt.de/~logik/keimel/Papers/appendixB.pdf)

**The remaining distinction is arithmetic-specific construction and total cost.** None of the inspected methods was found to implement this complete output-sensitive backward-ceiling constructor for the stated machine. This is a bounded search result, not proof of novelty. Moreover, an unpublished specialization can still be too straightforward or too expensive to be significant. It needs either a stronger construction/composition algorithm or convincing application-level value.

Linear filtering and compiler papers matter for both architecture and application alternatives. RecFilter already uses local computation, boundary reconciliation and local recomputation. Maleki–Burtscher includes exact integer-linear cases, so “previous parallel recurrences are never exact” would be false. Recent 2026 filtering work provides strong numerical performance comparators, though its floating-point/reassociation contract differs from this integer machine. [RecFilter](https://mit-gfx.github.io/recfilter/recfilter.pdf), [Maleki–Burtscher](https://userweb.cs.txstate.edu/~burtscher/papers/asplos18.pdf), [Zhai–Paris](https://arxiv.org/html/2607.23763v1)

**Before a strong novelty claim, obtain the classic quantizer-loop work.** Parhi's 1991 *Pipelining in Algorithms with Quantizer Loops* explicitly concerns parallel branches and delayed decisions around quantizers. Its full method, and the 1989 incremental-block paper's roundoff treatment, remain unresolved comparisons. Lack of access cannot be used to rule them out. [Author bibliography and links](https://parhi.umn.edu/publications/journal-publications)

## Concrete application portfolio

These are candidates for experiments, not demonstrated wins. Their value is that each isolates a different requirement the project must satisfy.

| Candidate | Concrete anchor | Why use it | Main obstacle |
|---|---|---|---|
| AMR-WB `Deemph2` | Inspected 16-bit primitive reduces to `A=22282,D=32768,C=16384*x+16384`; native weighted-speech call has 256 samples | Strongest exactness motivation: standardized bit-exact code and conformance vectors | Different inspected source revisions must be unified; 12.8 ksample/s and independent calls make throughput significance weak |
| UKUI exponential blur | Native fixed-point integer recurrence on buffered byte images | Concrete scalar arithmetic and realistic complete image pipeline | Need target-platform signed shift and frozen coefficient; rows/channels already parallel; compatibility need and rate target unproven |
| SiPM detector emulation | Three positive-pole banks; published feedback timing problem and look-ahead implementation | Strongest physical fast-stream lead | Internal rounded-state contract missing; existing solution works; buffering allowance and benefit remain unknown |
| Financial EMA replay and quote-liquidity smoothing (6 November follow-up) | Native 17-bit rounded FPGA price EMAs; published quote-time liquidity EWMA at .97 retention | Concrete exact arithmetic benchmark plus useful proposed financial feature; captured data allow buffered replay | Need real-tape K/rate measurements, precision validation for new integer ports, and an advantage over shift/add, unrolling and symbol interleaving |

The codec lead comes from [AOSP source](https://android.googlesource.com/platform/frameworks/av/%2B/dd833ba601e642d72da2200a2fd9c3fa1cb69d2d/media/module/codecs/amrwb/enc/src/deemph.c) and [ITU's bit-exact implementation description](https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=13429). Its mathematical reduction, mixed-revision limitation and test vectors are documented in the application review. The blur lead comes from [UKUI's packaged source](https://sources.debian.org/src/ukui-session-manager/1.1.3.1-1/ukui-session/gsm-blur.c). The physical lead is the [SiPM emulator preprint](https://arxiv.org/html/2607.00841v1).

Radio DC correction deserves lower priority: a tiny adaptation parameter means slow contraction. General biquads, state-dependent envelope attack/release, and feedback control are not automatically supported. Even superficially similar integer blur implementations can place quantization differently and lose monotonicity. Do not adopt a workload merely because its ideal transfer function has one pole.

For usefulness, distinguish three questions: does the arithmetic fit; does anyone need its exact old outputs; and does the complete executor improve their system? The codec best answers the second question, blur provides a readily specified buffered kernel, and SiPM best motivates the third. None currently answers all three.

## What the new checks establish

The **4 November version** of the WIP's nominal 16-bit model clipped every update to `[-8,7]`. For `[100,0,0]` at `a=1/2`, it produced `[7,3,1]`, whereas the intended 16-bit result was `[100,50,25]`. Serial/parallel equality could therefore hide a shared reference error. The fetched `FilterSimulation.py` now uses configured state bounds. Other historical audit findings and recorded results remain in the source-linked audit; this follow-up is not a full re-audit of the updated implementation.

An independent exact-integer implementation passed 47,352 entry-state comparisons, 300 composition cases and 4,782 replay-output comparisons in the documented finite test suite. Separately, the codec arithmetic reduction passed 524,288 primitive-model comparisons. Neither result is hardware equivalence or native application conformance.

The width sweep exposes the main performance risk. At `a=255/256`, `L=64`, true 16-bit silence retains **51,012 thresholds**; at `L=4096`, it retains **255**. Full-scale random inputs often force coalescence through saturation, while modestly scaled inputs can retain large maps. In fact silence preserves 256 distinct fixed states for this coefficient, so an arbitrarily small K is impossible regardless of block length. This is a derived counterexample to treating the spec's logarithmic estimate as a universal guarantee.

The count `(K+3)L` mixes forward and inverse operations, and `P/(K+3)` ignores boundary resolution, storage, output ordering and unequal arithmetic costs. Measure actual inverse circuitry, memory and batch scheduling. The direct serial loop's delay is a baseline constraint, not a universal lower bound on all exact implementations.

## What would make the project publishable

A credible systems paper needs all of the following:

1. **A precise difference from the closest methods.** Explicitly acknowledge saturation-map prefix hardware, convergence-aware FSM execution, quantizer-loop pipelining and the elementary inverse mathematics.
2. **A useful algorithmic or architectural contribution.** Examples to investigate are shared inverse computation, hybrid arithmetic/threshold summaries, or a resource-aware constructor that chooses between inverse thresholds and restricted forward tables. These are hypotheses requiring their own novelty checks.
3. **An exact, complete implementation.** Preserve every required output and state across batch boundaries, including signed rounding, saturation, map overflow and fallback. Count preparation and replay.
4. **A native requirement and fair advantage.** Show better sustained throughput at matched resources and acceptable delay, or fewer resources at a fixed required service level, against the best exact baseline. Show why exactness matters to the application.
5. **An honest operating envelope.** Publish failure regions, worst-case K, silence/low-amplitude behavior, fallback service and cases where a simpler implementation wins.

A practical evaluation paper could fit SiPS if these conditions hold; a stronger reusable architecture/tool contribution could fit FPGA. Those are audience-fit judgments, not acceptance predictions. A theoretical note based only on map closure and the ceiling inverse looks weak, and an ML framing is unsupported. Official venue scope sources are in [FILTER_LITERATURE.md](FILTER_LITERATURE.md).

The immediate next decision is whether **one** native exact workload can show a plausible equal-resource advantage after correcting the reference and measuring constructor cost. If not, preserve the correctness results and stop or narrow the acceleration claim. The detailed [experiment plan](EXPERIMENT_PLAN.md) is designed to reach that decision before investing in a full architecture.

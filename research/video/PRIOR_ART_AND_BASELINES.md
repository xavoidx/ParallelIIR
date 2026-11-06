# Spatial recursive video filtering: prior art and decisive baselines

Reviewed 6 November 2026. This is an adversarial application/literature pass for a proposed exact integer, one-pole FPGA executor at UHD 4K60. It reads [the earlier literature review](../FILTER_LITERATURE.md) and [the third-pass verdict](../direction/THIRD_PASS_VERDICT.md). It does not report RTL synthesis, board measurements, an exhaustive priority search, or a proven native customer requirement.

## Verdict

**Spatial recursive filtering is a credible high-rate application family, but the conjunction needed for this project is unproved:** a real rate bottleneck, a prescribed per-sample integer rounding contract, and a complete improvement over the strongest exact alternative at acceptable latency. Merely naming “4K60 fixed-point recursive blur” establishes none of those three together.

The inspected native implementations are especially inconvenient for an exact-integer motivation: OpenCV's recursive domain transform and FFmpeg's Gaussian IIR both use floating-point internal recurrences, even with integer images. A new integer implementation can be useful, but reproducing its own chosen arithmetic does not establish compatibility with either native filter. The relevant potential consumer is an existing fixed-point ISP/RTL/software reference whose *internal update contract* must be preserved. No such consumer was established by this pass.

ParallelIIR should first compete with exact 2/4-pixel combinational unrolling and buffered row interleaving. Independent column and temporal-pixel lanes are particularly strong. Its bitmap must also compete with the project's shared-base relative-rank representation. Linear look-ahead, RecFilter, and GPU numerical filtering remain performance/quality comparators; treating all of them as already bit-exact implementations of an integer recurrence would be incorrect.

## 1. The rate is real; the single-chain bottleneck is conditional

Take **UHD 3840 × 2160 at exactly 60 frames/s**, rather than unspecified “4K.” Derived active demand is `3840*2160*60 = 497,664,000` pixels/s. For the common 4400 × 2250 timing, total pixel clock is 594 MHz. AMD's current timing table gives those totals, and its gamma-LUT guide explicitly specifies 297 MHz at 2 pixels/clock or 148.5 MHz at 4 pixels/clock for 4K60. These are video interface requirements, not evidence that a four-deep recursive arithmetic path closes timing. [AMD video timing](https://docs.amd.com/r/en-US/pg290-v-smpte-uhdsdi-rx-ss/Video-Resolutions), [AMD throughput guidance](https://docs.amd.com/r/en-US/pg285-v-gamma-lut/Throughput).

| Pixels accepted per clock | Clock for average active pixels only | Clock for 594 Mpixel/s timed stream |
|---|---:|---:|
| 1 | 497.664 MHz | 594 MHz |
| 2 | 248.832 MHz | 297 MHz |
| 4 | 124.416 MHz | 148.5 MHz |
| 8 | 62.208 MHz | 74.25 MHz |

The average-rate column assumes sufficient buffering and a valid schedule through blanking. A design exposed directly to timed bursts must handle the burst column or prove its buffering bound. A documented AMD reference pipeline transports 4 pixels/clock at 150 MHz for UHD60. This supports using four-pixel hardware as an ordinary baseline, without demonstrating any particular recursive filter. [AMD VCK190 reference design](https://docs.amd.com/r/en-US/ug1442-vck190-base-trd/HDMI-Rx-Capture).

Three different dependencies must be separated:

* **Horizontal spatial recursion:** adjacent pixels of one row really are dependent. Different rows and color components are independent for a prescribed separable pass. Raster arrival makes buffered row interleaving a scheduling/memory tradeoff, not an immediate free substitution.
* **Vertical spatial recursion:** adjacent raster pixels belong to different column states. Four adjacent columns can use four independent exact lanes. Each column is revisited only on the next row, leaving ample pipeline separation; charge state RAM ports and read/modify/write hazards.
* **Temporal per-pixel recursion:** each image location has its own history. UHD has 8,294,400 such chains, each updated only 60 times/s. The 497.664 Mupdates/s aggregate does not require a single chain to run at that speed. Frame-state bandwidth and the rest of the ISP may dominate.

These observations are dependencies of the stated recurrences, not a claim that every image algorithm is separable or that every memory layout supports conflict-free access. They do invalidate using aggregate video rate as proof of an unavoidable single-state recurrence wall.

Count the entire filter. Four directional passes require four state updates per channel per output pixel; three iterations of that structure require twelve. At UHD60, twelve passes on three color channels mean **17.916 G scalar state updates/s**, derived before guidance generation and conversion. Reporting a local engine's “pixels/s” without the number of passes, channels and replicated stages is ambiguous. Anti-causal processing also requires future samples: at least row buffering for a reverse horizontal pass, and potentially frame-scale storage/delay for reverse vertical execution, depending on the chosen full schedule.

Memory can erase an arithmetic win. As a derived traffic example, one read plus one write of a 16-bit scalar image at UHD60 is 1.991 GB/s. Four independently materialized directional passes consume 7.963 GB/s per channel, excluding coefficients, padding and protocol overhead. Fusion can reduce that traffic; replay and local-map buffers can increase it. Measure actual external transfers and internal bank/port pressure for both implementations.

## 2. Audit the actual arithmetic before selecting a native target

### OpenCV recursive domain transform: close shape, different contract

In upstream `opencv_contrib`'s inspected `4.x` header, `WorkType`, `DistType` and `IDistType` are `float`. The header exposes horizontal work by rows and vertical work by columns. [Primary header, typedefs and pass ranges](https://raw.githubusercontent.com/opencv/opencv_contrib/4.x/modules/ximgproc/src/dtfilter_cpu.hpp).

The implementation converts the source into its working type, executes the RF passes/iterations, and converts to the requested destination depth afterward. A scalar update has the form `cur += alpha * (prev - cur)`. Guidance-derived coefficients vary with position; later iterations modify them. Thus 8-bit input/output does **not** imply flooring to 8 bits at each recursive step. A floor-quantized one-pole replacement is a different arithmetic program. Inspected the RF dispatch, horizontal/vertical update loops and coefficient creation; did not compile or compare outputs. The links are moving branches, so a later experiment must pin an exact commit and compiler/FP contraction settings. [Primary implementation](https://raw.githubusercontent.com/opencv/opencv_contrib/4.x/modules/ximgproc/src/dtfilter_cpu.inl.hpp).

Guidance computed entirely from known source pixels can make a coefficient schedule available in advance. That is promising for future exact-map work, but the project's current fixed-coefficient certification constants and one-deletion capacity proof cannot simply be reused for arbitrary varying coefficients, zero/identity steps, changed pass shapes or resets. Derive the actual extension before claiming support for domain transform.

### FFmpeg `gblur`: a production one-pole example that still uses float

Upstream `vf_gblur.c` copies integer pixels into a float work buffer. After the Gaussian IIR and postscaling it writes integer outputs using `lrintf`; it also accepts float images. The filter distributes horizontal work across rows and vertical work across column ranges. Inspected the input/output conversion and scheduling path, not every ISA dispatch. [Primary filter source](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/vf_gblur.c).

The generic core uses float `nu`, with updates such as `ptr[x] += nu * ptr[x-1]` and a corresponding reverse pass; postscaling clips float results. Its vertical core explicitly processes eight independent columns together. This is unusually clear primary evidence for both arithmetic-contract mismatch and a strong ordinary parallel baseline. It does not demonstrate that a floor-after-every-update accelerator preserves FFmpeg output. Pin the repository and selected optimized kernel before any compatibility claim. [Primary generic kernel](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/vf_gblur_init.h).

### NVIDIA VPI: relevant deployed numerical comparator, not evidence of integer exactness

The current VPI 4.1 documentation describes a third-order recursive Gaussian, causal/anti-causal row/column processing and overlap across passes, citing Nehab–Maximo 2016. This is broader than a positive scalar one-pole. The inspected public algorithm page does not prescribe a per-step integer floor/saturation machine. Supported integer image formats, if present for a backend, cannot fill that gap. Use VPI for an application-quality/throughput comparison after matching order, sigma, border behavior and transfer costs; do not call its output an exact-integer oracle without backend arithmetic evidence. Depth: full algorithm description, not proprietary implementation or performance-table reproduction. [Official VPI algorithm documentation](https://docs.nvidia.com/vpi/algo_recursive_gaussian_filter.html).

### What would establish a suitable native exact contract

Obtain an actual reference containing all of: state/input widths; fractional scale; signedness; initialization and row/column border rules; coefficient quantization; product and accumulator widths; overflow behavior; rounding offset and direction; clipping location; pass order; reset behavior; and output timing. Then identify the reason the consumer needs or materially values identical outputs: existing RTL conformance, deterministic cross-platform deployment, regression/golden-image compatibility, or reproducible downstream decisions. These are possible motivations, not evidence that an existing customer has them.

“Fixed point,” “accurate,” “integer pixels,” and “exact Gaussian” are insufficient. Exactness to the continuous Gaussian, ideal real recurrence, a selected floating-point implementation and a specified rounded integer trajectory are distinct promises.

## 3. Primary prior art and reading depth

The following additions supplement the existing project bibliography. None establishes priority for the whole proposed executor, and no access failure is evidence of novelty.

| Source | What was actually inspected | Consequence for this project |
|---|---|---|
| Nehab–Maximo–Lima–Hoppe 2011, *GPU-Efficient Recursive Filtering and Summed-Area Tables* | Full PDF available; formulation, block/perimeter architecture, precision and evaluation sections inspected | Parallel boundary reconciliation, multi-pass fusion and memory reduction are established. Precision evaluation uses relative residual, not identity to samplewise integer rounding. [Author PDF](https://hhoppe.com/recursive.pdf) |
| Chaurasia et al. 2015, *Compiling High Performance Recursive Filters* | Full PDF available; tiled schedule and evaluation arithmetic checked, prior project review supplies fuller transformation discussion | Experiments explicitly use float32. RecFilter is a strong numerical/scheduling comparator; it does not supply a proof for moving or deleting integer quantizers. [Author PDF](https://mit-gfx.github.io/recfilter/recfilter.pdf) |
| Cong–Huang–Zou 2011, *Accelerating Fluid Registration Algorithm on Multi-FPGA Platforms*, FPL, DOI 10.1109/FPL.2011.20 | Indexed author-uploaded full-text extraction, especially Gaussian architecture and accuracy sections; direct repeat open later failed | One-pole recursive Gaussian PEs interleave independent 1D sequences to hide MADD latency, with forward/backward units and BRAM buffering. Their fixed-point conversion is assessed by application accuracy; exact update rounding was not recovered. [Author-uploaded paper](https://www.researchgate.net/publication/220759507_Accelerating_Fluid_Registration_Algorithm_on_Multi-FPGA_Platforms), [institutional bibliography](https://cdsc.ucla.edu/publications/) |
| Khorbotly–Hassan–Veillette 2017, *Synthesis of recursive linear-phase filters for fixed-point hardware platforms* | Full publisher HTML, §§3–5 and §7 inspected; equation images not all individually decoded | Recursive exponential basis, switching/reset and bounded finite-word error are explicit. Some coefficients are rounded and some precision is deliberately reduced. Its full-precision cancellation discussion concerns another arithmetic contract, not identity to this project's quantized contraction. [Primary full text](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-cds.2016.0123) |
| Ferreira–Gastal–Schnorr–Navaux 2020, *Performance and Error Analysis of Recursive Edge-Aware Gaussian Filters on GPUs* | Full publisher PDF available; formulation, approximation/error analysis and implementation discussion inspected, not run | Independent blocks with extended context and approximated boundary conditions deliberately trade error for speed. This is an application alternative when exact execution is optional. Its complex recurrence is outside the present scalar monotone-map contract. [Primary PDF](https://conferences.computer.org/sibgrapi/pdfs/SIBGRAPI2020-2PHUGH67ZBfLyHWbyZRFxI/927400a085/927400a085.pdf) |
| Gu–Parhi, *Low complexity Tomlinson–Harashima precoders*, published disclosure US20070014345A1, 2007 | Inventor-authored disclosure, background, pipelined structure and precomputation explanation inspected; equation images not fully reconstructed | Decomposing nonlinear feedback into a pipelined IIR and a finite-level compensation/precomputation path is established. It is a modulo/communications architecture, not a directly audited implementation of the video floor rule. [Primary disclosure](https://patents.google.com/patent/US20070014345A1/en) |

The FPL paper's ordinary interleaving schedule is a direct architectural challenge even though its numerical contract differs. Keeping *each lane's identical integer operations* while changing the order among independent lanes is exact by construction. This inference does not require its authors to have implemented this project's integer rule.

The companion SASP 2011 paper, *3D Recursive Gaussian IIR on GPU and FPGAs—A case for accelerating bandwidth-bounded applications*, DOI 10.1109/SASP.2011.5941081, was bibliographically confirmed through the institutional list above; its primary full text was not obtained. Secondary abstract mirrors describe it as bandwidth-bounded. Do not attribute detailed arithmetic or measured modern-UHD behavior to that uninspected paper.

For 2017, a full-precision implementation preserving pole-zero cancellation and a rounded implementation stabilized by reset are different targets. Neither the word *exact* in the first discussion nor the word *fixed-point* in the second establishes preservation of an arbitrary original quantized state machine.

The 2020 paper remarks that small errors can disappear in 8-bit output conversion. That is an application-quality argument, not universal bit identity: even an error much smaller than one output unit can cross a rounding boundary. If only final integer pixels must match, output-level equality must be verified or certified; a generic bounded real error is insufficient.

The unresolved classic Parhi 1991 quantizer-loop paper remains an explicit reading obligation in the earlier project review. The accessible Gu–Parhi disclosure reinforces that “nonlinear quantization prevents all prior pipelining” is false. A serious comparison must distinguish conventional linear look-ahead with changed roundoff from exact speculative/precomputed quantizer branches.

## 4. The exact baseline must preserve every intermediate quantizer

For a simple concrete counterexample, define `F(s,x)=floor((3*s+x)/4)`. Starting at `s=1`, inputs `x1=0,x2=2` produce `0,0`. Collapsing the two ideal affine updates and rounding only at the end instead gives `floor((9*1+3*0+4*2)/16)=1`. Thus algebraic look-ahead by itself is not the correct exact baseline.

Conversely, an exact two-pixel combinational block computes `t=F(s,x0); u=F(t,x1)` with *both* original quantizers. Four-pixel unrolling is the corresponding four-stage composition. It is a serious baseline because it has no predictor, certificate construction, rank/select, boundary resolution or replay. Its disadvantage is a longer combinational feedback path, which must be measured after routing. Arithmetic specialization matters: dyadic coefficients can produce shifts/adds rather than general multiplies, and `A=D-1` deserves a quotient/remainder or subtract-and-shift implementation that preserves unsigned floor semantics. Do not infer signed truncation behavior from an unsigned identity.

| Exact candidate | Strength | Cost or qualification to measure |
|---|---|---|
| Best scalar one-pixel RTL | Smallest complete design; constant-coefficient specialization | Routed recurrence-loop timing; actual input/output handshake |
| Exact 2/4/8-pixel combinational composition | Preserves the source machine without summary overhead | Clock falls as depth grows; compare achieved `pixels_per_clock*f_route` |
| Pipelined row interleaving / multiple independent streams | Preserves intra-row order; hides arithmetic latency | Buffering, resequencing, bank layout, startup latency and available independent rows |
| Parallel column states | Natural exact independence in raster order | State RAM banks/ports, lane count, border and reverse-pass scheduling |
| Independent temporal-pixel lanes | Vast number of independent states | Frame-state read/write bandwidth, not single-chain speed |
| Full-state transfer table and composition for small state widths | Generic exact function baseline | 256 states at 8 bits is small enough to test; construction, memory ports and composition bandwidth count |
| Restricted forward enumeration / candidate replay | Simple exact construction on certified domains | Reuse shared arithmetic; avoid artificially charging a general multiplier per candidate |
| Shared-base relative-rank table | The project's strongest current summary competitor; common full-width base/remainder plus narrow lanes | Physical compare/decrement timing, fanout, bitslicing, ports and memory |
| Bitmap summary | Compact payload | Rank/select feedback, deletion/index update, complete resolution/replay and certification |
| Finite-compensation / branch precomputation | Close classic nonlinear-loop alternative | Derive compensation alphabet and exact width/rounding; synthesize practical 2/4-step versions |

For row interleaving, do not compare a frame-buffered baseline against a zero-buffer streaming target without disclosing delay. Conversely, if the full filter already needs a reverse pass/frame store, do not prohibit the baseline from using the same stored rows. Four 3840-pixel rows at 16 bits occupy 245,760 payload bits; this derived illustration excludes ping-pong duplication, banking and control. Measure the real arrangement rather than calling interleaving either free or impossible.

Redundant state or finite compensation deserves attention before a bitmap architecture is declared best. An extra remainder/carry can change the arithmetic representation without changing logical outputs, but merely retaining all discarded fractional bits changes the source machine unless its discarded-rounding effects are reconstructed exactly. The appropriate test is sequential equivalence to the frozen reference, not equality of ideal transfer functions.

## 5. Small inexpensive FPGA gate

The intended target is a **small inexpensive FPGA**, so headline throughput on a large GPU or multi-FPGA server does not establish useful implementation cost. The classic numerical systems above are architectural precedents and application alternatives; they are not price-matched hardware results.

Choose one actually affordable board/part with the required input/output interface and a stated LUT, RAM-bank, DSP and clock budget. Charge any external video bridge, frame memory and extra FPGA required by the design. A part that can host an isolated arithmetic engine but cannot carry the specified video interface/memory schedule is not a complete UHD60 solution.

For that target, make the first comparison deliberately small: exact dyadic one-pole 1/2/4-pixel shift/add RTL, a few buffered/interleaved rows, and bitmap versus shared-base ranks on the *same* certified interval. Small pixel/state widths and constant coefficients favor cheap exact arithmetic, so a general-multiplier baseline would be especially misleading. Parameterize true state precision independently from image output depth; an 8-bit output does not prove that only 8 state bits suffice for the selected reference.

Do not assume a summary array is inexpensive because its mask has few bits. Include predictor endpoint widths and products, local input storage, rank/select or rank-lane logic, replay duplication and concurrent RAM ports. If the whole engine misses the small device's budget, test a smaller/phased configuration and report its actual service rate. Do not use a larger device to rescue the performance claim while keeping the inexpensive-device motivation.

On a tightly constrained part, **meeting UHD60 with exact ordinary lanes/unrolling at lower total resource cost is a negative result for the proposed accelerator**, even if the latter has a higher local arithmetic rate. A worthwhile alternative result would be sustaining the same video workload on a demonstrably cheaper/smaller part, or leaving measured resources for the rest of the pipeline. Neither has yet been demonstrated.

## 6. A falsifiable experiment and stop rule

1. **Freeze the application first.** Secure a native reference with a compatibility reason and a UHD60 requirement, or label the experiment honestly as a newly specified exact-integer blur. A native OpenCV/FFmpeg replacement requires matching their actual float semantics or declaring a new quality contract.
2. **Locate the bottleneck.** Measure a complete exact scalar/multi-lane baseline with the real pass order, IO, line/frame buffers and coefficient production. Record whether arithmetic recurrence, external bandwidth, bank conflicts, or reverse-pass schedule limits service. A temporal filter or naturally interleaved vertical pass should not be sold as a single-state acceleration problem.
3. **Start with the cheap challengers.** Route exact 1/2/4-pixel implementations, buffered row interleaving and column lanes. Use the same coefficient, widths, device/speed grade, tool version, constraints and allowable buffering as the candidate. These tests can falsify the application fit before building a full predictor array.
4. **Compare both summary representations.** First supply the same valid certified domains to bitmap and relative-rank engines to isolate representation cost. Then add the real certificate/predictor, boundary resolution, replay, buffers, all output generation and coefficient costs. The isolated result is not complete throughput.
5. **Prove the promised arithmetic.** Exhaust small widths and directed boundary cases against literal sequential updates; formally check RTL where feasible. Include all-zero/constant ramps, checkerboards, high-contrast edges, maximum values, high-retention coefficients and line/frame resets. Check every internal state if that is the contract, and every output pixel in the full schedule. PSNR/SSIM is not an exactness test.
6. **Report a Pareto comparison.** At fixed UHD60 service and maximum permitted delay, compare LUT/FF/DSP/BRAM and measured energy if available. At equal device resources, compare sustained complete frame rate. Include burst handling, stalls, first/worst output latency, external bytes/frame, certificate maxima and any fallback deadline.

**Go** only if a genuine exactness consumer and an arithmetic-limited operating region survive, and the full architecture improves on the best exact baseline by a predefined useful margin. **Stop or narrow** if ordinary lanes/unrolling meet the target more cheaply, if memory is the limiting resource, if buffering already enables cheap interleaving, or if bounded-error numerical filtering is acceptable and wins on the application's quality criterion. Meeting 4K60 alone proves a throughput target, not superiority, novelty or a need for exact integer execution.

An entropy-coder probability update is a separate video workload: bitstream compatibility can establish a much stronger exactness reason than blur. It still needs its own causality and bottleneck audit; a probability update accelerator is not automatically a faster arithmetic coder. That alternate direction is outside this spatial review's checked primary literature.

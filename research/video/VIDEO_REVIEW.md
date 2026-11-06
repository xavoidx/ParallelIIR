# Video application review: the three-condition search remains open

6 November 2026. Priority: **small, inexpensive FPGAs**, following the user's clarification. This review adds native-source inspection, spatial/video literature, a system-budget audit and executable arithmetic checks to the earlier financial review.

**We found genuine one-pole integer filters in video-related code, but no application yet demonstrates all three conditions together.** The strongest new exactness lead is VVC/AV1 probability adaptation inside video entropy coding. The cleanest new spatial-filter control is Arm-2D's integer IIR blur. Neither has a measured complete advantage over the best exact alternative. Treating either as an established flagship would repeat the mistake of confusing arithmetic compatibility with application value.

## The decision table

Here, “rate bottleneck” means the **matching recurrence** limits a required service rate, not merely that its application processes many pixels. “Beating” means better complete throughput at matched resources, or fewer resources/a smaller part at the required throughput and latency, with all interfaces and buffering included.

| Candidate | Rate bottleneck | Bit exactness needed/desired | Beats best exact alternative | Decision |
|---|---|---|---|---|
| VLC temporal motion blur | Aggregate video bandwidth is real; each pixel's recurrence advances once/frame | Native rounded integer filter; a historical rounding fix addressed a visible color defect | No; independent pixel lanes avoid the supposed serial bottleneck | Useful exactness example, poor flagship |
| Arm-2D spatial IIR blur | Adjacent horizontal pixels are dependent; no blur-specific UHD60 target miss found | Exact native replacement is a credible compatibility goal, not a demonstrated normative requirement | Unknown; effective state is only 8 bits and native Helium already vectors independent rows/columns | Best new spatial arithmetic/control workload |
| UKUI exponential blur | Matching recurrence; buffered rows/channels provide independence | Native fixed-point compatibility can be desired; no consumer requirement obtained | Unknown | Retain as control, not new success evidence |
| Shotcut exponential blur / FFmpeg Gaussian / OpenCV recursive domain transform | Real recursive image/video processing | Inspected recurrences use floating internal states, despite integer images | Current integer executor does not preserve that native contract | Do not relabel them as matching fixed-point applications |
| VVC probability hypotheses / AV1 adaptive CDFs | Entropy coding has documented rate/dependency pressure; probability-update stage not isolated | Strong: exact entropy-state behavior for a fixed token stream and initialization | Unknown; cheap shift/add, context scheduling, and existing multi-bin coding are strong alternatives | Best new lead for a targeted trace/profile experiment; encoder-side only for the current method |
| Industrial high-rate line-scan imaging | A manufacturer advertises 16,384 pixels × 1 million lines/s | No matching exact one-pole processing stage established | Unknown; line independence and substantial I/O still matter | Demand lead only |

Native formulas, pinned source revisions and reading limits are in [NATIVE_FILTER_SEARCH.md](NATIVE_FILTER_SEARCH.md); entropy formulas and causal restrictions are in [ENTROPY_CODING_CANDIDATE.md](ENTROPY_CODING_CANDIDATE.md). The line-scan source and device/interface evidence are in [SYSTEMS_APPLICATION_GATE.md](SYSTEMS_APPLICATION_GATE.md).

## Why 4K60 alone is insufficient

UHD 3840×2160×60 contains **497.664 million active pixel positions/s**. A common 4400×2250 timing has a **594 MHz** pixel clock, conventionally transported as four pixels/clock at 148.5 MHz or two at 297 MHz. These rates are real; they are not measurements of a recursive filter. [Intel video architecture white paper](https://cdrdv2-public.intel.com/813481/a-framework-for-high-performance-image-and-video-processing-on-fpgas-white-paper.pdf).

For temporal smoothing, there are 8,294,400 independent per-pixel histories, each advancing at 60 Hz. For vertical smoothing, adjacent raster pixels normally update different column states. Both permit ordinary pipelined exact arithmetic. **The horizontal pass is the relevant recurrence challenge:** several adjacent pixels arriving together can require several dependent updates within one clock.

Even that challenge has two strong exact alternatives:

1. **Small exact unrolling:** evaluate two/four original updates, retaining every intermediate rounding. This can lengthen the feedback path but avoids certification, summaries and replay. Its routed timing decides whether it works.
2. **Buffered independent rows:** fill a stripe, process its rows in parallel, and restore raster order. This preserves every scalar operation and needs line buffering rather than necessarily a complete frame.

The system audit derives a conservative four-row schedule at 148.5 MHz: 3,840 compute cycles per row fit inside the 4,400-cycle stripe arrival period. Ping-pong input/output stripes use 16 stored lines, or 120 KiB for one 16-bit component, with roughly 59 µs startup under that schedule. These are **derived scheduling figures, not routed hardware results**. They show why merely forbidding a full-frame buffer does not eliminate row parallelism. More passes, channels and coefficient/state storage must be added separately.

The literature already exploits independent sequences, tile boundaries and memory locality. RecFilter uses floating-point evaluation; that prevents treating it as an integer-exact oracle but does not erase its architectural relevance. [Chaurasia et al., 2015](https://mit-gfx.github.io/recfilter/recfilter.pdf), [Nehab et al., 2011](https://hhoppe.com/recursive.pdf). The detailed [prior-art review](PRIOR_ART_AND_BASELINES.md) also covers FPGA interleaving, finite-word error studies and quantizer-loop precomputation.

## What the small-FPGA preference changes

Use the iCE40UP5K as a stringent budget example, not as a promised raw-UHD60 platform. At an **assumed 50 MHz kernel clock**, UHD60 needs about ten active pixels/clock on average or twelve during 594-Mpixel/s raster bursts. That is substantially more demanding than a two- or four-sample demonstration. The earlier financial prototype's illustrative cycle count does not establish this service rate.

The [system audit's small-FPGA section](SYSTEMS_APPLICATION_GATE.md#7-small-inexpensive-fpga-follow-up-reject-the-up5k-system-sketch-first) separates the device's GPIO timing, global-clock limit, DSP configuration and SPRAM clock. For illustration, carrying one 8-bit component both into and out of the FPGA over ordinary 50-MHz DDR data pins requires at least 40 input plus 40 output pins at the average active rate, before control. The SG48 package has 39 user I/Os. This rejects **that interface sketch**, not every use of the device or every faster I/O arrangement.

Likewise, 128 KiB of SPRAM is not enough evidence that the 120-KiB stripe example works: the latter assumed four row engines at 148.5 MHz, while SPRAM is specified separately at up to 70 MHz and has limited ports. At a lower kernel clock, more independent rows and banks are required. The audit calculates these constraints and distinguishes EBR from SPRAM. [Lattice iCE40 UltraPlus datasheet](https://www.latticesemi.com/api/document/download?id=51968), [SPRAM guide](https://www.latticesemi.com/view_document?document_id=51966).

A more capable low-cost FPGA/interface arrangement may support the raw-video workload, but affordability, timing and total board cost must be checked for a concrete part. Adding an expensive capture bridge or external-memory subsystem solely to make a tiny arithmetic core look cheap would not establish a useful system advantage. A kernel-only replay experiment remains useful for RTL learning, provided it is labeled as such.

The entropy candidate avoids assuming a raw-pixel interface to the accelerator. It still needs a measured token/bin interface budget: compressed bit rate, token rate, context-ID traffic and probability-update rate are different quantities.

## The most useful next direction

**Do not commit to a full video accelerator yet. Run two bounded selection experiments.** Both should reject weak applications early.

**A. Spatial-filter control.** Use the pinned Arm-2D gray8 update at a documented blur degree, with its native initialization, pass order and partial-framebuffer behavior. Establish exact serial and small-unrolled RTL first. Compare a buffered-row schedule if the application's latency allows it. This is a manageable learning workload with real source semantics; calling it a required 4K60 product needs an actual acceptance target.

**B. Encoder probability-state profile.** Instrument a pinned VVC encoder after token decisions are fixed. Capture bin/context order, available-ahead depth, configured shifts, resets/snapshots and stalls. Determine whether a hot context's probability update actually limits an existing multi-bin coder. Its two integer one-pole hypotheses fit the prototype; AV1 additionally needs a variable-rate/offset certificate extension. A decoder is not the initial target, because future symbols are unresolved.

If B shows no probability-stage bottleneck, stop that candidate regardless of how attractive normative exactness sounds. If A is handled more cheaply by unrolling or independent rows, keep it as a correctness benchmark. This is how we continue the three-condition search without converting a promising name into an unsupported success claim.

## High-level RTL roadmap

1. **Freeze one contract and one budget.** Specify the native update, effective state width, coefficient settings, reset/border behavior, input/output format, target device, required sustained/burst rate, and allowed latency/RAM. Identify who benefits from identical results.
2. **Build the best small exact datapath first.** Specialize constant arithmetic. VVC's two branches can share a shift/subtract core with conditional complements; Arm's effective state is just eight bits. Add forwarding and real stalls where contexts or memory require them.
3. **Establish the complete baseline.** Measure serial, 2/4-way exact unrolling, legal independent-state scheduling, memory ports and interfaces. First verify that the budget is possible at all. Increasing sample count per clock is not a win if achieved clock or I/O collapses.
4. **Compare representations in isolation.** Give bitmap and shared-base relative-rank engines the same entry domains. Measure area and feedback timing. Relative ranks share the wide arithmetic too; a naive full-width table is not the only competitor.
5. **Integrate the full proposed method only after a favorable result.** Add independent certificates, exact boundary resolution, replay, reordering, tails and changes of configuration. Charge all buffers and all predictor widths. A supplied-certificate benchmark is not complete performance.
6. **Make the application decision.** Require identical required outputs and a predeclared useful improvement over the strongest exact baseline at equal constraints. For an encoder, check final bytes for fixed tokens; for blur, check full native images and boundaries. Report both the winning region and cases where the simpler design wins.

There is no synthesis/routing toolchain installed in this workspace, and no board/native video trace was measured during this pass. Consequently the third condition remains **unmeasured**, not “probably satisfied.” Literature can identify the experiment and strong competitors; it cannot supply the missing performance result for our architecture.

## Reading order and reproducible evidence

1. [Pinned Arm-2D scalar blur](https://github.com/ARM-software/Arm-2D/blob/26c3b341703a21b241586eec8ddc753931b66e76/Library/Source/__arm_2d_filter_iir_blur.c) together with its [Helium counterpart](https://github.com/ARM-software/Arm-2D/blob/26c3b341703a21b241586eec8ddc753931b66e76/Library/Source/__arm_2d_filter_iir_blur_helium.c): understand the native recurrence and independent-row alternative.
2. [Schwarz et al., VVC quantization and entropy coding, §IV](https://refubium.fu-berlin.de/handle/fub188/33130) and [pinned VVenC probability model](https://github.com/fraunhoferhhi/vvenc/blob/6441f64f9997e9ab8a12d4ac600998a104aa5ddf/source/Lib/CommonLib/Contexts.h): the strongest new exactness-motivated candidate.
3. [Fu et al., 2023 CABAC hardware](https://www.mdpi.com/1424-8220/23/9/4293): context hazards, exact precomputation and complete-coder performance. Its implemented context model is not VVC's two-EWMA model.
4. [Nehab et al., 2011](https://hhoppe.com/recursive.pdf) and [RecFilter, 2015](https://mit-gfx.github.io/recfilter/recfilter.pdf): the scheduling, boundary and memory-locality prior art to beat.
5. [Gu–Parhi nonlinear-feedback disclosure](https://patents.google.com/patent/US20070014345A1/en) and the existing [third-pass verdict](../direction/THIRD_PASS_VERDICT.md): avoid claiming that exact precomputation or ordered-map deletion is itself new.
6. [Device/interface audit](SYSTEMS_APPLICATION_GATE.md): read before selecting the board or quoting a pixels/clock result.

New saved evidence:

| Artifact | What it establishes |
|---|---|
| [Native source audit](NATIVE_FILTER_SEARCH.md) | Arm/VLC matches; float/nonlinear exclusions; source pins and limits |
| [Spatial prior art and baselines](PRIOR_ART_AND_BASELINES.md) | Recursive-image methods, exact competitors and fair comparison conditions |
| [System gate](SYSTEMS_APPLICATION_GATE.md) | Rate arithmetic, exact row-buffer alternative and small-FPGA budget checks |
| [Entropy candidate](ENTROPY_CODING_CANDIDATE.md) | VVC/AV1 reductions, strong exactness motivation and encoder/decoder restrictions |
| [Native checks](native_arithmetic_checks.py) / [results](native_arithmetic_results.json) | 16,711,680 Arm and 8,323,072 VLC expression/range comparisons |
| [Entropy checks](entropy_arithmetic_checks.py) / [results](entropy_arithmetic_results.json) | Exhaustive primitive reductions and synthetic exact-map/certificate/replay checks |
| [Independent entropy audit](ENTROPY_INDEPENDENT_AUDIT.md), [checks](entropy_independent_checks.py) / [results](entropy_independent_results.json) | All 13 configured VVC rate pairs, map-derived replay entries, pre-update combined indices, and the conditional-complement exact baseline |

These are source and arithmetic results, not evidence that we have met the full application gate. No original RTL/simulation implementation was changed. The research recommendation remains conditional on a complete measured advantage.

# Video system/application gate: 4K60 is real bandwidth, not yet a scalar-recurrence win

6 November 2026. Independent system audit for the exact positive scalar integer recurrence discussed in [APPLICATIONS.md](../APPLICATIONS.md) and [THIRD_PASS_VERDICT.md](../direction/THIRD_PASS_VERDICT.md). This note contains literature evidence and derived schedules; no video filter, RTL, camera or board was benchmarked.

**Verdict:** 4K60 provides a credible reason to investigate multi-sample hardware, but the reviewed evidence does not establish all three requested gates together: a matching scalar dependency that misses the rate, a real requirement or value for preserving its integer outputs, and a complete implementation beating the strongest exact alternatives. A horizontal, low-latency streaming filter is the most credible conditional target. Temporal denoising, background averaging, display temporal smoothing and vertical filtering are weak single-chain targets because adjacent raster pixels generally update different states.

## 1. What the interface evidence actually establishes

Intel's architecture white paper explicitly places 4K60 at four pixels per clock at 148.5 MHz, two at 297 MHz, or one at 594 MHz; it describes the traditional multi-pixel architecture and newer devices' ability to approach the higher clock. This is evidence for an interface-rate problem and common engineering response, not measured timing for the proposed recurrence. [Intel, *A Framework for High-Performance Image and Video Processing on FPGAs*, p. 2](https://cdrdv2-public.intel.com/813481/a-framework-for-high-performance-image-and-video-processing-on-fpgas-white-paper.pdf).

AMD's Video Processing Subsystem supports one, two, four or eight pixels per clock and 8–16 bits per component; its RGB packing explicitly contains multiple separate pixels and color components. These buses do not turn RGB into one scalar feedback chain. [AMD PG231, AXI4-Stream Video](https://docs.amd.com/r/en-US/pg231-v-proc-ss/AXI4-Stream-Video).

AMD's tested 2160p60 timing is 3840×2160 active within 4400×2250 total. Derived rates are therefore:

| Quantity | Calculation | Result |
|---|---|---:|
| Active pixels/frame | 3840×2160 | 8,294,400 |
| Active average pixel rate | 3840×2160×60 | 497.664 Mpixel/s |
| Timed full-raster pixel rate | 4400×2250×60 | 594 Mpixel/s |
| Total line period | 4400/594 MHz | 7.407407 µs |
| Active line duration | 3840/594 MHz | 6.464646 µs |
| Frame period | 1/60 | 16.666667 ms |

This timing is a particular supported mode, not a claim that every 4K60 transport has identical blanking. [AMD PG236, tested RGB/YUV444 resolutions](https://docs.amd.com/r/en-US/pg236-v-hdmi-rx-ss/Tested-Video-Resolutions-for-RGB-4-4-4-and-YCbCr-4-4-4?contentId=LibLjrKnNO8awPeqhI8Bhw).

An active-only buffered job can spread work into blanking; an unbuffered live timed interface must handle its bursts. Altera documents that most HDMI, SDI and DisplayPort connectivity IP cannot accept backpressure because this breaks video timing. A rare overflow/fallback cannot simply stall the source indefinitely. [Altera Streaming Video Protocol, optional backpressure](https://docs.altera.com/r/docs/683397/current/altera-streaming-video-protocol-specification/optional-backpressure).

## 2. Dependency audit by application

| Candidate | True serial direction | Consequence for this proposal |
|---|---|---|
| Temporal exponential background/denoise | Same pixel across frames | At 60 fps, each pixel state updates at 60 Hz. The raster's nearly 500 million updates/s are millions of independent chains. Bank state memory and pipeline ordinary arithmetic first. |
| Temporal local dimming | Same zone across frames | Per-zone frame updates, with far fewer states than pixels; the image statistics frontend may be fast, but that does not make the smoothing recurrence fast. |
| Vertical causal one-pole | Same column down successive rows | 3840 columns offer independent state; one state is revisited about every 7.407 µs during active rows in this mode. Four adjacent pixels can usually use four independent column states. |
| Horizontal causal one-pole | Adjacent pixels within a row | Four adjacent pixels on a 4-PPC bus can belong to the same dependency chain. Exact unrolling or block methods may be useful, conditional on timing and buffering constraints. |
| Forward/backward separable blur | Rows/columns in each pass, with direction changes | Native passes and intermediate images matter. Required reverse passes already impose buffering; exploit independent rows and channels before claiming a serial bottleneck. |
| Global exposure/AWB/control smoothing | Successive frames or statistics reports | Output depends on scene/sensor feedback; future inputs may be unavailable. High pixel ingest rate is not the control-state update rate. |

OpenCV's `accumulateWeighted` directly documents independent per-channel, per-pixel running-average updates and a 32- or 64-bit floating accumulator. It establishes the temporal structure, but **does not supply native integer floor/clip semantics** for this project. A fixed-point port can be a valid new implementation if independently justified; it cannot be described as bit-exact acceleration of that floating-point API. [OpenCV 4.13 motion analysis reference](https://docs.opencv.org/4.13.0/d7/df3/group__imgproc__motion.html).

FFmpeg's `hqdn3d` is a useful counterexample to equating every recursive video denoiser with this contract. Its stored frame history is 16-bit, but `lowpass` computes a difference-indexed correction table, `cur + coef[d]`; the table uses a nonlinear similarity law. The spatial path also mixes row and frame history. It is not an audited constant-coefficient affine one-pole. Its temporal-only branch demonstrates independent pixel histories, not one high-rate time sequence. [FFmpeg upstream `vf_hqdn3d.c`](https://github.com/FFmpeg/FFmpeg/blob/master/libavfilter/vf_hqdn3d.c).

Real ISP interfaces do expose integer IIR controls: Intel IPU3's Linux UAPI documents a previous-row IIR weight and horizontal FIR taps in its chroma-noise-reduction configuration. The header does not disclose the entire filter equation, internal rounding, adaptive coefficient selection or a horizontal one-state timing bottleneck. Its documented previous-row direction actually favors column interleaving. Do not infer this project's exact state machine from a register width. [Linux upstream IPU3 UAPI, frozen revision](https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux.git/%2B/9b9eaee9828fe98b030cf43ac50065a54a2f5d52/drivers/staging/media/ipu3/include/uapi/intel-ipu3.h).

LG's local-dimming disclosure explicitly applies temporal IIR or FIR filtering to block dimming values over frame periods to suppress flicker. It neither fixes an integer one-pole realization nor establishes pixel-rate feedback. It supports a real smoothing use, with the wrong time axis for the headline rate. [LG inventor-authored disclosure, US20120133685A1, temporal filter 16](https://patents.google.com/patent/US20120133685A1/en).

## 3. Memory and exact row-parallelism are serious competitors

The following are derived payload estimates, excluding alignment, ECC, refresh, arbitration, metadata and other video stages. For an uncompressed 3840×2160 frame:

| Storage representation | One frame | One read + one write per frame at 60 fps |
|---|---:|---:|
| One 16-bit component/state | 16.5888 MB | 1.990656 GB/s |
| RGB, packed 8-bit components | 24.8832 MB | 2.985984 GB/s |
| Three 16-bit component states | 49.7664 MB | 5.971968 GB/s |
| RGB, three float32 accumulator states | 99.5328 MB | 11.943936 GB/s |

A temporal implementation must retain the appropriate previous state for every pixel; even a perfect recurrence accelerator does not eliminate that state traffic. Current-frame reads, output writes and capture/display transfers can be additional traffic. Conversely, a stored previous frame does not force an extra complete frame of algorithmic delay: causal updates can stream as the current frame arrives. Delaying every update to accumulate temporal blocks would add many frame periods and is generally a poor fit for live denoising.

For a horizontal filter with independent row resets, **no full-frame buffer is needed to exploit row parallelism**. Consider this deliberately simple exact stripe schedule at 4 PPC/148.5 MHz:

1. Gather four successive rows into one input stripe while the preceding stripe is processed.
2. Four ordinary serial row engines each execute one state update/clock, preserving every native rounding. Each consumes 3840 clocks = 25.858586 µs. A stripe arrives every four line periods = 29.629630 µs; the compute stage fits with 560 clocks of slack.
3. Store the four completed rows in an output stripe and emit them in raster order, four pixels/clock with native line timing.
4. Ping-pong each input and output stripe. A conservative payload budget is sixteen lines total: 61,440 pixels, or 120 KiB at 16 bits/pixel and 180 KiB at RGB24. This assumes three arithmetic lanes per RGB pixel, as required by any component-wise RGB design.

With fixed stripe slots, capture stripe k, compute it in the next slot, and emit it in the following slot: roughly 59.26 µs first-pixel delay plus arithmetic/control margin. The stripe pipeline sustains the stream without an off-chip frame store. It requires banking/ports that actually support four input/output pixels per clock; this is an unimplemented feasible-work schedule, not a routed area/timing result. End-of-frame partial stripes, resets and coefficients need explicit handling. For 2160 rows, four-row stripes divide the active height exactly.

This construction applies only when horizontal rows are independent and compute can use buffered samples. A stage whose first-row entry depends on the preceding row's filtered exit is different; establish that this cross-row dependence is native and meaningful rather than an artifact introduced to manufacture one chain. If rows are already in memory, independent row scheduling is easier still. A vertical or nonlinear coupled stage must be scheduled separately.

Consequently, a convincing low-buffer accelerator claim needs a measured constraint substantially tighter than “no framebuffer”: for example an allowed additional delay below one line, insufficient line RAM for stripe buffers, or a genuine continuous chain whose state crosses line boundaries. At short latency, compare direct two/four-update combinational unrolling, coefficient-specialized shift/add implementations and rounding-aware exact look-ahead. Retaining each truncation is necessary; replacing nested floors by an unrounded linear look-ahead is not automatically exact.

## 4. Bit-exactness: normative, contractual, or a numerical choice

H.264 decoder conformance requires the specified reconstructed sample values to match the reference process. That genuine standard requirement cannot be borrowed for arbitrary denoising or blur around the codec. H.264.1 explicitly observes that the display process lies outside H.264's normative scope and can change values or timing while the decoder remains conformant. This spatial-filter review did not establish a matching pixel-domain exponential smoother inside a normative reconstruction loop. [ITU-T H.264 (08/2024), clause C.4](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-H.264-202408-I%21%21PDF-E&lang=e&type=items); [ITU-T H.264.1 (10/2014), clause 6.5.6](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-H.264.1-201410-S%21%21PDF-E&lang=e&type=items). The separate [entropy review](ENTROPY_CODING_CANDIDATE.md) does identify matching probability-state updates with a strong bitstream-compatibility motivation; those are a different application and have a decoder causality obstacle.

Desired exactness can still have system value: an FPGA replacement for an installed software filter, matching an existing ISP's golden traces, fixed-point hardware/software co-simulation, deterministic regression, reproducible offline mastering or preserving a downstream vision decision. These are **candidate acceptance contracts**, not demonstrated customer requirements in this audit. Obtain the named consumer, revision, numerical format and consequence of a mismatch. FFmpeg documents reproducibility/regression as a purpose of its muxer bitexact option, but that option does not prove that a particular recursive filter requires bit identity. [FFmpeg format flags](https://www.ffmpeg.org/ffmpeg-formats.html).

For a newly chosen fixed-point filter, first justify image quality, temporal/spatial response and state precision against a stated reference. Then exact execution of that chosen machine is a legitimate technical objective. An approximate IIR or FIR with indistinguishable accepted outputs remains a system competitor if bit-exact compatibility is merely desirable. Report both results without claiming a normative need.

## 5. More demanding leads, still conditional

Very wide line-scan cameras provide stronger rate evidence than an invented giant display. Teledyne DALSA lists a 16,384-pixel Linea HS2 model at 1,000 kHz line rate: 16.384 Gpixel/s by multiplication. That is a real acquisition specification, not evidence that the camera contains or needs an exact one-pole spatial smoother. It also supplies one million independent lines/second, so multiple line engines and buffering remain powerful. A near-sensor filter with a documented sub-line latency budget, limited on-chip RAM and mandatory compatibility would be worth an application interview. [Teledyne DALSA Linea HS2 manufacturer specification](https://www.teledynedalsa.com/en/products/imaging/cameras/linea-HS2/).

Other useful searches are a genuine scan-order scalar state that intentionally persists across lines; prerecorded scanwise correction inputs with a documented fixed-point output contract; or hardware/software interchange where preserving every stored high-precision state matters. None was verified here. A scene-adaptive coefficient selected from unresolved state, feedback-dependent acquisition, or a multipole recursive Gaussian cannot inherit the current fixed positive scalar proof without additional work.

## 6. Decisive experiment and stop rule

**First obtain one actual horizontal streaming stage specification.** Freeze native source/RTL or explicitly justify a new integer filter: equation, coefficient, denominator, state width, sample width, every rounding/saturation, row initialization, direction, component ordering, output precision, dynamic changes and reset behavior. Record device, clock/PPC, actual video format, permitted startup/steady latency, line-memory budget and the reason exactness matters. A named rate alone is insufficient.

Then run one end-to-end comparison at the required timing:

- Ordinary serial/component-parallel design; exact 2- and 4-sample unrolling; any valid coefficient-specialized or rounding-aware look-ahead; stripe/row-parallel engines; the shared-base relative-rank representation from the third-pass verdict; and the proposed compact-map representation with its complete certificate, resolution, replay, buffering and fallback.
- Include line gather/reorder memory and ports on both sides, input acceptance during active bursts, every output, initial-state/reset correctness and maximum latency. Evaluate routed clock, DSP/LUT/register/RAM use and sustained worst-case frame service, not isolated map operations or average favorable blocks.
- Compare every state/output with a pinned scalar oracle over video stimuli and adversarial extremes. Prove or exhaustively check short blocks across all legal entry states. If narrower output pixels hide state differences, retain state equivalence when it is part of the compatibility contract.
- If exactness is a chosen property, compare the best accepted approximate filter at the same image-quality criterion. Do not change native coefficients solely to make certificates small. If native slow contraction creates large maps, report that failure.

**Pass only if** the full design meets a real rate/latency/resource target missed by the strongest valid exact baseline, or improves measured resource cost at that target enough to justify its complexity, and the exact numerical contract has an identified use. If ordinary unrolling or modest stripe buffering wins, retain the work as an exact arithmetic comparison and reject 4K60 as the flagship system claim.

## 7. Small inexpensive FPGA follow-up: reject the UP5K system sketch first

User clarification: prioritize small inexpensive FPGAs. The 148.5-MHz stripe schedule above is a system counter-baseline, **not a claim that it fits or closes timing on UP5K**. A small kernel's faster arithmetic is useful only after a credible input/output and memory architecture exists.

Primary UP5K specifications relevant to this distinction:

| Item | Manufacturer specification |
|---|---|
| SG48 GPIO | 39 total general-purpose I/Os; board availability can be smaller |
| EBR | 120 Kbit = thirty 4-Kbit blocks; up to 16-bit data ports, separate read/write ports |
| SPRAM | Four 16K×16 single-port blocks = 128 KiB |
| SPRAM timing | 70 MHz `fMAXSRAM` specification |
| DSP timing | 50 MHz for signed 8×8/16×16 multiplication **bypassing** pipeline registers |
| Global clock network | 185 MHz maximum under stated commercial conditions |
| Ordinary LVCMOS33/25 buffers | 250 MHz maximum buffer speed, explicitly measured with a toggling pattern |
| Registered I/O with PLL | Clock-to-output 2.4 ns; input setup 7.3 ns, hold −1.1 ns |

These are different limits. The buffer toggling figure is not an arbitrary-data DDR lane guarantee; the global-clock ceiling is not achieved kernel frequency. The reviewed datasheet does not supply a universal certified GPIO-DDR payload rate. Select the actual PIO mode, voltage, load, PLL phase and board clock, then close both-edge input/output timing with external delays. [Lattice UP datasheet 2.4, §§3.1.5–6, 4.19–25, 5.2](https://www.latticesemi.com/api/document/download?id=51968). The manufacturer's device table separately confirms the UP5K resource inventory. [Lattice UltraPlus device selection](https://www.latticesemi.com/Products/FPGAandCPLD/iCE40UltraPlus?ActiveTab=Data+Sheet).

Raw payload arithmetic, before sync/protocol overhead:

| Samples carried | One direction, active average | One direction, timed active burst | Input + output, active average |
|---|---:|---:|---:|
| One 8-bit component | 3.981312 Gbit/s | 4.752 Gbit/s | 7.962624 Gbit/s |
| One 16-bit component | 7.962624 Gbit/s | 9.504 Gbit/s | 15.925248 Gbit/s |
| RGB24 | 11.943936 Gbit/s | 14.256 Gbit/s | 23.887872 Gbit/s |

For a conditional ordinary-DDR link at 50 MHz, each data pin carries at most two bits/clock = 100 Mbit/s **if timing closes**. Even one 8-bit component then needs 40 input and 40 output data pins on average; instantaneous bursts need 48 each without absorbing buffers. At 70 MHz DDR the average minimum is 29 pins in each direction. Both exceed the entire SG48 inventory before clocks/control. Thus a same-50/70-MHz ordinary-GPIO raw-video input/output proposal already fails, independently of the recurrence. A separate faster PHY domain changes this calculation and must be demonstrated. Even granting an ideal 185-MHz both-edge PIO domain and all 39 pins for data gives only 14.43 Gbit/s combined: insufficient for RGB24 input plus output, while not excluding every monochrome configuration. These are bounds on the stated interface architecture, not a proof that every possible UP5K video role is impossible.

The internal kernel also needs substantial width at modest clocks. At 50 MHz, the active average is 9.95328 pixels/clock, requiring at least ten; direct burst service requires twelve because 594/50=11.88. At 70 MHz these lower bounds become eight and nine. Components add parallel arithmetic lanes; treating RGB as one chain does not reduce payload. Absorbing blanking can relax burst service only with a proven buffer and sustained schedule.

The prior 120-KiB stripe payload nearly fills 128-KiB SPRAM and is already based on four 148.5-MHz row engines. At 50 MHz the same conservative twelve-row-engine version uses 48 buffered lines: 360 KiB for 16-bit samples, or 540 KiB RGB24. Twelve engines are a convenient burst-matching example, not a proven minimum; an eleven-engine line-slot schedule can use horizontal blanking because 3840/50 MHz = 76.8 µs is below eleven line periods = 81.4815 µs. It still requires 330 KiB with the same conservative buffering. A tighter streaming schedule may reduce storage but must be constructed and checked.

Capacity alone is insufficient even for the original stripe. At a 70-MHz SPRAM clock, the four ports together provide at most 4×16×70 MHz = 4.48 Gbit/s of aggregate read-or-write word traffic under an optimistic full-utilization schedule. Storing and later reading each 16-bit incoming pixel already requires 15.925248 Gbit/s active-average traffic, before a separate output stripe. The original all-SPRAM store/process/reorder arrangement therefore fails bandwidth as well as its 148.5-MHz assumption. EBR ports can supply more parallel traffic, but thirty blocks total only 15 KiB; adding that capacity to SPRAM does not create a single large multiported memory. Register/LUT buffers, packing, bank assignment, phased accesses and external memory must be charged explicitly. No complete replacement schedule was built here.

Broader small-device families deserve a separate budget rather than an UP5K extrapolation. Lattice lists ECP5 options from 12K LUTs with 576 Kbit EBR to 84K LUTs with 3744 Kbit EBR, and 28–156 18×18 multipliers. [Lattice ECP5 device table](https://www.latticesemi.com/Products/FPGAandCPLD/ECP5?ActiveTab=Data+Sheet). CrossLink-NX documents up to two four-lane hardened D-PHY interfaces, 2.5 Gbit/s per lane, plus 1066-Mbit/s ×16 memory support. These provide credible video-interface options, not a filter-throughput result; two PHYs used for receive/transmit do not pool their full nominal rate into each direction, and protocol overhead still matters. [Lattice CrossLink-NX datasheet 2.4, features](https://www.latticesemi.com/-/media/LatticeSemi/Documents/DataSheets/CrossLink/FPGA-DS-02049-2-4-CrossLink-NX-Family.ashx?document_id=52780). No price, cheapest part or complete board cost was verified, so neither family is declared affordable for the user's budget.

**Small-FPGA rejection gate:** before any 4K60 accelerator commitment, require a named board/package, input/output format and proven pin/PHY service; a clocked memory-bank schedule including capture/replay/reorder; and routed kernel timing at the required PPC. Reject any proposed configuration failing one of these bounds. Smaller resolutions, a buffered internal kernel fed by another device, selected components/features, or a broader FPGA remain possible experiments, but are different system claims.

## Evidence depth and limits

Sources accessed 6 November 2026. Intel's nine-page PDF was opened; the PPC/rate discussion on page 2 was read. AMD interface and timing pages, Altera backpressure text, OpenCV function documentation, FFmpeg relevant source sections and LG temporal-filter paragraphs were inspected. IPU3 and ITU conformance evidence was obtained from primary-source indexed excerpts; full hardware arithmetic and complete standards were not audited. The small-device follow-up opened the UP5K 2.4 PDF and inspected the cited timing/architecture text, manufacturer device tables, and indexed CrossLink-NX 2.4 features; no board PHY or DDR interface was validated. Some older Intel URLs redirected to unavailable pages; the accessible Intel PDF and current Altera page replace them. FFmpeg master and other mutable documentation must be pinned before implementation. No source in this note establishes a native complete integer horizontal one-pole together with a measured 4K60 failure. The derived memory/rate/schedule calculations establish counter-baselines and obligations, not a measured win or an impossibility theorem.

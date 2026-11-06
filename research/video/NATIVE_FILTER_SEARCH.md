# Native video and spatial-filter search

6 November 2026. This is a source audit, not a throughput experiment. The question is whether a **native** fixed-point one-pole stage simultaneously has a real rate/dependency bottleneck, useful exact compatibility, and an advantage for ParallelIIR over the strongest exact alternatives.

**Result: no reviewed video candidate establishes all three.** A new, clean native spatial match is Arm-2D's integer IIR blur. A particularly instructive native temporal match is VLC's motion blur: its rounding was changed to fix a visible color defect. Neither establishes the missing single-stream performance result. Shotcut's actual exponential video blur is floating point; substituting UKUI's integer arithmetic would change the implementation being accelerated.

## Strongest new spatial arithmetic match: Arm-2D

Read the [scalar implementation](https://github.com/ARM-software/Arm-2D/blob/26c3b341703a21b241586eec8ddc753931b66e76/Library/Source/__arm_2d_filter_iir_blur.c), [Helium implementation](https://github.com/ARM-software/Arm-2D/blob/26c3b341703a21b241586eec8ddc753931b66e76/Library/Source/__arm_2d_filter_iir_blur_helium.c), and [API/header](https://github.com/ARM-software/Arm-2D/blob/26c3b341703a21b241586eec8ddc753931b66e76/Library/Include/__arm_2d_filter_iir_blur.h). All three were fetched at the same commit; their blobs equal the default-branch files read during this audit.

The gray8 implementation uses a `uint16_t` accumulator, byte pixels, `hwRatio=256-chBlurDegree`, and this inner update:

```c
tAcc.hwC += ((*pchChannel) - tAcc.hwC) * hwRatio >> 8;
```

It writes the accumulator back to the byte image after every update. The header identifies degree 128–239 as the blur range and 0–127 as generic antialiasing. Zero bypasses processing in the software wrapper. Forward horizontal/vertical paths exist separately; optional reverse paths and partial-framebuffer state are additional native behavior that an implementation must preserve. The region and framebuffer configuration are part of the workload, not free scheduling choices.

Independent arithmetic reduction, for the Cortex targets' 32-bit `int` promotions and arithmetic signed shift, is

`s' = floor((d*s + (256-d)*x)/256)`, with `D=256`, `A=d`, `rho=0`, `H=255`.

For `1<=d<=255` this matches the current positive-contraction contract. Starting from the first pixel, state stays in `[0,255]`; storage is 16 bits but effective state precision is eight bits. The signed multiplication is bounded in magnitude by 65,025, safely within a 32-bit intermediate. A Python exhaustive expression check covered **16,711,680** `(d,s,x)` combinations, confirming the reduction and invariant for every legal byte state/input and nonzero byte degree. This checks integer-expression semantics; it is not compiled-source or SIMD equivalence validation.

The ideal certificate scale is `R=floor(255/(256-d))`. Examples are:

| Native degree d | Pole | R |
|---:|---:|---:|
| 128 | 1/2 | 1 |
| 224 | 7/8 | 7 |
| 239 | 239/256 | 15 |
| 255 | 255/256 | 255 |

The last degree is accepted by the byte-valued implementation but outside the header's documented blur range. These are the exact-predictor bounds, **not** implemented finite-precision predictor capacities or observed production settings. At d=239 a small mask is mathematically plausible; the equally small base datapath makes direct exact arithmetic unusually inexpensive too.

### Its existing baseline is already substantial

The Helium gray8 code processes **eight independent rows** together for a horizontal pass, gathering/scattering at row-stride offsets. It processes eight independent columns together for a vertical pass, using contiguous loads/stores within each row. Each lane retains its own serial accumulator and uses signed doubling multiply-high for the Q8 update. The code preserves partial-framebuffer boundary accumulators and includes tail handling. Thus this is actual native recurrence-preserving SIMD across independent scanlines, not a hypothetical escape hatch.

Arm-2D describes its application context as embedded display processing and [its generic benchmark](https://github.com/ARM-software/Arm-2D/blob/main/README.md#3-examples-benchmark-and-templates) uses 320×240 RGB565 with a 30-fps frequency metric. **That generic benchmark does not benchmark IIR blur.** No blur-specific frame-rate miss, critical feedback timing result, deployed 4K60 configuration, or maximum tolerated delay was found. Existing [release notes](https://github.com/ARM-software/Arm-2D/releases/tag/v1.2.2) specifically report improved Helium support for IIR blur, establishing optimization effort without establishing an unmet target.

Bit equality to the selected C implementation is a sensible drop-in-accelerator goal: it avoids unexpected image differences and makes backend verification clear. The inspected material does not make exact equality a normative standard, promise cross-backend equality, or establish that a perceptually equivalent blur is unacceptable. The README's API backward-compatibility statement should not be inflated into a bit-exact-output guarantee.

**Verdict:** good native scalar/spatial correctness workload, stronger source qualification than a newly invented integer video filter. It is not yet an application win. Its effective eight-bit state, existing eight-row/column SIMD, and ordinary exact unrolling are serious competitors.

## Strongest temporal exactness lesson: VLC motion blur

[Pinned native source](https://github.com/videolan/vlc/blob/6bfcad4267f57f1e487503f4da16b033be01e3ca/modules/video_filter/motionblur.c) stores the previous filtered picture, initializes it from the first input picture, and updates each visible byte using old-factor `f` in 1–127 (default 80), new-factor `128-f`, and rounding constant 64. The factor is sampled once per picture. After filtering, the complete result becomes the next stored picture. This is byte arithmetic even when a format has wider logical samples; select an actual 8-bit format for a pixel-meaningful experiment.

Independent reduction is

`s'[p] = floor((f*s[p] + (128-f)*x[p] + 64)/128)`.

This is exactly `D=128`, `A=f`, `rho=64`, `H=255`; all 8,323,072 legal `(f,s,x)` combinations passed exhaustive native-expression/affine-reduction equality and model range checks. Initialization with the current first frame makes that frame unchanged. Configuration changes between frames require the variable-coefficient extension or independently configured runs; do not silently apply constant-coefficient capacity proofs across changes.

The [rounding-fix commit](https://github.com/videolan/vlc/commit/6bfcad4267f57f1e487503f4da16b033be01e3ca) explains that adding 64 prevents greenish saturation at high values. This is unusually concrete evidence that native quantization affects an application. It motivates preserving the **chosen current implementation**, not claiming a standards-mandated bitstream contract. The previous implementation is a different integer machine.

Fatal bottleneck issue: `p` indexes millions of independent pixel-byte streams. A particular pixel's next state is needed one frame later, about 16.67 ms at 60 fps. Consecutive pixels in the raster loop do not feed each other. SIMD or parallel multiply/add/shift units can process them directly while keeping every native rounding. Temporal block summarization instead needs multiple future frames and replay/storage; it does not cure a 497.7-MHz scalar feedback loop, because that loop does not exist here. A memory/whole-frame bottleneck is possible but unmeasured and cannot be relabeled as a single-recurrence bottleneck.

## Video filters whose names conceal incompatible arithmetic

| Actual implementation inspected | Source-level finding | Consequence |
|---|---|---|
| Shotcut Blur: Exponential → frei0r IIRblur type 0 | Shotcut metadata selects `frei0r.IIRblur`; UI sets type 0. Frei0r uses `float_rgba`, a floating one-tap four-direction filter, floating boundary compensation and final byte conversion. | Native one-pole video workload, **not** native fixed-point floor arithmetic. Integer replacement needs a new numerical-fidelity study. |
| FFmpeg gblur | `float` image buffer, floating pole/scale/boundary parameters; integer images are converted into this buffer and rounded back afterward. | Byte/10-bit input does not make recursive state integer. |
| FFmpeg hqdn3d | `lowpass(prev,cur)` indexes a nonlinear coefficient table using shifted `prev-cur`; the table uses a similarity power law. | State-dependent nonlinear map, not one fixed affine floor update; spatial dependency alone does not rescue compatibility. |
| Qt expblur | Stored-state feedback quantizes before multiplying, unlike UKUI. | Already excluded in APPLICATIONS.md: its stored-state map can decrease at an adjacent-state boundary. |
| SSIMULACRA2 in VMAFx | Developer ADR reports IIR dominating CPU cost and exactness work, but the blur is floating **three-pole** recursive Gaussian. | A valuable real-performance/precision precedent, outside the scalar positive-floor contract. |

Primary links for that table: [Shotcut metadata](https://github.com/mltframework/shotcut/blob/master/src/qml/filters/blur_exponential/meta.qml), [Shotcut type selection](https://github.com/mltframework/shotcut/blob/master/src/qml/filters/blur_exponential/ui.qml), [Frei0r wrapper](https://github.com/dyne/frei0r/blob/master/src/filter/blur/IIRblur.c), [Frei0r engine](https://github.com/dyne/frei0r/blob/0954fc5b066a5a87020ccaa4657fb1caa7e94884/src/filter/blur/fibe.h), [FFmpeg gblur](https://github.com/FFmpeg/FFmpeg/blob/master/libavfilter/vf_gblur.c), [FFmpeg hqdn3d](https://github.com/FFmpeg/FFmpeg/blob/master/libavfilter/vf_hqdn3d.c), [Qt code](https://codebrowser.dev/qt6/qtbase/src/gui/painting/qimageeffects.cpp.html), [VMAFx ADR-0201](https://github.com/VMAFx/vmafx/blob/master/docs/adr/0201-ssimulacra2-vulkan-kernel.md).

Frei0r's engine already unrolls processing across two rows to break dependency chains and arranges loops for cache locality. [Shotcut's own release note](https://www.shotcut.org/blog/new-release-191020/) reports improved blur performance with parallel processing. Those facts reinforce the need to compare against the actual application backend, even if a fixed-point port were justified.

## What a defensible 4K60 experiment must establish

The following rates are derived workload arithmetic, **not measured requirements of the above stages**: 3840×2160×60 = 497,664,000 active pixel positions/s. A two-direction per-channel spatial filter requires about 995 million state updates/s, and four directions about 1.99 billion; RGB multiplies update count by three. Blanking, conversion, boundaries and memory traffic add work. These counts do not imply the same rate on a single dependent state. Horizontal row streams reset; vertical states are spread over columns; color channels add independence.

For an incoming raster with several adjacent pixels/cycle, the horizontal pass can expose an actual within-cycle recurrence. Then compare a small exact unroll retaining every rounding, row interleaving with its required line buffers/reordering, and block methods at the **same latency and memory-port budget**. Row interleaving may need more initial lines than a short within-row block, so it must be charged, not assumed free. Conversely, a buffered full-frame application cannot claim a narrow latency exception to exclude available scanline parallelism.

The minimum fair comparison set is:

1. The selected native serial kernel and its existing SIMD backend, with independent rows/columns/channels/frames used wherever legal.
2. Exact small unrolling, preserving intermediate shifts and native initialization, at its achieved clock and full-frame memory schedule.
3. Shared-base relative-rank tables on the **same certified domains**, with one full-width base/remainder update and small parallel comparisons/decrements. Comparing only against repeated full-width candidate trajectories overstates the bitmap advantage.
4. Bitmap/threshold maps, including finite certificate generation, all wide arithmetic, map queries, replay, input/output traffic, carry between groups, tails, parameter changes and exact fallback.

Measure complete sustained frame rate and end-to-end delay at equal resources, not constructor-only cycle counts. Validate every native state/byte, including boundaries and framebuffer tiles. No candidate in this audit supplies these measurements. For Arm-2D, its eight-bit state makes general full-state methods less extravagant than in the 17/32-bit financial examples; this strengthens rather than weakens the exact baseline obligation.

## Evidence and reproducibility limits

The persisted [native_arithmetic_checks.py](native_arithmetic_checks.py) separately implements literal native expressions and affine reductions, enumerates all cases above, and writes [native_arithmetic_results.json](native_arithmetic_results.json). Run `python3 research/video/native_arithmetic_checks.py` from the repository root. The persisted script was executed successfully, including the additional explicit VLC affine-equality check; results record its SHA-256 and exact coverage counts. Failures use explicit exceptions and do not depend on Python assertions. This is deterministic arithmetic validation, with no timing or benchmark claim. The eight-bit effective Arm state also means cheap FPGA direct arithmetic and small-state exact alternatives deserve especially strong attention.

The native source bodies above were read through the GitHub connector; direct raw-web fetches and shell DNS failed. The current Arm-2D files were checked again at the common commit given above. Scalar blob: `a771c931427c41b55ae7235eed2e02c6eb3c6921`; Helium blob: `0c27789e350b835dddaf31cfaf747c14697c7156`; header blob: `10e916b6192e03f75e7f544f1f704b6f2ec22e7d`. VLC's pinned source blob is `4e2d95def93f10bb01505e6ce533f70d60de5e24`. Other mutable default-branch sources must be pinned as a unified build before benchmarking.

No native clips, source builds, CPU benchmarks, RTL, synthesis, routed timing or energy measurements were produced. The exhaustive checks are expression/range checks only. Search included native FFmpeg, Shotcut/Frei0r, VLC, Arm-2D and targeted ISP/FPGA/4K recursive-filter queries. Search incompleteness is not proof that no suitable video stage exists. The next useful commitment is a measured owner-supplied spatial-filter target and exact-backend acceptance criterion; another generic statement that video has many pixels would not close the application gap.

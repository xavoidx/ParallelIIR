# Application audit: exact buffered scalar recurrence

Evidence reviewed 2026-11-04. Scope: one scalar integer state, `s' = clip(floor((A*s+C)/D))`, `0 <= A < D`, overflow-free intermediates, known block inputs, every serial output preserved. Read `SPEC.md` and both supplied October decision/appendix texts. This is an application audit, not a proof that acceleration is useful.

**Finding: no reviewed application establishes all four requirements simultaneously: native matching integer semantics, acceptable buffering, a demonstrated single-stream bottleneck, and a requirement unmet by simpler exact hardware.** AMR-WB de-emphasis provides the strongest exactness motivation, UKUI exponential blur provides a concrete source-level recurrence, and SiPM waveform synthesis provides a physical fast-stream lead. They serve different experimental purposes; none yet passes the complete application gate.

## Ranked leads and exclusions

| Priority | Native application | What is established | What prevents a success claim |
|---|---|---|---|
| 1 for exactness benchmark | AMR-WB encoder Deemph2 | Bit-exact standard, source-level arithmetic reduction, native buffered call and test vectors | Inspected revisions must be unified; low single-stream rate and independent calls; no system speedup established |
| 2 for arithmetic validation | UKUI desktop background exponential blur | Buffered image; actual scalar fixed-point update and formats available | Rows, columns, channels offer independent work; no measured one-row bottleneck, hard pixel rate, or required exact compatibility |
| 1 for application interview | SiPM detector waveform emulator | Scalar positive poles, physical fast stream, explicit feedback timing failure, event FIFO | Internal rounding/state width absent; existing look-ahead already meets throughput; buffering budget absent |
| 3 | Buffered replay of a native fixed-point one-pole stage | Future inputs available by construction | Must identify an existing stage and reason to preserve its old integer outputs; “offline” alone supplies neither |
| 4 | USRP automatic DC correction | Native first-order correction and tiny adaptation parameter | Source semantics unresolved; slow contraction; current FPGA already implements it |
| Exclude as flagship now | Detector baseline/pole-zero processing | Real fixed-point FPGA systems exist | Gating, integrators, multiple state variables, and insufficient rounding details; no scalar matching bottleneck verified |
| Exclude as native evidence | Financial EWMA | Positive scalar mathematical recurrence | Native floor/saturation not specified; daily/monthly rate is weak evidence for a fast single stream |
| Exclude as blanket claim | Audio envelope, image recursive Gaussian, control | All contain recurrence families | State-dependent attack/release, higher-order state, or closed-loop unknown inputs can violate the contract |

### 1. Concrete source match: UKUI blur

The packaged upstream implementation uses `z += (alpha*((pixel<<7)-z))>>16`, with `aprec=16`, `zprec=7`, byte samples and `gint` state. Its radius law is integer conversion of `65536*(1-expf(-2.3/(radius+1)))`; row/column passes operate on an existing Cairo surface. [A1](https://sources.debian.org/src/ukui-session-manager/1.1.3.1-1/ukui-session/gsm-blur.c)

Independent derivation: with arithmetic signed right shift, set `D=65536`, `A=D-alpha`, `C=alpha*128*pixel`, legal state `[0,32640]`. Since integer `z+floor(t/D)=floor((Dz+t)/D)`, this is precisely the supported update for `0<alpha<=65536`. The interval is invariant, so clipping is inactive rather than an invented change to the code. For `0<=alpha<=65536`, the product magnitude is at most `65536*32640 = 2,139,095,040 < 2^31`; the update remains in range. An integer coefficient rounded to zero gives an identity transition, outside strict contraction, and should be handled explicitly. Freeze the actual generated integer coefficient rather than approximating the radius law on a different floating-point library. Confirm compiler/platform signed-shift behavior.

No production radius distribution, rate or latency target was obtained. Independent scanlines/channels are the cheaper parallelism to beat. Materialize each pass before mapping the next: original pixels cannot replace previously modified pixels.

### 2. Closest fast physical lead: SiPM emulator

Carsi et al. implement three independent one-pole banks, `y[n]=M*y[n-1]+x[n]`, `M=exp(-Ts/tau)`, with `Ts=.8 ns` and demonstrated `tau=1,50,100 ns`. Eight phases run at 156.25 MHz. They report that naive feedback misses timing and that two-step look-ahead reaches II=1; shaping latency is 83.2 ns. Coefficients are truncated to 27 bits; saturation and 16-bit quantization are described at the combined output. Internal state width, exact recursive rounding, and overflow behavior are not specified. [A2](https://arxiv.org/html/2607.00841v1)

Consequently the *real-valued shape* fits but the exact integer machine remains unknown. Obtain the HLS types/code, integer coefficients, quantization points and golden output traces. A final combiner's saturation cannot be moved into each bank. Choose one decay bank for the scalar experiment; preserve the full downstream combiner when testing application outputs. The three banks alone are independent work, while the eight subphases represent a single time sequence.

Independent estimates for those physical constants are poles about .449329, .984127, .992032. They are not the unpublished native integer coefficients. The fast rise should contract rapidly; the slow decay is the harder map workload. The paper's implementation already meets the output requirement, so the plausible research objective would be lower resource cost at that rate or a documented future configuration, not rescuing an unmet current requirement. Event FIFO presence does not authorize microseconds of delay. Ask for a maximum allowed shaping delay before choosing block length. Also compare event-driven decay shortcuts for sparse bins.

### 3. Radio DC correction: strong reason for caution

UHD documents an automatic single-tap RX IIR, a device-dependent default parameter `2^-20`, and a fixed manual-offset mode. Its displayed difference equation should not be used to infer the internal accumulator's exact positive-pole recurrence; source arithmetic was not recovered in this audit. [A3](https://files.ettus.com/manual/page_calibration.html)

If source inspection establishes an average update with pole `1-2^-20`, its unrounded time constant is about 1,048,576 samples. As an illustrative lower-pressure calculation, reducing an initial width of 65535 to 16 by ideal contraction takes about `ln(65535/16)*2^20 = 8.72 million` samples, before accounting for per-step rounding. This is not a compactness guarantee. Report sample rate only after fixing a particular device and actual stage clock; none is assumed here.

GNU Radio's named DC Blocker is another trap: its documented default is a length-32 delay-line construction, with long-form group delay `2D-2`, rather than the scalar quantized one-pole target. It is a useful application comparator, not evidence that all DC blockers fit. [A4](https://wiki.gnuradio.org/index.php/DC_Blocker)

### 4. Detector restoration, pole-zero correction, and control

The 2025 online pulse-compensation paper reports Q-format FPGA work and a system reaching 83 MHz with 222 logic elements. The accessible indexed implementation excerpt does not establish the exact state machine or a remaining throughput shortfall. Pole-zero cancellation and unfolding must be separated from a leaky baseline estimator; an accumulator with coefficient one falls outside `A<D`. Baseline inhibition decided from the unresolved filtered state also breaks known-`C`/known-coefficient assumptions. No complete native arithmetic configuration is claimed from this source. [A5](https://www.mdpi.com/2079-9292/14/3/493)

A separate real bottleneck exists in qubit flux predistortion: the QubiC paper reports 1 GS/s operation, 500 MHz fabric, a representative integrator/SOS/20-tap FIR chain and 162 ns latency using scattered look-ahead. That representative chain is outside the scalar contract. It establishes a reason to study recursive hardware but does not establish exact serial-rounding preservation or buffer tolerance for this proposal. [A6](https://arxiv.org/html/2609.16488v1)

For closed-loop control, future sensor inputs usually depend on previous outputs. A prerecorded stimulus is a different offline experiment and cannot demonstrate online closed-loop acceleration. These exclusions follow from the proposal's contract, not a claim that all detector/control systems are unsuitable.

### 5. Image and audio near-misses; finance

Qt's exponential blur is *not* interchangeable with UKUI's arithmetic. The inspected Qt implementation updates `z += alpha*(input-(z>>aprec))` with `aprec=12`, `zprec=10`. Across consecutive states `qD-1` and `qD`, the output difference is `1-alpha`, potentially negative. Thus its map is not even monotone for `alpha>1`; the proposed threshold theorem cannot be applied to its stored state. A transformed-state equivalence would need a new proof and preservation of every output. [A7](https://codebrowser.dev/qt6/qtbase/src/gui/painting/qimageeffects.cpp.html)

CMSIS Q15 DF1 is a useful exact hardware/software baseline framework: the standard function documents 64-bit accumulation and final Q15 saturation; its generic state is four words per section. Only a native section with second feedback coefficient zero, positive first feedback coefficient below the effective denominator, and known feed-forward terms reduces to this scalar problem. Do not zero coefficients of an existing biquad and call the result native. Q31 and fast variants have different overflow/precision behavior. [A8](https://arm-software.github.io/CMSIS-DSP/latest/group__BiquadCascadeDF1.html)

An audio attack/release detector that chooses its coefficient by comparing input with unresolved envelope state is outside the fixed known-coefficient update. A fixed smoothing stage after rectification can fit, but this audit found no primary implementation simultaneously establishing its arithmetic and single-stream throughput need. Audio-rate channel replication is not evidence of accelerating one stream.

RiskMetrics documents EWMA decay choices including .94 and .97 and historical daily observations. This establishes a mathematical scalar recurrence, not native integer floor-and-clip semantics or a high-rate dependency bottleneck. A newly quantized finance benchmark would be a synthetic workload unless an actual integer production implementation and compatibility requirement are obtained. [A9](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a)

## Public stimuli and an exact experiment

1. **Reproducible detector events:** SimSiPM supplies seeded simulation (`sensor.rng().seed(42)`), photon hit lists and hits-only generation. Pin a commit/configuration and retain the emitted hit timestamps/amplitudes before .8 ns binning. Reproduce the paper's single event and pile-up cases, then sweep fixed seeds and event rates. These are generated stimuli, not recorded experimental waveforms or a supplied golden fixed-point model. [A10](https://github.com/EdoPro98/SimSiPM)
2. **Recorded detector stress data:** the Majorana release supplies raw germanium waveforms in HDF5 with metadata and calibrated energies. Use records independently with their provided initial-baseline convention. Do not concatenate event snippets to manufacture a continuous acquisition stream. Native estimator coefficients and state-reset rules still require a separate source. [A11](https://sanfordlab.org/publications-and-reports/majorana-demonstrator-data-release-aiml-applications)
3. **Buffered images:** OpenEXR's official corpus includes ramps, bright rings, high-contrast patterns and scanline images. Define and publish conversion to Cairo 8-bit pixels before timing, or prefer already-byte source images. EXR-to-byte conversion is preprocessing, not a native recursive filter. Add all-zero/all-255, alternating extremes and ramps as explicitly synthetic adversarial tests. [A12](https://openexr.com/en/latest/test_images/index.html)

Prioritize AMR-WB once a consistent source release is obtained, because its exactness requirement is stronger. UKUI's *unchanged* update is the simpler buffered-kernel experiment while that source qualification proceeds. The following image experiment is proposed; no native application traces or timing were run during the audit.

- Freeze source/package version, integer `alpha`, format, row/column order, initial state, target compiler and shift semantics. Save input bytes, every serial state and output byte, and a checksum. Start with one channel of one pass; then preserve the whole image pipeline.
- Compare optimized serial code, independent row/channel parallelism, exact unrolling that retains every shift, forward-only restricted tables, and compact maps. Do not compare only against a giant full-domain LUT or a floating-point reference. For SiPM add its native look-ahead implementation as a separate application baseline; establish whether it is bit-identical before counting it as an exact baseline.
- Sweep only block lengths/capacities/parallel-worker counts, not native arithmetic chosen to improve maps. Report runtime coefficient/radius as a separate workload dimension, including unfavorable values. Use real observed radii when available; label the initial radius sweep experimental.
- Count endpoint construction, all inverse walks/divisions, map composition, boundary evaluation, replay, input/output storage and reorder traffic, and fallback. Resolve batch-to-batch dependence. Compare at equal routed FPGA resources or equal CPU cores with memory traffic included.
- Verify every state and byte against serial. Exhaustively check every entry state in `[0,32640]` for selected short UKUI blocks, plus complete-trace tests across all stimuli. Negative internal multiplication differences must round down, not toward zero. Inject capacity overflow and prove exact fallback; measure its worst-case sustained service.
- Record thresholds per block (maximum as well as distribution), first-output latency, full-frame/batch latency, sustained samples/second, bytes moved and resources. A single-line speedup does not count as system value if row-parallel execution is faster. No energy claim without measured complete-system power.
- Gate: obtain an actual native latency/rate target and a baseline that misses it, or show an equal-resource cost reduction with a documented exact-compatibility need. If neither occurs, retain the kernel as an arithmetic benchmark and do not promote it as the flagship application.

## Source registry and reading depth

The 12 sources above are primary papers, project documentation, source distributions or official dataset pages. A mirrored source distribution remains the original code rather than a third-party explanation. All accessed 2026-11-04; mutable pages/branches must be pinned before experiments.

| Key | Reading depth | Evidential limit |
|---|---|---|
| A1 UKUI 1.1.3.1-1 source | Indexed source body: inner update, row/column loops, coefficient and format calls | Direct open intermittently failed; not compiled; no production workload profile |
| A2 Carsi et al., 2026 preprint | HTML full technical narrative, equations 1–8, implementation and validation | No HLS code or complete integer semantics supplied |
| A3 UHD manual | Frontend-correction section and parameter text | Native RTL URL guesses failed; manual equation insufficient to establish arithmetic |
| A4 GNU Radio official wiki | Whole filter description and parameters | No source-level arithmetic audit needed for structural exclusion |
| A5 Pulse compensation, Electronics 14(3):493 | Indexed hardware excerpt only | Direct HTML/PDF access failed; no numerical-semantic conclusions |
| A6 Huszabianlou et al., 2026 preprint | Abstract, architecture/format navigation and selected architecture text | Not a full bit-level implementation audit |
| A7 Qt source | Relevant source body via Codebrowser mirror, lines 24–160 and calls around 300 | Official raw/cgit retrieval failed; pin official source before implementation |
| A8 CMSIS-DSP official reference | DF1 state order, Q15 and Q31 scaling/overflow sections | Generic library contract, not a specific deployed coefficient configuration |
| A9 RiskMetrics 1996 | Indexed EWMA table/forecast discussion | No production integer code or fast-stream requirement |
| A10 SimSiPM project | README simulation/seed/hits APIs and custom-waveform section | No dataset downloaded or generator executed |
| A11 Majorana release | Official release overview | HDF5 and technical appendix not downloaded; no assumed sample rate |
| A12 OpenEXR corpus | Official test-image descriptions | No images downloaded; conversion must be fixed explicitly |

## Search and access log

Queries used on 2026-11-04 (targeted audit, not exhaustive):

- `FPGA digital baseline restoration first order IIR pole zero correction 125 MHz fixed point`; located A5 and adjacent detector examples, but no complete scalar native machine.
- `site.github.com DC blocker fixed point ">>" "32768"`, `site.github.com Ettus dc_offset correction alpha set_dc_offset_auto single pole`, and `"dc_offset.v" "integrator" EttusResearch uhd`; located A3. Guessed raw source paths under `usrp3/lib/dsp` and `usrp2/sdr_lib` failed. No RTL claim is made.
- `site.github.com "expblur" "aprec"`; located A1/A7, separating two materially different quantization placements.
- `QubiC flux predistortion IIR fixed point source first order`; located A6 and adjacent predistortion papers. Most representative systems are integrator/SOS chains.
- Parent supplied A2; opened full HTML and followed its SimSiPM reference to A10.
- `site.arm-software.github.io CMSIS DSP arm_biquad_cascade_df1_q15 saturation`; inspected A8 as an arithmetic baseline family.
- `site.riskmetrics.com 1996 technical document lambda 0.94 0.97 EWMA`; located publisher-hosted A9; excluded finance as native quantized evidence.
- `site.pjrc.com envelope detector audio library attack release filter`; results mainly concerned DAHDSR generation rather than a documented scalar detector. No unsupported native audio example retained.
- `site.tamu.edu detector waveform dataset pulse open data germanium` and OpenEXR test-image searches; located A11/A12 as concrete stimuli, not proof of demand.

Direct shell network downloads also failed DNS resolution; no unavailable code is described as read. Search failures are gaps in this audit, not evidence that matching applications do not exist.

## Standardized codec de-emphasis

**Best candidate for an exactness-motivated benchmark: AMR-WB encoder `Deemph2`, particularly the buffered weighted-speech call.** This establishes a useful benchmark lead, not a high-throughput need. The source audit below distinguishes this function from superficially similar de-emphasis variants. It does not certify an entire deployed codec or the latest normative source attachment.

ITU explicitly describes G.722.2 Annex C as its bit-exact ANSI-C implementation. This supplies a real reason to preserve integer outputs, unlike an arbitrary quantization of a floating-point filter. [A13](https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=13429)

The inspected VisualOn/AOSP `Deemph2` uses 16-bit samples/state and 32-bit intermediates. Each step forms `x*32768`, adds `2*mu*state` with saturating `L_add`, and applies `voround`; the last output becomes the saved state. Both the first sample and subsequent samples use this path. The same file's `Deemph` instead uses a different first-sample rounding macro, and its `Deemph_32` uses unchecked shifts/additions: neither should inherit the following qualification. [A14](https://android.googlesource.com/platform/frameworks/av/%2B/dd833ba601e642d72da2200a2fd9c3fa1cb69d2d/media/module/codecs/amrwb/enc/src/deemph.c)

The inspected primitive header implements `voround(q)` by saturating `q+32768` and extracting its signed high word. Its `L_mac` is saturating addition after a doubled 16-bit product. The separate `vo_round` macro lacks this explicit saturating-add step. This distinction matters at the positive rail. [A15](https://android.1.googlesource.com/platform/frameworks/av/%2B/7aeb9029d26cde995cb6f76748ebe36c7bdc9be3/media/module/codecs/amrwb/enc/inc/basic_op.h)

Independent reduction for `0<=mu<32768`, with `sat32` and `sat16` denoting signed saturation:

```
q = sat32(32768*x + 2*mu*s)
s' = floor(sat32(q + 32768)/65536)
   = sat16(floor((mu*s + 16384*x + 16384)/32768))
```

The product `2*mu*s` cannot overflow signed 32 bits in this positive coefficient range. Intermediate saturation is absorbable *here*: below the negative 32-bit rail both expressions yield -32768; above the positive rail both yield 32767; inside the rails the same rounding offset applies, with positive rounding overflow likewise yielding 32767. This proof is specific to this scaling/order. It is not a general permission to move saturation through a codec chain. The resulting supported contract is `A=mu`, `D=32768`, `C=16384*x+16384`, state `[-32768,32767]`, using widened arithmetic to construct `C` and the numerator.

A Python model of these inspected primitive semantics compared this reduction for every 16-bit entry state at eight input values (`-32768,-32767,-1,0,1,16000,32766,32767`): **524,288 comparisons, zero differences**. This was executed during the follow-up; it is not a compiled reference-code test or complete input-space coverage.

The actual encoder call is `Deemph2(wsp,TILT_FAC,L_FRAME,&st->mem_wsp)` after all residual samples have been computed. There are also 64-sample `xn` and `h1` calls; `h1` resets its local state, while `mem_w0` is subsequently updated by other encoder arithmetic. Do not concatenate those calls into an invented single uninterrupted recurrence. [A16](https://android.googlesource.com/platform/frameworks/av/%2B/1e6a675fccdc37afcfb337f8fa97d1ddab90adf0/media/codecs/amrwb/enc/src/voAMRWBEnc.c)

Official constants give `TILT_FAC=22282`, `L_FRAME=256` at 12.8 kHz, `L_SUBFR=64`, and 320 external samples at 16 kHz. Thus the weighted-speech block covers 20 ms; the coefficient is exactly `22282/32768`, about .68. [A17](https://www.itu.int/epublications/en/publication/itu-t-g-722-2-annex-c-2017-12-fixed-point-c-code/en)

The weighted-speech buffer is an especially clean known-input block, but 20 ms framing is not a license to add another 20 ms of latency. Time within the existing frame service deadline must be measured. At 12,800 updates/second, one stream is unlikely to stress ordinary FPGA arithmetic; many simultaneous calls are independently parallelizable. The useful initial claim is exact buffered-kernel execution and perhaps offline conformance replay, not a demonstrated communications throughput bottleneck. Codec-wide speedup must include the much larger remaining encoder pipeline.

Public standardized stimuli are stronger here than the earlier generic datasets: TS 26.174 provides accompanying ZIPs with encoder `.INP`, coded `.COD`, and decoded `.OUT` sequences, including speech, silence, sweeps, saturation stress and mode switching. It specifies identical outputs after the stated homing procedure, with an explicit first-frame exception for hardware testing. [A18](https://www.etsi.org/deliver/etsi_ts/126100_126199/126174/18.00.00_60/ts_126174v180000p.pdf)

Concrete next experiment: obtain a *single consistent* normative source release and matching vectors; instrument its real `wsp` arrays, coefficient and entry/exit state; run the complete encoder unchanged first. Substitute only `Deemph2`, preserving every saturation and saved state. Compare intermediate traces and final `.COD` outputs, including homing and DTX paths; retain native frame boundaries. Benchmark serial, exact unrolling, restricted forward tables, threshold construction/composition/replay and channel-parallel execution at equal resources. The short contraction time is promising for compactness but measured total work and codec-wide benefit still decide usefulness.

Qualification limits: A14, A15 and A16 were accessible at different AOSP revisions; same-revision direct retrieval attempts failed. Their inspected semantics support the reduction, but the combined configuration must be pinned and compiled before calling it a fully verified native implementation. The normative attachment itself was not downloaded. No EVS .75 implementation was audited; EVS is not claimed as a second matching configuration.

Additional source registry (all accessed 2026-11-04):

| Key | Reading depth | Limit |
|---|---|---|
| A13 ITU G.722.2 Annex C | Official recommendation description | Establishes bit-exact purpose, not particular function arithmetic |
| A14 AOSP/VisualOn deemph.c | Indexed complete three-function source body | Frozen source URL; not compiled |
| A15 AOSP basic_op.h | Indexed `voround`, `vo_round`, `L_add`/MAC semantics | Different revision from A14; pin consistent source before implementation |
| A16 AOSP encoder main | Full page and selected call/reset/update contexts | Proves native calls, not complete codec conformance |
| A17 ITU Annex C electronic publication | Global constants and call graph/static-state tables | No source attachment downloaded |
| A18 ETSI TS 126 174 V18.0.0 | Scope, file format/homing and codec test sequence clauses | Vector ZIPs not downloaded/run |

Follow-up search log: `AMR WB deemph.c L_deposit_h L_mac round mem mu`, `"deemph.c" "L_mac" "mu"`, `"static_vo Word16 voround" "L_add"`, `"Deemph2" "TILT_FAC"`, and targeted AOSP call-site searches. These exposed the rounding-macro and variant differences above. Official ITU/ETSI sources were then used to establish constants and exactness motivation.

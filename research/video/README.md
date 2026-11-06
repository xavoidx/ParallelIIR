# Video and small-FPGA application search

Start with [VIDEO_REVIEW.md](VIDEO_REVIEW.md), the shareable verdict, reading list and high-level RTL roadmap. The three-condition search remains open: no reviewed video application yet establishes a matching rate bottleneck, a useful exactness contract, and superiority over the best exact implementation together.

The new leads are native Arm-2D spatial IIR blur and exact VVC/AV1 entropy probability updates. VLC temporal blur illustrates why aggregate pixel rate is not a single-state dependency. Detailed source, literature, system and arithmetic evidence is linked from the review.

Reproduce the source-expression checks from the repository root:

```sh
python3 research/video/native_arithmetic_checks.py
python3 research/video/entropy_arithmetic_checks.py
python3 research/video/entropy_independent_checks.py
```

The first exhausts about 25 million byte-state/input/parameter cases and takes longer. These commands write their JSON results alongside the scripts; they do not build native codecs or measure hardware performance.

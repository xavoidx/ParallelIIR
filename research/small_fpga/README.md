# Small-FPGA research pass

Start with [SMALL_FPGA_REVIEW.md](SMALL_FPGA_REVIEW.md): the wider application search, recommended experiments, evidence status, reading list and high-level RTL roadmap. No application yet demonstrates all three required gates together.

| File | Role |
|---|---|
| [DEVICE_FIRST_APPLICATIONS.md](DEVICE_FIRST_APPLICATIONS.md) | Deployed small-device systems; pinned HackRF arithmetic audit; instrumentation priorities |
| [NARROW_STREAM_REVIEW.md](NARROW_STREAM_REVIEW.md) | PDM, sigma-delta, pulse/count monitors, native IIR IP and exact alternatives |
| [LOCKIN_SOURCE_AUDIT.md](LOCKIN_SOURCE_AUDIT.md) | RePLIA clock/recurrence audit and Gregorat's implemented timing remedy |
| [RESOURCE_EFFICIENT_DIRECTION.md](RESOURCE_EFFICIENT_DIRECTION.md) | Shared residual channels, run processing, sparse observations, independent conceptual challenge and audit |
| [OBSERVATION_FIRST_PROTOTYPE.md](OBSERVATION_FIRST_PROTOTYPE.md) | Exact block exit/peak/alarm and finite-history certificates; derivation and limits |
| [observation_checks.py](observation_checks.py), [results](observation_results.json) | Reproducible constructed-model checks; no native benchmark or hardware result |
| [observation_independent_checks.py](observation_independent_checks.py), [results](observation_independent_results.json) | Independent oracle and broader input/domain checks, with source hashes |

All reports date from 6 November 2026. The sources establish deployed systems and relevant arithmetic; the software tests establish finite-case correctness of the constructed model. Device fit, timing, power, practical advantage and publication novelty remain unestablished.

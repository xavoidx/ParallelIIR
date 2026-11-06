#!/usr/bin/env python3
"""Exhaustive native-expression reductions; NOT source-build or performance tests.

Run: python3 research/video/native_arithmetic_checks.py

The literal models below transcribe the selected scalar expressions. Python's
signed right shift models the arithmetic signed shift assumed for the Arm C
target; it does not verify a compiler, target ABI, or the original sources.
The affine models independently evaluate the derived nonnegative numerator
using integer floor division. Every legal byte state/input and selected native
coefficient is enumerated. No elapsed times or throughput estimates are output.
"""

import hashlib
import json
from pathlib import Path


def arm_literal_native(state: int, pixel: int, degree: int) -> int:
    ratio = 256 - degree
    return state + (((pixel - state) * ratio) >> 8)


def arm_affine_reduced(state: int, pixel: int, degree: int) -> int:
    return (degree * state + (256 - degree) * pixel) // 256


def vlc_literal_native(state: int, pixel: int, factor: int) -> int:
    old_factor = factor
    new_factor = 128 - old_factor
    return ((state * old_factor) + (1 << 7 >> 1)
            + (pixel * new_factor)) >> 7


def vlc_affine_reduced(state: int, pixel: int, factor: int) -> int:
    return (factor * state + (128 - factor) * pixel + 64) // 128


def check_all(native, affine, coefficients: range) -> dict:
    checked = 0
    for coefficient in coefficients:
        for state in range(256):
            for pixel in range(256):
                literal = native(state, pixel, coefficient)
                reduced = affine(state, pixel, coefficient)
                if literal != reduced:
                    raise RuntimeError({
                        "failure": "native_affine_mismatch",
                        "coefficient": coefficient,
                        "state": state,
                        "pixel": pixel,
                        "native": literal,
                        "affine": reduced,
                    })
                if not 0 <= literal <= 255:
                    raise RuntimeError({
                        "failure": "byte_invariant_violation",
                        "coefficient": coefficient,
                        "state": state,
                        "pixel": pixel,
                        "native": literal,
                    })
                checked += 1
    expected = len(coefficients) * 256 * 256
    if checked != expected:
        raise RuntimeError(f"Coverage mismatch: {checked} != {expected}")
    return {
        "coefficient_inclusive": [coefficients.start, coefficients.stop - 1],
        "state_inclusive": [0, 255],
        "pixel_inclusive": [0, 255],
        "enumerated_cases": checked,
        "native_affine_equalities": checked,
        "byte_invariant_checks": checked,
        "status": "passed",
    }


def main() -> None:
    script = Path(__file__).resolve()
    result = {
        "schema_version": 1,
        "scope": "Exhaustive scalar integer-expression and range checks only.",
        "not_verified": [
            "Original C compilation or execution",
            "Compiler/ABI signed-shift and integer-promotion behavior",
            "Helium or other SIMD backend equivalence",
            "Image boundaries, pass ordering, framebuffer tiles, or resets",
            "ParallelIIR certificates, constructors, replay, or hardware",
            "Frame rate, clock rate, resources, energy, or performance advantage",
        ],
        "model_assumptions": [
            "Arm signed right shift rounds toward negative infinity",
            "Arm C int can represent all modeled intermediates (32-bit target)",
            "No overflow or saturation; coefficient fixed for each checked update",
            "Stored state and input byte are both in [0,255]",
        ],
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "arm_gray8": {
            "source_url": "https://github.com/ARM-software/Arm-2D/blob/"
                          "26c3b341703a21b241586eec8ddc753931b66e76/"
                          "Library/Source/__arm_2d_filter_iir_blur.c",
            "source_blob_sha": "a771c931427c41b55ae7235eed2e02c6eb3c6921",
            "literal_model": "s + (((x-s)*(256-d)) >> 8)",
            "affine_model": "(d*s + (256-d)*x) // 256",
            "parameter_note": "Nonzero byte degrees; documented blur range is 128..239."
                              " Degree zero bypass is not modeled.",
            **check_all(arm_literal_native, arm_affine_reduced, range(1, 256)),
        },
        "vlc_motionblur": {
            "source_url": "https://github.com/videolan/vlc/blob/"
                          "6bfcad4267f57f1e487503f4da16b033be01e3ca/"
                          "modules/video_filter/motionblur.c",
            "source_blob_sha": "4e2d95def93f10bb01505e6ce533f70d60de5e24",
            "literal_model": "(s*f + (1 << 7 >> 1) + x*(128-f)) >> 7",
            "affine_model": "(f*s + (128-f)*x + 64) // 128",
            "parameter_note": "All configured factor values 1..127; default is 80.",
            **check_all(vlc_literal_native, vlc_affine_reduced, range(1, 128)),
        },
    }
    destination = script.with_name("native_arithmetic_results.json")
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "scope": result["scope"],
        "arm_cases": result["arm_gray8"]["enumerated_cases"],
        "vlc_cases": result["vlc_motionblur"]["enumerated_cases"],
        "status": "passed",
        "results": str(destination),
    }, sort_keys=True))


if __name__ == "__main__":
    main()

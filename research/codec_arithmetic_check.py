#!/usr/bin/env python3
"""Check a mathematical model of inspected AMR-WB Deemph2 primitives.

Run: python research/codec_arithmetic_check.py
This does NOT compile a native codec or establish codec conformance.
Source fragments were inspected at DIFFERENT AOSP revisions; pin a consistent
normative release before making a native implementation equivalence claim.
Python integers deliberately avoid C signed overflow/shift undefined behavior.
"""

import json
from pathlib import Path

MU = 22282
INPUTS = [-32768, -32767, -1, 0, 1, 16000, 32766, 32767]
SOURCES = {
    "deemph2": "https://android.googlesource.com/platform/frameworks/av/%2B/dd833ba601e642d72da2200a2fd9c3fa1cb69d2d/media/module/codecs/amrwb/enc/src/deemph.c",
    "primitives": "https://android.1.googlesource.com/platform/frameworks/av/%2B/7aeb9029d26cde995cb6f76748ebe36c7bdc9be3/media/module/codecs/amrwb/enc/inc/basic_op.h",
    "caller": "https://android.googlesource.com/platform/frameworks/av/%2B/1e6a675fccdc37afcfb337f8fa97d1ddab90adf0/media/codecs/amrwb/enc/src/voAMRWBEnc.c",
}


def saturate(value, bits):
    return max(-(1 << (bits - 1)), min((1 << (bits - 1)) - 1, value))


def primitive_model(state, sample):
    # L_mult's exceptional (-32768)*(-32768) case is impossible for MU>0.
    # Model x<<15 and doubled multiplication as mathematical operations.
    accumulator = saturate(sample * 32768 + 2 * MU * state, 32)
    rounded = saturate(accumulator + 32768, 32)
    # Signed high-word extraction has arithmetic-right-shift/floor semantics.
    return rounded // 65536


def reduced_model(state, sample):
    return saturate((MU * state + 16384 * sample + 16384) // 32768, 16)


def main():
    comparisons = 0
    differences = 0
    first_difference = None
    for sample in INPUTS:
        for state in range(-32768, 32768):
            reference = primitive_model(state, sample)
            reduced = reduced_model(state, sample)
            comparisons += 1
            if reference != reduced:
                differences += 1
                if first_difference is None:
                    first_difference = dict(state=state, sample=sample,
                                            reference=reference, reduced=reduced)
    result = {
        "experiment": "AMR-WB Deemph2 inspected-primitive arithmetic model",
        "coefficient": MU,
        "state_interval_inclusive": [-32768, 32767],
        "inputs": INPUTS,
        "comparisons": comparisons,
        "differences": differences,
        "first_difference": first_difference,
        "reference_formula": "floor(sat32(sat32(32768*x+2*mu*s)+32768)/65536)",
        "reduced_formula": "sat16(floor((mu*s+16384*x+16384)/32768))",
        "sources": SOURCES,
        "source_reading": "Indexed source bodies at different AOSP revisions; no consistent release compiled.",
        "scope": "All 65536 states at eight selected inputs; not all input-state pairs; mathematical model only.",
        "native_compiled_conformance": False,
    }
    output = Path(__file__).with_name("codec_arithmetic_results.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"comparisons": comparisons, "differences": differences,
                      "results": str(output)}))
    if differences:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

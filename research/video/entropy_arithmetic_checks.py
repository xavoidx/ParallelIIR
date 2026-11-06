#!/usr/bin/env python3
"""Source-expression arithmetic audit, NOT a codec build or hardware benchmark.

VVenC source pin: 6441f64f9997e9ab8a12d4ac600998a104aa5ddf,
source/Lib/CommonLib/Contexts.{h,cpp}. AV1 update contract: libaom prob.h
52de8996066ff8b3130aa53ae4ce1527254b930b and AV1 parsing specification.
Synthetic stimuli only. Run from any directory; results are saved alongside.
"""
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "direction" / "certified_mask_checks.py"
sys.path.insert(0, str(CORE.parent))
from certified_mask_checks import Rule, advance_mask, build_mask, certificates, evaluate


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def packed_vvc_step(q, bit, bits, rate):
    """Reconstruct the masked native storage; q is its unscaled value."""
    shift = 15 - bits
    mask = ((1 << bits) - 1) << shift
    packed = q << shift
    down = (packed >> rate) & mask
    # Current source's upMove table equals this masked constant.
    up = (0x7fff >> rate) & mask
    packed_next = packed - down + (up if bit else 0)
    check(packed_next & ((1 << shift) - 1) == 0, "alignment")
    return packed_next >> shift


def av1_step(s, toward_top, rate):
    if toward_top:
        return s + ((32768 - s) >> rate)
    return s - (s >> rate)


def vvc_checks():
    primitive = candidates = replay_outputs = traces = boundaries = 0
    caps = []
    rng = random.Random(6021)
    for bits, rates in ((10, range(2, 6)), (14, range(5, 10))):
        for rate in rates:
            d = 1 << rate
            high = (1 << bits) - 1
            input_one = (1 << bits) - d
            rule = Rule(d - 1, d, bits, d - 1)
            for s in range(high + 1):
                for bit in (0, 1):
                    exact = packed_vvc_step(s, bit, bits, rate)
                    reduced = rule.step(s, bit * input_one)
                    check(exact == reduced and 0 <= exact <= high, "VVC reduction")
                    primitive += 1
            max_width = 0
            sequences = [[0] * 129, [1] * 129,
                         [i & 1 for i in range(129)],
                         [rng.randrange(2) for _ in range(129)]]
            for seq in sequences:
                initial = (high + 1) // 2
                inputs = [b * input_one for b in seq]
                blocks = [inputs[i:i+16] for i in range(0, len(inputs), 16)]
                bitblocks = [seq[i:i+16] for i in range(0, len(seq), 16)]
                certs, _, _ = certificates(rule, blocks, initial, bits + 12, 4)
                entry = initial
                resolved_entries = []
                for block, bitblock, cert in zip(blocks, bitblocks, certs):
                    lo, hi, _, _ = cert
                    check(lo <= entry <= hi, "VVC certified entry")
                    max_width = max(max_width, hi - lo)
                    summary = build_mask(rule, block, lo, hi)
                    for trial in range(lo, hi + 1):
                        native = trial
                        for b in bitblock:
                            native = packed_vvc_step(native, b, bits, rate)
                        check(evaluate(summary, trial) == native, "VVC map")
                        candidates += 1
                    resolved_entries.append(entry)
                    # Resolve the next boundary ONLY through the transition map.
                    # The native oracle never supplies a replay entry.
                    entry = evaluate(summary, entry)
                    boundaries += 1
                replay = []
                for bitblock, resolved in zip(bitblocks, resolved_entries):
                    for b in bitblock:
                        resolved = packed_vvc_step(resolved, b, bits, rate)
                        replay.append(resolved)
                check(replay[-1] == entry, "VVC final mapped boundary")
                literal, s = [], initial
                for b in seq:
                    s = packed_vvc_step(s, b, bits, rate)
                    literal.append(s)
                check(replay == literal, "VVC every-output replay")
                replay_outputs += len(replay)
                traces += 1
            caps.append(dict(state_bits=bits, shift=rate,
                             ideal_floor_error_width=d-1,
                             observed_certificate_width=max_width))
    return dict(primitive_comparisons=primitive, traces=traces,
                certified_boundaries=boundaries, local_map_candidates=candidates,
                replay_outputs=replay_outputs, configurations=caps)


def av1_checks():
    primitive = adjacent = rate_checks = maps = entries = 0
    for rate in range(4, 8):
        d = 1 << rate
        for toward_top in (False, True):
            c = 32768 if toward_top else d - 1
            previous = None
            for s in range(32769):
                native = av1_step(s, toward_top, rate)
                check(native == ((d - 1) * s + c) // d, "AV1 reduction")
                check(0 <= native <= 32768, "AV1 range")
                if previous is not None:
                    check(native - previous in (0, 1), "AV1 adjacency")
                    adjacent += 1
                previous = native
                primitive += 1
    for n in range(2, 17):
        for count in range(33):
            normative = 3 + (count > 15) + (count > 31) + min(n.bit_length()-1, 2)
            simplified = 4 + (count >> 4) + (n > 3)
            check(normative == simplified, "AV1 rate")
            rate_checks += 1
    # Variable-rate / variable-offset maps: domains supplied explicitly.
    # This does NOT test or claim the fixed-offset certificate theorem for AV1.
    rng = random.Random(6201)
    for n in (2, 3, 4, 8, 16):
        symbols = [rng.randrange(n) for _ in range(80)]
        for element in (0, n - 2):
            for initial_count in (0, 15, 31, 32):
                for lo, width in ((0, 31), (16000, 127), (32737, 31)):
                    base, mask, count = lo, (1 << width) - 1, initial_count
                    expected = list(range(lo, lo + width + 1))
                    for symbol in symbols:
                        rate = 4 + (count >> 4) + (n > 3)
                        d = 1 << rate
                        up = element < symbol  # libaom stores inverse CDFs.
                        c = 32768 if up else d - 1
                        base, mask, _ = advance_mask(base, mask, d - 1, d, c)
                        expected = [av1_step(s, up, rate) for s in expected]
                        count += count < 32
                    for i, expected_exit in enumerate(expected):
                        got = base + (mask & ((1 << i) - 1)).bit_count()
                        check(got == expected_exit, "AV1 variable map")
                        entries += 1
                    maps += 1
    return dict(primitive_comparisons=primitive, adjacent_differences=adjacent,
                rate_cases=rate_checks, variable_maps=maps,
                variable_map_entry_comparisons=entries,
                certificate_claim="none: variable offset/rate requires a separate bound")


def main():
    result = dict(
        scope="Synthetic source-expression equivalence; no compiled codec, real tape, RTL or speed measurement",
        vvc_source_commit="6441f64f9997e9ab8a12d4ac600998a104aa5ddf",
        vvc_header_blob="c495aebabd519f41f3926fd9169766eb0ed90d01",
        vvc_tables_blob="7ffa2dca2e5f3c4f79ba9dfa154fc791a16b15f2",
        core_sha256=hashlib.sha256(CORE.read_bytes()).hexdigest(),
        audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        vvc=vvc_checks(), av1=av1_checks())
    (HERE / "entropy_arithmetic_results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

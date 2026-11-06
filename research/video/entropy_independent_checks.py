#!/usr/bin/env python3
"""Independent source-expression and execution-path audit, not a codec build.

Pinned VVenC tables/header were separately fetched with the GitHub connector.
This script reconstructs their unsigned packed updates, resolves block entries
using only summaries, and then checks replayed packed lanes and pre-update joint
indices. It imports the project's certificate/map functions; it is not an
independent proof of those functions or of an all-input capacity theorem.
"""

import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "direction" / "certified_mask_checks.py"
sys.path.insert(0, str(CORE.parent))
from certified_mask_checks import Rule, build_mask, certificates, evaluate

VVC_COMMIT = "6441f64f9997e9ab8a12d4ac600998a104aa5ddf"
VVC_HEADER_BLOB = "c495aebabd519f41f3926fd9169766eb0ed90d01"
VVC_TABLES_BLOB = "7ffa2dca2e5f3c4f79ba9dfa154fc791a16b15f2"
UP0 = (0x7fe0, 0x3fe0, 0x1fe0, 0x0fe0, 0x07e0, 0x03e0,
       0x01e0, 0x00e0, 0x0060, 0x0020, 0, 0, 0, 0, 0, 0)
UP1 = (0x7ffe, 0x3ffe, 0x1ffe, 0x0ffe, 0x07fe, 0x03fe,
       0x01fe, 0x00fe, 0x007e, 0x003e, 0x001e, 0x000e,
       0x0006, 0x0002, 0, 0)


def check(value, message):
    if not value:
        raise AssertionError(message)


def configured_rates():
    rows = []
    for window in range(16):
        k0 = 2 + ((window >> 2) & 3)
        k1 = 3 + k0 + (window & 3)
        if k1 <= 9:
            rows.append((window, k0, k1))
    check(len(rows) == 13, "configured pair count")
    check(len({(k0, k1) for _, k0, k1 in rows}) == 13,
          "configured pairs distinct")
    return rows


def vvc_checks():
    rng = random.Random(9271)
    table_checks = complement_checks = packed_checks = index_checks = 0
    traces = resolved_boundaries = 0
    max_widths = {}
    for bits, table in ((10, UP0), (14, UP1)):
        mask = ((1 << bits) - 1) << (15 - bits)
        for k, actual in enumerate(table):
            check(actual == ((32767 >> k) & mask), "native upMove table")
            table_checks += 1
        for k in (range(2, 6) if bits == 10 else range(5, 10)):
            high = (1 << bits) - 1
            for s in range(high + 1):
                # Unifies the two native branches using a shift/subtract core.
                down = s - (s >> k)
                up = s - (s >> k) + (high >> k)
                via_complement = high - ((high - s) - ((high - s) >> k))
                check(up == via_complement == s + ((high - s) >> k),
                      "conditional complement baseline")
                check(0 <= down <= high and 0 <= up <= high, "branch range")
                complement_checks += 1

    for _, k0, k1 in configured_rates():
        for pattern in ("zero", "one", "alternating", "random"):
            seq = [0 if pattern == "zero" else 1 if pattern == "one"
                   else i % 2 if pattern == "alternating" else rng.randrange(2)
                   for i in range(128)]
            post_lanes, pre_lanes = [], []
            for bits, k in ((10, k0), (14, k1)):
                d = 1 << k
                rule = Rule(d - 1, d, bits, d - 1)
                inputs = [bit * ((1 << bits) - d) for bit in seq]
                blocks = [inputs[i:i + 16] for i in range(0, len(inputs), 16)]
                initial = 1 << (bits - 1)
                certs, _, _ = certificates(rule, blocks, initial, bits + 12, 4)
                summaries = [build_mask(rule, block, cert[0], cert[1])
                             for block, cert in zip(blocks, certs)]
                key = f"b{bits}_k{k}"
                max_widths[key] = max(max_widths.get(key, 0),
                                      max(c[1] - c[0] for c in certs))
                # Resolve all entries from maps before running any replay.
                entries, entry = [], initial
                for summary in summaries:
                    entries.append(entry)
                    entry = evaluate(summary, entry)
                    resolved_boundaries += 1
                before, after = [], []
                for block, start in zip(blocks, entries):
                    state = start
                    for x in block:
                        before.append(state << (15 - bits))
                        state = rule.step(state, x)
                        after.append(state << (15 - bits))
                pre_lanes.append(before)
                post_lanes.append(after)

            native = [16384, 16384]
            for i, bit in enumerate(seq):
                check((native[0] + native[1]) >> 8 ==
                      (pre_lanes[0][i] + pre_lanes[1][i]) >> 8,
                      "pre-update combined state index")
                index_checks += 1
                for lane, (bits, k, table) in enumerate(((10, k0, UP0),
                                                        (14, k1, UP1))):
                    mask = ((1 << bits) - 1) << (15 - bits)
                    native[lane] -= (native[lane] >> k) & mask
                    native[lane] += table[k] & -bit
                    check(native[lane] == post_lanes[lane][i],
                          "native packed lane versus summary-resolved replay")
                    packed_checks += 1
            traces += 1
    return dict(configured_rate_pairs=[dict(window=w, rate0=k0, rate1=k1)
                                       for w, k0, k1 in configured_rates()],
                native_table_entries=table_checks,
                conditional_complement_state_cases=complement_checks,
                traces=traces, trace_length=128, initialization="packed (16384,16384)",
                summary_resolved_boundaries=resolved_boundaries,
                native_packed_lane_checks=packed_checks,
                pre_update_combined_index_checks=index_checks,
                observed_certificate_widths=max_widths,
                excluded="fraction-bit table values/accumulated costs, compiled codec, default rate0=0, real traces, RTL, throughput")


def av1_checks():
    # Compare inverse-CDF formulas to complements of the forward-CDF update.
    # The closed interval includes the Q15 scale endpoint 32768; storage needs
    # 16 unsigned bits. This does not instantiate Rule(bits=15), whose high is
    # only 32767, or claim a certificate for variable offsets/rates.
    cases = 0
    for k in range(4, 8):
        d = 1 << k
        for inverse_up in (False, True):
            for inverse in range(32769):
                forward = 32768 - inverse
                target = 0 if inverse_up else 32768
                if target < forward:
                    forward -= (forward - target) >> k
                else:
                    forward += (target - forward) >> k
                reference = 32768 - forward
                c = 32768 if inverse_up else d - 1
                got = ((d - 1) * inverse + c) // d
                check(got == reference and 0 <= got <= 32768,
                      "AV1 complement and floor reduction")
                cases += 1
    return dict(forward_inverse_formula_cases=cases,
                inclusive_state_domain=[0, 32768], unsigned_storage_bits=16,
                excluded="full CDF vectors, syntax/context selection, counts/resets/update-disable flags, certificate theorem, range coder and whole-codec equivalence")


def main():
    out = dict(
        scope="Synthetic source-expression and summary-resolved replay checks only; no compiled codec, fraction-bit lookup, accumulated RDO costs, real trace, RTL, speed or whole-codec equivalence",
        vvc_source_commit=VVC_COMMIT, vvc_header_blob=VVC_HEADER_BLOB,
        vvc_tables_blob=VVC_TABLES_BLOB,
        source_reading="Pinned header and cpp fetched separately through GitHub connector; native update constants transcribed here and checked against documented table formula",
        av1_source="https://aomediacodec.github.io/av1-spec/#symbol-decoding-process",
        core_sha256=hashlib.sha256(CORE.read_bytes()).hexdigest(),
        audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        vvc=vvc_checks(), av1=av1_checks())
    path = HERE / "entropy_independent_results.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent literal-oracle checks for the observation-first research model.

Exercises arbitrary inputs and restricted domains, peak clamp extremes, inverse
alarm cut boundaries, image-restricted composition, and finite-history bounds.
Root sources/results are read only. Writes only this audit's JSON companion.
No hardware, workload fit, formal equivalence, advantage, or novelty claim.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
TARGET = HERE / "observation_checks.py"
PERSISTED = HERE / "observation_results.json"


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(a, d, rho, sequence, state):
    """Literal original recurrence, without target rank or inverse helpers."""
    peak = -1
    for sample in sequence:
        state = (a * state + (d - a) * sample + rho) // d
        peak = max(peak, state)
    return state, peak


def run():
    source_hash = digest(TARGET)
    spec = importlib.util.spec_from_file_location("observation_audit_target", TARGET)
    target = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = target
    spec.loader.exec_module(target)
    core_hash = digest(target.CORE)
    persisted = json.loads(PERSISTED.read_text())
    check(source_hash == persisted["script_sha256"], "persisted source hash")
    check(core_hash == persisted["core_sha256"], "persisted core hash")
    # Call the root checks without invoking main or rewriting its JSON.
    check(target.exhaustive_checks() == persisted["exhaustive"], "root exhaustive result")
    check(target.composition_checks() == persisted["composition_entry_checks"],
          "root composition result")
    check(target.streamed_checks() == persisted["streamed"], "root stream result")

    rng = random.Random(11062026)
    entries = cut_boundaries = compositions = histories = 0
    clamp_regions = dict(above=0, below=0, inside=0)
    for case in range(12000):
        bits = rng.randrange(1, 17)
        high = (1 << bits) - 1
        d = rng.randrange(2, 258)
        a = rng.randrange(1, d)
        rho = rng.randrange(d)
        rule = target.Rule(a, d, bits, rho)
        lo = rng.randrange(high + 1)
        hi = min(high, lo + rng.randrange(128))
        sequence = [rng.randrange(high + 1) for _ in range(rng.randrange(1, 40))]
        threshold = rng.choice([0, high, high + 1, rng.randrange(high + 2)])
        summary = target.build(rule, sequence, lo, hi, threshold)
        cut = target.inverse_alarm(rule, sequence, threshold)
        expected_cut = hi + 1
        for entry in range(lo, hi + 1):
            end, peak = walk(a, d, rho, sequence, entry)
            check(summary.query(entry) == (end, peak, peak >= threshold),
                  (case, entry, "literal exit/peak/alarm"))
            check((entry >= cut) == (peak >= threshold),
                  (case, entry, "inverse cut"))
            if peak >= threshold:
                expected_cut = min(expected_cut, entry)
            entries += 1
        check(summary.alarm_entry == expected_cut, "restricted-domain alarm sentinel")
        for entry in {0, high, max(0, cut - 1), min(high, cut)}:
            _, peak = walk(a, d, rho, sequence, entry)
            check((entry >= cut) == (peak >= threshold), "inverse cut boundary")
            cut_boundaries += 1

        # Observe the full-width deltas independently to show clamp coverage.
        base, peak_base = lo, None
        for sample in sequence:
            base = (a * base + (d - a) * sample + rho) // d
            if peak_base is not None:
                delta = base - peak_base
                region = ("above" if delta > hi - lo else
                          "below" if delta < lo - hi else "inside")
                clamp_regions[region] += 1
            peak_base = base if peak_base is None else max(peak_base, base)

        # Restrict the second summary to the first summary's exact image.
        end_lo = walk(a, d, rho, sequence, lo)[0]
        end_hi = walk(a, d, rho, sequence, hi)[0]
        tail = [rng.randrange(high + 1) for _ in range(rng.randrange(1, 10))]
        second = target.build(rule, tail, end_lo, end_hi, threshold)
        for entry in {lo, hi, rng.randrange(lo, hi + 1)}:
            mid, peak1, hit1 = summary.query(entry)
            end, peak2, hit2 = second.query(mid)
            end_ref, peak_ref = walk(a, d, rho, sequence + tail, entry)
            check((end, max(peak1, peak2), hit1 or hit2) ==
                  (end_ref, peak_ref, peak_ref >= threshold), "restricted composition")
            compositions += 1

        initial = rng.randrange(high + 1)
        start = rng.randrange(len(sequence) + 1)
        lookback = rng.randrange(len(sequence) + 4)
        cert_lo, cert_hi = target.history(rule, sequence, start, lookback, initial)
        true_state = walk(a, d, rho, sequence[:start], initial)[0]
        check(cert_lo <= true_state <= cert_hi, "history contains actual state")
        width = 0 if max(0, start - lookback) == 0 else high
        for _ in range(min(start, lookback)):
            width = (a * width + d - 1) // d
        check(cert_hi - cert_lo <= width, "history width recurrence")
        histories += 1

    # An above-threshold entry is excluded from the post-update peak.
    rule = target.Rule(1, 2, 4, 0)
    summary = target.build(rule, [0], 15, 15, 15)
    check(summary.query(15) == (7, 7, False), "post-update-only peak")
    for bad in (-1, 16):
        try:
            summary.query(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-domain query accepted")
    check(source_hash == digest(TARGET), "source changed during audit")
    check(core_hash == digest(target.CORE), "core changed during audit")
    return dict(
        scope="Synthetic scalar integer research model; no RTL, workload fit, formal equivalence, advantage, or novelty claim",
        audit_script_sha256=digest(Path(__file__)),
        target_script_sha256=source_hash,
        core_sha256=core_hash,
        root_persisted_results_reproduced=True,
        seed=11062026,
        random_cases=12000,
        independent_domain_entry_comparisons=entries,
        inverse_cut_boundary_comparisons=cut_boundaries,
        restricted_image_compositions=compositions,
        general_input_history_certificates=histories,
        peak_clamp_regions_exercised=clamp_regions,
        post_update_fixture="passed",
        domain_rejections="passed",
        limitations="Seeded cases support the derivations; not exhaustive over all configurations. Composition checks compose queries/observables, not a materialized parallel merged-summary circuit. No work counts interpreted as clocks or resource savings.",
    )


if __name__ == "__main__":
    result = run()
    (HERE / "observation_independent_results.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

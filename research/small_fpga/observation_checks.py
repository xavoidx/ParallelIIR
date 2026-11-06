#!/usr/bin/env python3
"""Synthetic exact exit/peak/alarm summaries and finite-history certificates.

No native deployment, hardware throughput, area, energy or novelty claim.
Peak means maximum POST-UPDATE state, not an upcrossing or entry-inclusive peak.
Run from any directory; write JSON beside this script.
"""
from bisect import bisect_left
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "direction" / "certified_mask_checks.py"
sys.path.insert(0, str(CORE.parent))
from certified_mask_checks import Rule


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def ceil_div(n, d):
    return -((-n) // d)


@dataclass(frozen=True)
class Summary:
    lo: int
    hi: int
    exit_base: int
    exit_ranks: tuple
    peak_base: int
    peak_ranks: tuple
    alarm_entry: int  # hi+1 means no legal entry triggers this threshold.

    def query(self, entry):
        if not self.lo <= entry <= self.hi:
            raise ValueError("Query outside summary domain")
        i = entry - self.lo
        return (self.exit_base + self.exit_ranks[i],
                self.peak_base + self.peak_ranks[i], entry >= self.alarm_entry)


def build(rule, inputs, lo, hi, threshold):
    if not inputs or not 0 <= lo <= hi <= rule.high:
        raise ValueError("Nonempty block and legal domain required")
    if not 0 <= threshold <= rule.high + 1:
        raise ValueError("Threshold outside supported state/sentinel interval")
    if any(type(x) is not int or not 0 <= x <= rule.high for x in inputs):
        raise ValueError("Input outside unsigned invariant domain")
    width = hi - lo
    base, ranks = lo, list(range(width + 1))
    peak_base, peak_ranks = None, None
    alarm_entry = hi + 1
    for x in inputs:
        base, rem = divmod(rule.a * base + rule.c(x), rule.d)
        ranks = [u + (rem - rule.m * u) // rule.d for u in ranks]
        # The Boolean observable is a single threshold in original-entry order.
        first = bisect_left(ranks, threshold - base)
        alarm_entry = min(alarm_entry, lo + first)
        if peak_base is None:
            peak_base, peak_ranks = base, ranks[:]
        else:
            # Full-width base comparison/range detection is still needed.
            delta = max(-width, min(width, base - peak_base))
            peak_ranks = [max(v, delta + u) - max(0, delta)
                          for v, u in zip(peak_ranks, ranks)]
            peak_base = max(peak_base, base)
        for values in (ranks, peak_ranks):
            check(values[0] == 0 and values[-1] <= width, "rank range")
            check(all(b-a in (0, 1) for a, b in zip(values, values[1:])),
                  "ordered unit increments")
    return Summary(lo, hi, base, tuple(ranks), peak_base,
                   tuple(peak_ranks), alarm_entry)


def literal(rule, inputs, initial):
    states = []
    for x in inputs:
        initial = (rule.a * initial + rule.m * x + rule.offset) // rule.d
        states.append(initial)
    return states


def inverse_alarm(rule, inputs, threshold):
    """One backward pass; constant inverse division is charged, not free."""
    cut = rule.high + 1
    for x in reversed(inputs):
        target = min(threshold, cut)
        cut = max(0, min(rule.high + 1,
                        ceil_div(rule.d * target - rule.c(x), rule.a)))
    return cut


def history(rule, inputs, block_start, lookback, initial):
    start = max(0, block_start - lookback)
    lo, hi = (initial, initial) if start == 0 else (0, rule.high)
    for x in inputs[start:block_start]:
        lo, hi = rule.step(lo, x), rule.step(hi, x)
    return lo, hi


def lookback_bound(rule, target):
    width, count = rule.high, 0
    while width > target:
        narrower = ceil_div(rule.a * width, rule.d)
        if narrower == width:
            return None
        width, count = narrower, count + 1
    return count


def exhaustive_checks():
    blocks = entries = alarms = 0
    for bits in range(1, 5):
        for d in (2, 3, 4, 5, 8):
            for a in range(1, d):
                for rho in (0, d - 1):
                    rule = Rule(a, d, bits, rho)
                    for length in range(1, 5):
                        for pattern in product((0, rule.high), repeat=length):
                            threshold = rule.high // 2 + 1
                            summary = build(rule, pattern, 0, rule.high, threshold)
                            cut = inverse_alarm(rule, pattern, threshold)
                            for entry in range(rule.high + 1):
                                states = literal(rule, pattern, entry)
                                exit_state, peak, alarm = summary.query(entry)
                                check((exit_state, peak, alarm) ==
                                      (states[-1], max(states), max(states) >= threshold),
                                      "exit / peak / forward alarm")
                                check(alarm == (entry >= cut), "backward alarm")
                                entries += 1
                            blocks += 1
                            # Include always/never sentinels.
                            for t in (0, rule.high, rule.high + 1):
                                cut = inverse_alarm(rule, pattern, t)
                                for entry in range(rule.high + 1):
                                    check((entry >= cut) ==
                                          (max(literal(rule, pattern, entry)) >= t),
                                          "inverse alarm sentinel")
                                    alarms += 1
    return dict(blocks=blocks, exit_peak_forward_alarm_entry_checks=entries,
                backward_alarm_sentinel_entry_checks=alarms)


def composition_checks():
    rng = random.Random(3166)
    checks = 0
    for _ in range(200):
        rule = Rule(3, 4, 5, rng.randrange(4))
        left = [rng.randrange(32) for _ in range(rng.randrange(1, 10))]
        right = [rng.randrange(32) for _ in range(rng.randrange(1, 10))]
        t = rng.randrange(rule.high + 2)
        one, two = (build(rule, v, 0, rule.high, t) for v in (left, right))
        for entry in range(32):
            mid, p1, hit1 = one.query(entry)
            end, p2, hit2 = two.query(mid)
            all_states = literal(rule, left + right, entry)
            check((end, max(p1, p2), hit1 or hit2) ==
                  (all_states[-1], max(all_states), max(all_states) >= t),
                  "state / observable composition")
            checks += 1
    return checks


def streamed_checks():
    rng = random.Random(6181)
    rows, domains, boundary_checks = [], 0, 0
    for bits in (8, 16, 32):
        for a, d in ((3, 4), (15, 16), (63, 64), (127, 128), (97, 100)):
            rule = Rule(a, d, bits, d // 2)
            target = min(rule.high, (d - 1) // (d - a))
            warm = lookback_bound(rule, target)
            check(warm is not None, "attainable history width")
            length = 64
            inputs = [rng.randrange(2) * rule.high for _ in range(warm + 4*length)]
            initial, threshold = rule.high // 3, 3 * rule.high // 4
            summaries = []
            for start in range(0, len(inputs), length):
                lo, hi = history(rule, inputs, start, warm, initial)
                check(hi-lo <= target, "history width bound")
                summaries.append(build(rule, inputs[start:start+length], lo, hi, threshold))
                domains += 1
            # No output replay: resolve each block's exact state, peak and alarm.
            resolved, entry = [], initial
            for summary in summaries:
                entry, peak, alarm = summary.query(entry)
                resolved.append((entry, peak, alarm))
            oracle = literal(rule, inputs, initial)
            for j, got in enumerate(resolved):
                states = oracle[j*length:(j+1)*length]
                check(got == (states[-1], max(states), max(states) >= threshold),
                      "history-certified streamed observables")
                boundary_checks += 1
            rows.append(dict(bits=bits, a=a, d=d, rho=rule.offset,
                             guaranteed_width=target, history_samples=warm,
                             native_updates_per_input_at_L64=1+2*warm/64,
                             native_updates_per_input_at_L256=1+2*warm/256))
    return dict(configurations=rows, certified_domains=domains,
                exact_observation_triples=boundary_checks,
                accounting="Two history endpoint updates per history sample plus one shared-base update per block input; excludes ranks, peak/alarm, lookup, memory, pipeline and I/O. NOT cycles or throughput.")


def main():
    fixture_rule = Rule(3, 4, 8)
    fixture = literal(fixture_rule, [255]*8 + [0]*56, 0)
    out = dict(scope="Constructed scalar model only; no native workload, RTL, advantage or novelty claim",
               script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
               core_sha256=sha256(CORE.read_bytes()).hexdigest(),
               exhaustive=exhaustive_checks(),
               composition_entry_checks=composition_checks(),
               streamed=streamed_checks(),
               missed_endpoint_example=dict(threshold=200, endpoint=fixture[-1],
                                            peak=max(fixture), any_exceedance=max(fixture)>=200),
               peak_contract="max of post-update states; not entry-inclusive peak, first hit, upcrossing count, dwell time or feedback-triggered reset")
    (HERE / "observation_results.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

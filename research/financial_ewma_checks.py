#!/usr/bin/env python3
"""Exact arithmetic characterization, not a market-data or hardware benchmark.

Run: python3 research/financial_ewma_checks.py
Uses only the standard library. All stimuli are synthetic and reproducible.
Native formulas are transcribed from sources in FINANCIAL_EWMA_PRIOR_ART.md;
these checks do not compile or validate the original projects' RTL.
"""

from bisect import bisect_right
from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path
import random


def ceil_div(n, d):
    return -((-n) // d)


@dataclass(frozen=True)
class Contract:
    name: str
    bits: int
    a: int
    d: int
    offset: int = 0
    piecewise: bool = False
    status: str = "proposed integer implementation"

    @property
    def high(self):
        return (1 << self.bits) - 1

    def step(self, state, price):
        if self.piecewise:
            delta = price - state
            return state + (1 if delta >= 0 else -1) * (abs(delta) // self.d)
        return (self.a * state + (self.d - self.a) * price + self.offset) // self.d

    def inverse(self, target, price):
        # Smallest legal entry with output >= target, or high+1 if absent.
        if target <= self.step(0, price):
            return 0
        if target > self.step(self.high, price):
            return self.high + 1
        if self.piecewise:
            numerator = (self.d * target - price if target <= price else
                         self.d * (target - 1) + 1 - price)
            return ceil_div(numerator, self.d - 1)
        return ceil_div(self.d * target - (self.d - self.a) * price - self.offset,
                        self.a)

    def width_bound_step(self, width):
        if self.piecewise:
            # Maximal width for a shared input, including intervals straddling it.
            return width - max(0, (width - self.d + 1) // self.d)
        return ceil_div(self.a * width, self.d)


CONTRACTS = [
    Contract("fast_half", 16, 1, 2, status="synthetic favorable control"),
    Contract("normalized_15_16", 16, 15, 16),
    Contract("columbia_61_64", 17, 61, 64, 32,
             status="native report/HDL arithmetic reconstruction"),
    Contract("columbia_63_64", 17, 63, 64, 32,
             status="native report/HDL arithmetic reconstruction"),
    Contract("columbia_127_128", 17, 127, 128, 64,
             status="native report/HDL arithmetic reconstruction"),
    Contract("liquidity_97_100", 16, 97, 100),
    Contract("volatility_197_200", 16, 197, 200),
    Contract("span_10000", 16, 9999, 10001,
             status="proposed unadjusted integer variant; not native adjusted float EWMA"),
    Contract("illinois_difference_16bit", 16, 15, 16, piecewise=True,
             status="native documented rule; 16-bit state chosen for experiment"),
    Contract("illinois_difference_32bit", 32, 15, 16, piecewise=True,
             status="native documented rule; 32-bit state chosen for experiment"),
]


def trace(contract, inputs, entry):
    outputs = []
    for price in inputs:
        entry = contract.step(entry, price)
        outputs.append(entry)
    return outputs


def summary(contract, inputs):
    low = trace(contract, inputs, 0)[-1]
    high = trace(contract, inputs, contract.high)[-1]
    thresholds = []
    for target in range(low + 1, high + 1):
        entry = target
        for price in reversed(inputs):
            entry = contract.inverse(entry, price)
        thresholds.append(entry)
    assert thresholds == sorted(set(thresholds))
    return low, thresholds


def check_arithmetic():
    counts = dict(inverse_comparisons=0, adjacent_pairs=0, width_bound_checks=0,
                  block_entry_comparisons=0, replay_output_comparisons=0)
    templates = [Contract("floor", 5, 15, 16),
                 Contract("rounded61", 5, 61, 64, 32),
                 Contract("rounded63", 5, 63, 64, 32),
                 Contract("rounded127", 5, 127, 128, 64),
                 Contract("piecewise", 5, 15, 16, piecewise=True)]
    for c in templates:
        for price in range(c.high + 1):
            outputs = [c.step(s, price) for s in range(c.high + 1)]
            assert min(outputs) >= 0 and max(outputs) <= c.high
            for left, right in zip(outputs, outputs[1:]):
                assert right - left in (0, 1)
                counts["adjacent_pairs"] += 1
            for target in range(-1, c.high + 3):
                expected = next((s for s, out in enumerate(outputs) if out >= target),
                                c.high + 1)
                assert c.inverse(target, price) == expected
                counts["inverse_comparisons"] += 1
            for lo in range(c.high + 1):
                for hi in range(lo, c.high + 1):
                    assert outputs[hi] - outputs[lo] <= c.width_bound_step(hi - lo)
                    counts["width_bound_checks"] += 1
    # Explicitly vary D for the derived piecewise width bound and inverse.
    for d in (2, 3, 4, 8):
        c = Contract("piecewise", 5, d - 1, d, piecewise=True)
        for price in range(c.high + 1):
            outputs = [c.step(s, price) for s in range(c.high + 1)]
            for target in range(-1, c.high + 3):
                expected = next((s for s, out in enumerate(outputs) if out >= target),
                                c.high + 1)
                assert c.inverse(target, price) == expected
                counts["inverse_comparisons"] += 1
            for lo in range(c.high + 1):
                for hi in range(lo, c.high + 1):
                    assert outputs[hi] - outputs[lo] <= c.width_bound_step(hi - lo)
                    counts["width_bound_checks"] += 1
    small = [Contract("half", 3, 1, 2), Contract("rounded", 3, 5, 8, 4),
             Contract("floor", 3, 7, 8),
             Contract("piecewise", 3, 3, 4, piecewise=True)]
    for c in small:
        for block in product(range(c.high + 1), repeat=3):
            base, thresholds = summary(c, block)
            for entry in range(c.high + 1):
                assert base + bisect_right(thresholds, entry) == trace(c, block, entry)[-1]
                counts["block_entry_comparisons"] += 1
        rng = random.Random(20261106)
        blocks = [[rng.randrange(c.high + 1) for _ in range(7)] for _ in range(13)]
        summaries = [summary(c, b) for b in blocks]
        for initial in range(c.high + 1):
            entries, state = [], initial
            for base, thresholds in summaries:
                entries.append(state)
                state = base + bisect_right(thresholds, state)
            replay = [out for block, entry in zip(blocks, entries)
                      for out in trace(c, block, entry)]
            reference = trace(c, [x for b in blocks for x in b], initial)
            assert replay == reference
            counts["replay_output_comparisons"] += len(replay)
    return counts


def characterize(c):
    lengths = (16, 64, 256, 1024, 4096)
    width, count = c.high, 0
    bounds = {}
    while True:
        next_width = c.width_bound_step(width)
        if next_width == width:
            break
        width, count = next_width, count + 1
        if count in lengths:
            bounds[str(count)] = width
        assert count < 1000000
    for length in lengths:
        if length >= count:
            bounds[str(length)] = width
    mid = (c.high + 1) // 2
    rng = random.Random(20261106)
    walk, p = [], mid
    for _ in range(max(lengths)):
        p = max(0, min(c.high, p + rng.choice((-1, 0, 1))))
        walk.append(p)
    patterns = {
        "constant_midpoint": [mid] * max(lengths),
        "one_tick_random_walk": walk,
        "alternating_rails": [0, c.high] * (max(lengths) // 2),
        "uniform_full_domain": [rng.randrange(c.high + 1) for _ in range(max(lengths))],
    }
    measured = {}
    for name, inputs in patterns.items():
        lo, hi, table = 0, c.high, {}
        for n, price in enumerate(inputs, 1):
            lo, hi = c.step(lo, price), c.step(hi, price)
            if n in lengths:
                table[str(n)] = hi - lo
                assert hi - lo <= bounds[str(n)]
        measured[name] = table
    # Synthetic independently generated blocks: a modest distribution, not traffic evidence.
    block_widths = []
    for _ in range(32):
        lo, hi = 0, c.high
        for _ in range(256):
            price = rng.randrange(c.high + 1)
            lo, hi = c.step(lo, price), c.step(hi, price)
        block_widths.append(hi - lo)
    return {
        "name": c.name, "bits": c.bits, "A": c.a, "D": c.d,
        "rounding_offset": c.offset, "piecewise": c.piecewise, "status": c.status,
        "bound_at_L": bounds, "bound_plateau_K": width,
        "first_L_at_bound_plateau": count,
        "ideal_eight_worker_rate_over_clock_at_bound": 8 / (width + 3),
        "workers_for_two_events_per_clock_at_bound_no_overheads": 2 * (width + 3),
        "synthetic_endpoint_K": measured,
        "uniform_32_blocks_L256_K": {"min": min(block_widths), "max": max(block_widths),
                                      "mean": sum(block_widths) / len(block_widths)},
    }


def main():
    result = {
        "description": "Exact integer checks; synthetic stimuli; no hardware or financial backtest",
        "seed": 20261106,
        "passed": check_arithmetic(),
        "assumptions": [
            "Unsigned [0,2**bits-1] price/state, wide exact intermediates; convex maps need no clip",
            "Full legal entry-state domain, not an observed local range",
            "K is image width / number of thresholds, not number of image states",
            "Rate model P/(K+3) assumes equal one-cycle forward/inverse transitions and no overhead",
            "Bound plateaus are conservative guarantees, not predicted typical K",
            "One synthetic trace per pattern; 32 uniform blocks give a separate small sample",
            "Proposed fixed-point contracts do not preserve original float/decimal arithmetic",
        ],
        "contracts": [characterize(c) for c in CONTRACTS],
    }
    path = Path(__file__).with_name("financial_ewma_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "result_file": str(path)}, indent=2))
    for row in result["contracts"]:
        print(row["name"], "bound K/L", row["bound_plateau_K"],
              row["first_L_at_bound_plateau"], "constant/walk/IID K at 4096",
              [row["synthetic_endpoint_K"][p]["4096"] for p in
               ("constant_midpoint", "one_tick_random_walk", "uniform_full_domain")])


if __name__ == "__main__":
    main()

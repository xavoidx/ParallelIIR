"""Reproducible research checks; leaves the WIP implementation unchanged.

Run from any directory: python research/audit.py
Only standard library is needed except for the optional original-model check.
These are semantic and image-width experiments, not performance benchmarks.
"""
from bisect import bisect_right
from itertools import product
from pathlib import Path
import hashlib
import json
import math
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parent.parent


def step(s, A, D, C, lo, hi):
    return max(lo, min(hi, (A * s + C) // D))


def trace(s, ops, lo, hi):
    out = []
    for A, D, C in ops:
        s = step(s, A, D, C, lo, hi)
        out.append(s)
    return out


def exit_state(s, ops, lo, hi):
    for A, D, C in ops:
        s = step(s, A, D, C, lo, hi)
    return s


def ceildiv(a, b):
    return -((-a) // b)


def inverse(t, op, lo, hi):
    A, D, C = op
    if t <= lo:
        return lo
    if t > hi:
        return hi + 1
    if A == 0:
        return lo if step(lo, A, D, C, lo, hi) >= t else hi + 1
    return max(lo, min(hi + 1, ceildiv(D * t - C, A)))


def summary(ops, lo, hi):
    base = exit_state(lo, ops, lo, hi)
    top = exit_state(hi, ops, lo, hi)
    thresholds = []
    for t in range(base + 1, top + 1):
        for op in reversed(ops):
            t = inverse(t, op, lo, hi)
        thresholds.append(t)
    return base, thresholds


def evaluate(m, s):
    return m[0] + bisect_right(m[1], s)


def compose(f, g, lo, hi):
    """Return g after f. Each threshold of g is pulled back through f."""
    base = evaluate(g, evaluate(f, lo))
    top = evaluate(g, evaluate(f, hi))
    ts = []
    for target in range(base + 1, top + 1):
        g_threshold = g[1][target - g[0] - 1]
        # All targets in the composed image are above f's base and reachable.
        ts.append(f[1][g_threshold - f[0] - 1])
    return base, ts


def correctness():
    count = 0
    blocks = 0
    # Every length-three input sequence over this alphabet, every legal state.
    for bits in (3, 4):
        lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        for A, D in ((0, 1), (1, 2), (2, 3), (3, 4), (63, 64)):
            for xs in product((lo, -1, 0, 1, hi), repeat=3):
                ops = [(A, D, D * x) for x in xs]
                m = summary(ops, lo, hi)
                assert all(a < b for a, b in zip(m[1], m[1][1:]))
                values = [exit_state(s, ops, lo, hi) for s in range(lo, hi + 1)]
                assert all(b - a in (0, 1) for a, b in zip(values, values[1:]))
                assert all(evaluate(m, s) == v for s, v in zip(range(lo, hi + 1), values))
                blocks += 1
                count += hi - lo + 1
    rng = random.Random(20261104)
    randomized = 0
    compositions = 0
    output_count = 0
    for _ in range(300):
        bits = rng.choice((4, 6, 8))
        lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        ops = []
        for _ in range(rng.randrange(3, 30)):
            D = rng.choice((1, 2, 3, 4, 16, 64))
            ops.append((rng.randrange(D), D, rng.randrange(2 * D * lo, 2 * D * hi + 1)))
        i, j = len(ops) // 3, 2 * len(ops) // 3
        parts = [ops[:i], ops[i:j], ops[j:]]
        ms = [summary(p, lo, hi) for p in parts]
        left = compose(compose(ms[0], ms[1], lo, hi), ms[2], lo, hi)
        right = compose(ms[0], compose(ms[1], ms[2], lo, hi), lo, hi)
        assert left == right == summary(ops, lo, hi)
        for s in range(lo, hi + 1):
            assert evaluate(left, s) == exit_state(s, ops, lo, hi)
            randomized += 1
        state = rng.randint(lo, hi)
        reference = trace(state, ops, lo, hi)
        replay = []
        for p, m in zip(parts, ms):
            replay.extend(trace(state, p, lo, hi))
            state = evaluate(m, state)
        assert replay == reference
        output_count += len(reference)
        compositions += 1
    return dict(exhaustive_blocks=blocks, exhaustive_state_comparisons=count,
                random_state_comparisons=randomized, composition_cases=compositions,
                replay_outputs=output_count, mismatches=0)


def width_sweep():
    lo, hi = -32768, 32767
    rng = random.Random(20261104)
    rows = []
    for A, D in ((1, 2), (3, 4), (63, 64), (255, 256), (511, 512)):
        for L in (64, 256, 1024, 4096):
            bound = hi - lo
            for _ in range(L):
                bound = ceildiv(A * bound, D)
            for mode in ('silence', 'alternating_extremes', 'uniform_full_range',
                         'uniform_scaled', 'sine_scaled'):
                widths, clips = [], []
                repetitions = 16 if mode.startswith('uniform') else 1
                amplitude = max(1, ((D - A) * hi) // (4 * D))
                for _ in range(repetitions):
                    if mode == 'silence':
                        xs = [0] * L
                    elif mode == 'alternating_extremes':
                        xs = [hi if i % 2 else lo for i in range(L)]
                    elif mode == 'uniform_full_range':
                        xs = [rng.randint(lo, hi) for _ in range(L)]
                    elif mode == 'uniform_scaled':
                        xs = [rng.randint(-amplitude, amplitude) for _ in range(L)]
                    else:
                        xs = [round(amplitude * math.sin(2 * math.pi * i / 127)) for i in range(L)]
                    ops = [(A, D, D * x) for x in xs]
                    widths.append(exit_state(hi, ops, lo, hi) - exit_state(lo, ops, lo, hi))
                    s, nclip = 0, 0
                    for x in xs:
                        raw = A * s // D + x
                        nclip += raw < lo or raw > hi
                        s = max(lo, min(hi, raw))
                    clips.append(nclip / L)
                rows.append(dict(A=A, D=D, L=L, mode=mode, blocks=repetitions,
                                 K_min=min(widths), K_median=statistics.median(widths),
                                 K_max=max(widths), certified_bound=bound,
                                 clipping_fraction_mean=statistics.mean(clips)))
    return rows


def original_model_check():
    sys.path.insert(0, str(ROOT))
    try:
        from GoldenModel import ParallelFilter
    except ImportError as e:
        return {'unavailable': str(e)}
    model = ParallelFilter(0.5, 1, 16)
    xs = [100, 0, 0]
    actual = model.serialPass(xs)[1]
    expected = trace(0, [(1, 2, 2 * x) for x in xs], -32768, 32767)
    assert actual != expected
    return dict(input=xs, actual_declared_16bit=actual, intended_16bit=expected,
                original_source_sha256=hashlib.sha256((ROOT / 'GoldenModel.py').read_bytes()).hexdigest())


def main():
    data = dict(date='2026-11-04', scope='Software semantics and endpoint widths only; no speed measurements',
                python=sys.version, correctness=correctness(),
                original_model=original_model_check(), width_sweep=width_sweep())
    path = Path(__file__).with_name('audit_results.json')
    path.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({k: v for k, v in data.items() if k != 'width_sweep'}, indent=2))
    print(f'Wrote {len(data["width_sweep"])} width configurations to {path}')


if __name__ == '__main__':
    main()

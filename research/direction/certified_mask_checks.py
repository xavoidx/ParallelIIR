#!/usr/bin/env python3
"""Research prototype: certified block domains and forward deletion masks.

python3 research/direction/certified_mask_checks.py

Exact Python integers, synthetic data, no hardware timing claims. The predictor
uses finite-precision outward-rounded affine maps and a parallel-prefix topology;
it does NOT use the serial exact reference to supply boundary certificates.
Only nonnegative affine coefficients/contributions and invariant unsigned states
are implemented. General signed/saturating/difference-truncated rules are outside
this prototype. Software rank/select is a correctness model, not a circuit model.
"""

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import random
from typing import NamedTuple

REFERENCE_MAX_MASK_WIDTH = 65_536  # Software allocation guard, not FPGA admission.


class MapSummary(NamedTuple):
    base: int
    mask: int
    total_deletions: int
    max_deletions: int
    factored_updates: int
    lo: int
    hi: int

def require_integer(name, value, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        raise ValueError(f"{name} must be an integer" +
                         (f" >= {minimum}" if minimum is not None else ""))


def validate_inputs(rule, inputs):
    if not inputs:
        raise ValueError("At least one input is required")
    for x in inputs:
        require_integer("input", x, 0)
        if x > rule.high:
            raise ValueError("Input exceeds the invariant unsigned domain")


def fraction_record(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def display_float(value):
    # Display-only: an exact finite bound can exceed binary64's finite range.
    try:
        return float(value)
    except OverflowError:
        return None


def ceil_div(n, d):
    return -((-n) // d)


def select1(mask, rank):
    """Zero-based bit position of the one-based rank-th set bit."""
    require_integer("mask", mask, 0)
    require_integer("rank", rank, 1)
    if rank > mask.bit_count():
        raise ValueError("Selected rank is outside the mask")
    for _ in range(rank - 1):
        mask &= mask - 1
    return (mask & -mask).bit_length() - 1


@dataclass(frozen=True)
class Rule:
    a: int
    d: int
    bits: int
    offset: int = 0

    def __post_init__(self):
        for name in ("a", "d", "bits", "offset"):
            require_integer(name, getattr(self, name))
        if not (0 < self.a < self.d and self.bits > 0 and 0 <= self.offset < self.d):
            raise ValueError("Expected 0<A<D, positive state bits, and 0<=offset<D")

    @property
    def m(self):
        return self.d - self.a

    @property
    def high(self):
        return (1 << self.bits) - 1

    def c(self, x):
        return self.m * x + self.offset

    def step(self, s, x):
        return (self.a * s + self.c(x)) // self.d


def affine_block(rule, inputs, q):
    validate_inputs(rule, inputs)
    require_integer("fixed-point scale", q, 1)
    # y_out = g*y_in+h, with each endpoint stored in units of 1/q.
    num, den = rule.a ** len(inputs), rule.d ** len(inputs)
    glo, ghi = q * num // den, ceil_div(q * num, den)
    hlo = hhi = 0
    for x in inputs:
        hlo = (rule.a * hlo + rule.c(x) * q) // rule.d
        hhi = ceil_div(rule.a * hhi + rule.c(x) * q, rule.d)
    return glo, ghi, hlo, hhi


def compose(after, before, q):
    # Both intervals enclose nonnegative affine parameters. Each operation rounds
    # outwards. Finite-precision compositions need not be associative as sets;
    # the selected prefix tree still encloses its exact real affine composition.
    al, au, bl, bu = after
    cl, cu, dl, du = before
    return (al * cl // q, ceil_div(au * cu, q),
            al * dl // q + bl, ceil_div(au * du, q) + bu)


def prefixes(maps, q):
    # Hillis-Steele: independent combines within a level. This correctness
    # prototype performs O(P log P) combines; it does not claim a work-optimal scan.
    levels, combines, stride = 0, 0, 1
    current = maps[:]
    while stride < len(current):
        old = current
        current = [compose(old[i], old[i-stride], q) if i >= stride else old[i]
                   for i in range(len(old))]
        combines += len(old) - stride
        levels += 1
        stride *= 2
    return [(q, q, 0, 0)] + current[:-1], levels, combines


def certificates(rule, blocks, initial, fraction_bits, group_blocks=None):
    require_integer("initial", initial, 0)
    require_integer("fraction_bits", fraction_bits, 0)
    if group_blocks is not None:
        require_integer("group_blocks", group_blocks, 1)
    if initial > rule.high or not blocks:
        raise ValueError("Invalid initial state or empty block sequence")
    q = 1 << fraction_bits
    local = [affine_block(rule, b, q) for b in blocks]
    size = group_blocks or len(blocks)
    result, levels, combines = [], 0, 0
    # Carry an enclosure of the GLOBAL unrounded trajectory, not an exact state
    # obtained from serial execution or previous-group boundary resolution.
    carry_lo = carry_hi = initial*q
    for start in range(0, len(local), size):
        group = local[start:start+size]
        prefix, depth, work = prefixes(group, q)
        levels += depth
        combines += work
        for i, (gl, gu, hl, hu) in enumerate(prefix):
            zlo = gl*carry_lo//q+hl
            zhi = ceil_div(gu*carry_hi,q)+hu
            # Per-update floor error <= (D-1)/D; geometric total <= (D-1)/(D-A).
            lo = max(0, ceil_div(zlo * rule.m - q * (rule.d-1), q * rule.m))
            hi = min(rule.high, zhi // q)
            if start+i == 0:
                lo = hi = initial
            assert lo <= hi
            result.append((lo, hi, zlo, zhi))
        gl,gu,hl,hu=compose(group[-1],prefix[-1],q)
        carry_lo,carry_hi=gl*carry_lo//q+hl,ceil_div(gu*carry_hi,q)+hu
        combines += 1
    return result, levels, combines


def uniform_capacity_bound(rule, length, group_size, fraction_bits):
    """Sufficient all-input bound across arbitrarily many FIXED full groups.

    Exact rational bound calculation, not measured traffic. Assumes unsigned
    bounded inputs, offset in [0,D), constant A/D, specified outward arithmetic
    and sufficient intermediate width. Partial groups require a separate bound.
    """
    require_integer("length", length, 1)
    require_integer("group_size", group_size, 1)
    require_integer("fraction_bits", fraction_bits, 0)
    q=1 << fraction_bits
    smax=Fraction(rule.high)+Fraction(rule.offset,rule.m)
    wh=0
    for _ in range(length):
        wh=ceil_div(rule.a*wh,rule.d)+1
    num,den=rule.a**length,rule.d**length
    local=(q*num//den,ceil_div(q*num,den),Fraction(wh,q))
    def bound_comp(after,before):
        al,au,ea=after
        bl,bu,eb=before
        return (al*bl//q,ceil_div(au*bu,q),
                Fraction(au,q)*eb+Fraction(au-al,q)*smax+ea+Fraction(2,q))
    rows=[local]*group_size
    stride=1
    while stride<group_size:
        old=rows
        rows=[bound_comp(old[i],old[i-stride]) if i>=stride else old[i]
              for i in range(group_size)]
        stride*=2
    exclusive=[(q,q,Fraction(0))]+rows[:-1]
    gl,gu,eh=bound_comp(local,exclusive[-1])
    if gu>=q:
        return {"finite_carry_bound":False,"reason":"quantized group gain upper bound >= 1"}
    delta=Fraction(gu-gl,q)*smax+eh+Fraction(2,q)
    carry_error=delta/(1-Fraction(gu,q))
    widest=max(Fraction(u,q)*carry_error+Fraction(u-l,q)*smax+e+Fraction(2,q)
               for l,u,e in exclusive)
    complete=widest+Fraction(rule.d-1,rule.m)
    cap=min(rule.high,complete.numerator//complete.denominator)
    return {"finite_carry_bound":True,"mask_width_cap":cap,
            "max_deletions_cap":ceil_div(rule.m*cap,rule.d),
            "predictor_width_bound_exact":fraction_record(widest),
            "carry_width_bound_exact":fraction_record(carry_error),
            "predictor_width_bound_state_units":display_float(widest),
            "carry_width_bound_state_units":display_float(carry_error),
            "scope":"all bounded inputs, fixed coefficient, fixed full groups, specified outward arithmetic"}


def advance_mask(base, mask, a, d, c):
    for name, value in (("base", base), ("a", a), ("d", d), ("c", c)):
        require_integer(name, value)
    require_integer("mask", mask, 0)
    if not 0 < a < d:
        raise ValueError("Mask update requires 0<A<D")
    k, m = mask.bit_count(), d-a
    value, remainder = divmod(a * base + c, d)
    remove, rank, boundaries = 0, remainder // m + 1, 0
    # All ranks refer to the OLD set-bit order, so multi-delete is simultaneous.
    while rank <= k:
        remove |= 1 << select1(mask, rank)
        boundaries += 1
        rank = (remainder + boundaries * d) // m + 1
    new_mask = mask & ~remove
    assert k - new_mask.bit_count() <= ceil_div(m*k, d)
    return value, new_mask, boundaries


def build_mask(rule, block, lo, hi, *, max_width=REFERENCE_MAX_MASK_WIDTH):
    validate_inputs(rule, block)
    require_integer("lo", lo, 0)
    require_integer("hi", hi, 0)
    if not lo <= hi <= rule.high:
        raise ValueError("Invalid map entry domain")
    require_integer("max_width", max_width, 0)
    if hi-lo > max_width:
        raise ValueError("Map domain exceeds the reference mask allocation limit")
    base, mask = lo, (1 << (hi-lo)) - 1
    total = largest = factored_updates = 0
    for x in block:
        factored_updates += mask.bit_count()+1
        base, mask, deletions = advance_mask(base, mask, rule.a, rule.d, rule.c(x))
        total += deletions
        largest = max(largest, deletions)
    return MapSummary(base, mask, total, largest, factored_updates, lo, hi)


def evaluate(summary, entry, lo=None, hi=None):
    if not isinstance(summary, MapSummary):
        raise ValueError("A map summary with its bound entry domain is required")
    if (lo is not None and lo != summary.lo) or (hi is not None and hi != summary.hi):
        raise ValueError("Query domain differs from the domain stored in the summary")
    lo, hi = summary.lo, summary.hi
    for name, value in (("entry", entry), ("lo", lo), ("hi", hi)):
        require_integer(name, value)
    if not lo <= entry <= hi:
        raise ValueError("Map query is outside its certified entry domain")
    base, mask = summary[:2]
    require_integer("base", base)
    require_integer("mask", mask, 0)
    if mask.bit_length() > hi-lo:
        raise ValueError("Map mask exceeds its declared entry domain")
    return base + (mask & ((1 << (entry-lo)) - 1)).bit_count()


def serial(rule, inputs, initial):
    out = []
    for x in inputs:
        initial = rule.step(initial, x)
        out.append(initial)
    return out


def primitive_checks():
    comparisons = cases = 0
    # Arbitrary signed bases/C and every mask up to width 7, including multi-delete.
    for d in range(2, 11):
        for a in range(1, d):
            for width in range(8):
                for mask in range(1 << width):
                    base = -5 + mask % 11
                    c = -2*d + (mask*7+width) % (4*d+1)
                    new_base, new_mask, _ = advance_mask(base, mask, a, d, c)
                    for j in range(width+1):
                        old_value = base + (mask & ((1 << j)-1)).bit_count()
                        direct = (a*old_value+c)//d
                        assert direct == new_base + (new_mask & ((1 << j)-1)).bit_count()
                        comparisons += 1
                    cases += 1
    return dict(mask_update_cases=cases, mask_entry_comparisons=comparisons)


def end_to_end(rule, inputs, length, initial, fraction_bits, verify_candidates=True,
               group_blocks=None):
    validate_inputs(rule, inputs)
    require_integer("length", length, 1)
    require_integer("initial", initial, 0)
    require_integer("fraction_bits", fraction_bits, 0)
    if initial > rule.high:
        raise ValueError("Initial state exceeds the invariant domain")
    if group_blocks is not None:
        require_integer("group_blocks", group_blocks, 1)
    blocks = [inputs[i:i+length] for i in range(0, len(inputs), length)]
    certs, levels, combines = certificates(rule, blocks, initial, fraction_bits,group_blocks)
    maps = [build_mask(rule, block, lo, hi)
            for block, (lo, hi, _, _) in zip(blocks, certs)]
    entries, entry = [], initial
    bound_checks = candidate_checks = 0
    for block, cert, summary in zip(blocks, certs, maps):
        lo, hi, _, _ = cert
        if not lo <= entry <= hi:
            raise ValueError("Resolved entry is outside the certified domain")
        entries.append(entry)
        if verify_candidates:
            for trial in range(lo, hi+1):
                assert evaluate(summary, trial, lo, hi) == serial(rule, block, trial)[-1]
                candidate_checks += 1
        entry = evaluate(summary, entry, lo, hi)
        bound_checks += 1
    replay = [v for b, e in zip(blocks, entries) for v in serial(rule, b, e)]
    reference = serial(rule, inputs, initial)
    assert replay == reference
    # Independently verify that the finite-precision predictor encloses exact
    # rational affine boundaries on small traces only; large fractions are not RTL.
    rational_checks = 0
    if len(inputs) <= 128:
        z, pos, q = Fraction(initial), 0, 1 << fraction_bits
        for b, (_, _, zl, zu) in zip(blocks, certs):
            assert Fraction(zl, q) <= z <= Fraction(zu, q)
            rational_checks += 1
            for x in b:
                z = (rule.a*z+rule.c(x))/rule.d
                pos += 1
    full_k = [serial(rule, b, rule.high)[-1]-serial(rule, b, 0)[-1] for b in blocks]
    widths = [hi-lo for lo, hi, _, _ in certs]
    predictor_widths_exact = [Fraction(zu-zl,1 << fraction_bits) for _, _, zl, zu in certs]
    uniform=None
    size=group_blocks or len(blocks)
    if all(len(b)==length for b in blocks) and len(blocks)%size==0:
        uniform=uniform_capacity_bound(rule,length,size,fraction_bits)
        if uniform["finite_carry_bound"]:
            assert max(widths)<=uniform["mask_width_cap"]
            bound = uniform["predictor_width_bound_exact"]
            assert max(predictor_widths_exact)<=Fraction(bound["numerator"],bound["denominator"])
    return {
        "blocks": len(blocks), "block_length": length, "fraction_bits": fraction_bits,
        "group_blocks": group_blocks or len(blocks),
        "certificate_width_min": min(widths), "certificate_width_max": max(widths),
        "certificate_width_mean": sum(widths)/len(widths),
        "predictor_enclosure_width_max_state_units": display_float(max(predictor_widths_exact)),
        "full_domain_exit_K_min": min(full_k), "full_domain_exit_K_max": max(full_k),
        "restricted_exit_K_max": max(m[1].bit_count() for m in maps),
        "max_deletions_one_update": max(m[3] for m in maps),
        "deletions_total": sum(m[2] for m in maps),
        "constructor_only_operation_counts": {
            "mask_base_updates":len(inputs),
            "mask_rank_selects":sum(m[2] for m in maps),
            "same_domain_factored_forward_state_updates":sum(m[4] for m in maps),
            "same_domain_inverse_transition_steps":sum(m[1].bit_count()*len(b) for m,b in zip(maps,blocks)),
            "same_domain_inverse_endpoint_steps":2*len(inputs),
            "full_domain_inverse_transition_steps":sum(k*len(b) for k,b in zip(full_k,blocks)),
            "predictor_offset_endpoint_updates":2*len(inputs),
            "interval_prefix_products_unspecialized":4*combines,
            "interval_application_products_unspecialized":2*len(blocks)+2*ceil_div(len(blocks),size),
            "comparison_limit":"Forward counts evolve separate candidate states; shared-base relative-rank tables are a stronger required baseline",
        },
        "prefix_levels": levels, "prefix_interval_combines": combines,
        "certificate_checks": bound_checks, "map_entry_checks": candidate_checks,
        "replay_output_checks": len(reference), "rational_predictor_checks": rational_checks,
        "sufficient_uniform_capacity_bound":uniform,
    }


def main():
    if not __debug__:
        raise RuntimeError("Run the verification suite without -O; it relies on assertions")
    checks = primitive_checks()
    rng = random.Random(20261106)
    small_runs = []
    # Deliberately coarse predictor precision tests widened certificates/multi-delete.
    for a,d in ((1,2),(3,4),(15,16),(61,64),(97,100)):
        for bits in (5, 9):
            r = Rule(a,d,bits,d//2)
            inputs = [rng.randrange(r.high+1) for _ in range(96)]
            for precision in (3, bits+8):
                small_runs.append(end_to_end(r, inputs, 8, r.high//2, precision))
    results = []
    for name, a, d, offset in (("normalized_15_16",15,16,0),
                               ("columbia_61_64",61,64,32),
                               ("columbia_63_64",63,64,32),
                               ("columbia_127_128",127,128,64),
                               ("liquidity_97_100",97,100,0)):
        for bits in (17, 32):
            r = Rule(a,d,bits,offset)
            for pattern in ("constant", "one_tick_walk", "full_range_uniform"):
                mid, p = r.high//2, r.high//2
                inputs=[]
                for _ in range(512):
                    p=max(0,min(r.high,p+rng.choice((-1,0,1))))
                    inputs.append(mid if pattern=="constant" else p if pattern=="one_tick_walk"
                                  else rng.randrange(r.high+1))
                row=end_to_end(r,inputs,32,mid,bits+12)
                row.update(name=name,A=a,D=d,offset=offset,state_bits=bits,pattern=pattern)
                results.append(row)
    # Explicitly compare coarse and fine certificates without changing exact outputs.
    coarse = max(s["max_deletions_one_update"] for s in small_runs)
    group_runs=[]
    for a,d in ((15,16),(63,64),(97,100)):
        r=Rule(a,d,32)
        inputs=[rng.randrange(r.high+1) for _ in range(4096)]
        row=end_to_end(r,inputs,32,r.high//2,44,group_blocks=8)
        row.update(A=a,D=d,state_bits=32,pattern="full_range_uniform")
        group_runs.append(row)
    aggregate={k:sum(s[k] for s in small_runs+results+group_runs) for k in
               ("certificate_checks","map_entry_checks","replay_output_checks","rational_predictor_checks")}
    checks.update(aggregate)
    out={"description":"Certified finite-precision affine block prefix + exact forward mask + full replay",
         "seed":20261106,"stimuli":"synthetic only; no market data downloaded",
         "scope":"unsigned invariant convex floor EMA, constant A/D, integer offset; no saturation",
         "checks_passed":checks,"coarse_precision_max_deletions_per_update":coarse,
         "hardware_status":"not synthesized; software rank/select and predictor costs are not clock cycles",
         "small_precision_stress_runs":small_runs,"configurations":results,
         "multiple_group_certificate_carry":group_runs}
    path=Path(__file__).with_name("certified_mask_results.json")
    path.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"checks_passed":checks,"result_file":str(path),
                      "coarse_max_deletions":coarse},indent=2))
    for row in results:
        if row["pattern"]=="one_tick_walk":
            print(row["name"],row["state_bits"],"full K",row["full_domain_exit_K_max"],
                  "cert W",row["certificate_width_max"],"maxdeletions",row["max_deletions_one_update"])


if __name__=="__main__":
    main()

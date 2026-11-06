#!/usr/bin/env python3
"""A stronger exact comparator: shared full-width base plus relative ranks.

This is a representation/correctness comparison, not a CPU or FPGA benchmark.
Data are synthetic. Both methods receive exactly the same certified intervals.
Run: python3 research/direction/representation_checks.py
"""

import json
from pathlib import Path
import random

import certified_mask_checks as subject


def rank_step(base, ranks, a, d, c):
    new_base, remainder = divmod(a*base+c,d)
    k = ranks[-1] if ranks else 0
    m = d-a
    if m*k <= d-1:
        deleted_rank = remainder//m+1
        # Rank zero is implicit and need not be stored or updated.
        result = [u-int(u>=deleted_rank) for u in ranks] if deleted_rank<=k else ranks[:]
    else:
        result = [u+(remainder-m*u)//d for u in ranks]
    return new_base,result


def independent_primitive_checks():
    rng = random.Random(20261108)
    entries = 0
    for _ in range(3000):
        d = rng.randrange(2,130)
        a = rng.randrange(1,d)
        width = rng.randrange(33)
        mask = rng.getrandbits(width)
        base = rng.randrange(-100,101)
        c = rng.randrange(-3*d,3*d+1)
        ranks = [(mask & ((1 << i)-1)).bit_count() for i in range(1,width+1)]
        new_base,new_ranks = rank_step(base,ranks,a,d,c)
        expected = [(a*(base+u)+c)//d for u in [0]+ranks]
        actual = [new_base]+[new_base+u for u in new_ranks]
        if expected != actual:
            raise AssertionError((base,ranks,a,d,c,expected,actual))
        entries += len(expected)
    return {"primitive_cases":3000,"primitive_entry_comparisons":entries}


def compare(rule,inputs,length,initial,precision):
    blocks = [inputs[i:i+length] for i in range(0,len(inputs),length)]
    certs,_,_ = subject.certificates(rule,blocks,initial,precision)
    checks = 0
    summaries = []
    mask_bits = rank_bits = max_width = merging_rank_slots = rank_slots = 0
    for block,(lo,hi,_,_) in zip(blocks,certs):
        width = hi-lo
        max_width = max(max_width,width)
        mask_bits += width
        rank_bits += width*width.bit_length()
        base,ranks = lo,list(range(1,width+1))
        literal = list(range(lo,hi+1))
        for x in block:
            old = ranks
            base,ranks = rank_step(base,ranks,rule.a,rule.d,rule.c(x))
            rank_slots += width
            if ranks != old:
                merging_rank_slots += width
            # Independent original recurrence applied to every literal candidate.
            literal = [(rule.a*s+rule.c(x))//rule.d for s in literal]
            if literal != [base]+[base+u for u in ranks]:
                raise AssertionError("Relative-rank map differs from literal trajectories")
            checks += len(literal)
        bitmap = subject.build_mask(rule,block,lo,hi)
        for i,expected in enumerate(literal):
            if subject.evaluate(bitmap,lo+i,lo,hi) != expected:
                raise AssertionError("Bitmap differs from relative-rank table")
            checks += 1
        summaries.append((base,ranks))
    entry,entries = initial,[]
    for (lo,hi,_,_),(base,ranks) in zip(certs,summaries):
        if not lo<=entry<=hi:
            raise AssertionError("Actual entry outside certificate")
        entries.append(entry)
        i = entry-lo
        entry = base+(ranks[i-1] if i else 0)
    replay = [x for block,entry in zip(blocks,entries) for x in subject.serial(rule,block,entry)]
    if replay != subject.serial(rule,inputs,initial):
        raise AssertionError("Relative-rank replay differs from serial")
    return {"max_certificate_width":max_width,
            "literal_entry_comparisons":checks,"replay_outputs":len(replay),
            "base_updates_each_representation":len(inputs),
            "mask_bits_all_blocks":mask_bits,
            "rank_bits_all_blocks_excluding_implicit_zero":rank_bits,
            "narrow_rank_lane_slots":rank_slots,
            "narrow_rank_lane_slots_on_merging_updates":merging_rank_slots,
            "cost_limit":"bits are representation payloads; narrow parallel lanes, rank/select, predictor and replay have unmeasured physical costs"}


def main():
    rng = random.Random(20261108)
    checks = independent_primitive_checks()
    rows = []
    for a,d,offset in ((15,16,0),(61,64,32),(63,64,32),(127,128,64),(97,100,0)):
        rule = subject.Rule(a,d,17,offset)
        for pattern in ("constant","one_tick_walk","uniform"):
            mid = rule.high//2
            price = mid
            inputs = []
            for _ in range(512):
                price=max(0,min(rule.high,price+rng.choice((-1,0,1))))
                inputs.append(mid if pattern=="constant" else price if pattern=="one_tick_walk"
                              else rng.randrange(rule.high+1))
            row=compare(rule,inputs,32,mid,29)
            row.update(A=a,D=d,offset=offset,state_bits=17,pattern=pattern)
            rows.append(row)
    checks["literal_entry_comparisons"]=sum(r["literal_entry_comparisons"] for r in rows)
    checks["replay_outputs"]=sum(r["replay_outputs"] for r in rows)
    out={"purpose":"Mandatory arithmetic-shared relative-rank baseline vs bitmap",
         "seed":20261108,"checks_passed":checks,"configurations":rows,
         "conclusion":"Both representations share one full-width base update per input and one input traversal. Bitmap advantage is a physical storage/timing question, not demonstrated by prior independent-trajectory work counts."}
    target=Path(__file__).with_name("representation_results.json")
    target.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"checks_passed":checks,"result_file":str(target)},indent=2))
    print("Width-63 representation payload: mask=63 bits; relative ranks=378 bits (implicit zero omitted)")


if __name__ == "__main__":
    main()

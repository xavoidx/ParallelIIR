#!/usr/bin/env python3
"""Independent adversarial oracle checks for certified_mask_checks.py.

Tables of every candidate output and Fraction recurrences supply expectations;
no deletion-rank equation supplies an expected mask. Small finite carry graphs
are explored to exhaustion, yielding an all-time check for those configurations.
This is an executable audit, not a general formal proof.
"""
from collections import deque
from fractions import Fraction
from itertools import product
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import certified_mask_checks as subject

ROOT = Path(__file__).parent
COUNTS = dict(primitive_cases=0, primitive_entries=0, traces=0, candidate_entries=0,
              rational_boundaries=0, replay_outputs=0, carry_graph_configs=0,
              carry_graph_states=0, carry_graph_edges=0)


def floor(x):
    return x.numerator // x.denominator


def ceil(x):
    return -floor(-x)


def step(rule, state, datum):
    # Literal integer evaluation, independent of the subject's step/c helper.
    # Exact unrounded expectations below use Fraction separately.
    return (rule.a * state + (rule.d-rule.a)*datum + rule.offset) // rule.d


def literal_trace(rule, tape, entry):
    values = []
    for datum in tape:
        entry = step(rule, entry, datum)
        values.append(entry)
    return values


def exact_affine(rule, tape):
    gain, offset = Fraction(1), Fraction(0)
    for datum in tape:
        gain *= Fraction(rule.a, rule.d)
        offset = Fraction(rule.a*offset+(rule.d-rule.a)*datum+rule.offset, rule.d)
    return gain, offset


def primitive_tables():
    for d in range(2, 9):
        for a in range(1, d):
            for width in range(7):
                for mask in range(1 << width):
                    positions = [(mask >> i) & 1 for i in range(width)]
                    for base, c in ((-d,-2*d),(-1,-1),(0,0),(d,d-1),(d,2*d)):
                        old = [base]
                        for increment in positions:
                            old.append(old[-1]+increment)
                        expected = [floor(Fraction(a*v+c,d)) for v in old]
                        expected_bits = [expected[i+1]-expected[i] for i in range(width)]
                        assert all(v in (0,1) for v in expected_bits)
                        new_base,new_mask,deletions = subject.advance_mask(base,mask,a,d,c)
                        assert new_base == expected[0]
                        assert [(new_mask>>i)&1 for i in range(width)] == expected_bits
                        assert deletions == sum(positions)-sum(expected_bits)
                        COUNTS['primitive_cases'] += 1
                        COUNTS['primitive_entries'] += len(expected)


def check_trace(rule,tape,length,initial,precision,group):
    blocks = [tape[i:i+length] for i in range(0,len(tape),length)]
    certs,_,_ = subject.certificates(rule,blocks,initial,precision,group)
    assert len(certs) == len(blocks)
    expected_trace = literal_trace(rule,tape,initial)
    q = 1 << precision
    z, entry, replay = Fraction(initial), initial, []
    for block,(lo,hi,zl,zu) in zip(blocks,certs):
        assert Fraction(zl,q) <= z <= Fraction(zu,q)
        assert 0 <= z-entry <= Fraction(rule.d-1,rule.d-rule.a)
        assert lo <= entry <= hi
        summary = subject.build_mask(rule,block,lo,hi)
        # Literal enumeration of EVERY legal candidate, independently of ranks.
        table = [literal_trace(rule,block,v)[-1] for v in range(lo,hi+1)]
        assert summary[0] == table[0]
        for i,v in enumerate(table):
            assert subject.evaluate(summary,lo+i,lo,hi) == v
        assert [(summary[1]>>i)&1 for i in range(hi-lo)] == [b-a for a,b in zip(table,table[1:])]
        own_replay = literal_trace(rule,block,entry)
        entry = subject.evaluate(summary,entry,lo,hi)
        assert entry == own_replay[-1]
        replay.extend(own_replay)
        for datum in block:
            z = Fraction(rule.a*z+(rule.d-rule.a)*datum+rule.offset,rule.d)
        COUNTS['candidate_entries'] += len(table)
        COUNTS['rational_boundaries'] += 1
    assert replay == expected_trace
    COUNTS['replay_outputs'] += len(tape)
    COUNTS['traces'] += 1


def traces():
    # Exhaust all three-event tapes, all initial states and every offset for
    # small denominators; varied block grouping includes non-power-of-two scans.
    for d in range(2,6):
        for a in range(1,d):
            for offset in range(d):
                r = subject.Rule(a,d,2,offset)
                for tape in product(range(4), repeat=3):
                    for initial in (0,3):
                        for precision,length,group in ((0,1,3),(1,1,2),(4,2,3)):
                            check_trace(r,tape,length,initial,precision,group)
    rng = random.Random(99154061)
    # Unequal blocks, partial final groups, offsets at endpoints, high retention,
    # tiny denominator, coarse scale and larger words, boundary-valued inputs.
    for _ in range(600):
        d = rng.choice((2,3,7,16,64,257,1000))
        a = rng.choice((1,d-1,rng.randrange(1,d)))
        bits = rng.choice((1,2,5,8))
        offset = rng.choice((0,d-1,rng.randrange(d)))
        r = subject.Rule(a,d,bits,offset)
        n,length = rng.randrange(1,42),rng.randrange(1,10)
        tape = [rng.choice((0,r.high,rng.randrange(r.high+1))) for _ in range(n)]
        precision = rng.choice((0,1,3,bits+8))
        check_trace(r,tape,length,rng.choice((0,r.high,rng.randrange(r.high+1))),precision,rng.choice((1,2,3,5,7)))
    # Wide-word/high-memory cases are explicit: arbitrary coarse precision with
    # thousands of deletions also exercises the deliberately slow select model,
    # rather than adding a distinct mathematical obligation.
    for r,precision in ((subject.Rule(999,1000,12,999),0),
                        (subject.Rule(65535,65536,32,65535),44)):
        check_trace(r,[0,r.high,0,r.high,0,r.high,0,r.high,0],4,r.high//2,precision,3)


def interval_apply(bounds,lo,hi,q):
    gl,gu,hl,hu=bounds
    return (floor(Fraction(gl*lo,q))+hl,ceil(Fraction(gu*hi,q))+hu)


def closed_carry_graph(rule,length,p,precision):
    """Explore the predictor's complete finite carry automaton, for all tapes.

    Subject interval maps are the system being checked. Their exact affine
    enclosures are checked with independent rational extrema at EVERY edge.
    Since every initial carry and every input label is included, closure gives
    an all-future-time result for this individual finite configuration.
    """
    q=1<<precision
    capacity=subject.uniform_capacity_bound(rule,length,p,precision)
    if not capacity['finite_carry_bound']:
        return
    pb=capacity['predictor_width_bound_exact']
    cb=capacity['carry_width_bound_exact']
    prefix_bound=Fraction(pb['numerator'],pb['denominator'])
    carry_bound=Fraction(cb['numerator'],cb['denominator'])
    labels=[]
    for tape in product(range(rule.high+1),repeat=length*p):
        blocks=[tape[i:i+length] for i in range(0,len(tape),length)]
        maps=[subject.affine_block(rule,b,q) for b in blocks]
        pre,_,_=subject.prefixes(maps,q)
        full=subject.compose(maps[-1],pre[-1],q)
        exact=[exact_affine(rule,tape[:i*length]) for i in range(p)]
        labels.append((pre,full,exact,exact_affine(rule,tape)))
    todo=deque((s*q,s*q) for s in range(rule.high+1))
    seen=set(todo)
    while todo:
        lo,hi=todo.popleft()
        for pre,full,expre,exfull in labels:
            for bounds,(g,h) in zip(pre,expre):
                zl,zu=interval_apply(bounds,lo,hi,q)
                assert Fraction(zl,q) <= g*Fraction(lo,q)+h
                assert g*Fraction(hi,q)+h <= Fraction(zu,q)
                assert Fraction(zu-zl,q) <= prefix_bound
                lower=max(0,ceil(Fraction(zl,q)-Fraction(rule.d-1,rule.d-rule.a)))
                upper=min(rule.high,floor(Fraction(zu,q)))
                assert upper-lower <= capacity['mask_width_cap']
            nxt=interval_apply(full,lo,hi,q)
            g,h=exfull
            assert Fraction(nxt[0],q) <= g*Fraction(lo,q)+h
            assert g*Fraction(hi,q)+h <= Fraction(nxt[1],q)
            assert Fraction(nxt[1]-nxt[0],q) <= carry_bound
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
            COUNTS['carry_graph_edges'] += 1
        assert len(seen)<100000, 'Unexpectedly large graph; audit bounds need adjustment'
    COUNTS['carry_graph_configs']+=1
    COUNTS['carry_graph_states']+=len(seen)
    return dict(a=rule.a,d=rule.d,bits=rule.bits,offset=rule.offset,length=length,
                p=p,fraction_bits=precision,reachable_carries=len(seen),labels=len(labels),
                mask_width_cap=capacity['mask_width_cap'])


def observations():
    # Diagnostic probes preserve evidence without requiring bugs to remain.
    probes={}
    for label, thunk in {
        'float_rule_accepted':lambda: repr(subject.Rule(0.5,2,3)),
        'out_of_domain_evaluation':lambda: subject.evaluate(subject.build_mask(subject.Rule(1,2,3),[0],2,3),4,2,3),
        'large_word_capacity':lambda: subject.uniform_capacity_bound(subject.Rule(1,2,1024),2,1,1),
        'zero_group_capacity':lambda: subject.uniform_capacity_bound(subject.Rule(1,2,3),1,0,3),
    }.items():
        try:
            probes[label]={'returned':thunk()}
        except Exception as exc:
            probes[label]={'exception':type(exc).__name__,'message':str(exc)}
    return probes


def optimized_api_regressions():
    code = '''
import certified_mask_checks as c
r=c.Rule(1,2,3)
cases=[lambda:c.Rule(0.5,2,3),lambda:c.evaluate(c.build_mask(r,[0],2,3),4,2,3),lambda:c.certificates(r,[[8]],0,3),lambda:c.uniform_capacity_bound(r,0,1,3),lambda:c.advance_mask(0,-1,1,2,0),lambda:c.evaluate(c.build_mask(r,[0],2,3),3,2,4),lambda:c.build_mask(c.Rule(1,2,17),[0],0,65537)]
for f in cases:
    try: f()
    except ValueError: pass
    else: raise RuntimeError('Invalid input accepted with assertions disabled')
x=c.uniform_capacity_bound(c.Rule(1,2,1024),2,1,1)
if x['predictor_width_bound_state_units'] is not None or not x['predictor_width_bound_exact']['numerator']>0:
    raise RuntimeError('Exact bound was lost to display overflow')
'''
    result=subprocess.run([sys.executable,'-O','-c',code],cwd=ROOT,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return {'interpreter_flags':['-O'],'invalid_inputs_rejected':7,'domain_substitution_rejected':True,
            'overlarge_allocation_rejected':True,'exact_overflow_display_check':True}


def main():
    source_hash=hashlib.sha256(Path(subject.__file__).read_bytes()).hexdigest()
    primitive_tables()
    print('primitive literal tables passed', flush=True)
    traces()
    print('exhaustive and randomized literal tapes passed', flush=True)
    graphs=[]
    for a,d in ((1,2),(1,3),(2,3),(3,4)):
        for offset in (0,d-1):
            for length,p,precision in ((1,1,2),(1,3,2),(2,2,3)):
                graph=closed_carry_graph(subject.Rule(a,d,1,offset),length,p,precision)
                if graph:
                    graphs.append(graph)
    out=dict(subject_sha256=source_hash,seed=99154061,checks_passed=COUNTS,
             exhaustive_closed_carry_graphs=graphs,api_observations=observations(),
             optimized_api_regressions=optimized_api_regressions(),
             limits='Finite configurations and finite exhaustive graphs; general proof obligations are in INDEPENDENT_MATH_AUDIT.md.')
    path=ROOT/'independent_audit_results.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'counts':COUNTS,'output':str(path),'api_observations':out['api_observations']},indent=2))


if __name__=='__main__':
    if not __debug__:
        raise SystemExit('Run audit checks without -O; API checks launch -O separately')
    main()

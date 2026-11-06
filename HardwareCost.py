from FilterSimulation import ParallelFilter
import math
import random
import statistics

def compute_latency(L, target_speedup, target_K):
    overhead = 2 # Constant overhead, at least 2 for smin and smax passes
    W = target_K + overhead + 1
    P = target_speedup * W
    latency = int(L * P)
    
    return latency, P    

def block_length(a_num, a_den, bits, max_L=100000, max_K=1000):
    for K in range(0, max_K):
        g = 2**bits - 1
        for L in range(1, max_L):
            g = -(-a_num * g // a_den)   # ceil(a*g) in integer arithmetic
            if g <= K:
                return L, K
    return None

def ComputeHardwareCost(P, target_K): # Need to get better understanding of RTL first
    return

a_num = 63
a_den = 64
target_speedup = 1.5
bits = 16

L, K = block_length(a_num, a_den, bits)
print(f"Latency = {compute_latency(L, target_speedup, K)[0]} samples\nK = {K}")

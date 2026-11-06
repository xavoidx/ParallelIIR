from FilterSimulation import ParallelFilter
import math
import random
import statistics

filter16bit = ParallelFilter(0.5, latency=702, L=36, bits=16)
K_values = []
input_length = 702
a_values = [3/4]

TestSignals16Bit = []

'''
N = 32
for i in range(0, N+1):
    # Includes silence (N = 32)
    sig = [int(math.sin(math.pi * x * i / N) * 2**15) for x in range(input_length)]
    TestSignals16Bit.append(sig)
'''


#Full scale DC inputs
TestSignals16Bit.append([2**15-1] * input_length)
TestSignals16Bit.append([-(2**15)] * input_length)

#Random Signal
num_rand = 10
for _ in range(num_rand):
    sig = [int(random.random() * 2**15) for _ in range(input_length)] 
    TestSignals16Bit.append(sig)

for a in a_values:
    filter16bit.a = a
    for signal in TestSignals16Bit:
        print(signal)
        K_values.append(filter16bit.computeOutputs(signal)[1])

print(f"Max threshold count: {max(K_values)}\n" +
        f"Mean threshold count: {statistics.mean(K_values)}\n" +
        f"Median threshold count: {statistics.median(K_values)}")
from FilterSimulation import ParallelFilter
import math
import random


filter4bit = ParallelFilter(0.5, 4, 4)

a_values = [63/64, 127/128, 255/256, 511/512]
Test4Bit = False
Test16Bit = True

#Exhaustive test of 4-Bit inputs
k = 15 #Input range
Num_inputs = 4
Passed = True
if Test4Bit:
    for a in a_values:
        filter4bit.a = a
        iteration = 0
        for i in range(k**Num_inputs):
            iteration += 1
            input = []
            x = i
            for _ in range(Num_inputs):
                x, d = divmod(x, 15)
                input.append(d-8)
            _, y_serial = filter4bit.serialPass(input)
            y_parallel, _ = filter4bit.computeOutputs(input)
            if y_serial != y_parallel:
                print(f"FAIL:\n input: {input}\n" + 
                f"Serial output: {y_serial}\n" + 
                f"Parallel output: {y_parallel}\n" +
                f"a = {a}\n" +
                f"Iteration {iteration}\n")
                Passed = False
            if not Passed:
                break


filter16bit = ParallelFilter(0.5, 4, 16)

#Sines at w = pi/8, pi/4, 3pi/8, etc.
if Test16Bit:
    for input_length in range(20, 30):
        TestSignals16Bit = []
        N = 256
        for i in range(0, N+1):
            sig = [int(math.sin(math.pi * x * i / N) * 2**15) for x in range(input_length)]
            TestSignals16Bit.append(sig)

        #Full scale DC inputs
        TestSignals16Bit.append([2**15-1] * input_length)
        TestSignals16Bit.append([-(2**15)] * input_length)

        #Random Signal
        num_rand = 100
        for _ in range(num_rand):
            sig = [int(random.random() * 2**15) for _ in range(input_length)] 
            TestSignals16Bit.append(sig)
        
        for a in a_values:
            filter16bit.a = a
            for signal in TestSignals16Bit:
                _, y_serial = filter16bit.serialPass(signal)
                y_parallel, _ = filter16bit.computeOutputs(signal)
                if y_serial != y_parallel:
                    print(f"FAIL:\n input: {signal}\n" + 
                    f"Serial output: {y_serial}\n" + 
                    f"Parallel output: {y_parallel}\n" +
                    f"a = {a}\n")
                    Passed = False

if Passed:
    print("All inputs passed.")

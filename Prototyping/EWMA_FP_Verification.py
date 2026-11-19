from FilterSimulation import ParallelFilter

pf = ParallelFilter(61/64, 0, 0, 16)

inputs = [0x0401, 0x0402, 0x0403, 0x0404, 0x0405, 0x0406, 0x0407, 0x0408]

y = pf.serialPassEWMA_FP(inputs, 0x10)

for out in y:
    print(f"{hex(out)}, ", end="")
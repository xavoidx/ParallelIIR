import numpy as np
import math

class ParallelFilter:
    def __init__(self, a, P, bits):
        self.P = P
        self.a = a
        self.bits = bits
        self.maxState = 2**(bits-1)-1 
        self.minState = -1 * 2**(bits-1)

    def serialPass(self, x: list, s_0: int = 0):
            state = s_0
            y = []
            for input in x:
                state = max(-8, min(7, math.floor(self.a * state) + int(input)))
                y.append(state)
            output_state = state

            return output_state, y 
    
    def computeOutputs(self, x: list):
        x_np = np.array(x)
        blocks = np.array_split(x_np, self.P)
        kMaps = []
        y = []

        KMaps = [None] * len(blocks)
        smins = [None] * len(blocks)
        entry_states = [None] * len(blocks)

        # NOTE: separating which iterations over blocks
        #       can be done in parallel and which must be 
        #       done serially.

        #PARALLEL
        for i in range(0, len(blocks)):
            KMaps[i], smins[i], smax = self.buildKMap(blocks[i])

        #SERIAL
        exit_state = 0
        for i in range(0, len(blocks)):
            entry_states[i] = exit_state
            thresholds = KMaps[i].values()
            threshold_count = 0
            for threshold in thresholds:
                if entry_states[i] >= threshold:
                    threshold_count += 1
            exit_state = smins[i] + threshold_count

        #PARALLEL
        for i in range(0, len(blocks)):
            y.extend(self.serialPass(blocks[i], s_0=entry_states[i])[1])

        return y


    def buildKMap(self, block: np.ndarray):
        KMap = {}
        smin = self.serialPass(block, s_0=self.minState)[0]
        smax = self.serialPass(block, s_0=self.maxState)[0]
        K = smax - smin
        for threshold in range(smax, smin, -1):
            prev_state = threshold
            for input in block[::-1]:
                prev_state = math.ceil((prev_state - input) / self.a)
            KMap[threshold] = int(prev_state)
        return KMap, smin, smax


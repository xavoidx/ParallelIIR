## Basic Outline of Chain

Input enters and is buffered according to some adjustable parameters that determine block length, block count, which then determines the latency of the system. This latency needs to be characterized based on the clock rate, but we will save that for later. 

The serial case runs at some fixed loop delay, t_loop, where it can only pump out 1/t_loop samples per second, regardless of how much hardware you add. This is the figure we are trying to beat. With some latency cost, we are trying to see if we can have throughput > 1/t_loop through parallelism. 

The equation L ~= tau * ln(R / K), with tau ~= 1/(1-a), characterizes the required block length for some target number of thresholds K, but is an estimation that is only accurate for larger a. Tau is the time constant of this one pole filter, and thus for low corner frequencies, our a value will be relatively close to one, and tau will be a big number, requiring a greater block size. 

We can then characterize the work W (clock cycles per sample in the length L computed) as W = c + K + 1, with the total chain speedup being P / W. c represents constant overhead that doesn't scale with K, and is ~2-3 samples. It is at least 2 due to the min and max passes, maybe 3 due to some extra implementation-specific overhead. The +1 represents the one replay pass. 

This means our latency in seconds is L(P + c + K + 1) * T_s, where P is the number of parallel blocks (where the parallel speedup comes from), and T_s is the sampling period. Thus, we want to keep L low for latency, but we also want to keep K low, as more thresholds means more work needs to be done per block before we can replay them. Each threshold requires its own pass through the block. 

Essentially, we want to have P as high as possible, but that either creates more latency or reduces L---reducing L means increasing K, increasing the work done per sample. The goal here is to find a sweet spot. 
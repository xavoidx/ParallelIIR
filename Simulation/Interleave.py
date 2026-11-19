from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def InterleaveStream(input_file: str, output_file: str, P: int, L: int):
    f_out = []
    input_file = SCRIPT_DIR / input_file
    output_file = SCRIPT_DIR / output_file
    with open(input_file, "r", encoding="utf-8") as file:
        f_interleaved = [[] for _ in range(L)]
        idx = 0

        for line in file:
            f_interleaved[idx % L].append(line.rstrip('\n'))
            idx += 1
            if idx == L * P:
                idx = 0
                for list in f_interleaved:
                    f_out.extend(list)
                f_interleaved = [[] for _ in range(P)]
        for list in f_interleaved:
            f_out.extend(list)

    with open(output_file, "w") as file:
        for input in f_out:
            file.write(input)
            file.write("\n")

P = 4
L = 3

InterleaveStream("test.txt", "testOut.txt", P, L)

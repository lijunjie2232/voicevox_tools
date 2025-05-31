from Compressor import Compressor
from multiprocessing.pool import ThreadPool as Pool
from pathlib import Path
from itertools import repeat
from tqdm import tqdm


def compress(args):
    input, output, compressor = args
    compressor.compress(input, output)
    return 0


if __name__ == "__main__":
    compressor = Compressor()
    ROOT = Path(__file__).parent.resolve()
    dir = ROOT / "../output"
    files = list(dir.glob("*.wav"))
    with Pool(processes=4) as pool:
        result = pool.imap(
            compress,
            zip(
                files,
                repeat(dir),
                repeat(compressor),
            ),
        )
        for _ in tqdm(result, total=len(files), desc="compress"):
            pass

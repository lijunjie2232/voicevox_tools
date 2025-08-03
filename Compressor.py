from pydub import AudioSegment
from pathlib import Path


class Compressor:
    def __init__(self, out_fmt="mp3", bitrate="64k"):
        self.out_fmt = out_fmt
        self.bitrate = bitrate

    def compress(
        self,
        data=None,
        in_file=None,
        out_file=None,
        overwrite=False,
    ):
        sound = None
        assert out_file, "out_file is not specified"
        out_file = Path(out_file)
        assert out_file.parent.exists(), f"{out_file.parent} is not found"
        if isinstance(data, bytes):
            sound = AudioSegment(data)
        elif isinstance(in_file, Path) or isinstance(in_file, str):
            sound = AudioSegment.from_wav(in_file)
        else:
            raise ValueError("data or in_file is not valid")
        if out_file.is_dir() and in_file is not None:
            out_file = out_file / f"{in_file.stem}.{self.out_fmt}"
        if out_file.is_file() and not overwrite:
            return
        sound.export(out_file, format=self.out_fmt, bitrate=self.bitrate)


if __name__ == "__main__":
    c = Compressor()
    c.compress("output.wav", "output.mp3")

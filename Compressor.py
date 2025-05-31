from pydub import AudioSegment
from pathlib import Path


class Compressor:
    def __init__(self, out_fmt="mp3", bitrate="64k"):
        self.out_fmt = out_fmt
        self.bitrate = bitrate

    def compress(self, in_file, out, overwrite=False):
        if Path(out).is_dir():
            out = out / f"{in_file.stem}.{self.out_fmt}"
        if Path(out).is_file() and not overwrite:
            return
        sound = AudioSegment.from_wav(in_file)
        sound.export(out, format=self.out_fmt, bitrate=self.bitrate)


if __name__ == "__main__":
    c = Compressor()
    c.compress("output.wav", "output.mp3")

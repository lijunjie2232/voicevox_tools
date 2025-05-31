from pydub import AudioSegment


class Compressor:
    def __init__(self, out_fmt="mp3", bitrate="64k"):
        self.out_fmt = out_fmt
        self.bitrate = bitrate

    def compress(self, in_file, out_file):
        sound = AudioSegment.from_wav(in_file)
        sound.export(out_file, format=self.out_fmt, bitrate=self.bitrate)


if __name__ == "__main__":
    c = Compressor()
    c.compress("output.wav", "output.mp3")

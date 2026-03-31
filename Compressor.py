from pydub import AudioSegment
from pathlib import Path
import subprocess


class Compressor:
    def __init__(self, out_fmt="mp3", bitrate="32k", sample_rate="22050", channels=1):
        """
        Initialize audio compressor with optimized settings for small file size.
        
        Args:
            out_fmt: Output format (default: mp3)
            bitrate: Bitrate in kbps (default: 32k, lower = smaller file)
            sample_rate: Sample rate in Hz (default: 22050, speech-optimized)
            channels: Number of channels (default: 1 for mono, best for speech)
        """
        self.out_fmt = out_fmt
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.channels = channels

    def compress(
        self,
        data=None,
        in_file=None,
        out_file=None,
        overwrite=False,
        use_ffmpeg_optimized=False,
    ):
        """
        Compress audio file with optional ffmpeg optimization.
        
        Args:
            data: Audio data in bytes
            in_file: Input audio file path
            out_file: Output audio file path
            overwrite: Whether to overwrite existing file
            use_ffmpeg_optimized: Use ffmpeg with VBR for better compression (recommended)
        """
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
        
        # Use ffmpeg with VBR for better compression if available
        if use_ffmpeg_optimized and self.out_fmt == "mp3":
            try:
                self._compress_with_ffmpeg(sound, out_file)
                return
            except Exception as e:
                print(f"FFmpeg compression failed, falling back to pydub: {e}")
        
        # Fallback to pydub compression
        sound.export(
            out_file, 
            format=self.out_fmt, 
            bitrate=self.bitrate,
            parameters=[
                "-ar", str(self.sample_rate),  # Sample rate
                "-ac", str(self.channels),     # Channels (mono for speech)
            ]
        )
    
    def _compress_with_ffmpeg(self, sound, out_file):
        """
        Use ffmpeg with VBR (Variable Bit Rate) for optimal compression.
        This produces much smaller files while maintaining good quality for speech.
        """
        # Create a temporary wav file
        temp_wav = out_file.with_suffix(".tmp.wav")
        sound.export(temp_wav, format="wav")
        
        # FFmpeg command with VBR for MP3
        # -q:a 0-9 where 0 is best quality (highest bitrate), 9 is worst (lowest)
        # q:a 4 gives good quality speech at ~32-64kbps average
        # q:a 5-6 gives smaller files (~16-32kbps) still good for speech
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_wav),
            "-vn",  # No video
            "-acodec", "libmp3lame",  # MP3 codec
            "-q:a", "5",  # VBR quality level (4-6 recommended for speech)
            "-ar", str(self.sample_rate),  # Sample rate
            "-ac", str(self.channels),  # Mono channel
            str(out_file)
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        finally:
            # Clean up temp file
            if temp_wav.exists():
                temp_wav.unlink()
    
    def set_quality(self, quality="small"):
        """
        Set predefined quality presets.
        
        Args:
            quality: 'tiny' (16k), 'small' (24k), 'medium' (32k), 'high' (64k)
        """
        presets = {
            "tiny": {"bitrate": "16k", "sample_rate": "16000", "q": "7"},
            "small": {"bitrate": "24k", "sample_rate": "22050", "q": "5"},
            "medium": {"bitrate": "32k", "sample_rate": "22050", "q": "4"},
            "high": {"bitrate": "64k", "sample_rate": "44100", "q": "2"},
        }
        
        if quality in presets:
            preset = presets[quality]
            self.bitrate = preset["bitrate"]
            self.sample_rate = preset["sample_rate"]
            self.ffmpeg_q = preset["q"]
        else:
            raise ValueError(f"Unknown quality preset: {quality}")


if __name__ == "__main__":
    c = Compressor()
    # Test different quality settings
    print("Testing compression with different quality levels...")
    
    test_file = "output.wav"
    if Path(test_file).exists():
        for quality in ["tiny", "small", "medium", "high"]:
            c.set_quality(quality)
            output_file = f"output_{quality}.mp3"
            c.compress(test_file, output_file, use_ffmpeg_optimized=True)
            size = Path(output_file).stat().st_size / 1024  # KB
            print(f"{quality}: {size:.1f} KB")
    else:
        c.compress("output.wav", "output.mp3")

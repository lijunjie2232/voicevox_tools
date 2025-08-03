from PyPDF2 import PdfReader
from pathlib import Path
import os
import re
from pprint import pprint
from tqdm import tqdm
from VoicevoxEngine import VoicevoxEngine
from Compressor import Compressor
import json
import genanki

_SPEAKER_IDS = [13, 23]
_COMPRESSOR = Compressor()

# init voicevox engine
_ENGINE = VoicevoxEngine("http://127.0.0.1:9817")
for speaker_id in _SPEAKER_IDS:
    _ENGINE.speaker_init(
        speaker=speaker_id,
    )
with open("params_hook.json", "r", encoding="utf-8") as f:
    _params_hook = json.load(f)


def line_handle(line):
    line = line.strip()
    while line and line[-1].isdigit():
        line = line[:-1].strip()
    return line.strip()


def post_handle(text, count):
    results = text.split("Ａ：")
    target = results[1]
    a, b = target.split("Ｂ：")

    a = "".join(
        list(
            filter(
                lambda x: x,
                [line_handle(i) for i in a.strip().split("\n")],
            )
        )[::2]
    )
    b = "".join(
        list(
            filter(
                lambda x: x,
                [line_handle(i) for i in b.strip().split("\n")],
            )
        )[::2]
    )
    a = a.strip()
    b = b.strip()

    return Kaiwa(count, a, b)


class Kaiwa:
    def __init__(self, hash, a, b, speaker_ids=(13, 23)):
        self.hash = str(hash).rjust(8, "0")
        self.a = a
        self.b = b
        self.wav_a = {}
        self.wav_b = {}
        self.speaker_ids = speaker_ids
        self.init_wav()

    def init_wav(self):
        for speaker_id in self.speaker_ids:
            self.wav_b[speaker_id] = _ENGINE.tts(
                speaker=speaker_id,
                text=self.b,
                params_hook=(
                    _params_hook[str(speaker_id)] if speaker_id in _params_hook else {}
                ),
            )
            self.wav_a[speaker_id] = _ENGINE.tts(
                speaker=speaker_id,
                text=self.a,
                params_hook=(
                    _params_hook[str(speaker_id)] if speaker_id in _params_hook else {}
                ),
            )

    def to_mp3(self, output_dir):
        output_dir = Path(output_dir)
        for speaker_id in self.speaker_ids:
            wav_a = self.wav_a[speaker_id]
            wav_b = self.wav_b[speaker_id]
            Compressor().compress(
                data=wav_a,
                out_file=f"{output_dir}/{self.hash}_{speaker_id}_a.mp3",
            )
            Compressor().compress(
                data=wav_b,
                out_file=f"{output_dir}/{self.hash}_{speaker_id}_b.mp3",
            )


if __name__ == "__main__":
    import pdfplumber

    page_list = [
        [16, 46],
        [60, 90],
    ]
    page_index = []
    for i in page_list:
        page_index.extend(list(range(i[0], i[1])))

    count = 0

    ROOT = Path(__file__).parent.resolve()
    wav_dir = ROOT / "wav"
    wav_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = genanki.Model(
        "1603374340",
        "Picture Card",
        fields=[
            {"name": "FrontImage"},
            {"name": "BackImage"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{FrontImage}}",
                "afmt": "{{BackImage}}",
            },
        ],
    )
    deck_id = 2059401230
    deck = genanki.Deck(deck_id, "話せる300")
    media_files = []
    ctx = """%s<h1>%s</h1><br>[sound:%s]"""

    with pdfplumber.open(ROOT / "pdf" / "hanaseru300.pdf") as pdf:
        for idx in tqdm(page_index):
            text = pdf.pages[idx].extract_text()
            count += 1
            kaiwa = post_handle(text, count)
            kaiwa.to_mp3(wav_dir)
            speaker_1 = _SPEAKER_IDS[0]
            speaker_2 = _SPEAKER_IDS[1]

            media_files.append(f"{wav_dir}/{kaiwa.hash}_{speaker_1}_a.mp3")
            media_files.append(f"{wav_dir}/{kaiwa.hash}_{speaker_2}_b.mp3")
            media_files.append(f"{wav_dir}/{kaiwa.hash}_{speaker_2}_a.mp3")
            media_files.append(f"{wav_dir}/{kaiwa.hash}_{speaker_1}_b.mp3")

            note = genanki.Note(
                model=model,
                fields=[
                    ctx
                    % (
                        "A: ",
                        kaiwa.a,
                        f"{kaiwa.hash}_{speaker_1}_a.mp3",
                    ),
                    ctx
                    % (
                        "B: ",
                        kaiwa.b,
                        f"{kaiwa.hash}_{speaker_2}_b.mp3",
                    ),
                ],
            )
            deck.add_note(note)
            
            note = genanki.Note(
                model=model,
                fields=[
                    ctx
                    % (
                        "A: ",
                        kaiwa.a,
                        f"{kaiwa.hash}_{speaker_2}_a.mp3",
                    ),
                    ctx
                    % (
                        "B: ",
                        kaiwa.b,
                        f"{kaiwa.hash}_{speaker_1}_b.mp3",
                    ),
                ],
            )
            deck.add_note(note)
    
    # 生成APKG文件
    my_package = genanki.Package(deck)
    my_package.media_files = media_files
    my_package.write_to_file(ROOT / "hanaseru300.apkg")
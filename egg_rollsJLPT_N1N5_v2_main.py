import argparse
from VoicevoxEngine import VoicevoxEngine
from pathlib import Path
from tqdm import tqdm
from pprint import pprint
import genanki
import json


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base_url",
        type=str,
        default="http://localhost:50021",
        help="base url of Voicevox Engine",
    )
    parser.add_argument(
        "--txt_dir",
        type=str,
        default="txt",
        help="a dir contains txt file(s)",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="output",
        help="output directory",
    )
    parser.add_argument(
        "--speaker_name",
        type=str,
        default="",  # WhiteCUL
        help="speaker name",
    )
    parser.add_argument(
        "--speaker_style",
        type=str,
        default="",  # ノーマル
        help="speaker style name",
    )
    parser.add_argument(
        "--speaker_id",
        type=int,
        default=-1,  # 23
        help="speaker id",
    )
    parser.add_argument(
        "--speaker_ids",
        nargs="+",
        default=[],  # 23
        help="speaker ids",
    )
    parser.add_argument(
        "--speaker_uuid",
        type=str,
        default="",  # 67d5d8da-acd7-4207-bb10-b5542d3a663b
        help="speaker uuid",
    )
    parser.add_argument(
        "--exact_name",
        action="store_true",
        help="query speaker name by exact match",
    )
    parser.add_argument(
        "--query_only",
        action="store_true",
        help="query speaker info only",
    )
    parser.add_argument(
        "--model_id",
        type=int,
        default=1607362319,
        help="model id of anki",
    )
    parser.add_argument(
        "--deck_id",
        type=int,
        default=2059400510,
        help="model id of anki",
    )

    args, extra_params = parser.parse_known_args()
    params_hook = {}
    for i in range(0, len(extra_params), 2):
        if i + 1 >= len(extra_params):
            raise ValueError("Unmatched argument provided.")
        key = extra_params[i].lstrip("-")
        value = extra_params[i + 1]
        params_hook[key] = value
    return args, params_hook


def print_speaker_styles(speaker_styles):
    for sss in speaker_styles:

        print(f"********************** {sss.name} **********************")
        print(f"speaker_uuid: {sss.speaker_uuid}")
        print("----------------------- styles -----------------------")
        pprint(sss.styles)
        print("----------------- supported features -----------------")
        pprint(sss.supported_features)
        print("------------------------------------------------------")
        print(f"version: {sss.version}")
        print()


class WordCache:
    def __init__(self, path):
        self.path = Path(path)
        self.cache = {}
        self.count = -1
        self.just_long = 16
        self.init()

    def init(self):
        if self.path.is_file():
            with open(self.path, "r") as f:
                data = json.load(f)
                self.cache = data["cache"]
                self.count = data["count"]

    def get_id(self, key):
        if key not in self.cache:
            self.count += 1
            self.cache[key] = str(self.count).rjust(self.just_long, "0")
        return self.cache[key]

    def to_dict(self):
        return {"cache": self.cache, "count": self.count}

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)


def main(args, params_hook):
    # init voicevox engine
    engine = VoicevoxEngine(base_url=args.base_url)
    # get args
    cache_dir = Path(args.out_dir)
    word_cache_file = cache_dir / "words.json"
    txt_dir = Path(args.txt_dir)
    assert txt_dir.is_dir(), "txt_dir is not found"
    cache_dir.mkdir(parents=True, exist_ok=True)

    speaker_uuid = args.speaker_uuid
    speaker_name = args.speaker_name
    speaker_id = args.speaker_id
    speaker_ids = args.speaker_ids

    # init speaker id
    if speaker_id < 0 and not speaker_ids:  # get speaker_id first
        if not speaker_uuid and not speaker_name:
            if args.query_only:
                speakers = engine.speakers
                # pprint(speakers)
                print_speaker_styles(speakers)
                return
            else:
                raise ValueError(
                    "speaker_uuid or speaker_name must be provided or specify query_only."
                )
        else:
            print("----------- match by -----------")
            print(f"speaker uuid: {speaker_uuid}")
            print(f"speaker name: {speaker_name}")
            print(f"exactly match: {args.exact_name}")
            print("--------------------------------")
            speaker_styles = engine.get_speaker_style(
                speaker_uuid=speaker_uuid,
                name=speaker_name,
                amb_match=not args.exact_name,
            )
            if len(speaker_styles) == 0:
                print("no matched speaker found.")
                return
            print_speaker_styles(speaker_styles)
            if args.query_only:
                return
            speaker_ids = [
                int(i)
                for i in input(
                    "Press specify speaker id to continue, if more than one, split with ',': "
                ).split(",")
            ]
    elif speaker_id > 0:
        speaker_ids = [speaker_id]

    # 创建一个模型
    model_id = args.model_id
    deck_id = args.deck_id
    word_cache = WordCache(word_cache_file)

    target_tags = [
        "N5",
        "N4",
        "N3",
        "N2",
        "N1",
        "オノマトペ",
        "外",
        "N4N5真题词汇补充",
    ]
    model = genanki.Model(
        model_id,
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
    decks = [
        genanki.Deck(deck_id + idx, f"JLPT単語::{tag}")
        for idx, tag in enumerate(target_tags)
    ]
    media_files = []

    for speaker_id in speaker_ids:
        engine.speaker_init(
            speaker=speaker_id,
        )
        print(f"init speaker: {speaker_id}")

    a_ctx = """[sound:%s]""" * len(speaker_ids)
    b_ctx = """<h1>%s</h1><br>"""

    for idx, target_tag in enumerate(tqdm(target_tags, desc="generate anki tag")):
        deck = decks[idx]
        words = []
        with open(txt_dir / f"{target_tag}.txt", "r", encoding="utf-8") as f:
            words = f.read().strip().split("\n")
            for line in f:
                words.append(line.strip())
            for word in tqdm(words, desc="generate anki words"):
                file_name = word_cache.get_id(word)
                resources = []
                for speaker_id in speaker_ids:
                    file_path = cache_dir / f"{file_name}_{speaker_id}.wav"
                    if not file_path.is_file():
                        engine.tts(
                            speaker=speaker_id,
                            text=word,
                            params_hook=params_hook,
                            output=file_path,
                        )
                    assert file_path.is_file(), "file generates error"
                    resources.append(file_path.name)
                    media_files.append(file_path.__str__())
                resources = tuple(resources)
                a = a_ctx % resources
                b = b_ctx % word + a
                note = genanki.Note(
                    model=model,
                    fields=[
                        a,
                        b,
                    ],
                    tags=[target_tag],
                )
                deck.add_note(note)
        word_cache.save()
    # 生成APKG文件
    my_package = genanki.Package(decks)
    my_package.media_files = media_files
    my_package.write_to_file("mn_cards.apkg")


if __name__ == "__main__":
    args, params_hook = get_args()
    main(args, params_hook)

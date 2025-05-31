import argparse
from VoicevoxEngine import VoicevoxEngine
from pathlib import Path
from tqdm import tqdm
from pprint import pprint
import genanki
import json
from Compressor import Compressor


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base_url",
        type=str,
        default="http://localhost:50021",
        help="base url of Voicevox Engine",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="txt",
        help="txt file or dir contains txt file(s)",
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
        "--params_hook",
        type=str,
        default="params_hook.json",
        help="specified json path to load params hook from file",
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

    return parser.parse_args()


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
        self.just_long = 6
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


def main(args):
    # init voicevox engine
    engine = VoicevoxEngine(base_url=args.base_url)
    # get args
    cache_dir = Path(args.out_dir)
    word_cache_file = cache_dir / "voice_cache.json"
    txt_file = Path(args.input)
    assert txt_file.exists(), f"{txt_file.absolute()} is not found"
    cache_dir.mkdir(parents=True, exist_ok=True)

    params_hook = {}
    try:
        print(f"try to load params hook from  {args.params_hook}")
        with open(args.params_hook, "r", encoding="utf-8") as f:
            params_hook = json.load(f)
    except FileNotFoundError:
        print(f"{args.params_hook} is not found")
    except json.JSONDecodeError:
        print(f"{args.params_hook} is not valid json")
    except Exception as e:
        print(f"load params hook failed: {e}")
    print("params hook:")
    pprint(params_hook)
    

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
    else:
        speaker_ids = [int(i) for i in speaker_ids]

    word_cache = WordCache(word_cache_file)

    compressor = Compressor()

    for speaker_id in speaker_ids:
        engine.speaker_init(
            speaker=speaker_id,
        )
        print(f"init speaker: {speaker_id}")

    txt_files = [txt_file]
    if txt_file.is_dir():
        txt_files = list(txt_file.glob("*.txt"))

    return
    for txt_file in tqdm(txt_files):
        with open(
            txt_file,
            "r",
            encoding="utf-8",
        ) as f:
            words = f.read().strip().split("\n")
            for word in tqdm(
                words,
                desc="generate voice",
                leave=False,
            ):
                file_name = word_cache.get_id(word)
                for speaker_id in speaker_ids:
                    file_path = cache_dir / f"{file_name}_{speaker_id}.wav"
                    cfile_path = cache_dir / f"{file_path.stem}.mp3"
                    if not file_path.is_file():
                        engine.tts(
                            speaker=speaker_id,
                            text=word,
                            params_hook=(
                                params_hook[str(speaker_id)]
                                if speaker_id in params_hook
                                else {}
                            ),
                            output=file_path,
                        )
                    assert file_path.is_file(), "file generates error"
                    if not cfile_path.is_file():
                        compressor.compress(file_path, cfile_path)
                    assert cfile_path.is_file(), "compressed file generates error"
        word_cache.save()


if __name__ == "__main__":
    args = get_args()
    main(args)

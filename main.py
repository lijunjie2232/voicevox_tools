import argparse
from VoicevoxEngine import VoicevoxEngine
from pathlib import Path
from tqdm import tqdm
from pprint import pprint


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base_url",
        type=str,
        default="http://localhost:50021",
        help="base url of Voicevox Engine",
    )
    parser.add_argument(
        "--txt",
        type=str,
        default="sample.txt",
        help="input file of word list in txt format",
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
        "--speaker_uuid",
        type=str,
        default="",  # 67d5d8da-acd7-4207-bb10-b5542d3a663b
        help="speaker uuid",
    )
    parser.add_argument(
        "--query_only",
        action="store_true",
        help="query speaker info only",
    )

    args, extra_params = parser.parse_known_args()
    hook_params = {}
    for i in range(0, len(extra_params), 2):
        if i + 1 >= len(extra_params):
            raise ValueError("Unmatched argument provided.")
        key = extra_params[i].lstrip("-")
        value = extra_params[i + 1]
        hook_params[key] = value
    return args, hook_params

def main(args, hook_params):
    engine = VoicevoxEngine(base_url=args.base_url)
    out_dir = Path(args.out_dir)
    txt_file = Path(args.txt)
    speaker_uuid = args.speaker_uuid
    speaker_name = args.speaker_name
    speaker_id = args.speaker_id
    if speaker_id < 0:  # get speaker_id first
        if not speaker_uuid and not speaker_name:
            if args.query_only:
                speakers = engine.speakers
                pprint(speakers)
                return
            else:
                raise ValueError(
                    "speaker_uuid or speaker_name must be provided or specify query_only."
                )
        else:
            speaker_styles = speakers.get_speaker_style(
                speaker_uuid=speaker_uuid,
                speaker_name=speaker_name,
            )
            if len(speaker_styles) == 0:
                ValueError("speaker_uuid or speaker_name is not found.")
                return
            if args.query_only:
                pprint(speaker_styles)
                return
            if len(speaker_styles) > 1:
                # pprint(speaker_styles)
                # pprint("speaker_uuid or speaker_name is ambiguous.")
                # speaker_id = int(input("Press specify speaker id to continue: "))
                for ss in speaker_styles:
                    print("**********************************")
                    print(f"name: {ss.name}")
                    print(f"speaker_uuid: {ss.speaker_uuid}")
                    print("------------- styles -------------")
                    pprint(ss.styles)
                    print("------- supported features -------")
                    pprint(ss.supported_features)
                    print("----------------------------------")
                    print(f"version: {ss.version}")
                    print("**********************************")
            else:
                speaker_id = speaker_styles[0]


if __name__ == "__main__":
    args, hook_params = get_args()
    main(args, hook_params)

import re
import argparse
from VoicevoxEngine import VoicevoxEngine
from pathlib import Path
from pprint import pprint
import json
from Compressor import Compressor
from copy import deepcopy
import uuid
import logging

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
        default="input.jsonl",
        help="input jsonl file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.jsonl",
        help="output jsonl file with audio_files field",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="output_audio",
        help="output directory for audio files",
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
    parser.add_argument(
        "--compress",
        action="store_true",
        help="compress audio files to mp3",
    )

    return parser.parse_args()


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)


def validate_jsonl_file(file_path):
    """Validate JSONL file and return valid lines and errors."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    valid_lines = []
    errors = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
            valid_lines.append((line_num, line, entry))
        except json.JSONDecodeError as e:
            errors.append({
                "line_num": line_num,
                "error": f"Invalid JSON: {str(e)}",
                "content": line[:100] + "..." if len(line) > 100 else line
            })
    
    return valid_lines, errors


def print_speaker_styles(speaker_styles, logger=None):
    if logger is None:
        logger = setup_logging()
    
    for sss in speaker_styles:
        logger.info(f"********************** {sss.name} **********************")
        logger.info(f"speaker_uuid: {sss.speaker_uuid}")
        logger.info("----------------------- styles -----------------------")
        pprint(sss.styles)
        logger.info("----------------- supported features -----------------")
        pprint(sss.supported_features)
        logger.info("------------------------------------------------------")
        logger.info(f"version: {sss.version}")
        logger.info("")


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
    logger = setup_logging()
    
    # Print header
    logger.info("="*60)
    logger.info("Voicevox TTS JSONL Processor")
    logger.info("="*60)
    logger.info("")
    
    # init voicevox engine
    logger.info("[1/5] Initializing Voicevox Engine...")
    logger.info(f"     Base URL: {args.base_url}")
    engine = VoicevoxEngine(base_url=args.base_url)
    logger.info("     ✓ Engine initialized successfully")
    logger.info("")
    
    # get args
    input_file = Path(args.input)
    output_file = Path(args.output)
    out_dir = Path(args.out_dir)
    
    assert input_file.exists(), f"{input_file.absolute()} is not found"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("[2/5] Configuration loaded:")
    logger.info(f"     Input file:  {input_file.absolute()}")
    logger.info(f"     Output file: {output_file.absolute()}")
    logger.info(f"     Audio dir:   {out_dir.absolute()}")
    logger.info("")

    params_hook = {}
    try:
        logger.info(f"[3/5] Loading params hook from {args.params_hook}...")
        with open(args.params_hook, "r", encoding="utf-8") as f:
            params_hook = json.load(f)
        logger.info(f"     ✓ Params hook loaded successfully")
    except FileNotFoundError:
        logger.info(f"     ⚠ {args.params_hook} not found (using default params)")
    except json.JSONDecodeError:
        logger.info(f"     ⚠ {args.params_hook} is not valid json (using default params)")
    except Exception as e:
        logger.info(f"     ⚠ Failed to load params hook: {e}")
    
    if "global" in params_hook:
        global_hook = params_hook["global"]
        # copy global_hook to each speaker hook
        for speaker_id in params_hook:
            if speaker_id == "global":
                continue
            params_hook[speaker_id].update(global_hook)
    
    logger.info("     Params hook configuration:")
    pprint(params_hook)
    logger.info("")

    speaker_uuid = args.speaker_uuid
    speaker_name = args.speaker_name
    speaker_id = args.speaker_id
    speaker_ids = args.speaker_ids

    logger.info("[4/5] Speaker initialization:")
    logger.info(f"     Speaker UUID: {speaker_uuid if speaker_uuid else 'N/A'}")
    logger.info(f"     Speaker Name: {speaker_name if speaker_name else 'N/A'}")
    logger.info(f"     Speaker IDs:  {speaker_ids}")
    logger.info("")
    
    # init speaker id
    if speaker_id < 0 and not speaker_ids:  # get speaker_id first
        if not speaker_uuid and not speaker_name:
            if args.query_only:
                speakers = engine.speakers
                print_speaker_styles(speakers, logger)
                return
            else:
                raise ValueError(
                    "speaker_uuid or speaker_name must be provided or specify query_only."
                )
        else:
            logger.info("     Matching criteria:")
            logger.info(f"       - Exact match: {args.exact_name}")
            logger.info("")
            speaker_styles = engine.get_speaker_style(
                speaker_uuid=speaker_uuid,
                name=speaker_name,
                amb_match=not args.exact_name,
            )
            if len(speaker_styles) == 0:
                logger.info("     ✗ No matched speaker found.")
                return
            
            # Display matched speaker styles info (not in query mode)
            logger.info("     Matched speakers:")
            for ss in speaker_styles:
                logger.info(f"       - {ss.name} (UUID: {ss.speaker_uuid})")
                for style in ss.styles:
                    logger.info(f"         • Style ID: {style.id}, Name: {style.name}")
            logger.info("")
            
            print_speaker_styles(speaker_styles, logger)
            if args.query_only:
                return
            speaker_ids_input = input("\nEnter speaker ID(s) to continue (comma-separated): ")
            speaker_ids = [int(i.strip()) for i in speaker_ids_input.split(",")]
    elif speaker_id > 0:
        speaker_ids = [speaker_id]
    else:
        speaker_ids = [int(i) for i in speaker_ids]
    
    # Display detailed speaker info for specified speakers (not in query mode)
    if not args.query_only:
        logger.info("     Speaker details:")
        for sid in speaker_ids:
            try:
                # Get speaker info from engine
                speaker_info = None
                for ss in engine.speakers:
                    for style in ss.styles:
                        if style.id == sid:
                            speaker_info = {
                                "name": ss.name,
                                "uuid": ss.speaker_uuid,
                                "style_name": style.name,
                                "style_id": style.id
                            }
                            break
                    if speaker_info:
                        break
                
                if speaker_info:
                    logger.info(f"       Speaker {sid}:")
                    logger.info(f"         Name: {speaker_info['name']}")
                    logger.info(f"         UUID: {speaker_info['uuid']}")
                    logger.info(f"         Style: {speaker_info['style_name']}")
                else:
                    logger.info(f"       Speaker {sid}: Unknown speaker")
            except Exception as e:
                logger.info(f"       Speaker {sid}: Error getting details - {e}")
        logger.info("")
    
    logger.info(f"     Final speaker IDs: {speaker_ids}")
    
    # Initialize all speakers
    for speaker_id in speaker_ids:
        engine.speaker_init(speaker=speaker_id)
        logger.info(f"     ✓ Initialized speaker {speaker_id}")
    
    compressor = Compressor() if args.compress else None
    logger.info(f"     MP3 compression: {'Enabled' if args.compress else 'Disabled'}")
    logger.info("")

    # read and validate input jsonl
    logger.info("[5/5] Validating and processing input JSONL file...")
    logger.info(f"     File: {input_file.absolute()}")
    valid_lines, errors = validate_jsonl_file(input_file)
    
    if errors:
        logger.info("")
        logger.info(f"     ⚠ Found {len(errors)} invalid line(s):")
        for error in errors:
            logger.info(f"       Line {error['line_num']}: {error['error']}")
            logger.info(f"         Content: {error['content']}")
        logger.info("")
        
        # Ask user if they want to continue
        response = input("     Continue with valid lines only? (y/n): ")
        if response.lower() != 'y':
            logger.info("Processing cancelled.")
            return
        logger.info(f"     Continuing with {len(valid_lines)} valid line(s)...\n")
    else:
        logger.info(f"     ✓ JSONL file is valid ({len(valid_lines)} entries)\n")
    
    output_data = []
    total_entries = len(valid_lines)
    
    for idx, (line_num, line, entry) in enumerate(valid_lines, 1):
        # Log progress in [completed/total] format
        logger.info(f"[{idx}/{total_entries}] Processing entry at line {line_num}")
        
        # Check if sentence field exists
        if "sentence" not in entry:
            warning_msg = f"Warning: 'sentence' field not found at line {line_num}"
            logger.info(warning_msg)
            entry["_processing_error"] = warning_msg
            output_data.append(entry)
            continue
        
        sentence = entry["sentence"]
        audio_files = []
        
        # Generate one UUID per sentence (not per speaker)
        file_id = str(uuid.uuid4())[:8]
        
        for speaker_id in speaker_ids:
            # Use the same file_id for all speakers of the same sentence
            file_ext = "mp3" if args.compress else "wav"
            file_name = f"{file_id}_speaker{speaker_id}.{file_ext}"
            file_path = out_dir / file_name
            
            # Generate TTS
            logger.info(f"Generating audio by speaker_{speaker_id} for: {sentence[:50]}...")
            engine.tts(
                speaker=speaker_id,
                text=sentence,
                params_hook=(
                    params_hook[str(speaker_id)]
                    if str(speaker_id) in params_hook
                    else {}
                ),
                output=file_path,
            )
            
            assert file_path.is_file(), f"Failed to generate audio file: {file_path}"
            
            # Compress to mp3 if requested
            if args.compress:
                wav_file = file_path.with_suffix(".wav")
                if wav_file.is_file():
                    compressor.compress(wav_file, file_path)
                    assert file_path.is_file(), f"Failed to compress audio file: {file_path}"
            
            audio_files.append(str(file_path))
        
        # Add audio_files to the entry
        entry["audio_files"] = audio_files
        output_data.append(entry)
        logger.info(f"[{idx}/{total_entries}] Generated {len(audio_files)} audio file(s) for entry\n")
    
    # write output jsonl
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in output_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    logger.info("="*60)
    logger.info("Processing Complete!")
    logger.info("="*60)
    logger.info(f"✓ Output written to: {output_file.absolute()}")
    logger.info(f"✓ Audio files saved to: {out_dir.absolute()}")
    logger.info(f"✓ Total entries processed: {len(output_data)}")
    logger.info("="*60)


if __name__ == "__main__":
    args = get_args()
    main(args)

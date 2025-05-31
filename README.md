# voicevox_tools
tools for voicevox

- `VoicevoxEngine` is a tool for generating audio of text via voicevox engine
- `Compressor` is a tool for compressing audio files
- `main.py` show a example to generate audio files from txt file(s), one line in a txt file will be regarded as one sentence and generate one sentence.

!!! **`VoicevoxEngine` should work with voicevox engine and tested on version 0.23.0, version larger than 0.23.0 might work too in theory, download voicevox engine from [official repo](https://github.com/VOICEVOX/voicevox_engine/releases/tag/0.23.0)**

## Usage

```shell
usage: main.py [-h] [--base_url BASE_URL] [--input INPUT] [--out_dir OUT_DIR] [--speaker_name SPEAKER_NAME]
               [--speaker_style SPEAKER_STYLE] [--speaker_id SPEAKER_ID] [--speaker_ids SPEAKER_IDS [SPEAKER_IDS ...]]
               [--speaker_uuid SPEAKER_UUID] [--params_hook PARAMS_HOOK] [--exact_name] [--query_only]

options:
  -h, --help            show this help message and exit
  --base_url BASE_URL   base url of Voicevox Engine
  --input INPUT         txt file or dir contains txt file(s)
  --out_dir OUT_DIR     output directory
  --speaker_name SPEAKER_NAME
                        speaker name
  --speaker_style SPEAKER_STYLE
                        speaker style name
  --speaker_id SPEAKER_ID
                        speaker id
  --speaker_ids SPEAKER_IDS [SPEAKER_IDS ...]
                        speaker ids
  --speaker_uuid SPEAKER_UUID
                        speaker uuid
  --params_hook PARAMS_HOOK
                        specified json path to load params hook from file
  --exact_name          query speaker name by exact match
  --query_only          query speaker info only
```
# voicevox_tools
tools for voicevox

- `VoicevoxEngine` is a tool for generating audio of text via voicevox engine.
- `Compressor` is a tool for compressing audio files.
- `main.py` show an example to generate audio files from txt file(s), one line in a txt file will be regarded as one sentence and generate one sentence.
- `egg_rollsJLPT_N1N5_v2_main.py` is an example to generate audio files from txt file(s) and then generate anki card with these audio.

!!! **`VoicevoxEngine` should work with voicevox engine and tested on version 0.23.0, version larger than 0.23.0 might work too in theory, download voicevox engine from [official repo](https://github.com/VOICEVOX/voicevox_engine/releases/tag/0.23.0).**

## Requirements

- `git clone https://github.com/lijunjie2232/voicevox_tools.git && cd voicevox_tools` to clone this project and enter its directory.
- `pip install -r requirements.txt` to install requirements of voicevox engine.
- (optional) `pip install -r requirements_anki.txt` to install requirements for generating anki cards.

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

- first start voicevox engine and then run `main.py`.
- `--base_url` is the base url of voicevox engine, `http://localhost:50021` by default.
- `--speaker_name` and `--speaker_uuid` is the speakers' name and uuid, one uuid is certain to specify a speaker, however name supports partial match if `--exact_name` is not specifie, `--speaker_style` means there is more than one model of one speaker.
- if `--speaker_id` is specified, only one speaker modle will be used to generate audio, then if `--speaker_id` not spcified but `--speaker_ids` is specified, all speaker models specified by `--speaker_ids` will be used to generate audio.
- This is said that one speaker can have multiple models with different styles, but one model only has one `speaker_id` and one speaker only has one `speaker_name` and one `speaker_uuid`.
- `--params_hook` specified json path to load params hook from file, params of one model: [referance from official doc](https://voicevox.github.io/voicevox_engine/api), apis like `/audio_query` will complain the means of all params that could be changed, `params_hook.json` is an example. the params be specified in "global" will applied in all the models to be used, however, if params specified both in "{speaker_id}" and "global", only the params in "{speaker_id}" will be used.

example:

1. query all speakers and styles:
    ```shell
    python main.py --query_only
    ```

2. query style of one speaker by uuid:
    ```shell
    python main.py --speaker_uuid 67d5d8da-acd7-4207-bb10-b5542d3a663b --query_only
    ```

3. to generate audio from txt files in `txt` dir using speaker `13` and `23`, output to `out` dir:
    ```shell
    python main.py --speaker_ids 13 23 --input txt --out_dir out
    ```
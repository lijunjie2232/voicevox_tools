import requests
from pprint import pprint
from pathlib import Path


class SpeakerStyle:
    def __init__(self, id: int, name: str, type: str):
        self.id = id
        self.name = name
        self.type = type

    def __repr__(self):
        return self.to_dict()

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
        }


class SpeakerSupportedFeatures:
    def __init__(self, permitted_synthesis_morphing: str):
        self.permitted_synthesis_morphing = permitted_synthesis_morphing

    def to_dict(self):
        return {
            "permitted_synthesis_morphing": self.permitted_synthesis_morphing,
        }

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.to_dict()


class SpeakerStylesInfo:
    def __init__(
        self,
        name: str,
        speaker_uuid,
        styles: list[dict],
        version: str,
        supported_features: dict,
    ):
        self.name = name
        self.speaker_uuid = speaker_uuid
        self.styles = [SpeakerStyle(**style) for style in styles]
        self.version = version
        self.supported_features = SpeakerSupportedFeatures(**supported_features)

    def to_dict(self):
        return {
            "name": self.name,
            "speaker_uuid": self.speaker_uuid,
            "styles": [style.to_dict() for style in self.styles],
            "version": self.version,
            "supported_features": self.supported_features.to_dict(),
        }

    def __repr__(self):
        return self.to_dict()

    def __str__(self):
        return str(self.to_dict())


class VoicevoxEngine:

    def __init__(
        self,
        base_url: str = "http://localhost:50021",
        device: str = "cuda",
    ):
        self.session = requests.Session()
        self.base_url = base_url
        self.device = self.check_devices(device)
        self.speakers = self.get_speakers()
        pass

    def req(self, *args, **kwargs):
        return_type = "json()"
        success_code = 200
        if "return_type" in kwargs:
            return_type = kwargs.pop("return_type")
        if "success_code" in kwargs:
            success_code = kwargs.pop("success_code")
        response = self.session.request(*args, **kwargs)

        if response.status_code != success_code:
            try:
                pprint(response.json())
            except:
                # pprint(response)
                pass
            raise Exception(f"response returned status code: {response.status_code}")

        try:
            if not return_type:
                return response
            if return_type.endswith("()"):
                return_type = return_type[:-2]
                return getattr(response, return_type)()
            return getattr(response, return_type)
        except Exception as e:
            pprint(e)
            return response

    def get_devices(self):
        return self.req(
            "GET",
            url=f"{self.base_url}/supported_devices",
        )

    def check_devices(self, device="cuda"):
        response = self.get_devices()
        assert device in response, Exception(f"Device {device} is not supported")

        pprint(
            "supported devices are: " + f"{[k for k, v in response.items() if v]}",
        )

        if not response[device]:
            raise Exception(f"Device {device} is not available in this environment")
        else:
            pprint(f"{device} is available, device set to {device}")

        return device

    def get_speakers(self):
        return self.req(
            "GET",
            f"{self.base_url}/speakers",
        )

    def get_speaker_info(
        self,
        speaker_uuid,
        resource_format="base64",
        core_version=None,
    ):
        params = {
            "speaker_uuid": speaker_uuid,
            "resource_format": resource_format,
        }
        if core_version:
            params["core_version"] = core_version
        return self.req(
            "GET",
            f"{self.base_url}/speaker_info",
            params=params,
        )

    def audio_query(
        self,
        speaker: int,
        text: str,
    ):
        return self.req(
            "POST",
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": speaker},
        )

    def update_params(
        self,
        params,
        **kwargs,
    ):
        params.update(**kwargs)
        return params

    def synthesis(
        self,
        speaker: int,
        params: dict,
        enable_interrogative_upspeak=True,
    ):
        return self.req(
            "POST",
            f"{self.base_url}/synthesis",
            json=params,
            params={
                "enable_interrogative_upspeak": enable_interrogative_upspeak,
                "speaker": speaker,
            },
            return_type="content",
        )

    def refresh_speaker(self):
        self.speakers = self.get_speakers()

    def get_speaker_style(
        self,
        speaker_uuid: str = None,
        name: str = None,
        amb_match: bool = True,
    ):
        assert speaker_uuid or name, Exception(
            "at least one of speaker_uuid or name is required"
        )

        def uuid_filter(speaker):
            if not speaker_uuid:
                return True
            return speaker["speaker_uuid"] == speaker_uuid

        def name_filter(speaker):
            if not name:
                return True
            if amb_match:
                return name.lower() in speaker["name"].lower()
            return speaker["name"] == name

        def speaker_filter(speaker):
            return uuid_filter(speaker) and name_filter(speaker)

        speaker = list(filter(speaker_filter, self.speakers))

        return speaker

    def speaker_init_check(self, **kwargs):
        """
        kwargs:
            speaker(required)   [integer] (Speaker)
            core_version    [string] (Core Version)
        """
        return self.req(
            "POST",
            f"{self.base_url}/is_initialized_speaker",
            params=kwargs,
        )

    def speaker_init(self, **kwargs):
        """
        kwargs:
            speaker(required)   [integer] (Speaker)
            skip_reinit [boolean] (Skip Reinit) Default: False 既に初期化済みのスタイルの再初期化をスキップするかどうか
            core_version    [string] (Core Version)
        """
        self.req(
            "POST",
            f"{self.base_url}/initialize_speaker",
            params=kwargs,
            return_type=None,
            success_code=204,
        )
        return True

    def tts(
        self,
        speaker,
        text,
        params_hook: dict = {},
        output=None,
        overwrite=False,
    ):
        params = self.audio_query(speaker, text)
        params = self.update_params(params, **params_hook)
        wav = self.synthesis(speaker, params)
        if output:
            output = Path(output)
            if not output.is_file() or overwrite:
                assert output.parent.is_dir(), Exception(
                    f"output directory {output.parent} does not exist"
                )
                with open(output, "wb") as f:
                    f.write(wav)
            return
        return wav


if __name__ == "__main__":
    base_url = "http://localhost:50021"

    v = VoicevoxEngine(device="cuda")
    speakers = v.get_speakers()
    speaker_info = v.get_speaker_info("67d5d8da-acd7-4207-bb10-b5542d3a663b")
    speaker_style = v.get_speaker_style(
        speaker_uuid="67d5d8da-acd7-4207-bb10-b5542d3a663b",
    )
    pprint(speaker_style)
    for ss in speaker_style:
        SpeakerStylesInfo(**ss)
    v.speaker_init(speaker=23, skip_reinit=True)
    # params = v.audio_query(23, "こんにちは")

    # pprint(params)
    wav = v.tts(23, "こんにちは", output="output.wav")
    pass

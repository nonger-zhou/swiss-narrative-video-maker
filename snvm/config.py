import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    whisper_model: str
    edge_tts_voice: str


def load_settings() -> Settings:
    load_env_file(Path(".env"))

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        whisper_model=os.getenv("WHISPER_MODEL", "small"),
        edge_tts_voice=os.getenv("EDGE_TTS_VOICE", "zh-CN-XiaoxiaoNeural"),
    )


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

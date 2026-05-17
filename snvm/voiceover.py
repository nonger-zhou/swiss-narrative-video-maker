import importlib.util
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .certificates import apply_certifi_environment
from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


def is_edge_tts_available() -> bool:
    return importlib.util.find_spec("edge_tts") is not None


def generate_voiceover(scene_plan_path: Path, output_dir: Path, voice: str) -> Path:
    if not is_edge_tts_available():
        raise SnvmError(
            "edge-tts is not installed or not available in this Python environment. "
            "Install project requirements before generating voiceover."
        )

    apply_certifi_environment()
    initialize_project_output(output_dir)
    scene_plan = read_json(scene_plan_path)
    scenes = _require_scenes(scene_plan)
    text = _voiceover_text(scenes)
    if not text:
        raise SnvmError("Scene plan has no rewritten voiceover text.")

    voiceover_dir = output_dir / "voiceover"
    voiceover_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "voiceover.mp3"
    subtitle_path = voiceover_dir / "voiceover.srt"

    command = [
        sys.executable,
        "-m",
        "edge_tts",
        "--voice",
        voice,
        "--text",
        text,
        "--write-media",
        str(audio_path),
        "--write-subtitles",
        str(subtitle_path),
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SnvmError(f"edge-tts failed with exit code {exc.returncode}") from exc

    if not audio_path.exists():
        raise SnvmError(f"edge-tts finished but did not create {audio_path}")

    write_json(
        voiceover_dir / "voiceover_metadata.json",
        {
            "voice": voice,
            "source_scene_plan": str(scene_plan_path),
            "audio_path": str(audio_path),
            "subtitle_path": str(subtitle_path) if subtitle_path.exists() else None,
            "generated_at": _now_iso(),
        },
    )
    return audio_path


def _require_scenes(scene_plan: Any) -> list[dict[str, Any]]:
    if not isinstance(scene_plan, dict) or not isinstance(scene_plan.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")
    return scene_plan["scenes"]


def _voiceover_text(scenes: list[dict[str, Any]]) -> str:
    parts = []
    for scene in scenes:
        text = str(
            scene.get("reviewed_voiceover")
            or scene.get("final_voiceover")
            or scene.get("rewritten_voiceover")
            or scene.get("subtitle_text")
            or ""
        ).strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json


def write_scene_srt(
    scene_plan_path: Path,
    output_path: Path,
    *,
    target_duration: float | None = None,
) -> Path:
    scene_plan = read_json(scene_plan_path)
    if not isinstance(scene_plan, dict) or not isinstance(scene_plan.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")

    blocks = []
    source_duration = _source_duration(scene_plan["scenes"])
    scale = 1.0
    if target_duration and source_duration > 0:
        scale = target_duration / source_duration

    for index, scene in enumerate(scene_plan["scenes"], start=1):
        if not isinstance(scene, dict):
            raise SnvmError(f"Scene {index} must be a JSON object.")
        start = _float_value(scene.get("start_time"), 0.0) * scale
        end = _float_value(scene.get("end_time"), start + 3.0) * scale
        if end <= start:
            end = start + 3.0
        text = str(
            scene.get("reviewed_voiceover")
            or scene.get("final_voiceover")
            or scene.get("subtitle_text")
            or scene.get("rewritten_voiceover")
            or ""
        ).strip()
        if not text:
            continue
        blocks.append(f"{len(blocks) + 1}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}\n")

    if not blocks:
        raise SnvmError("Scene plan has no subtitle text.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(blocks), encoding="utf-8")
    return output_path


def _srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _source_duration(scenes: list[Any]) -> float:
    max_end = 0.0
    for scene in scenes:
        if isinstance(scene, dict):
            max_end = max(max_end, _float_value(scene.get("end_time"), 0.0))
    return max_end

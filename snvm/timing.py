from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output
from .review import estimate_zh_duration


def generate_timing_plan(scene_plan_path: Path, output_dir: Path) -> Path:
    initialize_project_output(output_dir)
    scene_plan = read_json(scene_plan_path)
    scenes = _require_scenes(scene_plan)

    timing_scenes = []
    for scene in scenes:
        source_duration = _duration(scene)
        voiceover_text = _voiceover_text(scene)
        voiceover_duration = estimate_zh_duration(voiceover_text)
        duration_delta = round(voiceover_duration - source_duration, 2)
        duration_ratio = _safe_ratio(voiceover_duration, source_duration)
        timing_action = _timing_action(scene, source_duration, voiceover_duration, duration_ratio)
        timing_scenes.append(
            {
                "scene_id": scene.get("scene_id", ""),
                "source_segment_id": scene.get("source_segment_id"),
                "start_time": scene.get("start_time"),
                "end_time": scene.get("end_time"),
                "source_duration": source_duration,
                "estimated_voiceover_duration": voiceover_duration,
                "duration_delta": duration_delta,
                "duration_ratio": duration_ratio,
                "visual_action": scene.get("visual_action"),
                "timing_action": timing_action,
                "recommendation": _recommendation(timing_action, duration_delta),
                "voiceover_text": voiceover_text,
            }
        )

    timing_plan = {
        "metadata": {
            "source_scene_plan": str(scene_plan_path),
            "generated_at": _now_iso(),
            "note": (
                "This plan is advisory. It does not alter compose yet. Use it to decide "
                "whether to compress narration, extend a scene, or add new visual material."
            ),
        },
        "summary": _summary(timing_scenes),
        "scenes": timing_scenes,
    }
    return write_json(output_dir / "timing_plan.json", timing_plan)


def _timing_action(
    scene: dict[str, Any],
    source_duration: float,
    voiceover_duration: float,
    duration_ratio: float,
) -> str:
    visual_action = str(scene.get("visual_action") or "")
    rewrite_text = _voiceover_text(scene)

    if not rewrite_text:
        return "remove_or_fill"
    if source_duration <= 0:
        return "needs_manual_timing"
    if duration_ratio <= 1.15:
        return "keep_timing"
    if duration_ratio <= 1.35:
        return "slightly_extend_scene"
    if duration_ratio <= 1.7 and visual_action in {
        "keep_original",
        "replace_with_user_footage",
        "search_alternative_or_keep",
    }:
        return "extend_or_slow_scene"
    if visual_action in {"recreate_chart", "recreate_map", "add_explanatory_visual"}:
        return "add_explanatory_visual_time"
    if voiceover_duration - source_duration >= 4.0:
        return "review_copy_or_add_material"
    return "freeze_last_frame_or_add_broll"


def _recommendation(timing_action: str, duration_delta: float) -> str:
    if timing_action == "keep_timing":
        return "Voiceover is close to the source duration. Keep the original timing."
    if timing_action == "slightly_extend_scene":
        return "Voiceover is slightly longer. Extend this scene locally instead of looping the full video."
    if timing_action == "extend_or_slow_scene":
        return "Extend, slow down, or hold this specific scene. Do not loop the whole source video."
    if timing_action == "add_explanatory_visual_time":
        return "Use the extra time for the planned chart, map, text card, or explanatory visual."
    if timing_action == "review_copy_or_add_material":
        return (
            f"Voiceover is about {duration_delta:.1f}s longer. Either compress the copy or add "
            "scene-specific B-roll, chart, map, or user footage."
        )
    if timing_action == "freeze_last_frame_or_add_broll":
        return "Freeze the final frame briefly or add B-roll tied to this scene."
    if timing_action == "remove_or_fill":
        return "No voiceover text found. Remove this scene or add narration."
    return "Manual timing needed."


def _summary(scenes: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    total_source = 0.0
    total_voiceover = 0.0
    for scene in scenes:
        counts[scene["timing_action"]] = counts.get(scene["timing_action"], 0) + 1
        total_source += float(scene.get("source_duration") or 0)
        total_voiceover += float(scene.get("estimated_voiceover_duration") or 0)
    return {
        "scene_count": len(scenes),
        "total_source_duration": round(total_source, 2),
        "estimated_total_voiceover_duration": round(total_voiceover, 2),
        "estimated_delta": round(total_voiceover - total_source, 2),
        "timing_action_counts": counts,
    }


def _voiceover_text(scene: dict[str, Any]) -> str:
    return str(
        scene.get("reviewed_voiceover")
        or scene.get("final_voiceover")
        or scene.get("rewritten_voiceover")
        or scene.get("subtitle_text")
        or ""
    ).strip()


def _require_scenes(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")
    return data["scenes"]


def _duration(scene: dict[str, Any]) -> float:
    start = _float_value(scene.get("start_time"), 0.0)
    end = _float_value(scene.get("end_time"), start)
    return round(max(0.0, end - start), 2)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 2)


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

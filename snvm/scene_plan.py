from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


VISUAL_ACTIONS = {
    "keep_original",
    "replace_with_user_footage",
    "recreate_chart",
    "recreate_map",
    "add_explanatory_visual",
    "search_alternative_or_keep",
    "remove",
}
DIFFICULTIES = {"easy", "medium", "hard"}


def generate_scene_plan(
    translation_path: Path,
    structure_path: Path,
    output_dir: Path,
) -> Path:
    initialize_project_output(output_dir)
    translation = read_json(translation_path)
    structure = read_json(structure_path)

    translations = _index_by_id(_require_segments(translation, translation_path))
    structures = _index_by_id(_require_segments(structure, structure_path))
    scene_ids = sorted(translations.keys(), key=_sort_key)
    if not scene_ids:
        raise SnvmError("Cannot generate scene plan because translation has no segments.")

    scenes = []
    for index, segment_id in enumerate(scene_ids, start=1):
        translated = translations[segment_id]
        analyzed = structures.get(segment_id, {})
        scene = {
            "scene_id": f"scene_{index:03d}",
            "source_segment_id": segment_id,
            "start_time": _float_value(translated.get("start"), 0.0),
            "end_time": _float_value(translated.get("end"), 0.0),
            "source_summary": str(analyzed.get("source_summary", "")),
            "translated_text": str(translated.get("translated_text", "")),
            "narrative_role": str(analyzed.get("narrative_role", "")),
            "rewritten_voiceover": str(
                analyzed.get("rewritten_voiceover")
                or translated.get("translated_text")
                or translated.get("source_text")
                or ""
            ),
            "visual_action": _valid_visual_action(analyzed.get("visual_action")),
            "visual_suggestion": str(analyzed.get("visual_suggestion", "")),
            "replacement_difficulty": _valid_difficulty(analyzed.get("replacement_difficulty")),
            "alternative_source_suggestions": _string_list(
                analyzed.get("alternative_source_suggestions", [])
            ),
            "search_keywords": _string_list(analyzed.get("search_keywords", [])),
            "fallback_action": _valid_visual_action(
                analyzed.get("fallback_action") or "keep_original"
            ),
            "subtitle_text": str(
                analyzed.get("rewritten_voiceover")
                or translated.get("translated_text")
                or ""
            ),
        }
        scenes.append(scene)

    scene_plan = {
        "metadata": {
            "source_translation": str(translation_path),
            "source_structure_analysis": str(structure_path),
            "generated_at": _now_iso(),
        },
        "scenes": scenes,
    }
    validate_scene_plan(scene_plan)
    return write_json(output_dir / "scene_plan.json", scene_plan)


def validate_scene_plan(scene_plan: Any) -> None:
    if not isinstance(scene_plan, dict) or not isinstance(scene_plan.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")

    required = {
        "scene_id",
        "start_time",
        "end_time",
        "source_summary",
        "translated_text",
        "narrative_role",
        "rewritten_voiceover",
        "visual_action",
        "visual_suggestion",
        "replacement_difficulty",
        "alternative_source_suggestions",
        "search_keywords",
        "fallback_action",
        "subtitle_text",
    }
    for index, scene in enumerate(scene_plan["scenes"], start=1):
        if not isinstance(scene, dict):
            raise SnvmError(f"Scene {index} must be a JSON object.")
        missing = sorted(required - set(scene.keys()))
        if missing:
            raise SnvmError(f"Scene {index} is missing required fields: {', '.join(missing)}")
        if scene["visual_action"] not in VISUAL_ACTIONS:
            raise SnvmError(f"Scene {index} has invalid visual_action: {scene['visual_action']}")
        if scene["fallback_action"] not in VISUAL_ACTIONS:
            raise SnvmError(f"Scene {index} has invalid fallback_action: {scene['fallback_action']}")
        if scene["replacement_difficulty"] not in DIFFICULTIES:
            raise SnvmError(
                f"Scene {index} has invalid replacement_difficulty: "
                f"{scene['replacement_difficulty']}"
            )


def _require_segments(data: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("segments"), list):
        raise SnvmError(f"{path} must contain a 'segments' list.")
    return data["segments"]


def _index_by_id(segments: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    indexed = {}
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            raise SnvmError(f"Segment {index} must be a JSON object.")
        indexed[segment.get("id", index)] = segment
    return indexed


def _sort_key(value: Any) -> tuple[int, str]:
    try:
        return (0, f"{int(value):09d}")
    except (TypeError, ValueError):
        return (1, str(value))


def _valid_visual_action(value: Any) -> str:
    value = str(value or "keep_original")
    if value not in VISUAL_ACTIONS:
        return "search_alternative_or_keep"
    return value


def _valid_difficulty(value: Any) -> str:
    value = str(value or "medium")
    if value not in DIFFICULTIES:
        return "medium"
    return value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _float_value(value: Any, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

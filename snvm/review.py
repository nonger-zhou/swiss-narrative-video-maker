import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output
from .scene_plan import validate_scene_plan


@dataclass(frozen=True)
class ReviewPaths:
    json_path: Path
    markdown_path: Path


def generate_scene_review(
    transcript_path: Path,
    translation_path: Path,
    scene_plan_path: Path,
    output_dir: Path,
) -> ReviewPaths:
    initialize_project_output(output_dir)

    transcript = read_json(transcript_path)
    translation = read_json(translation_path)
    scene_plan = read_json(scene_plan_path)
    scenes = _require_scenes(scene_plan)
    transcript_by_id = _index_by_id(_require_segments(transcript, transcript_path))
    translation_by_id = _index_by_id(_require_segments(translation, translation_path))

    review_scenes = []
    previous_entries = []
    for scene in scenes:
        segment_id = scene.get("source_segment_id")
        transcript_segment = transcript_by_id.get(segment_id, {})
        translation_segment = translation_by_id.get(segment_id, {})
        source_duration = _duration(scene)
        literal_translation = str(
            translation_segment.get("translated_text") or scene.get("translated_text") or ""
        )
        rewritten_voiceover = str(scene.get("rewritten_voiceover") or "")
        warnings = _review_warnings(
            scene,
            literal_translation,
            rewritten_voiceover,
            source_duration,
            previous_entries,
        )
        entry = {
            "scene_id": scene.get("scene_id", ""),
            "source_segment_id": segment_id,
            "start_time": scene.get("start_time"),
            "end_time": scene.get("end_time"),
            "source_text": str(
                translation_segment.get("source_text") or transcript_segment.get("text") or ""
            ),
            "literal_translation": literal_translation,
            "rewritten_voiceover": rewritten_voiceover,
            "estimated_literal_duration": _estimate_zh_duration(literal_translation),
            "estimated_voiceover_duration": _estimate_zh_duration(rewritten_voiceover),
            "source_duration": source_duration,
            "duration_ratio": _safe_ratio(_estimate_zh_duration(rewritten_voiceover), source_duration),
            "ai_warnings": warnings,
            "ai_suggested_revision": _suggest_revision(
                literal_translation,
                rewritten_voiceover,
                warnings,
            ),
            "user_note": "",
            "final_voiceover": rewritten_voiceover,
        }
        review_scenes.append(entry)
        previous_entries.append(entry)

    review = {
        "metadata": {
            "source_transcript": str(transcript_path),
            "source_translation": str(translation_path),
            "source_scene_plan": str(scene_plan_path),
            "generated_at": _now_iso(),
            "instructions": (
                "Edit user_note and final_voiceover. Then run "
                "`python -m snvm apply-review` to create scene_plan.reviewed.json."
            ),
        },
        "scenes": review_scenes,
    }

    json_path = write_json(output_dir / "scene_review.json", review)
    markdown_path = _write_markdown_review(output_dir / "scene_review.md", review_scenes)
    return ReviewPaths(json_path=json_path, markdown_path=markdown_path)


def apply_scene_review(
    scene_plan_path: Path,
    review_path: Path,
    output_dir: Path,
) -> Path:
    initialize_project_output(output_dir)
    scene_plan = read_json(scene_plan_path)
    review = read_json(review_path)
    scenes = _require_scenes(scene_plan)
    review_by_scene_id = {
        entry.get("scene_id"): entry
        for entry in _require_scenes(review)
        if isinstance(entry, dict)
    }

    reviewed_scenes = []
    for scene in scenes:
        updated = dict(scene)
        review_entry = review_by_scene_id.get(scene.get("scene_id"))
        if review_entry:
            final_voiceover = str(review_entry.get("final_voiceover") or "").strip()
            if final_voiceover:
                updated["reviewed_voiceover"] = final_voiceover
                updated["rewritten_voiceover"] = final_voiceover
                updated["subtitle_text"] = final_voiceover
            user_note = str(review_entry.get("user_note") or "").strip()
            if user_note:
                updated["user_note"] = user_note
        reviewed_scenes.append(updated)

    reviewed_plan = {
        "metadata": {
            **scene_plan.get("metadata", {}),
            "source_review": str(review_path),
            "review_applied_at": _now_iso(),
        },
        "scenes": reviewed_scenes,
    }
    validate_scene_plan(reviewed_plan)
    return write_json(output_dir / "scene_plan.reviewed.json", reviewed_plan)


def _review_warnings(
    scene: dict[str, Any],
    literal_translation: str,
    rewritten_voiceover: str,
    source_duration: float,
    previous_entries: list[dict[str, Any]],
) -> list[dict[str, str]]:
    warnings = []
    rewrite_duration = _estimate_zh_duration(rewritten_voiceover)
    literal_duration = _estimate_zh_duration(literal_translation)
    source_ratio = _safe_ratio(rewrite_duration, source_duration)
    literal_ratio = _safe_ratio(rewrite_duration, literal_duration)

    if source_ratio >= 1.6:
        warnings.append(
            {
                "type": "duration_over_source",
                "message": (
                    f"Voiceover is about {source_ratio:.1f}x the source scene duration. "
                    "Consider compressing text or adding scene-specific visuals."
                ),
            }
        )
    if literal_ratio >= 1.5:
        warnings.append(
            {
                "type": "rewrite_expansion",
                "message": (
                    f"Voiceover is about {literal_ratio:.1f}x the literal translation. "
                    "Check whether the extra explanation is intentional."
                ),
            }
        )

    duplicate = _find_duplicate(rewritten_voiceover, previous_entries)
    if duplicate:
        warnings.append(
            {
                "type": "possible_duplicate",
                "message": (
                    f"Possibly repeats {duplicate['scene_id']}: "
                    f"{duplicate['reason']}"
                ),
            }
        )

    if not str(scene.get("narrative_role") or "").strip():
        warnings.append(
            {
                "type": "missing_narrative_role",
                "message": "This scene has no narrative role from the analysis step.",
            }
        )
    return warnings


def _find_duplicate(
    rewritten_voiceover: str,
    previous_entries: list[dict[str, Any]],
) -> dict[str, str] | None:
    current_norm = _normalize_text(rewritten_voiceover)
    if not current_norm:
        return None
    current_facts = _fact_terms(rewritten_voiceover)

    for previous in reversed(previous_entries[-12:]):
        previous_text = str(previous.get("final_voiceover") or previous.get("rewritten_voiceover") or "")
        previous_norm = _normalize_text(previous_text)
        if not previous_norm:
            continue
        similarity = SequenceMatcher(None, current_norm, previous_norm).ratio()
        if similarity >= 0.72:
            return {
                "scene_id": str(previous.get("scene_id", "")),
                "reason": f"high text similarity ({similarity:.2f})",
            }

        previous_facts = _fact_terms(previous_text)
        shared_facts = sorted(current_facts & previous_facts)
        if len(shared_facts) >= 2:
            return {
                "scene_id": str(previous.get("scene_id", "")),
                "reason": "shared fact terms: " + ", ".join(shared_facts[:5]),
            }
    return None


def _suggest_revision(
    literal_translation: str,
    rewritten_voiceover: str,
    warnings: list[dict[str, str]],
) -> str:
    warning_types = {warning["type"] for warning in warnings}
    if "possible_duplicate" in warning_types:
        return "Rewrite this as a transition or new angle instead of repeating the same fact."
    if "rewrite_expansion" in warning_types or "duration_over_source" in warning_types:
        return literal_translation or rewritten_voiceover
    return ""


def _write_markdown_review(path: Path, review_scenes: list[dict[str, Any]]) -> Path:
    lines = [
        "# Scene Review",
        "",
        "Edit `scene_review.json` for machine-readable changes. This Markdown file is for reading.",
        "",
    ]
    for scene in review_scenes:
        lines.extend(
            [
                f"## {scene['scene_id']}  {_time_range(scene)}",
                "",
                "**Original Transcript**",
                "",
                f"> {scene['source_text']}",
                "",
                "**Literal Chinese Translation**",
                "",
                f"> {scene['literal_translation']}",
                "",
                "**Rewritten Chinese Voiceover**",
                "",
                f"> {scene['rewritten_voiceover']}",
                "",
                "**AI Review**",
                "",
            ]
        )
        warnings = scene.get("ai_warnings", [])
        if warnings:
            for warning in warnings:
                lines.append(f"- {warning['type']}: {warning['message']}")
        else:
            lines.append("- No obvious issue detected.")
        lines.extend(
            [
                "",
                f"Suggested revision: {scene['ai_suggested_revision'] or '(none)'}",
                "",
                "**User Note**",
                "",
                "<!-- Write user guidance in scene_review.json:user_note -->",
                "",
                "**Final Voiceover**",
                "",
                f"> {scene['final_voiceover']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _require_segments(data: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("segments"), list):
        raise SnvmError(f"{path} must contain a 'segments' list.")
    return data["segments"]


def _require_scenes(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise SnvmError("JSON must contain a 'scenes' list.")
    return data["scenes"]


def _index_by_id(segments: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    return {segment.get("id", index): segment for index, segment in enumerate(segments, start=1)}


def _duration(scene: dict[str, Any]) -> float:
    start = _float_value(scene.get("start_time"), 0.0)
    end = _float_value(scene.get("end_time"), start)
    return max(0.0, end - start)


def _estimate_zh_duration(text: str) -> float:
    return estimate_zh_duration(text)


def estimate_zh_duration(text: str) -> float:
    cleaned = re.sub(r"\s+", "", text)
    if not cleaned:
        return 0.0
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    other_chars = len(cleaned) - chinese_chars
    return round((chinese_chars / 4.5) + (other_chars / 8.0), 2)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 2)


def _normalize_text(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.lower(), flags=re.UNICODE)


def _fact_terms(text: str) -> set[str]:
    terms = set()
    lowered = text.lower()
    for match in re.findall(r"\d+(?:\.\d+)?|第[一二三四五六七八九十百千万\d]+", text):
        terms.add(match)
    for keyword in (
        "全球和平指数",
        "和平指数",
        "生活满意度",
        "瑞士",
        "德国",
        "排名",
        "第六",
        "安全",
        "工资",
        "税",
        "租金",
    ):
        if keyword in text:
            terms.add(keyword)
    for keyword in ("global peace index", "switzerland", "germany", "ranking"):
        if keyword in lowered:
            terms.add(keyword)
    return terms


def _time_range(scene: dict[str, Any]) -> str:
    return f"{scene.get('start_time', '')} - {scene.get('end_time', '')}"


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

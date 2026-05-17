from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


ISSUE_LABELS = {
    "voiceover_late": "Chinese voiceover/subtitle is late",
    "voiceover_early": "Chinese voiceover/subtitle is early",
    "visual_mismatch": "Visual does not match narration",
    "needs_material": "Needs additional or replacement material",
    "copy_too_long": "Chinese copy is too long",
    "duplicate_fact": "Possible duplicate fact",
    "other": "Other",
}


def generate_revision_plan(
    notes_path: Path,
    scene_plan_path: Path | None,
    timing_plan_path: Path | None,
    output_dir: Path,
) -> tuple[Path, Path]:
    initialize_project_output(output_dir)
    if not notes_path.exists():
        raise SnvmError(
            f"Alignment notes file does not exist: {notes_path}. "
            "Export alignment_notes.json from the review player first."
        )

    notes_data = read_json(notes_path)
    notes = _require_notes(notes_data, notes_path)
    scenes = _scene_index(read_json(scene_plan_path)) if scene_plan_path and scene_plan_path.exists() else {}
    timing = _timing_index(read_json(timing_plan_path)) if timing_plan_path and timing_plan_path.exists() else {}
    plan_scenes = _build_scene_revisions(notes, scenes, timing)

    revision_plan = {
        "metadata": {
            "source_notes": str(notes_path),
            "source_scene_plan": str(scene_plan_path) if scene_plan_path else None,
            "source_timing_plan": str(timing_plan_path) if timing_plan_path else None,
            "generated_at": _now_iso(),
            "instructions": (
                "Review this plan before editing scene_review.json, scene_plan.reviewed.json, "
                "or visual_replacements.json. This file is advisory and does not change the draft."
            ),
        },
        "summary": _summary(plan_scenes),
        "scenes": plan_scenes,
    }
    json_path = write_json(output_dir / "revision_plan.json", revision_plan)
    markdown_path = _write_markdown(output_dir / "revision_plan.md", revision_plan)
    return json_path, markdown_path


def _build_scene_revisions(
    notes: list[dict[str, Any]],
    scenes: dict[str, dict[str, Any]],
    timing: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    notes_by_scene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for note in notes:
        scene_id = str(note.get("scene_id") or "unknown")
        notes_by_scene[scene_id].append(note)

    revisions = []
    for scene_id, scene_notes in sorted(notes_by_scene.items(), key=_scene_sort_key):
        scene = scenes.get(scene_id, {})
        timing_entry = timing.get(scene_id, {})
        issue_counts = Counter(str(note.get("issue_type") or "other") for note in scene_notes)
        actions = _recommended_actions(issue_counts, scene_notes, scene, timing_entry)
        revisions.append(
            {
                "scene_id": scene_id,
                "time_range": _time_range(scene, scene_notes),
                "note_count": len(scene_notes),
                "issue_counts": dict(issue_counts),
                "highest_severity": _highest_severity(scene_notes),
                "recommended_actions": actions,
                "notes": [_clean_note(note) for note in scene_notes],
                "context": {
                    "source_text": _first_text(scene_notes, "source_text"),
                    "literal_translation": _first_text(scene_notes, "literal_translation"),
                    "voiceover": _first_text(scene_notes, "voiceover")
                    or _voiceover_text(scene),
                    "timing_action": timing_entry.get("timing_action") or _first_text(scene_notes, "timing_action"),
                    "visual_action": scene.get("visual_action") or _first_text(scene_notes, "visual_action"),
                    "timing_recommendation": timing_entry.get("recommendation", ""),
                },
            }
        )
    return revisions


def _recommended_actions(
    issue_counts: Counter,
    notes: list[dict[str, Any]],
    scene: dict[str, Any],
    timing: dict[str, Any],
) -> list[dict[str, str]]:
    actions = []
    if issue_counts["voiceover_late"]:
        actions.append(
            {
                "type": "adjust_alignment",
                "priority": "high",
                "suggestion": (
                    "Chinese narration/subtitle appears late. Review the marked timestamp and "
                    "consider moving this scene's Chinese cue earlier or shifting the scene boundary later."
                ),
            }
        )
    if issue_counts["voiceover_early"]:
        actions.append(
            {
                "type": "adjust_alignment",
                "priority": "high",
                "suggestion": (
                    "Chinese narration/subtitle appears early. Review the marked timestamp and "
                    "consider moving this scene's Chinese cue later or shifting the scene boundary earlier."
                ),
            }
        )
    if issue_counts["visual_mismatch"]:
        actions.append(
            {
                "type": "review_scene_boundary_or_visual",
                "priority": "high",
                "suggestion": (
                    "Visual and narration do not match. Check whether the scene boundary is wrong; "
                    "if the boundary is right, add a replacement asset in visual_replacements.json."
                ),
            }
        )
    if issue_counts["needs_material"]:
        actions.append(
            {
                "type": "add_visual_material",
                "priority": "medium",
                "suggestion": (
                    "Add B-roll, generated visual, chart, map, or user footage for this scene. "
                    "Use visual_replacements.json to attach the asset."
                ),
            }
        )
    if issue_counts["copy_too_long"] or _timing_needs_copy_review(timing):
        actions.append(
            {
                "type": "compress_copy",
                "priority": "medium",
                "suggestion": (
                    "Review the Chinese voiceover for length. Prefer compressing repeated explanation "
                    "before extending visuals."
                ),
            }
        )
    if issue_counts["duplicate_fact"]:
        actions.append(
            {
                "type": "deduplicate_copy",
                "priority": "medium",
                "suggestion": (
                    "Check whether this fact intentionally returns as a callback. If not, rewrite it "
                    "as a transition, consequence, or new angle instead of repeating the same statement."
                ),
            }
        )
    if _has_manual_notes(notes):
        actions.append(
            {
                "type": "read_user_notes",
                "priority": "medium",
                "suggestion": "Read the creator's written notes before editing this scene.",
            }
        )
    if not actions:
        actions.append(
            {
                "type": "manual_review",
                "priority": "low",
                "suggestion": "Review the notes for this scene and decide whether a text or timing edit is needed.",
            }
        )
    return actions


def _write_markdown(path: Path, revision_plan: dict[str, Any]) -> Path:
    summary = revision_plan["summary"]
    lines = [
        "# Revision Plan",
        "",
        "This file is generated from `alignment_notes.json`. It is advisory and does not modify the video.",
        "",
        "## Summary",
        "",
        f"- Scenes with notes: {summary['scene_count']}",
        f"- Total notes: {summary['note_count']}",
        f"- High-priority scenes: {summary['high_priority_scene_count']}",
        "",
        "Issue counts:",
        "",
    ]
    for issue_type, count in summary["issue_counts"].items():
        lines.append(f"- {issue_type}: {count}")

    for scene in revision_plan["scenes"]:
        lines.extend(
            [
                "",
                f"## {scene['scene_id']}  {scene['time_range']}",
                "",
                f"- Notes: {scene['note_count']}",
                f"- Highest severity: {scene['highest_severity']}",
                "",
                "Recommended actions:",
                "",
            ]
        )
        for action in scene["recommended_actions"]:
            lines.append(f"- [{action['priority']}] {action['type']}: {action['suggestion']}")

        context = scene["context"]
        lines.extend(
            [
                "",
                "Context:",
                "",
                f"- Timing action: {context.get('timing_action') or '(none)'}",
                f"- Visual action: {context.get('visual_action') or '(none)'}",
                f"- Timing recommendation: {context.get('timing_recommendation') or '(none)'}",
                "",
                "Voiceover:",
                "",
                f"> {context.get('voiceover') or '(empty)'}",
                "",
                "Notes:",
                "",
            ]
        )
        for note in scene["notes"]:
            note_text = note.get("note") or "(no written note)"
            lines.append(
                f"- {note['timecode']} | {note['issue_type']} | {note['severity']}: {note_text}"
            )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _summary(scenes: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts: Counter = Counter()
    high_priority = 0
    note_count = 0
    for scene in scenes:
        note_count += scene["note_count"]
        issue_counts.update(scene["issue_counts"])
        if any(action["priority"] == "high" for action in scene["recommended_actions"]):
            high_priority += 1
    return {
        "scene_count": len(scenes),
        "note_count": note_count,
        "high_priority_scene_count": high_priority,
        "issue_counts": dict(issue_counts),
    }


def _require_notes(data: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("notes"), list):
        raise SnvmError(f"{path} must contain a 'notes' list.")
    return [note for note in data["notes"] if isinstance(note, dict)]


def _scene_index(data: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        return {}
    return {
        str(scene.get("scene_id")): scene
        for scene in data["scenes"]
        if isinstance(scene, dict)
    }


def _timing_index(data: Any) -> dict[str, dict[str, Any]]:
    return _scene_index(data)


def _clean_note(note: dict[str, Any]) -> dict[str, Any]:
    time = _float_value(note.get("time"), 0.0)
    return {
        "time": round(time, 3),
        "timecode": _timecode(time),
        "issue_type": str(note.get("issue_type") or "other"),
        "issue_label": ISSUE_LABELS.get(str(note.get("issue_type") or "other"), "Other"),
        "severity": str(note.get("severity") or "medium"),
        "note": str(note.get("note") or "").strip(),
    }


def _time_range(scene: dict[str, Any], notes: list[dict[str, Any]]) -> str:
    if scene:
        start = _float_value(scene.get("start_time"), 0.0)
        end = _float_value(scene.get("end_time"), start)
        return f"{_timecode(start)} - {_timecode(end)}"
    times = [_float_value(note.get("time"), 0.0) for note in notes]
    if not times:
        return "unknown"
    return f"around {_timecode(min(times))}"


def _highest_severity(notes: list[dict[str, Any]]) -> str:
    ranking = {"low": 1, "medium": 2, "high": 3}
    highest = "low"
    for note in notes:
        severity = str(note.get("severity") or "medium")
        if ranking.get(severity, 2) >= ranking.get(highest, 1):
            highest = severity
    return highest


def _first_text(notes: list[dict[str, Any]], key: str) -> str:
    for note in notes:
        value = str(note.get(key) or "").strip()
        if value:
            return value
    return ""


def _voiceover_text(scene: dict[str, Any]) -> str:
    return str(
        scene.get("reviewed_voiceover")
        or scene.get("final_voiceover")
        or scene.get("rewritten_voiceover")
        or scene.get("subtitle_text")
        or ""
    ).strip()


def _timing_needs_copy_review(timing: dict[str, Any]) -> bool:
    return str(timing.get("timing_action") or "") in {
        "review_copy_or_add_material",
        "add_explanatory_visual_time",
    }


def _has_manual_notes(notes: list[dict[str, Any]]) -> bool:
    return any(str(note.get("note") or "").strip() for note in notes)


def _scene_sort_key(item: tuple[str, list[dict[str, Any]]]) -> tuple[float, str]:
    scene_id, notes = item
    first_time = min((_float_value(note.get("time"), 0.0) for note in notes), default=0.0)
    return (first_time, scene_id)


def _timecode(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes = int(seconds // 60)
    secs = seconds - (minutes * 60)
    return f"{minutes:02d}:{secs:05.2f}"


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

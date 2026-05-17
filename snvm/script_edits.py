from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output
from .scene_plan import validate_scene_plan


def apply_script_edits(
    scene_plan_path: Path,
    edits_path: Path,
    output_dir: Path,
) -> Path:
    initialize_project_output(output_dir)
    if not scene_plan_path.exists():
        raise SnvmError(f"Scene plan does not exist: {scene_plan_path}")
    if not edits_path.exists():
        raise SnvmError(
            f"Script edits file does not exist: {edits_path}. "
            "Export script_edits.json from the review player first."
        )

    scene_plan = read_json(scene_plan_path)
    edits_data = read_json(edits_path)
    scenes = _require_scenes(scene_plan)
    edits_by_scene = _edits_by_scene_id(edits_data)

    reviewed_scenes = []
    applied = []
    for scene in scenes:
        updated = dict(scene)
        edit = edits_by_scene.get(str(scene.get("scene_id") or ""))
        if edit:
            revised_voiceover = str(edit.get("revised_voiceover") or "").strip()
            if revised_voiceover:
                updated["reviewed_voiceover"] = revised_voiceover
                updated["rewritten_voiceover"] = revised_voiceover
                updated["subtitle_text"] = revised_voiceover
                updated["script_revision_intents"] = edit.get("revision_intents", [])
                note = str(edit.get("note") or "").strip()
                if note:
                    updated["script_revision_note"] = note
                applied.append(updated.get("scene_id", ""))
        reviewed_scenes.append(updated)

    reviewed_plan = {
        "metadata": {
            **scene_plan.get("metadata", {}),
            "source_script_edits": str(edits_path),
            "script_edits_applied_at": _now_iso(),
            "script_edits_applied_count": len(applied),
            "script_edits_applied_scenes": applied,
        },
        "scenes": reviewed_scenes,
    }
    validate_scene_plan(reviewed_plan)
    return write_json(output_dir / "scene_plan.reviewed.json", reviewed_plan)


def _require_scenes(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")
    return data["scenes"]


def _edits_by_scene_id(data: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("edits"), list):
        raise SnvmError("Script edits JSON must contain an 'edits' list.")

    edits = {}
    for index, edit in enumerate(data["edits"], start=1):
        if not isinstance(edit, dict):
            raise SnvmError(f"Script edit {index} must be a JSON object.")
        scene_id = str(edit.get("scene_id") or "")
        if scene_id:
            edits[scene_id] = edit
    return edits


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

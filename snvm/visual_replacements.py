from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


REPLACE_RECOMMENDED_ACTIONS = {
    "replace_with_user_footage",
    "recreate_chart",
    "recreate_map",
    "add_explanatory_visual",
    "search_alternative_or_keep",
}


def generate_visual_replacement_manifest(scene_plan_path: Path, output_dir: Path) -> Path:
    initialize_project_output(output_dir)
    scene_plan = read_json(scene_plan_path)
    scenes = _require_scenes(scene_plan)

    replacements = []
    for scene in scenes:
        visual_action = str(scene.get("visual_action") or "keep_original")
        if visual_action not in REPLACE_RECOMMENDED_ACTIONS:
            continue
        replacements.append(
            {
                "scene_id": scene.get("scene_id", ""),
                "mode": _mode_for_visual_action(visual_action),
                "asset_path": "",
                "fit": "cover",
                "start_offset": 0,
                "visual_action": visual_action,
                "visual_suggestion": scene.get("visual_suggestion", ""),
                "replacement_difficulty": scene.get("replacement_difficulty", ""),
                "search_keywords": scene.get("search_keywords", []),
                "notes": "Fill asset_path when you have a replacement image or video.",
                "enabled": False,
            }
        )

    manifest = {
        "metadata": {
            "source_scene_plan": str(scene_plan_path),
            "generated_at": _now_iso(),
            "instructions": (
                "Set enabled=true and asset_path to replace a scene visual. "
                "Supported asset_path types: mp4, mov, m4v, jpg, jpeg, png, webp."
            ),
        },
        "replacements": replacements,
    }
    return write_json(output_dir / "visual_replacements.json", manifest)


def load_visual_replacements(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path or not path.exists():
        return {}

    manifest = read_json(path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("replacements"), list):
        raise SnvmError("Visual replacement manifest must contain a 'replacements' list.")

    replacements = {}
    for index, replacement in enumerate(manifest["replacements"], start=1):
        if not isinstance(replacement, dict):
            raise SnvmError(f"Replacement {index} must be a JSON object.")
        if not replacement.get("enabled"):
            continue
        scene_id = str(replacement.get("scene_id") or "")
        asset_path = str(replacement.get("asset_path") or "").strip()
        if not scene_id or not asset_path:
            continue
        replacements[scene_id] = replacement
    return replacements


def resolve_asset_path(asset_path: str, manifest_path: Path | None, output_dir: Path) -> Path:
    path = Path(asset_path)
    if path.is_absolute():
        return path

    candidates = []
    if manifest_path:
        candidates.append(manifest_path.parent / path)
    candidates.append(output_dir / path)
    candidates.append(Path.cwd() / path)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _require_scenes(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")
    return data["scenes"]


def _mode_for_visual_action(visual_action: str) -> str:
    if visual_action == "recreate_chart":
        return "recreate_data_card"
    if visual_action == "recreate_map":
        return "recreate_map_card"
    if visual_action == "add_explanatory_visual":
        return "add_explanatory_visual"
    return "replace"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

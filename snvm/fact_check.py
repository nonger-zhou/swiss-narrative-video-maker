import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


URL_PATTERN = re.compile(r"https?://[^\s)>\]\"']+")


def generate_fact_check_summary(
    fact_checks_path: Path,
    scene_plan_path: Path | None,
    output_dir: Path,
) -> tuple[Path, Path]:
    initialize_project_output(output_dir)
    if not fact_checks_path.exists():
        raise SnvmError(
            f"Fact-check notes file does not exist: {fact_checks_path}. "
            "Export fact_check_notes.json from the review player first."
        )

    data = read_json(fact_checks_path)
    fact_checks = _require_fact_checks(data, fact_checks_path)
    scenes = _scene_index(read_json(scene_plan_path)) if scene_plan_path and scene_plan_path.exists() else {}
    entries = _build_entries(fact_checks, scenes)
    summary = {
        "metadata": {
            "source_fact_checks": str(fact_checks_path),
            "source_scene_plan": str(scene_plan_path) if scene_plan_path else None,
            "generated_at": _now_iso(),
            "instructions": (
                "Use this summary to decide what to change in scene_review.json or "
                "scene_plan.reviewed.json. It records external fact-check output but does not "
                "judge source reliability automatically."
            ),
        },
        "summary": _summary(entries),
        "scenes": entries,
    }
    json_path = write_json(output_dir / "fact_check_summary.json", summary)
    markdown_path = _write_markdown(output_dir / "fact_check_summary.md", summary)
    return json_path, markdown_path


def _build_entries(
    fact_checks: list[dict[str, Any]],
    scenes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_scene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in fact_checks:
        by_scene[str(item.get("scene_id") or "unknown")].append(item)

    entries = []
    for scene_id, checks in sorted(by_scene.items(), key=_scene_sort_key):
        scene = scenes.get(scene_id, {})
        normalized_checks = [_normalize_check(check) for check in checks]
        all_links = []
        for check in normalized_checks:
            all_links.extend(check["source_links"])
        entries.append(
            {
                "scene_id": scene_id,
                "time_range": _time_range(scene, checks),
                "check_count": len(normalized_checks),
                "source_links": sorted(set(all_links)),
                "suggested_next_step": _suggest_next_step(normalized_checks),
                "context": {
                    "source_text": _first_text(checks, "source_text"),
                    "literal_translation": _first_text(checks, "literal_translation"),
                    "voiceover": _first_text(checks, "voiceover") or _voiceover_text(scene),
                },
                "checks": normalized_checks,
            }
        )
    return entries


def _normalize_check(check: dict[str, Any]) -> dict[str, Any]:
    result_text = str(check.get("result_text") or "").strip()
    return {
        "created_at": check.get("created_at", ""),
        "time": _float_value(check.get("time"), 0.0),
        "timecode": _timecode(_float_value(check.get("time"), 0.0)),
        "selected_text": str(check.get("selected_text") or "").strip(),
        "checked_text": str(check.get("checked_text") or "").strip(),
        "result_text": result_text,
        "source_links": _extract_links(result_text),
        "possible_status": _guess_status(result_text),
    }


def _write_markdown(path: Path, summary: dict[str, Any]) -> Path:
    lines = [
        "# Fact Check Summary",
        "",
        "This file summarizes external fact-check results pasted in the review player.",
        "It does not verify sources automatically; use the links and notes to revise copy.",
        "",
        "## Summary",
        "",
        f"- Scenes with fact checks: {summary['summary']['scene_count']}",
        f"- Total fact checks: {summary['summary']['check_count']}",
        f"- Source links found: {summary['summary']['source_link_count']}",
        "",
    ]
    for scene in summary["scenes"]:
        lines.extend(
            [
                f"## {scene['scene_id']}  {scene['time_range']}",
                "",
                f"- Fact checks: {scene['check_count']}",
                f"- Suggested next step: {scene['suggested_next_step']}",
                "",
                "Voiceover:",
                "",
                f"> {scene['context'].get('voiceover') or '(empty)'}",
                "",
            ]
        )
        if scene["source_links"]:
            lines.append("Source links:")
            lines.append("")
            for link in scene["source_links"]:
                lines.append(f"- {link}")
            lines.append("")
        for index, check in enumerate(scene["checks"], start=1):
            lines.extend(
                [
                    f"### Check {index}  {check['timecode']}",
                    "",
                    f"- Possible status: {check['possible_status']}",
                    "",
                    "Checked text:",
                    "",
                    f"> {check['checked_text'] or check['selected_text'] or '(none)'}",
                    "",
                    "External result:",
                    "",
                    check["result_text"] or "(empty)",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    link_count = sum(len(entry["source_links"]) for entry in entries)
    check_count = sum(entry["check_count"] for entry in entries)
    return {
        "scene_count": len(entries),
        "check_count": check_count,
        "source_link_count": link_count,
    }


def _require_fact_checks(data: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("fact_checks"), list):
        raise SnvmError(f"{path} must contain a 'fact_checks' list.")
    return [item for item in data["fact_checks"] if isinstance(item, dict)]


def _scene_index(data: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        return {}
    return {
        str(scene.get("scene_id")): scene
        for scene in data["scenes"]
        if isinstance(scene, dict)
    }


def _extract_links(text: str) -> list[str]:
    return [link.rstrip(".,;") for link in URL_PATTERN.findall(text)]


def _guess_status(text: str) -> str:
    lowered = text.lower()
    if any(term in text for term in ("错误", "不准确", "证据不足", "有争议")):
        return "needs_revision"
    if any(term in text for term in ("过时", "旧数据", "最新数据")):
        return "check_current_data"
    if any(term in text for term in ("可信", "基本正确", "可以支持")):
        return "likely_supported"
    if any(term in lowered for term in ("incorrect", "unsupported", "outdated", "conflicting")):
        return "needs_revision"
    if any(term in lowered for term in ("supported", "verified", "credible")):
        return "likely_supported"
    return "manual_review"


def _suggest_next_step(checks: list[dict[str, Any]]) -> str:
    statuses = {check["possible_status"] for check in checks}
    if "needs_revision" in statuses:
        return "Revise the claim or replace it with a more cautious sourced statement."
    if "check_current_data" in statuses:
        return "Update the claim with the newest available data and cite the year/source."
    if "manual_review" in statuses:
        return "Read the pasted result and decide whether the voiceover needs a source-aware rewrite."
    return "Keep the claim if the source and data definition are acceptable."


def _time_range(scene: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    if scene:
        start = _float_value(scene.get("start_time"), 0.0)
        end = _float_value(scene.get("end_time"), start)
        return f"{_timecode(start)} - {_timecode(end)}"
    times = [_float_value(check.get("time"), 0.0) for check in checks]
    if not times:
        return "unknown"
    return f"around {_timecode(min(times))}"


def _first_text(items: list[dict[str, Any]], key: str) -> str:
    for item in items:
        value = str(item.get(key) or "").strip()
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


def _scene_sort_key(item: tuple[str, list[dict[str, Any]]]) -> tuple[float, str]:
    scene_id, checks = item
    first_time = min((_float_value(check.get("time"), 0.0) for check in checks), default=0.0)
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

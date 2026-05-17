import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output
from .subtitles import write_scene_srt
from .visual_replacements import load_visual_replacements, resolve_asset_path


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def compose_draft_video(
    source_path: Path,
    scene_plan_path: Path,
    voiceover_path: Path,
    output_dir: Path,
) -> Path:
    if not source_path.exists():
        raise SnvmError(f"Source video does not exist: {source_path}")
    if not voiceover_path.exists():
        raise SnvmError(f"Voiceover audio does not exist: {voiceover_path}")
    if not is_ffmpeg_available():
        raise SnvmError("ffmpeg is not installed or not available in PATH.")

    initialize_project_output(output_dir)
    voiceover_duration = _probe_duration(voiceover_path)
    subtitle_path = write_scene_srt(
        scene_plan_path,
        output_dir / "subtitles" / "scene_plan.srt",
        target_duration=voiceover_duration,
    )
    final_path = output_dir / "final.mp4"

    command = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(source_path),
        "-i",
        str(voiceover_path),
        "-i",
        str(subtitle_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map",
        "2:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-c:a",
        "aac",
        "-c:s",
        "mov_text",
        "-shortest",
        str(final_path),
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SnvmError(f"ffmpeg failed with exit code {exc.returncode}") from exc

    if not final_path.exists():
        raise SnvmError(f"ffmpeg finished but did not create {final_path}")

    write_json(
        output_dir / "composition_metadata.json",
        {
            "source_path": str(source_path),
            "scene_plan_path": str(scene_plan_path),
            "voiceover_path": str(voiceover_path),
            "voiceover_duration": voiceover_duration,
            "subtitle_path": str(subtitle_path),
            "final_path": str(final_path),
            "generated_at": _now_iso(),
            "note": (
                "Basic draft composition loops the source video as needed, replaces audio "
                "with generated voiceover, and embeds Chinese subtitles as an MP4 subtitle track."
            ),
        },
    )
    return final_path


def compose_scene_based_draft(
    source_path: Path,
    scene_plan_path: Path,
    timing_plan_path: Path,
    voiceover_path: Path,
    output_dir: Path,
    visual_replacements_path: Path | None = None,
) -> Path:
    if not source_path.exists():
        raise SnvmError(f"Source video does not exist: {source_path}")
    if not scene_plan_path.exists():
        raise SnvmError(f"Scene plan does not exist: {scene_plan_path}")
    if not timing_plan_path.exists():
        raise SnvmError(f"Timing plan does not exist: {timing_plan_path}")
    if not voiceover_path.exists():
        raise SnvmError(f"Voiceover audio does not exist: {voiceover_path}")
    if not is_ffmpeg_available():
        raise SnvmError("ffmpeg is not installed or not available in PATH.")

    initialize_project_output(output_dir)
    scene_plan = read_json(scene_plan_path)
    timing_plan = read_json(timing_plan_path)
    scenes = _require_scenes(scene_plan)
    timing_by_scene_id = _timing_by_scene_id(timing_plan)
    visual_replacements = load_visual_replacements(visual_replacements_path)

    work_dir = output_dir / "clips" / "scene_composer"
    work_dir.mkdir(parents=True, exist_ok=True)
    clip_records = []
    for index, scene in enumerate(scenes, start=1):
        timing = timing_by_scene_id.get(scene.get("scene_id"), {})
        clip_path = work_dir / f"{index:03d}_{scene.get('scene_id', f'scene_{index:03d}')}.mp4"
        replacement = visual_replacements.get(str(scene.get("scene_id") or ""))
        if replacement:
            clip_record = _render_replacement_clip(
                replacement,
                visual_replacements_path,
                output_dir,
                scene,
                timing,
                clip_path,
            )
        else:
            clip_record = _render_scene_clip(source_path, scene, timing, clip_path)
        clip_records.append(clip_record)

    concat_list_path = work_dir / "concat.txt"
    concat_list_path.write_text(
        "\n".join(f"file '{_ffmpeg_concat_path(record['path'])}'" for record in clip_records),
        encoding="utf-8",
    )

    silent_video_path = work_dir / "scene_video.mp4"
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list_path),
            "-c",
            "copy",
            str(silent_video_path),
        ]
    )

    subtitle_path = _write_scene_based_srt(clip_records, output_dir / "subtitles" / "scene_based.srt")
    final_path = output_dir / "final_scenes.mp4"
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video_path),
            "-i",
            str(voiceover_path),
            "-i",
            str(subtitle_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-map",
            "2:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-c:s",
            "mov_text",
            "-shortest",
            str(final_path),
        ]
    )

    if not final_path.exists():
        raise SnvmError(f"ffmpeg finished but did not create {final_path}")

    write_json(
        output_dir / "scene_composition_metadata.json",
        {
            "source_path": str(source_path),
            "scene_plan_path": str(scene_plan_path),
            "timing_plan_path": str(timing_plan_path),
            "voiceover_path": str(voiceover_path),
            "visual_replacements_path": str(visual_replacements_path) if visual_replacements_path else None,
            "subtitle_path": str(subtitle_path),
            "final_path": str(final_path),
            "generated_at": _now_iso(),
            "clips": [
                {
                    "scene_id": record["scene_id"],
                    "timing_action": record["timing_action"],
                    "source_duration": record["source_duration"],
                    "target_duration": record["target_duration"],
                    "render_action": record["render_action"],
                    "path": str(record["path"]),
                    "replacement_asset": record.get("replacement_asset"),
                    "replacement_mode": record.get("replacement_mode"),
                }
                for record in clip_records
            ],
            "note": (
                "Scene-based draft composition uses timing_plan.json to extend each scene "
                "locally. If visual_replacements.json enables a scene replacement, that "
                "scene is rendered from the provided image or video asset."
            ),
        },
    )
    return final_path


def _probe_duration(path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        return None

    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def _render_scene_clip(
    source_path: Path,
    scene: dict[str, Any],
    timing: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    start = _float_value(scene.get("start_time"), 0.0)
    end = _float_value(scene.get("end_time"), start)
    source_duration = round(max(0.1, end - start), 3)
    estimated_target = _float_value(timing.get("estimated_voiceover_duration"), source_duration)
    target_duration = round(max(0.5, estimated_target), 3)
    timing_action = str(timing.get("timing_action") or "keep_timing")
    render_action = _render_action(timing_action, source_duration, target_duration)

    if render_action == "trim":
        command = _scene_input_command(source_path, start, target_duration, output_path)
    elif render_action == "slow":
        factor = min(2.0, target_duration / source_duration)
        command = _scene_filter_command(
            source_path,
            start,
            source_duration,
            output_path,
            f"setpts={factor:.6f}*PTS,trim=duration={target_duration:.3f}",
        )
    else:
        freeze_duration = max(0.0, target_duration - source_duration)
        command = _scene_filter_command(
            source_path,
            start,
            source_duration,
            output_path,
            f"tpad=stop_mode=clone:stop_duration={freeze_duration:.3f},trim=duration={target_duration:.3f}",
        )

    _run_ffmpeg(command)
    if not output_path.exists():
        raise SnvmError(f"ffmpeg finished but did not create scene clip {output_path}")

    return {
        "scene_id": scene.get("scene_id", ""),
        "text": _scene_text(scene),
        "timing_action": timing_action,
        "source_duration": source_duration,
        "target_duration": target_duration,
        "render_action": render_action,
        "path": output_path,
    }


def _render_replacement_clip(
    replacement: dict[str, Any],
    manifest_path: Path | None,
    output_dir: Path,
    scene: dict[str, Any],
    timing: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    asset_path = resolve_asset_path(str(replacement.get("asset_path") or ""), manifest_path, output_dir)
    if not asset_path.exists():
        raise SnvmError(f"Replacement asset does not exist: {asset_path}")

    start = _float_value(scene.get("start_time"), 0.0)
    end = _float_value(scene.get("end_time"), start)
    source_duration = round(max(0.1, end - start), 3)
    target_duration = round(
        max(0.5, _float_value(timing.get("estimated_voiceover_duration"), source_duration)),
        3,
    )
    timing_action = str(timing.get("timing_action") or "keep_timing")
    suffix = asset_path.suffix.lower()

    if suffix in {".mp4", ".mov", ".m4v"}:
        command = _replacement_video_command(asset_path, replacement, target_duration, output_path)
        render_action = "replacement_video"
    elif suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        command = _replacement_image_command(asset_path, replacement, target_duration, output_path)
        render_action = "replacement_image"
    else:
        raise SnvmError(
            "Unsupported replacement asset type. Use mp4, mov, m4v, jpg, jpeg, png, or webp: "
            f"{asset_path}"
        )

    _run_ffmpeg(command)
    if not output_path.exists():
        raise SnvmError(f"ffmpeg finished but did not create replacement clip {output_path}")

    return {
        "scene_id": scene.get("scene_id", ""),
        "text": _scene_text(scene),
        "timing_action": timing_action,
        "source_duration": source_duration,
        "target_duration": target_duration,
        "render_action": render_action,
        "path": output_path,
        "replacement_asset": str(asset_path),
        "replacement_mode": replacement.get("mode"),
    }


def _scene_input_command(
    source_path: Path,
    start: float,
    duration: float,
    output_path: Path,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(source_path),
        "-an",
        "-vf",
        _base_video_filter(),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]


def _scene_filter_command(
    source_path: Path,
    start: float,
    duration: float,
    output_path: Path,
    timing_filter: str,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(source_path),
        "-an",
        "-vf",
        f"{_base_video_filter()},{timing_filter}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]


def _replacement_video_command(
    asset_path: Path,
    replacement: dict[str, Any],
    duration: float,
    output_path: Path,
) -> list[str]:
    start_offset = max(0.0, _float_value(replacement.get("start_offset"), 0.0))
    video_filter = _replacement_video_filter(replacement)
    return [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-ss",
        f"{start_offset:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(asset_path),
        "-an",
        "-vf",
        video_filter,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]


def _replacement_image_command(
    asset_path: Path,
    replacement: dict[str, Any],
    duration: float,
    output_path: Path,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(asset_path),
        "-an",
        "-vf",
        _replacement_video_filter(replacement),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]


def _base_video_filter() -> str:
    return "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=25"


def _replacement_video_filter(replacement: dict[str, Any]) -> str:
    fit = str(replacement.get("fit") or "contain").lower()
    if fit == "cover":
        return (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,fps=25"
        )
    return _base_video_filter()


def _render_action(timing_action: str, source_duration: float, target_duration: float) -> str:
    if target_duration <= source_duration * 1.05:
        return "trim"
    if timing_action in {"slightly_extend_scene", "extend_or_slow_scene"} and (
        target_duration / source_duration
    ) <= 1.7:
        return "slow"
    return "freeze_tail"


def _write_scene_based_srt(clip_records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    cursor = 0.0
    for record in clip_records:
        text = str(record.get("text") or "").strip()
        duration = _float_value(record.get("target_duration"), 0.0)
        start = cursor
        end = cursor + max(0.5, duration)
        cursor = end
        if not text:
            continue
        blocks.append(f"{len(blocks) + 1}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}\n")

    if not blocks:
        raise SnvmError("Scene plan has no subtitle text.")

    output_path.write_text("\n".join(blocks), encoding="utf-8")
    return output_path


def _run_ffmpeg(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SnvmError(f"ffmpeg failed with exit code {exc.returncode}") from exc


def _timing_by_scene_id(timing_plan: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(timing_plan, dict) or not isinstance(timing_plan.get("scenes"), list):
        raise SnvmError("Timing plan must contain a 'scenes' list.")
    return {
        str(scene.get("scene_id")): scene
        for scene in timing_plan["scenes"]
        if isinstance(scene, dict)
    }


def _require_scenes(scene_plan: Any) -> list[dict[str, Any]]:
    if not isinstance(scene_plan, dict) or not isinstance(scene_plan.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")
    return scene_plan["scenes"]


def _scene_text(scene: dict[str, Any]) -> str:
    return str(
        scene.get("reviewed_voiceover")
        or scene.get("final_voiceover")
        or scene.get("subtitle_text")
        or scene.get("rewritten_voiceover")
        or ""
    ).strip()


def _ffmpeg_concat_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "'\\''")


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

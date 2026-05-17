import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .errors import SnvmError
from .jsonio import write_json
from .pipeline import initialize_project_output
from .subtitles import write_scene_srt


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

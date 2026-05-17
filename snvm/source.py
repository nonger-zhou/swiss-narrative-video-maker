import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .errors import SnvmError
from .certificates import apply_certifi_environment
from .pipeline import initialize_project_output


@dataclass(frozen=True)
class SourceMetadata:
    input: str
    input_type: str
    source_path: str
    prepared_at: str


def prepare_source(input_value: str, output_dir: Path) -> SourceMetadata:
    initialize_project_output(output_dir)

    if _is_url(input_value):
        return _prepare_youtube_source(input_value, output_dir)

    return _prepare_local_source(Path(input_value), output_dir)


def save_source_metadata(metadata: SourceMetadata, output_dir: Path) -> Path:
    path = output_dir / "source_metadata.json"
    path.write_text(
        json.dumps(asdict(metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _prepare_local_source(input_path: Path, output_dir: Path) -> SourceMetadata:
    if not input_path.exists():
        raise SnvmError(f"Local source file does not exist: {input_path}")

    if not input_path.is_file():
        raise SnvmError(f"Local source is not a file: {input_path}")

    if input_path.suffix.lower() != ".mp4":
        raise SnvmError(f"Only .mp4 local files are supported in this task: {input_path}")

    target_path = output_dir / "source.mp4"

    try:
        if input_path.resolve() != target_path.resolve():
            shutil.copy2(input_path, target_path)
    except OSError as exc:
        raise SnvmError(f"Could not copy local video to {target_path}: {exc}") from exc

    return SourceMetadata(
        input=str(input_path),
        input_type="local_mp4",
        source_path=str(target_path),
        prepared_at=_now_iso(),
    )


def _prepare_youtube_source(url: str, output_dir: Path) -> SourceMetadata:
    if not shutil.which("yt-dlp"):
        raise SnvmError(
            "yt-dlp is not installed or not available in PATH. "
            "Install it before preparing YouTube sources."
        )

    target_path = output_dir / "source.mp4"
    command = [
        "yt-dlp",
        "--compat-options",
        "no-certifi",
        "--no-playlist",
        "--force-overwrites",
        "--no-continue",
        "-f",
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "--merge-output-format",
        "mp4",
        "-o",
        str(target_path),
        url,
    ]

    try:
        apply_certifi_environment()
        subprocess.run(command, check=True, env=os.environ.copy())
    except subprocess.CalledProcessError as exc:
        raise SnvmError(f"yt-dlp failed with exit code {exc.returncode}") from exc

    if not target_path.exists():
        raise SnvmError(f"yt-dlp finished but did not create {target_path}")

    return SourceMetadata(
        input=url,
        input_type="youtube_url",
        source_path=str(target_path),
        prepared_at=_now_iso(),
    )


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

import importlib.util
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .certificates import apply_certifi_environment
from .pipeline import initialize_project_output


@dataclass(frozen=True)
class TranscriptSegment:
    id: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptMetadata:
    source_path: str
    model: str
    device: str
    compute_type: str
    language: str | None
    detected_language: str | None
    detected_language_probability: float | None
    duration: float | None
    transcribed_at: str


@dataclass(frozen=True)
class Transcript:
    metadata: TranscriptMetadata
    segments: list[TranscriptSegment]


def is_faster_whisper_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def transcribe_source(
    source_path: Path,
    output_dir: Path,
    model_name: str,
    *,
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
) -> Path:
    if not source_path.exists():
        raise SnvmError(f"Source video does not exist: {source_path}")

    if not source_path.is_file():
        raise SnvmError(f"Source path is not a file: {source_path}")

    if not is_faster_whisper_available():
        raise SnvmError(
            "faster-whisper is not installed or not available in this Python environment. "
            "Install project requirements before running transcription."
        )

    apply_certifi_environment()
    initialize_project_output(output_dir)

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SnvmError(f"Could not import faster-whisper: {exc}") from exc

    try:
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        raw_segments, info = model.transcribe(str(source_path), language=language)
        segments = [
            TranscriptSegment(
                id=index,
                start=round(float(segment.start), 3),
                end=round(float(segment.end), 3),
                text=segment.text.strip(),
            )
            for index, segment in enumerate(raw_segments, start=1)
        ]
    except Exception as exc:
        raise SnvmError(f"Transcription failed: {exc}") from exc

    transcript = Transcript(
        metadata=TranscriptMetadata(
            source_path=str(source_path),
            model=model_name,
            device=device,
            compute_type=compute_type,
            language=language,
            detected_language=_get_info_value(info, "language"),
            detected_language_probability=_get_float_info_value(info, "language_probability"),
            duration=_get_float_info_value(info, "duration"),
            transcribed_at=_now_iso(),
        ),
        segments=segments,
    )

    transcript_path = output_dir / "transcript.json"
    transcript_path.write_text(
        json.dumps(_to_json_dict(transcript), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return transcript_path


def _to_json_dict(transcript: Transcript) -> dict[str, Any]:
    return {
        "metadata": asdict(transcript.metadata),
        "segments": [asdict(segment) for segment in transcript.segments],
    }


def _get_info_value(info: Any, name: str) -> Any:
    return getattr(info, name, None)


def _get_float_info_value(info: Any, name: str) -> float | None:
    value = _get_info_value(info, name)
    if value is None:
        return None
    return round(float(value), 3)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

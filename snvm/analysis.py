import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .certificates import certifi_ssl_context
from .config import Settings
from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def analyze_transcript(
    transcript_path: Path,
    output_dir: Path,
    settings: Settings,
) -> tuple[Path, Path]:
    if not settings.openai_api_key:
        raise SnvmError("OPENAI_API_KEY is missing. Add it to .env before running analysis.")

    initialize_project_output(output_dir)
    transcript = read_json(transcript_path)
    segments = _read_transcript_segments(transcript)

    translation_segments = []
    structure_segments = []
    opening_hook = ""
    visual_rhythm_notes = []
    memorable_lines = []
    ending_viewpoint = ""
    main_information_points = []

    chunks = list(_chunk_segments(segments, max_segments=35, max_chars=3500))
    for index, chunk in enumerate(chunks, start=1):
        analysis = _request_analysis_chunk(chunk, settings, index, len(chunks))
        translation_segments.extend(_require_list(analysis, "translation_segments"))
        structure_segments.extend(_require_list(analysis, "structure_segments"))

        if not opening_hook:
            opening_hook = str(analysis.get("opening_hook", ""))
        if index == len(chunks):
            ending_viewpoint = str(analysis.get("ending_viewpoint", ""))
        visual_rhythm = str(analysis.get("visual_rhythm", ""))
        if visual_rhythm:
            visual_rhythm_notes.append(visual_rhythm)
        memorable_lines.extend(_coerce_string_list(analysis.get("memorable_lines", [])))
        main_information_points.extend(
            _coerce_string_list(analysis.get("main_information_points", []))
        )

    translation = {
        "metadata": {
            "source_transcript": str(transcript_path),
            "model": settings.openai_model,
            "chunks": len(chunks),
            "generated_at": _now_iso(),
        },
        "segments": translation_segments,
    }
    structure = {
        "metadata": {
            "source_transcript": str(transcript_path),
            "model": settings.openai_model,
            "chunks": len(chunks),
            "generated_at": _now_iso(),
        },
        "opening_hook": opening_hook,
        "main_information_points": _dedupe(main_information_points),
        "visual_rhythm": "\n".join(visual_rhythm_notes),
        "memorable_lines": _dedupe(memorable_lines),
        "ending_viewpoint": ending_viewpoint,
        "segments": structure_segments,
    }

    translation_path = write_json(output_dir / "translation.json", translation)
    structure_path = write_json(output_dir / "structure_analysis.json", structure)
    return translation_path, structure_path


def _request_analysis_chunk(
    segments: list[dict[str, Any]],
    settings: Settings,
    chunk_index: int,
    chunk_count: int,
) -> dict[str, Any]:
    request_payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You analyze reference videos for a Chinese creator. Preserve the original "
                    "segment order, narrative rhythm, and information progression. Return only "
                    "valid JSON matching the requested shape."
                ),
            },
            {
                "role": "user",
                "content": _build_analysis_prompt(segments, chunk_index, chunk_count),
            },
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    response = _post_openai_chat_completion(request_payload, settings.openai_api_key)
    content = _extract_message_content(response)
    return _parse_json_object(content)


def _build_analysis_prompt(
    segments: list[dict[str, Any]],
    chunk_index: int,
    chunk_count: int,
) -> str:
    return (
        f"This is transcript chunk {chunk_index} of {chunk_count}. Analyze only this chunk, "
        "while preserving global segment ids and order.\n\n"
        "Analyze this timestamped transcript and return JSON with this exact top-level shape:\n"
        "{\n"
        '  "translation_segments": [\n'
        '    {"id": 1, "start": 0.0, "end": 4.2, "source_text": "", "translated_text": ""}\n'
        "  ],\n"
        '  "opening_hook": "",\n'
        '  "main_information_points": [""],\n'
        '  "visual_rhythm": "",\n'
        '  "memorable_lines": [""],\n'
        '  "ending_viewpoint": "",\n'
        '  "structure_segments": [\n'
        "    {\n"
        '      "id": 1,\n'
        '      "narrative_role": "",\n'
        '      "source_summary": "",\n'
        '      "rewritten_voiceover": "",\n'
        '      "visual_material_type": "",\n'
        '      "visual_action": "keep_original",\n'
        '      "visual_suggestion": "",\n'
        '      "replacement_difficulty": "medium",\n'
        '      "alternative_source_suggestions": [""],\n'
        '      "search_keywords": [""],\n'
        '      "fallback_action": "keep_original"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Keep the same segment ids, order, timestamps, and narrative progression.\n"
        "- Translate into natural Chinese, not word-by-word Chinese.\n"
        "- rewritten_voiceover must be original Chinese narration that stays faithful to each segment role.\n"
        "- visual_action must be one of: keep_original, replace_with_user_footage, recreate_chart, "
        "recreate_map, add_explanatory_visual, search_alternative_or_keep, remove.\n"
        "- replacement_difficulty must be easy, medium, or hard.\n\n"
        f"Transcript segments:\n{json.dumps(segments, ensure_ascii=False, indent=2)}"
    )


def _post_openai_chat_completion(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300, context=certifi_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SnvmError(f"OpenAI API request failed with HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise SnvmError(f"Could not reach OpenAI API: {exc.reason}") from exc
    except TimeoutError as exc:
        raise SnvmError("OpenAI API request timed out.") from exc


def _extract_message_content(response: dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SnvmError("OpenAI API returned an unexpected response shape.") from exc


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SnvmError(f"OpenAI response was not valid JSON: {exc}") from exc

    if not isinstance(value, dict):
        raise SnvmError("OpenAI response JSON must be an object.")
    return value


def _read_transcript_segments(transcript: Any) -> list[dict[str, Any]]:
    if not isinstance(transcript, dict) or not isinstance(transcript.get("segments"), list):
        raise SnvmError("Transcript JSON must contain a 'segments' list.")
    return transcript["segments"]


def _chunk_segments(
    segments: list[dict[str, Any]],
    *,
    max_segments: int,
    max_chars: int,
) -> list[list[dict[str, Any]]]:
    chunks = []
    current = []
    current_chars = 0
    for segment in segments:
        segment_chars = len(str(segment.get("text", "")))
        if current and (len(current) >= max_segments or current_chars + segment_chars > max_chars):
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(segment)
        current_chars += segment_chars
    if current:
        chunks.append(current)
    return chunks


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise SnvmError(f"OpenAI response JSON must contain a '{key}' list.")
    return value


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

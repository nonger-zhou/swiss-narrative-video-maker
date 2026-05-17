# Task 004: Transcription

## Goal

Add a transcription step after source preparation. The command reads a prepared video and writes timestamped transcript segments to `output/transcript.json`.

## Scope

- Add a CLI command for transcription.
- Use `faster-whisper`.
- Read `output/source.mp4` by default.
- Allow model selection through `WHISPER_MODEL` or a CLI override.
- Write a stable JSON file with metadata and timestamped segments.
- Give clear errors when the source file or dependency is missing.

## Out Of Scope

- Translation.
- Narrative structure analysis.
- Chinese rewriting.
- Scene plan generation.
- Voiceover generation.
- Video composition.

## Output

```text
output/
  transcript.json
```

## CLI

```powershell
python -m snvm transcribe
python -m snvm transcribe --source output/source.mp4 --model small
```

## Transcript Shape

```json
{
  "metadata": {
    "source_path": "output/source.mp4",
    "model": "small",
    "device": "cpu",
    "compute_type": "int8",
    "language": null,
    "detected_language": "en",
    "detected_language_probability": 0.98,
    "duration": 123.45,
    "transcribed_at": "2026-05-16T00:00:00+00:00"
  },
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 4.2,
      "text": "Original transcript text."
    }
  ]
}
```

## Verification

- `python -m snvm transcribe` reports a clear error if `output/source.mp4` is missing.
- `python -m snvm doctor` reports whether `faster-whisper` is available.
- `python -m compileall snvm` passes.

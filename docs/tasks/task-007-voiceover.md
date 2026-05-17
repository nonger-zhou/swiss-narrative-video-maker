# Task 007: Voiceover

## Goal

Generate Chinese narration audio from `output/scene_plan.json`.

## CLI

```powershell
python -m snvm voiceover
python -m snvm voiceover --voice zh-CN-XiaoxiaoNeural
```

## Output

```text
output/
  voiceover.mp3
  voiceover/
    voiceover.srt
    voiceover_metadata.json
```

## Notes

- Requires the `edge-tts` Python package.
- Uses `EDGE_TTS_VOICE` from `.env` unless overridden.

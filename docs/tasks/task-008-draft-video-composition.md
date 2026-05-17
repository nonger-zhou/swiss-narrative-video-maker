# Task 008: Draft Video Composition

## Goal

Compose a basic playable draft video from prepared source video, Chinese voiceover, and scene-plan subtitles.

## CLI

```powershell
python -m snvm compose
python -m snvm make-draft "C:\path\to\video.mp4"
```

## Output

```text
output/
  final.mp4
  subtitles/
    scene_plan.srt
  composition_metadata.json
```

## Notes

The first composer is intentionally simple. It loops the prepared source video if the generated Chinese narration is longer than the original clip, replaces the audio with `voiceover.mp3`, embeds a subtitle track, and writes `final.mp4`.

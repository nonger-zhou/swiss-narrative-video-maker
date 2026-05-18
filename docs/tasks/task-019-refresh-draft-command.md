# Task 019: Refresh Draft Command

## Goal

Make the post-edit rebuild workflow less fragile. After the creator edits scene scripts, they should not need to remember a long chain of commands. One command should apply script edits and rebuild the reviewed draft in the correct order.

## CLI

```powershell
python -m snvm refresh-draft
```

Default behavior:

1. Apply `output/script_edits.json` if present.
2. Regenerate `output/voiceover.mp3` from `output/scene_plan.reviewed.json`.
3. Regenerate `output/timing_plan.json`.
4. Compose `output/final_scenes.mp4`.
5. Regenerate `output/review_player.html`.

Preview without running text-to-speech or ffmpeg:

```powershell
python -m snvm refresh-draft --dry-run
```

## Options

- `--skip-script-edits`: use the existing scene plan without applying `script_edits.json`
- `--skip-compose`: regenerate script-dependent audio and timing, but skip video composition
- `--skip-review-player`: skip `review_player.html` generation
- `--voice`: override the Edge TTS voice
- `--visual-replacements`: provide a specific visual replacement manifest
- `--source`: provide a specific source video

## Notes

This command keeps scene order unchanged. It is designed for light and medium revision loops, not structural rearrangement.

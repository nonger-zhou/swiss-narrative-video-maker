# Task 012: Visual Alignment Review Player

## Goal

Create a local visual review page so the creator can watch the draft video and mark alignment problems while playing.

## CLI

```powershell
python -m snvm review-player
```

## Inputs

By default:

```text
output/
  final_scenes.mp4 or final.mp4
  scene_plan.reviewed.json or scene_plan.json
  timing_plan.json
```

## Outputs

```text
output/
  review_player.html
  review_player_data.json
```

The browser page can export:

```text
alignment_notes.json
```

## User Workflow

1. Run `python -m snvm review-player`.
2. Open `output/review_player.html`.
3. Play the draft video.
4. Mark issues such as:
   - Chinese voiceover is early.
   - Chinese voiceover is late.
   - visual does not match narration.
   - scene needs extra material.
   - copy is too long.
   - duplicate fact.
5. Export `alignment_notes.json`.

## Notes

This task only records alignment notes. A later task should consume exported notes and propose edits to `scene_review.json`, `timing_plan.json`, or scene boundaries.

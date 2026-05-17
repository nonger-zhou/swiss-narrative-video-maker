# Task 010: Scene Timing Plan

## Goal

Add an advisory timing step that explains what should happen when Chinese voiceover is longer than the source visual segment.

The goal is not to loop the whole video. The plan should identify which specific scenes need local extension, copy review, added B-roll, or explanatory visuals.

## CLI

```powershell
python -m snvm timing-plan
```

By default, it reads `output/scene_plan.reviewed.json` if present, otherwise `output/scene_plan.json`.

## Output

```text
output/
  timing_plan.json
```

## Timing Actions

- `keep_timing`
- `slightly_extend_scene`
- `extend_or_slow_scene`
- `add_explanatory_visual_time`
- `review_copy_or_add_material`
- `freeze_last_frame_or_add_broll`
- `remove_or_fill`
- `needs_manual_timing`

## Notes

This task does not replace the current draft composer. A later task should consume `timing_plan.json` and compose the video scene by scene.

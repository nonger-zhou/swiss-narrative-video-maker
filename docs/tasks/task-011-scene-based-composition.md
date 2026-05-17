# Task 011: Scene-Based Draft Composition

## Goal

Add a draft composer that consumes `timing_plan.json` and adjusts visuals per scene instead of looping the whole source video.

This task must not remove or replace the existing `compose` command. It adds a separate `compose-scenes` command so the older known-good composer remains available.

## CLI

```powershell
python -m snvm compose-scenes
python -m snvm compose-scenes --scene-plan output/scene_plan.reviewed.json
```

## Inputs

```text
output/
  source.mp4
  scene_plan.json or scene_plan.reviewed.json
  timing_plan.json
  voiceover.mp3
```

## Output

```text
output/
  final_scenes.mp4
  scene_composition_metadata.json
  subtitles/
    scene_based.srt
  clips/
    scene_composer/
```

## First Implementation

- `keep_timing`: cut the source scene normally.
- `slightly_extend_scene`: slow the scene locally when the required extension is small.
- `extend_or_slow_scene`: slow the scene locally when the stretch is still reasonable.
- `freeze_last_frame_or_add_broll`: freeze the scene's final frame for the extra time.
- `add_explanatory_visual_time`: hold the scene as a draft fallback until generated visual cards exist.
- `review_copy_or_add_material`: hold the scene as a draft fallback and preserve the warning in metadata.

## Later Work

- Generate real text cards, charts, and maps for explanatory visual time.
- Accept user-provided B-roll folders.
- Use real per-scene voiceover timings instead of estimated text duration.

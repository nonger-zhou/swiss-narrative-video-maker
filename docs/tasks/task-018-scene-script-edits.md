# Task 018: Scene Script Edits

## Goal

Support light and medium revision without changing the original scene order. The creator should be able to edit the final Chinese voiceover text for a scene, label why it was changed, export those edits, and apply them before regenerating voiceover, timing, subtitles, and video.

## Review Player

The review player adds a script editing panel for the current scene.

The creator can:

- edit the current scene's final Chinese voiceover text
- mark revision intents:
  - compress
  - deduplicate
  - fact fix
  - add explanation
  - more natural
  - needs source
- add a revision note
- save the current scene's script edit
- export `script_edits.json`

The player keeps the original scene order. It does not reorder scenes or alter visual sequence.

## CLI

```powershell
python -m snvm apply-script-edits
```

By default, the command reads:

```text
output/script_edits.json
output/scene_plan.reviewed.json
```

If `scene_plan.reviewed.json` is missing, it falls back to:

```text
output/scene_plan.json
```

It writes:

```text
output/scene_plan.reviewed.json
```

## Follow-Up Pipeline

After applying script edits, regenerate downstream outputs:

```powershell
python -m snvm voiceover --scene-plan output/scene_plan.reviewed.json
python -m snvm timing-plan --scene-plan output/scene_plan.reviewed.json
python -m snvm compose-scenes --scene-plan output/scene_plan.reviewed.json
python -m snvm review-player
```

## Notes

This task does not automatically rewrite text with AI. It records and applies human edits. Later tasks can add assisted rewrite suggestions based on fact-check summaries and revision plans.

# Task 009: Human Review Layer

## Goal

Add a review step that lets the creator inspect and edit the Chinese narration before voiceover generation.

The review layer must not replace the existing automatic pipeline. It is an optional quality-control step after `scene-plan`.

## CLI

```powershell
python -m snvm review
python -m snvm apply-review
```

## Outputs

```text
output/
  scene_review.md
  scene_review.json
  scene_plan.reviewed.json
```

## Review Fields

Each scene review shows:

- original transcript
- literal Chinese translation
- rewritten Chinese voiceover
- estimated source and voiceover duration
- warning for over-expanded rewrite
- warning for likely repeated facts
- user note
- final voiceover

## Workflow

1. Run `python -m snvm review`.
2. Read `output/scene_review.md`.
3. Edit `output/scene_review.json`, especially `final_voiceover`.
4. Run `python -m snvm apply-review`.
5. Generate voiceover and compose with `output/scene_plan.reviewed.json`.

## Non-Goals

- No UI editor yet.
- No automatic deletion of repeated scenes.
- No forced rewrite of the existing scene plan.

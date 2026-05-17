# Task 016: Alignment Revision Plan

## Goal

Turn the creator's review-player markers into a concrete editing checklist. The system should not automatically rewrite good scenes; it should summarize what the human marked and recommend the safest next edit.

## CLI

```powershell
python -m snvm revision-plan
```

By default, the command reads:

```text
output/alignment_notes.json
output/scene_plan.reviewed.json
output/timing_plan.json
```

It writes:

```text
output/revision_plan.json
output/revision_plan.md
```

## Behavior

The revision plan groups alignment notes by `scene_id` and includes:

- number of notes per scene
- issue counts
- highest marked severity
- source text, literal translation, and voiceover context when present
- timing and visual context from existing plans
- recommended actions

Recommended actions include:

- adjust alignment when Chinese narration or subtitles are early/late
- review scene boundary or visual replacement when picture and narration do not match
- add material when the creator marks that extra visual material is needed
- compress copy when timing or creator notes indicate the voiceover is too long
- deduplicate copy when a repeated fact is marked

## Notes

This task is advisory. It does not edit `scene_review.json`, `scene_plan.reviewed.json`, `timing_plan.json`, or `visual_replacements.json`. Later tasks can apply selected actions after the creator reviews the plan.

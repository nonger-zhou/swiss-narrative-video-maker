# Task 013: Review Player Text Comparison

## Goal

Improve the visual alignment review player so the creator can compare the three text layers while watching:

- original transcript
- literal Chinese translation
- final Chinese voiceover

## CLI

```powershell
python -m snvm review-player
```

## Behavior

The player reads `output/scene_review.json` when available and embeds these fields into the HTML review data:

- `source_text`
- `literal_translation`
- `rewritten_voiceover`
- `final_voiceover`
- `ai_warnings`

Exported alignment notes include the current scene's source text, literal translation, and voiceover so later correction steps can reason about the issue without reopening all source files.

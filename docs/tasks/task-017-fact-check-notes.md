# Task 017: Fact Check Notes

## Goal

Close the loop between external fact checking and local revision. The creator should be able to paste a ChatGPT, Perplexity, or other research result back into the review player, export it, and generate a scene-level summary for later copy edits.

## Review Player

The fact-check panel lets the creator:

- copy a prepared fact-check prompt
- open external research tools
- paste the returned answer into a text box
- record that answer for the current scene
- export `fact_check_notes.json`

Each recorded fact check stores:

- current scene ID
- current video time
- selected or checked text
- source transcript, literal translation, and voiceover context
- pasted external result
- the prompt that was used

## CLI

```powershell
python -m snvm fact-check-summary
```

By default, the command reads:

```text
output/fact_check_notes.json
output/scene_plan.reviewed.json
```

It writes:

```text
output/fact_check_summary.json
output/fact_check_summary.md
```

## Behavior

The summary groups fact-check notes by scene, extracts source links from the pasted result, and gives a conservative suggested next step:

- revise unsupported or inaccurate claims
- update claims with newer data
- manually review ambiguous results
- keep claims that appear supported and are properly scoped

## Notes

This task does not automatically judge source reliability or rewrite the voiceover. It preserves the external result and organizes it for a later source-aware rewrite step.

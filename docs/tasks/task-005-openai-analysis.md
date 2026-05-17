# Task 005: OpenAI Translation And Structure Analysis

## Goal

Read `output/transcript.json`, call the OpenAI API, and write:

```text
output/
  translation.json
  structure_analysis.json
```

## CLI

```powershell
python -m snvm analyze
python -m snvm analyze --transcript output/transcript.json
```

## Notes

- Requires `OPENAI_API_KEY` in `.env`.
- Uses `OPENAI_MODEL`, defaulting to `gpt-4.1-mini`.
- The prompt asks the model to preserve segment order, timestamps, narrative rhythm, and information progression.
- Visual suggestions are plain JSON fields so they remain editable before later steps.

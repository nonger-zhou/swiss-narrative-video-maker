# Task 006: Scene Plan Generation

## Goal

Combine `translation.json` and `structure_analysis.json` into the editable scene plan required by the MVP.

## CLI

```powershell
python -m snvm scene-plan
```

## Output

```text
output/
  scene_plan.json
```

## Validation

The generator validates required scene fields, supported `visual_action` values, supported fallback actions, and replacement difficulty values.

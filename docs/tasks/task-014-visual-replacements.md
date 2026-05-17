# Task 014: Visual Replacement Manifest

## Goal

Make visual replacement practical without turning the MVP into a full timeline editor. The creator should be able to generate a scene-level checklist, add replacement assets later, and rerender only through the normal scene composer.

## CLI

```powershell
python -m snvm visual-replacements
python -m snvm compose-scenes --visual-replacements output/visual_replacements.json
```

## Behavior

`visual-replacements` reads the reviewed scene plan when available and writes `output/visual_replacements.json`. It includes scenes whose `visual_action` suggests replacement, recreation, or added explanatory visuals.

Each replacement entry starts disabled. To use one, set:

- `enabled`: `true`
- `asset_path`: image or video path

Supported assets:

- `mp4`
- `mov`
- `m4v`
- `jpg`
- `jpeg`
- `png`
- `webp`

When `compose-scenes` receives a manifest, it renders enabled replacement assets for matching scene IDs. Image assets are held for the scene duration. Video assets are looped locally if needed to fill the scene duration. Scenes without enabled replacements keep the existing source-video cut, slow, or freeze behavior.

## Notes

This task does not yet generate replacement images automatically and does not edit the manifest from the browser player. It creates the reliable file contract needed for those later UI and generation steps.

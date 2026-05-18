# Swiss Narrative Video Maker

Swiss Narrative Video Maker is a small local-first video creation pipeline for learning from strong reference videos and producing Chinese narrative drafts.

The first version is not a full editing suite. It is a command-line workflow that turns a YouTube URL or local video into:

- a transcript with timestamps
- Chinese translation
- narrative structure analysis
- an editable scene plan
- Chinese rewritten voiceover
- a simple draft video

The product principle is:

> Structure faithful, Chinese expression original, visuals judged scene by scene.

## MVP Goal

Input a YouTube link or local video. The system automatically transcribes, translates, analyzes the original narrative structure, and generates a Chinese voiceover script based on that structure. The first version is for learning, research, and creation drafts. It outputs an editable scene plan and a simple composed video.

## What This Tool Should Preserve

The tool should not freely reinvent the reference video. It should preserve, unless there is a clear reason not to:

- original segment order
- narrative rhythm
- information progression
- opening hook
- transitions
- ending viewpoint

The creative changes should mainly happen in:

- Chinese expression
- creator commentary
- explanation for Chinese audiences
- visual replacement or recreation suggestions
- optional additional diagrams or data visuals

## MVP Pipeline

1. Input source
   - YouTube URL
   - local mp4 file
2. Fetch source video
   - YouTube via `yt-dlp`
   - local video read directly
3. Transcribe audio
   - `faster-whisper`
   - timestamped segments
4. Analyze and rewrite
   - OpenAI API
   - translation
   - structure analysis
   - faithful Chinese rewrite
   - visual action suggestions
5. Generate scene plan
   - `scene_plan.json`
6. Generate voiceover
   - first version: `edge-tts`
7. Compose draft video
   - `ffmpeg`
   - keep original clip, recreate visuals, replace footage, or add simple generated background according to the scene plan
8. Export outputs
   - `output/final.mp4`

## Expected Output Files

```text
output/
  source.mp4
  transcript.json
  translation.json
  structure_analysis.json
  scene_plan.json
  voiceover.mp3
  final.mp4
```

## Visual Handling Rules

The tool should not force replacement with empty placeholder images.

For each scene, it should decide one of:

- keep original visual
- replace with user footage
- recreate chart, map, timeline, or diagram
- add a new explanatory visual
- search for alternative source material
- remove visual if unnecessary

Hard-to-replace historical material should be handled carefully. The tool should first suggest possible alternative sources and search keywords. If no reasonable alternative exists, it can recommend keeping the original visual and explain why.

## Not In Version 1

- no ComfyUI
- no complex AI image generation
- no account system
- no cloud deployment
- no professional timeline editor
- no fully automatic publishing workflow

## Development Approach

Development is split into small task branches. Each task should:

- have a clear scope
- update documentation when behavior changes
- produce intermediate files for debugging
- work on Windows
- give clear errors at each pipeline step

## Current CLI Skeleton

The current basic pipeline is command-line first.

```powershell
python -m snvm doctor
python -m snvm init --output output
python -m snvm prepare-source "C:\path\to\video.mp4"
python -m snvm prepare-source "https://www.youtube.com/watch?v=..."
python -m snvm transcribe
python -m snvm analyze
python -m snvm scene-plan
python -m snvm review
python -m snvm apply-review
python -m snvm timing-plan
python -m snvm visual-replacements
python -m snvm voiceover
python -m snvm compose
python -m snvm compose-scenes
python -m snvm review-player
python -m snvm revision-plan
python -m snvm fact-check-summary
python -m snvm apply-script-edits
python -m snvm refresh-draft
python -m snvm make-draft "C:\path\to\video.mp4"
```

If `python` is not available on Windows yet, install Python 3.11 or newer and make sure it is added to PATH.

The first draft composer keeps the pipeline practical: it loops the prepared source video if needed, replaces the audio with generated Chinese voiceover, embeds subtitles, and writes `output/final.mp4`.

## Optional Review Workflow

After `scene-plan`, you can generate review files before voiceover:

```powershell
python -m snvm review
```

This writes:

```text
output/
  scene_review.md
  scene_review.json
```

The review shows each scene's original transcript, literal Chinese translation, rewritten Chinese voiceover, timing risk, and possible repetition warnings. Edit `scene_review.json` fields such as `user_note` and `final_voiceover`, then apply it:

```powershell
python -m snvm apply-review
python -m snvm timing-plan
python -m snvm voiceover --scene-plan output/scene_plan.reviewed.json
python -m snvm compose --scene-plan output/scene_plan.reviewed.json
```

`timing-plan` writes `output/timing_plan.json`. It compares each scene's source duration with the estimated Chinese voiceover duration and recommends whether to keep timing, extend that scene locally, add explanatory visuals, add B-roll, or review/compress the copy.

For a scene-based draft that uses `timing_plan.json`, run:

```powershell
python -m snvm compose-scenes --scene-plan output/scene_plan.reviewed.json
```

This writes `output/final_scenes.mp4`. It keeps the older `compose` command available and unchanged.

To prepare scene-level visual swaps, generate a replacement manifest:

```powershell
python -m snvm visual-replacements
```

This writes `output/visual_replacements.json` for scenes whose visual action suggests replacement, recreation, or extra explanatory visuals. When you have a replacement image or video, set that scene's `enabled` field to `true` and fill `asset_path`. Then compose with:

```powershell
python -m snvm compose-scenes --visual-replacements output/visual_replacements.json
```

Supported replacement assets are `mp4`, `mov`, `m4v`, `jpg`, `jpeg`, `png`, and `webp`. Enabled replacements are rendered only for their matching scene; other scenes keep the existing source-video timing behavior.

To review alignment visually while watching the draft video, generate a local player:

```powershell
python -m snvm review-player
```

Open `output/review_player.html` in a browser. The page lets you play the video, jump scene by scene, mark alignment issues, and export `alignment_notes.json`.

The player also shows a three-column text comparison for the current scene:

- original transcript
- literal Chinese translation
- final Chinese voiceover

For fact checking, select any sentence in the player and use the fact-check buttons. The player can copy a prepared verification prompt or open ChatGPT, Perplexity, or Google with the current scene context. The prompt asks for source links, publication year, data definitions, and safer rewrite suggestions when a claim is too absolute.

If a subtitle break splits one factual claim across two captions, use the editable fact-check focus box to write the complete claim first. Saved fact-check results are shown under the current scene and can be copied into the script-edit note as source-aware revision context.

After checking a claim in an external tool, paste the returned answer back into the review player and record it for the current scene. Export `fact_check_notes.json`, then summarize it:

```powershell
python -m snvm fact-check-summary
```

This writes `output/fact_check_summary.json` and `output/fact_check_summary.md`, grouped by scene with extracted source links and suggested next steps for source-aware copy revision.

After exporting `alignment_notes.json` from the player, generate a revision plan:

```powershell
python -m snvm revision-plan
```

This writes:

```text
output/
  revision_plan.json
  revision_plan.md
```

The revision plan groups notes by scene and recommends whether to adjust timing, review scene boundaries, compress copy, deduplicate facts, or add replacement visuals. It is advisory and does not modify the scene plan automatically.

For light and medium script revision, edit the current scene's Chinese voiceover text in the review player and export `script_edits.json`. Apply those edits with:

```powershell
python -m snvm apply-script-edits
python -m snvm voiceover --scene-plan output/scene_plan.reviewed.json
python -m snvm timing-plan --scene-plan output/scene_plan.reviewed.json
python -m snvm compose-scenes --scene-plan output/scene_plan.reviewed.json
python -m snvm review-player
```

Script edits keep the original scene order. They are for compressing, deduplicating, correcting facts, adding short explanations, and making the Chinese voiceover more natural before regenerating audio and subtitles.

The script editor can also copy a scene-level rewrite prompt for external AI tools. The prompt includes the original transcript, literal Chinese translation, current voiceover, timing recommendation, AI warnings, and saved fact-check results for that scene. The returned rewrite is not applied automatically; paste the preferred version into the script editor and save it.

To rebuild the reviewed draft after script edits, run:

```powershell
python -m snvm refresh-draft
```

This applies `script_edits.json` when present, regenerates `voiceover.mp3`, regenerates `timing_plan.json`, composes `final_scenes.mp4`, and regenerates `review_player.html`. Preview the planned steps without running TTS or ffmpeg:

```powershell
python -m snvm refresh-draft --dry-run
```

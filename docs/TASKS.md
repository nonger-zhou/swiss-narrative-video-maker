# Task Plan

Development should happen in small branches with narrow scope.

## Branch Naming

Use:

```text
codex/task-XXX-short-name
```

Example:

```text
codex/task-001-product-docs
```

## Task 001: Product Docs

Branch:

```text
codex/task-001-product-docs
```

Scope:

- establish project README
- write PRD
- record development workflow

Status:

- done

## Task 002: Python Project Skeleton

Branch:

```text
codex/task-002-python-skeleton
```

Scope:

- create package structure
- add CLI entry point
- add `requirements.txt`
- add `.env.example`
- add output directory handling
- add basic logging and error messages

Status:

- done

## Proposed Next Tasks

### Task 003: Source Input And Download

Scope:

- accept YouTube URL or local mp4
- use `yt-dlp` for YouTube
- save or copy source as `output/source.mp4`

Status:

- done

### Task 004: Transcription

Scope:

- integrate `faster-whisper`
- output timestamped `transcript.json`

Status:

- done

### Task 005: OpenAI Translation And Structure Analysis

Scope:

- call OpenAI API
- output `translation.json`
- output `structure_analysis.json`
- enforce structure fidelity
- produce visual action suggestions in plain language

Status:

- done

### Task 006: Scene Plan Generation

Scope:

- generate `scene_plan.json`
- validate required fields
- keep visuals scene-by-scene rather than forcing replacement

Status:

- done

### Task 007: Voiceover

Scope:

- integrate `edge-tts`
- generate Chinese voiceover mp3
- store per-scene timing data if available

Status:

- done

### Task 008: Draft Video Composition

Scope:

- use `ffmpeg`
- compose scenes according to `scene_plan.json`
- add voiceover and subtitles
- output `final.mp4`

Status:

- done

### Task 009: Human Review Layer

Scope:

- show original transcript, literal translation, and rewritten voiceover per scene
- flag likely duplicate facts and over-expanded rewrite text
- let the user edit a review JSON before regenerating voiceover
- keep the existing automatic pipeline working unchanged

Status:

- done

### Task 010: Scene Timing Plan

Scope:

- compare source scene duration with estimated Chinese voiceover duration
- recommend per-scene timing actions instead of looping the whole video
- flag scenes that should compress copy or add scene-specific visuals
- keep existing compose behavior unchanged until a later per-scene composer task

Status:

- done

### Task 011: Scene-Based Draft Composition

Scope:

- consume `scene_plan.json` or `scene_plan.reviewed.json`
- consume `timing_plan.json`
- cut the source video scene by scene
- locally slow or freeze scenes to match estimated Chinese narration timing
- output a separate scene-based draft without replacing the existing composer

Status:

- done

### Task 012: Visual Alignment Review Player

Scope:

- generate a local HTML player for reviewing draft video alignment
- show current scene metadata while the video plays
- let the user mark voiceover/visual alignment issues at the current timestamp
- export notes as JSON for later correction steps

Status:

- done

### Task 013: Review Player Text Comparison

Scope:

- show original transcript, literal Chinese translation, and final Chinese voiceover in the visual review player
- include AI review warnings in the player
- export alignment notes with the three text layers attached

Status:

- done

### Task 014: Visual Replacement Manifest

Scope:

- generate a scene-level `visual_replacements.json` from replacement recommendations
- let the creator attach generated or sourced image/video assets to specific scenes
- make `compose-scenes` render enabled replacement assets for their matching scene
- keep existing scene composition behavior unchanged when no replacement is enabled

Status:

- done

### Task 015: Fact Check Shortcuts

Scope:

- add fact-check shortcuts to the visual review player
- build prompts from selected text or the current scene's transcript, literal translation, and voiceover
- copy the prompt and open external research tools with the current claim context
- keep fact checking user-driven instead of generating an internal report

Status:

- done

### Task 016: Alignment Revision Plan

Scope:

- read `alignment_notes.json` exported from the review player
- group marked issues by scene
- generate `revision_plan.json` and `revision_plan.md`
- recommend next edits without automatically changing scene plans or copy

Status:

- done

### Task 017: Fact Check Notes

Scope:

- let the review player record pasted external fact-check results for the current scene
- export `fact_check_notes.json`
- generate `fact_check_summary.json` and `fact_check_summary.md`
- extract source links and suggest source-aware copy revision next steps

Status:

- done

### Task 018: Scene Script Edits

Scope:

- let the review player edit the current scene's final Chinese voiceover text
- record revision intents such as compression, deduplication, fact fix, and added explanation
- export `script_edits.json`
- apply script edits to `scene_plan.reviewed.json` without changing scene order

Status:

- done

### Task 019: Refresh Draft Command

Scope:

- add one command that applies script edits and regenerates downstream draft outputs
- rebuild voiceover, timing plan, scene-based video, and review player in the correct order
- auto-detect optional script edits and visual replacement manifests
- provide a dry-run mode so the creator can inspect planned steps first

Status:

- done

### Task 020: Fact Check Revision Bridge

Scope:

- add an editable fact-check focus field for claims split across subtitle lines
- show saved fact-check results for the current scene inside the review player
- let the creator carry a saved fact-check result into the script edit note
- mark carried fact-check context as fact fix and source-needed without automatically rewriting copy

Status:

- done

### Task 021: Scene Rewrite Prompts

Scope:

- add scene-level rewrite prompt shortcuts to the review player
- include original transcript, literal translation, current Chinese voiceover, timing guidance, warnings, and saved fact checks
- keep AI rewriting external and user-approved before saving script edits

Status:

- done

## Later Phase Directions

These are product directions discussed after the Version 1 single-video workflow:

- topic workspace for one theme across multiple reference videos, articles, and notes
- multilingual source discovery and Chinese translation
- claim matrix for repeated, differentiated, conflicting, accepted, and rejected viewpoints
- Markdown and Notion-friendly export
- direct Notion database sync in a later integration step
- personal media library for original phone photos and videos, with AI-assisted tagging by time, place, visual type, quality, and possible topic use
- low-cost high-quality TTS provider selection, including Volcengine / Doubao, OpenAI, Azure, Tencent, Alibaba, and optional custom creator voice

See `docs/ROADMAP.md` for details.

### Task 023: TTS Provider Research

Scope:

- compare free, cheap, and higher-quality TTS options for Chinese video narration
- distinguish local transcription cost from generated voice cost
- record official pricing and policy notes where available
- recommend a later provider abstraction and voice audition workflow

Status:

- done

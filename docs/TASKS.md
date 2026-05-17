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

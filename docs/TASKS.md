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

- in progress

## Proposed Next Tasks

### Task 002: Python Project Skeleton

Scope:

- create package structure
- add CLI entry point
- add `requirements.txt`
- add `.env.example`
- add output directory handling
- add basic logging and error messages

### Task 003: Source Input And Download

Scope:

- accept YouTube URL or local mp4
- use `yt-dlp` for YouTube
- save or copy source as `output/source.mp4`

### Task 004: Transcription

Scope:

- integrate `faster-whisper`
- output timestamped `transcript.json`

### Task 005: OpenAI Translation And Structure Analysis

Scope:

- call OpenAI API
- output `translation.json`
- output `structure_analysis.json`
- enforce structure fidelity
- produce visual action suggestions in plain language

### Task 006: Scene Plan Generation

Scope:

- generate `scene_plan.json`
- validate required fields
- keep visuals scene-by-scene rather than forcing replacement

### Task 007: Voiceover

Scope:

- integrate `edge-tts`
- generate Chinese voiceover mp3
- store per-scene timing data if available

### Task 008: Draft Video Composition

Scope:

- use `ffmpeg`
- compose scenes according to `scene_plan.json`
- add voiceover and subtitles
- output `final.mp4`


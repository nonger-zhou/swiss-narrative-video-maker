# Product Requirements Document

## Product Name

Swiss Narrative Video Maker

## Product Summary

Swiss Narrative Video Maker is a local command-line tool that helps a Chinese-speaking creator learn from high-quality reference videos about Switzerland, preserve their narrative structure, rewrite the narration in Chinese, and generate a simple draft video.

The goal is not to build a full editing suite in the first version. The goal is to build a reliable local pipeline from reference video to editable narrative plan and draft video.

## Target User

A creator making Chinese-language videos about Switzerland who wants to:

- study strong reference videos
- understand their narrative structure
- translate and rewrite them into Chinese
- keep the useful original structure
- add personal commentary and context
- decide which visuals to keep, replace, recreate, or search for
- generate a simple video draft for further review

## Core Product Principle

Structure faithful, Chinese expression original, visuals judged scene by scene.

This means:

- Do not redesign the whole video structure unless explicitly asked.
- Preserve the original segment order, rhythm, and information progression.
- Rewrite the narration in Chinese rather than mechanically translating it.
- Let the final visual choice depend on each scene's material type and replacement difficulty.

## Version 1 Goal

Input a YouTube URL or local mp4 file. The system should:

1. download or read the source video
2. transcribe the audio with timestamps
3. translate the transcript into Chinese
4. analyze the original narrative structure
5. generate an original Chinese voiceover script based on the original structure
6. output an editable `scene_plan.json`
7. generate Chinese voiceover audio
8. compose a simple `final.mp4`

The first version should produce a complete draft video, not necessarily a polished publish-ready film.

## Functional Requirements

### 1. Input

The tool supports:

- YouTube URL
- local mp4 file

### 2. Source Fetching

For YouTube:

- use `yt-dlp`
- save source video as `output/source.mp4`

For local video:

- copy or reference the local file as the source

### 3. Transcription

Use `faster-whisper`.

Output:

- `output/transcript.json`
- timestamped segments
- original language text where possible

### 4. Translation And Structure Analysis

Use the OpenAI API.

Output:

- `output/translation.json`
- `output/structure_analysis.json`

The analysis should include:

- Chinese translation
- opening hook
- main information points
- visual rhythm
- memorable lines
- ending viewpoint
- narrative roles for each segment
- visual material type
- replacement difficulty
- whether a scene should keep, replace, recreate, search alternatives, or add explanatory visuals

### 5. Faithful Chinese Rewrite

Generate Chinese narration that:

- follows the original structure closely
- keeps the same narrative role per segment
- does not randomly reorder scenes
- does not invent a new argument unless explicitly requested
- improves expression for Chinese audiences
- can include creator commentary when appropriate

### 6. Scene Plan

Output `output/scene_plan.json`.

Each scene should include:

```json
{
  "scene_id": "scene_001",
  "start_time": 0.0,
  "end_time": 12.5,
  "source_summary": "",
  "translated_text": "",
  "narrative_role": "",
  "rewritten_voiceover": "",
  "visual_action": "keep_original",
  "visual_suggestion": "",
  "replacement_difficulty": "hard",
  "alternative_source_suggestions": [],
  "search_keywords": [],
  "fallback_action": "keep_original",
  "subtitle_text": ""
}
```

Suggested `visual_action` values:

- `keep_original`
- `replace_with_user_footage`
- `recreate_chart`
- `recreate_map`
- `add_explanatory_visual`
- `search_alternative_or_keep`
- `remove`

### 7. Voiceover

First version:

- use `edge-tts`
- output `output/voiceover.mp3`

The video timing should follow the generated Chinese voiceover where possible. The tool should adapt visuals to the narration length rather than forcing Chinese narration into the original duration.

### 8. Video Composition

Use `ffmpeg`.

For each scene:

- if the visual should be kept, cut the relevant original clip
- if replacement material exists, use the replacement
- if a visual should be recreated but no implementation exists yet, create a simple readable draft visual
- avoid empty placeholder backgrounds unless there is no better option

Add:

- Chinese voiceover
- Chinese subtitles

Output:

- `output/final.mp4`

## Non-Goals For Version 1

- ComfyUI integration
- advanced AI image generation
- account system
- cloud deployment
- professional nonlinear editor UI
- complex transition editing
- automatic copyright clearance
- direct publishing to platforms

## Success Criteria

Version 1 is successful if a user can run a command and get:

- all intermediate JSON files
- a readable scene plan
- a Chinese rewritten narration
- generated voiceover audio
- a playable draft video

The output should be easy to inspect and manually improve.

## Risks

- Platform download rules and availability may change.
- `edge-tts` depends on Microsoft online voices.
- Some source visuals may create copyright risk if published directly.
- AI may over-rewrite unless prompts strongly enforce structure fidelity.
- Generated narration may require manual review for factual accuracy.


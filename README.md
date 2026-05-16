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


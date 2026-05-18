# Swiss Narrative Video Maker Roadmap

This roadmap records product directions discussed during development. These ideas are not all Version 1 scope. They describe later phases after the single-video draft workflow becomes stable.

## Current Core

The current product is a single-reference-video workflow:

1. import a YouTube URL or local video
2. transcribe the original audio
3. translate and analyze the source structure
4. produce a scene plan and Chinese voiceover draft
5. review original transcript, faithful translation, and rewritten Chinese voiceover side by side
6. fact-check claims externally with prepared prompts
7. edit scene-level Chinese copy
8. regenerate voiceover, timing, subtitles, and draft video

The product principle remains:

> Structure faithful, Chinese expression original, visuals judged scene by scene.

## Direction 1: Topic Workspace

The creator often starts from a topic rather than one reference video. For example:

> Why Switzerland feels better than Germany

The creator may already have two strong reference videos, then want to discover more relevant perspectives in German, English, Chinese, Japanese, and other languages.

A future topic workspace should support:

- grouping multiple videos, articles, or notes under one topic
- importing manually collected links
- optionally searching for related material across languages
- translating all useful source text into Chinese
- comparing repeated and differentiated viewpoints
- separating claims the creator accepts, rejects, or wants to verify
- producing a stronger original outline than any single source

This is a different kind of "batch" than mechanical mass scraping. The goal is not to download hundreds of videos. The goal is to build a richer, source-aware point of view for one topic.

Possible output structure:

```text
topic_project/
  sources/
    source_A/
    source_B/
    source_C/
  topic_brief.md
  claim_matrix.md
  selected_points.md
  final_outline.md
  final_script.md
```

## Direction 2: Multilingual Research

For one topic, the tool should eventually help search and compare sources in multiple languages.

Potential workflow:

1. User enters a topic in Chinese.
2. Tool generates multilingual search queries.
3. Tool collects candidate sources with title, URL, language, platform, and short summary.
4. User selects which sources are worth importing.
5. Tool transcribes or extracts text where possible.
6. Tool translates all source text into Chinese.
7. Tool builds a cross-source comparison.

The comparison should identify:

- repeated claims
- unique or differentiated angles
- conflicting numbers or definitions
- emotionally strong lines
- useful examples
- weak, exaggerated, or unsupported claims
- source links that should be kept for fact checking

This should remain user-guided. The tool can suggest sources and organize claims, but the creator decides what to trust and use.

## Direction 3: Claim Matrix

A topic-level claim matrix is central to multi-source creation.

Each row could represent one claim, number, example, or viewpoint:

```text
claim
source
language
source quote
Chinese translation
supporting sources
conflicting sources
fact-check status
creator decision
rewrite note
```

Suggested creator decisions:

- use
- use after rewrite
- fact-check first
- reject
- use as counterpoint
- save for later

This turns "watching references" into a deliberate editorial process.

## Direction 4: Notion And Markdown Export

The tool should support knowledge-base workflows.

Markdown export is the simplest first step:

- one Markdown file per source
- one Markdown file per topic summary
- one Markdown claim matrix

Obsidian and Notion solve related but different problems.

Obsidian is closest to a local Markdown knowledge base:

- content is stored as local `.md` files
- easy for a tool to export
- good for long-term text archives, backlinks, tags, and offline work
- less strong as a visual database or workflow dashboard

Notion is closer to a database plus page workspace:

- good for topics, statuses, tags, platforms, languages, and creator decisions
- good for table, board, calendar, and filtered views
- easy for the creator to browse and manage
- long text should live in page bodies rather than database properties
- direct sync requires Notion API setup and permissions

The recommended architecture is not either/or:

1. Always export local Markdown and JSON as the durable archive.
2. Optionally generate Notion-friendly Markdown for manual import.
3. Later add direct Notion database sync for users who configure it.

Notion support can come in three levels:

1. Notion-friendly Markdown export that the creator can paste or import manually.
2. A documented Notion database schema.
3. Direct Notion database sync through the Notion API.

For Notion, the database should act as an index, while long text should live in page bodies.

Possible Notion database properties:

- Title
- Topic
- Source URL
- Platform
- Language
- Status
- Local Video Path
- Transcript Status
- Fact Check Status
- Creator Decision
- Created At

Page body content can include:

- transcript
- faithful Chinese translation
- structure analysis
- useful points
- fact risks
- rewrite notes
- final script excerpts

## Direction 4.1: Custom API And Prompt Templates

Some competing tools let users configure their own API and prompts. This usually means:

- the user can choose which AI provider to call, such as OpenAI, Volcengine, Alibaba, Tencent, or another compatible model API
- the user can paste their own API key instead of relying on the tool author's account
- the user can define prompt templates for different tasks

Prompt templates are reusable instructions sent to the AI model. In this product, possible templates include:

- structure analysis prompt
- faithful Chinese translation prompt
- Chinese voiceover rewrite prompt
- short-video hook analysis prompt
- fact-check prompt
- topic-level claim matrix prompt
- Notion summary prompt
- visual replacement suggestion prompt

The value is flexibility. Different creators have different styles, platforms, and risk tolerance. A prompt template system would let the creator tune output without changing code.

Recommended future design:

```text
prompts/
  analyze_structure.md
  rewrite_voiceover.md
  fact_check.md
  topic_claim_matrix.md
  notion_summary.md
```

Each prompt can use placeholders:

```text
{{ transcript }}
{{ literal_translation }}
{{ voiceover }}
{{ topic }}
{{ creator_note }}
```

The tool fills placeholders with the current source data before calling the selected AI provider.

This should be added carefully. The default prompts should remain good enough for non-technical users, while advanced users can override them.

## Direction 5: Light Reference Saving, Heavy Original Media Management

Not every reference video needs to be downloaded. If the creator does not plan to reuse the visual material, it is often enough to keep:

- source URL
- transcript
- Chinese translation
- structure analysis
- useful points
- creator notes
- fact-check status

Original media is different. Photos and videos shot by the creator are long-term assets and deserve a real media library.

Future media library capabilities:

- import phone photos and videos
- read time and location metadata when available
- generate thumbnails
- classify content type, such as train, street, lake, supermarket, office, document, interview, screen recording
- detect basic quality issues, such as blurry, dark, shaky, or usable
- mark whether people appear in the shot
- suggest possible topic tags
- record creator-approved tags and usage notes
- search assets by topic, place, time, and visual type

AI can suggest tags, but the creator should confirm important tags and public-use decisions.

## Direction 6: Future UI

The current local review player is enough for Version 1 review. Later phases may need a more complete interface:

- topic dashboard
- source list
- claim matrix editor
- Notion export/sync settings
- media library browser
- scene-level draft editor

The UI should support real creative judgment rather than hiding everything behind one automatic button.

## Direction 7: Low-Cost High-Quality TTS

The first version uses `edge-tts` because it is free and good enough for drafts, but the voice quality should not define the final product.

Future voice work should include:

- a TTS provider abstraction
- voice audition samples
- Volcengine / Doubao TTS as the first paid Chinese-provider candidate
- OpenAI and Azure as quality/reference candidates
- optional Tencent and Alibaba provider tests
- script cleanup before TTS to remove filler words and overly long sentences
- later custom creator voice support with explicit consent and careful data handling

See `docs/research/tts-provider-comparison.md`.

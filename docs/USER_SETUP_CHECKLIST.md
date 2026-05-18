# User Setup Checklist

This checklist records the things the creator may need to decide or prepare before later workflow steps can work well.

The assistant should use this document as a reminder source. If a later task depends on an unfinished item, say clearly:

> You need to complete this item first, then we can continue.

## 1. Cloud Photo And Video Sync

Goal: know where phone photos and videos are currently backed up.

Check these services:

- iCloud Photos
- Google Photos
- OneDrive camera upload
- Dropbox camera uploads

For each service, record:

```text
Service:
Account:
Backup enabled: yes/no
Backup quality: original / compressed / unknown
Approx storage used:
Local Windows folder, if visible:
Notes:
```

Common Windows folders to inspect:

```text
C:\Users\Julia\OneDrive\Pictures
C:\Users\Julia\Dropbox\Camera Uploads
C:\Users\Julia\Pictures\iCloud Photos\Photos
```

Important distinction:

- A file visible in Windows may be fully downloaded.
- Or it may be a cloud-only placeholder.

For media analysis, original files need to be downloaded locally at least when the tool processes them.

## 2. Choose A Main Media Inbox

Goal: choose one place where new photos and videos arrive before classification.

Recommended pattern:

```text
Cloud sync or external drive
  -> SwissMediaInbox
  -> software scans this folder
  -> media_library catalog stores tags and thumbnails
```

Possible locations:

```text
C:\Users\Julia\OneDrive\SwissMediaInbox
D:\SwissMediaInbox
E:\SwissMediaInbox
```

Decision needed:

```text
Main media inbox path:
Should the software move files? no / later
Should the software only index files? yes
```

Initial recommendation:

- Do not move original files.
- Build an index and thumbnails first.
- Confirm the workflow before reorganizing anything.

## 3. Decide Original Media Storage Strategy

Goal: avoid filling every computer with all raw videos while still being able to work anywhere.

Recommended structure:

```text
Cloud drive / external SSD / NAS: original media
Local computer: current project files and downloaded-needed originals
media_library: catalog, thumbnails, tags, usage notes
Notion: index and planning, not huge original videos
GitHub: code only, not media files
```

Future laptop recommendation:

- RAM: 32GB or more
- SSD: 1TB minimum, 2TB preferred
- External SSD: 2TB or 4TB if handling lots of original video

## 4. Create A Media Library Workflow

Goal: make original phone footage searchable and usable for future videos.

Future software should scan the media inbox and create:

```text
media_library/
  catalog.json
  thumbnails/
  reports/
```

Each media item should eventually track:

- file path
- cloud status: downloaded / cloud-only / missing
- shot date and time
- GPS location if available
- file type: photo / video
- orientation: horizontal / vertical
- duration for videos
- thumbnail path
- visual description
- suggested tags
- quality notes: dark / blurry / shaky / usable
- privacy notes: faces / children / car plates / private homes
- possible topics: Swiss transport, living cost, city life, nature, politics, etc.
- creator decision: usable / do not use / needs review / favorite

## 5. Material Replacement Workflow

Goal: when a video scene needs replacement footage, use the media library instead of manually browsing thousands of files.

Expected workflow:

1. Mark a scene as needing replacement material.
2. Search the media library by topic, location, visual type, and orientation.
3. Review thumbnails and metadata.
4. Select a candidate.
5. If the original file is cloud-only, download it locally.
6. Bind the selected asset to the scene's `visual_replacements.json`.
7. Regenerate the draft video.

Example for a "Switzerland vs Germany" project:

```text
Needed scene material:
- Zurich street
- train station
- lake / mountain B-roll
- supermarket price tags
- voting envelope
- quiet residential street
```

The software should suggest matches from the creator's own library before recommending external footage.

## 6. External Reference Footage Rules

Goal: use other people's videos safely.

Reference videos can be used for:

- learning structure
- extracting transcript
- understanding camera style
- generating search keywords
- finding topic angles

Do not assume reference video footage can be reused publicly.

For any external material, record:

```text
Source URL:
Author/channel:
License:
Commercial use allowed: yes/no/unknown
Modification allowed: yes/no/unknown
Attribution required:
Risk level: low/medium/high
Decision: use / reference only / contact author / reject
```

If no license is visible, treat it as:

```text
Reference only. Do not publish this footage directly.
```

## 7. Notion And Markdown Setup

Goal: save important product decisions, research notes, topic ideas, and source summaries.

Recommended first step:

- Keep local Markdown and JSON as durable source files.
- Use Notion as the working dashboard.

Future Notion database fields:

```text
Title
Type: Decision / Idea / Research / Task / Source / Material
Topic
Status
Priority
Source URL
Local File Path
Summary
Decision
Created At
Linked Files
```

User needs to decide later:

```text
Notion workspace:
Database name:
Manual Markdown import first? yes/no
Direct Notion API sync later? yes/no
```

## 8. TTS Provider Setup

Goal: move beyond the current draft voice when needed.

Current state:

- Transcription uses local `faster-whisper`.
- Draft Chinese voiceover uses `edge-tts`.

Future decisions:

```text
Preferred draft TTS:
Preferred final TTS:
Need custom creator voice? yes/no/later
Budget per video:
```

Provider candidates:

- Edge TTS for free draft voices
- Volcengine / Doubao for Chinese final narration candidate
- OpenAI TTS for paid quality candidate
- Azure AI Speech for formal Microsoft API and possible custom voice
- Tencent / Alibaba for later Chinese provider tests

## 9. Practical Shooting Guidance

Goal: shoot original footage that is easy to use later.

For B-roll:

- shoot many stable short clips
- each clip should be at least 8-12 seconds
- important landscapes can be 15-20 seconds
- leave 2 seconds before and after the useful action
- shoot multiple angles at the same location
- avoid clear faces, children, car plates, private homes, and sensitive documents unless needed

One-take long recordings are useful for documenting an event, but the media library should later cut and tag usable segments.

## 10. Current Open Items

Use this section as a working list.

```text
[ ] Check which cloud services currently back up phone photos/videos.
[ ] Choose one main media inbox path.
[ ] Confirm whether files are fully downloaded or cloud-only placeholders.
[ ] Decide whether Notion starts as manual Markdown import or direct API sync.
[ ] Decide whether to test Volcengine / Doubao TTS first.
[ ] Decide whether to build the media library scanner as the next major module.
```

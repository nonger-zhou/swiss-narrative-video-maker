# Task 026: Topic Comment Insights

## Context

The creator referenced Johnny Harris' video:

```text
How Switzerland Engineered the Perfect Country
https://www.youtube.com/watch?v=OMbV1rIPhCg
```

The video is useful as a reference because it combines:

- Swiss railway construction history
- animated maps
- a strong travel challenge narrative
- interviews and expert access
- historical explanation connected to present-day experience

The creator wants to make a deep Chinese video inspired by this kind of structure, but from a different point of view:

> A Chinese person who has lived in Switzerland for a long time and operates a hotel explains how Switzerland's railway and public transport system shapes tourism, daily life, and the feeling that the country works unusually well.

The goal is not to copy one video. The goal is to combine several related references, official sources, local experience, and comments from viewers into an original Chinese story.

## Product Insight

Topic research should not only ingest the main video transcript. It should also capture useful context around the video:

- source links from the video description
- chapter structure
- official data sources mentioned by the creator
- expert names and institutions
- comments that correct, challenge, or enrich the story
- viewer reactions that reveal which points are emotionally resonant

Comments should be treated as leads, not final evidence.

## Comment Insights Workflow

Future workflow:

1. Import a reference video into a topic workspace.
2. Fetch top-level comments and replies when available.
3. Translate comments into Chinese.
4. Classify comments by editorial value.
5. Extract candidate claims, corrections, anecdotes, and emotional reactions.
6. Mark which items need fact checking.
7. Attach useful insights to the topic workspace and claim matrix.

Suggested comment categories:

- local correction
- expert correction
- personal experience
- historical detail
- data point
- disagreement
- useful analogy
- emotional reaction
- audience question
- source recommendation
- off-topic / low value

Example interpretation:

```text
Comment insight:
"Swiss trains are not punctual because Swiss people are magically punctual; the timetable and transfer system are designed so delays hurt the whole network."

Use as:
candidate angle

Verify with:
SBB / BAV / Rail 2000 / Taktfahrplan sources
```

## Topic Workspace Outputs

For a deep topic like Swiss railways, the workspace should eventually generate:

```text
topic_brief.md
source_summaries/
claim_matrix.md
comment_insights.md
source_links.md
shooting_list.md
visual_plan.md
personal_angle_outline.md
final_script.md
```

## Sources To Combine

For the Swiss railway topic, useful source categories include:

- Johnny Harris reference video and source document
- SBB official history
- SBB Historic
- Swiss Museum of Transport
- Swiss Federal Office of Transport (BAV)
- Swiss public transport statistics
- Rail 2000 / Taktfahrplan sources
- Gotthard / Simplon / Jungfrau railway history
- ETH transport planning research
- Wikimedia Commons / archival images where licensing allows
- creator's own local footage and hotel/tourism experience

## Visual Lessons To Borrow Without Copying

The creator liked:

- railway construction history
- maps that show how infrastructure connects the country
- seeing the mountains as a physical obstacle
- time pressure / travel challenge framing
- present-day experience tied back to historical engineering

Possible original visual approach:

- a custom Switzerland map showing mountains, valleys, major rail lines, tunnels, and tourist regions
- timeline of railway expansion
- simple tunnel cross-section graphics
- hotel guest journey maps: airport -> train -> hotel -> mountain village
- comparison between car-dependent travel and train-based travel
- creator-shot station, train, hotel, and tourist flow footage

## Creator Perspective

The final story should lean into the creator's lived position:

- long-term Chinese resident in Switzerland
- hotel operator seeing how tourists actually move through the country
- someone who can explain Swiss systems to Chinese viewers
- someone who can compare Swiss transport with German or Chinese expectations

Possible thesis:

> Switzerland's railways are not just transportation. They are the hidden operating system behind tourism, regional equality, and the everyday feeling that this country is reliable.

## Development Direction

This task is a planning note for a future feature branch. It should feed into:

- topic workspace
- comment ingestion
- multilingual source discovery
- claim matrix
- source-aware script generation
- map-based visual planning

It does not implement comment fetching yet.

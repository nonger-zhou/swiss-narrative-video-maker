# Task 015: Fact Check Shortcuts

## Goal

Let the creator verify factual claims without manually assembling context from JSON files or reopening separate notes. The review player should provide quick buttons that carry the current scene context into external research tools.

## Behavior

The review player adds a fact-check panel under the three-column text comparison.

The creator can:

- select one sentence or paragraph and copy a fact-check prompt for that exact text
- open ChatGPT with the generated prompt
- open Perplexity with the generated prompt
- search Google for the selected sentence or current Chinese voiceover line

If no text is selected, the prompt uses the current scene's:

- original transcript
- literal Chinese translation
- final Chinese voiceover

The prompt asks the external tool to identify factual claims, check numbers and non-numeric descriptions, provide original source links, name source years and definitions, and suggest safer Chinese rewrites when a sentence is too absolute.

## Notes

This task intentionally does not generate an internal fact-check report. The first version keeps verification user-driven and external, while making the handoff fast and repeatable.

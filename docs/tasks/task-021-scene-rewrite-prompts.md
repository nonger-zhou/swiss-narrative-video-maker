# Task 021: Scene Rewrite Prompts

## Goal

Help the creator ask an external AI tool for a careful scene rewrite without manually copying context from several panels.

## Review Player Changes

The script edit panel now has buttons to:

- copy a rewrite prompt for the current scene
- copy the prompt and open ChatGPT in a new tab

The prompt includes:

- original transcript
- literal Chinese translation
- current Chinese voiceover draft
- timing recommendation
- AI review warnings
- saved fact-check results for the scene

## Boundaries

The tool does not automatically apply the rewrite. The creator reviews the external answer, pastes the chosen version into the script editor, saves it, exports `script_edits.json`, and then runs `refresh-draft`.

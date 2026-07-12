---
name: ChipRow
description: A row of one-tap checkpoint chips — the learner's steering wheel between lesson beats (Start Gate, Got it / example / lost me, skips, Next Gate).
---

# ChipRow

A horizontal row of tappable chips that dispatch UI actions. This is how
the learner hands a signal back without typing: starting a lesson,
steering between beats, skipping a check, choosing what happens after the
Close.

Use it when the learner's next move is a *choice among a few named paths*.
Do not use it for free-text input (that's PromptInput / ExplainBack) or
for in-content options (that's QuizBlock / ChoicePicker).

Rules:

- At most one `primary` chip — the recommended path reads as such.
- `quiet` is for escapes the learner may take but isn't pushed toward
  (skips). Never make a skip primary.
- `note` is one gentle line, used at most once per lesson — a nudge,
  never pressure.
- After a tap the whole row disables; a checkpoint is answered once.

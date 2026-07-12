---
name: Button
description: An interactive button that dispatches an action back to you. Use for user-triggered operations — confirmations, submissions, choices.
---

# Button

The child (usually a Text) is the button's label, referenced by id. Clicking sends the action to you as a new `[UI action]` user turn, with the action's `context` values resolved from the surface's data model at click time — bind a context value to an input's path to receive what the user typed or selected.

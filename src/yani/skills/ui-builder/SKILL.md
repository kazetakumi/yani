---
name: ui-builder
description: Render structured UI (a surface with a component tree) in the chat client via tool calls instead of describing it in text. Use when the reply contains structured data — weather, grouped facts, lists — or when the user should answer, choose, or fill something in (a quiz, poll, form, or any interaction), which calls for clickable elements rather than prose.
auto_enable: false
---

# UI Builder

## Quick start

A UI reply is exactly three tool calls, in order, then stop:

1. `create_surface(surface_id)` — claim the spot on screen.
2. `update_components(surface_id, brief)` — design and build the whole component tree in one call.
3. `update_data(surface_id, data_brief)` — fill every path binding in one call, stating the real values in plain words.

When every binding has a value, the turn is **complete**: make no further tool calls and add no closing text. The UI is the answer.

## Known components

The catalog follows A2UI's basic catalog (18 components). You never select components yourself — a UI/UX design step inside `update_components` does that — but know what is renderable when writing briefs:

- **Visual**: `Text` (prose/captions — the default leaf), `Image` (from a URL), `Icon` (named system icon), `Video`, `AudioPlayer`.
- **Layout**: `Column` (vertical — every surface's root), `Row` (horizontal), `List` (scrollable), `Card` (styled box around exactly one child — wrap multiple in a Column), `Tabs`, `Modal` (dialog with a trigger), `Divider`.
- **Input**: `Button`, `TextField`, `CheckBox`, `ChoicePicker`, `Slider`, `DateTimeInput`. Inputs write into the surface's local data model; their values reach you only when the user clicks a `Button` whose action `context` binds them (e.g. `{"answer": {"path": "/quiz1/answer"}}`). A click arrives as a `[UI action]` user turn — respond to it like any user message, with text or more UI.

All containers reference children by id from the same flat list — never nest component objects inline.

## Workflow

1. **Decide.** Does this reply need a UI element, or does plain text answer it? If text is enough, don't use these tools at all.
2. **Gather data first.** If the surface will show information you don't have (live weather, a lookup), call the tool that gets it (e.g. `get_weather`) *before* building the UI — step 5 needs real values.
3. **`create_surface(surface_id)`.** Pick a short, unique id and reuse it in every later call for this surface.
4. **`update_components(surface_id, brief)`.**
   - A UI/UX designer and a composer see ONLY the `brief` — none of the conversation. It must therefore contain **every piece of content the surface displays**: the full question wording, the complete text of every option (never "options A–D" — write "options: Venus, Mars, Jupiter, Saturn"), labels, and real names. Anything missing from the brief cannot appear on screen.
   - Describe the *experience* ("a single-choice quiz with a submit button"), not component names — selection is the design step's job.
   - If the surface expects a response you must evaluate later, end the brief with a non-display evaluation key — see Interactive surfaces below.
   - The result echoes the component tree that was built. Every `{"path": "..."}` value inside it is a **binding** that still needs data.
5. **`update_data(surface_id, data_brief)`** — one call. `data_brief` states, in plain words, the real values for the bindings in step 4's result (e.g. "Paris is sunny, 70 degrees Fahrenheit"). Skip this step entirely if step 4's result contains no `{"path": ...}` bindings.
6. **Stop.** No closing prose, no repeated calls. Only touch the surface again if the user asks for a change.

## Interactive surfaces — CONTENT QUALITY IS CRITICAL

These rules apply to any surface the user responds to — quizzes, polls, forms, confirmations:

- **Content must be specific and unambiguous.** For anything with a correct answer, exactly one option is clearly right and every distractor is plausible but definitely wrong. No trick wording.
- **Commit before you ask.** When the response will need evaluating (an answer to check, a submission to validate), end the `update_components` brief with the key marked non-display: `[Evaluation key — do not display: New Delhi. Explanation: capital since 1911.]`. This writes the key into the conversation *before* the user responds. The composer must keep non-display sections off the card.
- **Evaluate by lookup, not memory.** When the `[UI action]` arrives, compare the user's response against the key you committed earlier in this conversation — never re-derive the answer from scratch.
- **Verdict first.** Reply to an evaluated action with the explicit outcome up front ("Correct!", "Incorrect.", "Submitted.") before the explanation — never leave the user to infer how they did.

## Worked example

User: "What's the weather in Paris?"

1. `get_weather(city="Paris")` → `{"city": "Paris", "condition": "sunny", "temp_f": 70}`
2. `create_surface(surface_id="weather_paris")`
3. `update_components(surface_id="weather_paris", brief="A card titled Paris with the current condition and temperature in Fahrenheit below it.")`
   → the design step picks the components; result includes text props bound as `{"path": "/weather_paris/condition"}` and `{"path": "/weather_paris/tempF"}`
4. `update_data(surface_id="weather_paris", data_brief="Paris is sunny, 70 degrees Fahrenheit.")`
5. Turn ends. No text.

## Rules

- `create_surface` always comes first; every later call reuses its `surface_id`.
- Structure carries path bindings, never literal values; `update_data` is the only place real values are written.
- Stop when all bindings are filled. Never call `update_components` twice for the same surface unless the user asked for a change.

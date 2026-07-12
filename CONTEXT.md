# harnessv2 (Yani)

An agent harness whose product is Yani, an interactive teaching assistant that delivers mentor-style lessons as real UI in a browser chat. Yani's audience is school students — non-programmers; lessons never contain code.

## Language

### The agent stack

**Harness**:
The Python loop and its subsystems that run the model: prompt assembly, tools, state, events. The model performs inside it; it never is it.

**Yani**:
The product identity — the teaching assistant persona the main model plays. Refuses non-teaching work.
_Avoid_: the assistant, the bot

**Main model**:
The LLM call that holds the conversation and orchestrates tools. Distinct from agents.

**Agent**:
A one-shot LLM call with its own system prompt (`agents/<name>/AGENT.md`), invoked inside a tool, never on the skills menu. Current residents: ui-designer, ui-composer, ui-data-writer.
_Avoid_: subagent skill

**Yani skill**:
A capability the main model discovers on the skills menu and loads with `load_skill` (`skills/<name>/SKILL.md`, `auto_enable` flag). Say "Yani skill" whenever "/mentor skill" could be confused with it.

**Mentor skill**:
The Claude-side `/mentor` skill (`~/.claude/skills/mentor/`) whose concepts and look are being ported into Yani. Source material, not runtime code.

### Lessons

**Lesson**:
One Concept Loop teaching unit, delivered as an ordered sequence of Blocks streamed into the chat. The mentor product's primary artifact.

**Concept Loop**:
The block grammar of a lesson: Hook, Anchor, Picture, Model, Formalize, Geometry, Practice, Explain-back, Evaluate. Code was removed for the school-student audience; Tree Locator and Summary were dropped (the Overview locates the lesson, the Close carries the mental model).

**Beat**:
A planner-declared group of consecutive blocks delivering one complete thought, always ending at a checkpoint. The unit shown on the Overview's route.
_Avoid_: segment, chunk

**Block**:
One Concept Loop unit, rendered as exactly one Surface. The atom of lesson delivery.
_Avoid_: section, element (for lesson units)

**Hook**:
One specific, guessable question about a real situation the learner recognizes, whose true answer IS the concept. Opens a curiosity gap the lesson is obliged to close: by the end, the learner can explain the hook scenario from first principles.
_Avoid_: introduction, motivation (a hook is a question, never a "why this matters" paragraph)

**Anchor**:
One analogy or scenario the learner already fully understands, used to seed the mental model — aimed at the learner's guess when one exists. Borrowed scaffolding with a debt: its failure points must be named and patched (Formalize) before the lesson ends. Fires only when the concept is far from what the learner knows.
_Avoid_: using an anchor as proof (analogies seed derivations, never conclude them)

**Lesson planner**:
The agent that turns a topic brief into the full ordered block plan — types and briefs — so the lesson keeps one running example.

**Paper theme**:
The single visual theme, ported from mentor.css: cream paper, handwriting accents, the block palette. There is no dark theme.

### Lesson interaction

**Overview**:
The learner-facing roadmap surface rendered from the block plan before any block streams — block titles and the running example in plain words.
_Avoid_: header, loop plan (the teacher's letter-code shorthand; never shown to the learner)

**Start Gate**:
The "Let's start" UI action on the Overview that begins block streaming. No block streams before it.

**Checkpoint**:
A pause at a load-bearing block boundary where the harness waits for the learner's Steering before composing the next block. Not every boundary is a checkpoint — hook and summary have none; Explain-back and Evaluate remain the deep checks.
_Avoid_: pause point

**Steering**:
The learner's checkpoint signal — advance ("Got it"), enrich ("Give me an example"), Re-anchor ("Lost me"), or Skip (Beats 4–6 only). Steering changes the path through the block plan, never the plan itself. Chip sets vary by boundary type.
_Avoid_: replanning (rejected: checkpoints must not recompose the remaining lesson)

**Skip**:
A quiet secondary chip on Practice, Explain-back, and Evaluate checkpoints. Skipping leaves the milestone "taught", never "demonstrated"; no learning record is written, the skip is logged, and the next session's review ritual collects the evidence debt. Recommended-to-stay is one gentle line, never repeated.

**Guess checkpoint**:
The first pause point, directly after the Hook: free-text guess plus a one-tap skip ("No idea — show me"). A guess is never demanded. The guess feeds the Anchor's brief immediately and resurfaces at Explain-back.

**Close**:
The mentor's chat message ending a lesson: warm verdict, then the one-line mental model as the final word. Never a block; never ends on the quiz score.

**Next Gate**:
The end-of-lesson chips ("Next lesson →" / "Done for today"). The learner opens every lesson and closes every session; the harness never auto-rolls into a new lesson.

**Re-anchor**:
The re-teach move on a real gap: re-enter at Anchor with a smaller concept and a fresh analogy. Maximum 2 per concept, then move on.

### Surfaces and UI

**Surface**:
One rendered UI unit in the chat scroll, owned by the server's surface store, addressed by `surface_id`. A lesson emits one per block.

**Catalog**:
The typed component contract: one folder per component (`ui_catalog/<Name>/`), schemas that constrain agent output by decoding, renderers client-side.

**Brief**:
The only content an agent sees. If a fact isn't in the brief, the agent doesn't know it.

**Binding**:
A `{"path": ...}` placeholder in a surface's structure that `update_data` fills later. Lesson prose is static and does not use bindings.

### Mentor state

**Workspace**:
Yani's durable teaching memory: markdown artifacts (mission, syllabus, learning records, notes) stored server-side, touched only through typed tools.

**Mission**:
The learner's concrete real-world goal; grounds every teaching decision. Absent mission ⇒ the session ritual demands an interview.

**Session ritual**:
The deterministic, zero-model-call harness function that reads the workspace each turn and injects the session's verdict (interview / review due / teach next) into the system prompt. The model executes the verdict, never chooses it.

**Evidence log**:
The raw, harness-appended record of every learner signal — quiz results, explain-backs, guesses, steering choices, practice attempts, skips — timestamped. Deterministic capture; no judgment. The substrate for later interaction analysis.

**Learning record**:
A judged artifact: Yani's decision that evidence demonstrates real understanding. Written only via the typed tool, never automatic.
_Avoid_: using "learning record" for raw evidence-log entries

**Evidence**:
What the learner actually demonstrated (quiz answers, explain-backs), arriving as UI actions. Coverage is not evidence.

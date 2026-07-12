"""Concept Loop blocks: typed content models + their component-tree mappers.

The block-composer agent thinks in *teaching content* (paragraphs, an
equation, quiz questions) — these models constrain its output by decoding.
The harness owns the markup mapping: each mapper deterministically turns
content into the block's component tree (Column root + Heading + pieces),
so agents never invent structure. Same boundary as the client catalog,
one level up: model proposes content, harness disposes composition.

Spec 0002: lessons are delivered as BEATS — planner-declared groups of
blocks, each ending at a checkpoint. The grammar has no code block
(ADR 0003: the audience is school students), and no summary/tree-locator
(the Overview locates the lesson; the chat Close carries the mental
model). clamp_beats() turns the planner's declaration into the runtime
beat list the harness cursor walks."""

from pydantic import BaseModel, Field
from typing import Literal

from .ui_catalog import FigureSketchProps, GraphBlockProps, QuizBlockProps


# ── planner output ──────────────────────────────────────────────

BlockType = Literal[
    "hook", "anchor", "picture", "model", "formalize", "geometry",
    "practice", "explain_back", "evaluate",
]

class PlannedBlock(BaseModel):
    type: BlockType
    title: str = Field(description='the block heading, e.g. "An everyday mystery"')
    brief: str = Field(description="self-contained content instructions for this block: every fact, wording, value and (for quizzes/practice) answer key the block must carry — the composer sees nothing else")


class PlannedBeat(BaseModel):
    label: str = Field(description='plain-words route entry shown to the learner on the Overview, e.g. "The core idea" — never letter codes')
    blocks: list[PlannedBlock]


class LessonPlan(BaseModel):
    title: str
    subtitle: str = Field(description="one-line promise of the lesson")
    why_you_care: str = Field(description="one sentence tying this concept to the learner's own mission, addressed as 'you'")
    running_example: str = Field(description="the ONE concrete example that threads every block")
    beats: list[PlannedBeat] = Field(description="the lesson in order: hook first, then 1-3 teaching beats, then practice / explain_back / evaluate")


# ── per-block content models (block-composer output) ────────────

class HookContent(BaseModel):
    paragraphs: list[str] = Field(description="pose the mystery; the learner must feel the gap. 1-3 paragraphs, ending in the one question they'll guess at")
    figure: FigureSketchProps | None = Field(None, description="optional sketch of the SITUATION — the scene, never the mechanism; null when the mystery has no honest visual")


class AnchorContent(BaseModel):
    paragraphs: list[str] = Field(description="one simple analogy or scenario the learner already fully understands — aimed at their guess when the brief carries one")
    definition_label: str = Field(description='e.g. "Definition — photosynthesis"')
    definition_text: str = Field(description="the new term pinned down in one or two sentences")


class PictureContent(BaseModel):
    lead_paragraph: str | None = Field(None, description="one sentence saying what the figure shows")
    figure: FigureSketchProps


class ModelContent(BaseModel):
    model_label: str = Field(description='e.g. "Mental model v1"')
    model_text: str = Field(description="the one-liner every later step attaches to")


class EquationSpec(BaseModel):
    label: str
    tex: str = Field(description="display TeX without \\\\[ \\\\] delimiters")
    tag: str | None = None
    caption: str | None = Field(None, description="the equation read aloud in plain words")


class SymbolRow(BaseModel):
    symbol: str = Field(description="TeX inline allowed, e.g. \\\\(N_0\\\\)")
    meaning: str = Field(description="what it is in the mental model's words")


class FormalizeContent(BaseModel):
    intro_paragraph: str | None = None
    equation: EquationSpec
    symbols: list[SymbolRow]
    break_label: str | None = Field(None, description='e.g. "Where the analogy breaks" — null if the anchor holds')
    break_text: str | None = None
    figure: FigureSketchProps | None = Field(None, description="optional small sketch beside the formal form; null unless it honestly helps")


class GeometryContent(BaseModel):
    lead_paragraph: str | None = None
    graph: GraphBlockProps


class PracticeContent(BaseModel):
    worked_paragraphs: list[str] = Field(description="walk ONE concrete problem start to finish with real numbers/situations — the teacher's turn")
    figure: FigureSketchProps | None = Field(None, description="optional sketch of the worked problem; null when it adds nothing")
    problem_text: str = Field(description="a near-twin of the worked problem for the learner to solve — same shape, different values")
    placeholder: str = Field(description='textarea placeholder, e.g. "Work it out — your answer and one line of why"')
    expected_answer: str = Field(description="the correct answer with a one-line solution path — NEVER shown to the learner; the mentor grades against it")


class ExplainBackContent(BaseModel):
    prompt_text: str = Field(description="what to explain, addressed to the learner — anchored to the hook scenario, resurfacing their guess when the brief carries one")
    placeholder: str = Field(description='e.g. "No jargon. What is it, really?"')


class EvaluateContent(BaseModel):
    quizzes: list[QuizBlockProps] = Field(description="1-3 retrieval questions applying the concept")


# Steering inserts (spec 0002): composed on demand from a mentor-written
# brief, never part of the plan. The cursor does not move.
class ExampleContent(BaseModel):
    paragraphs: list[str] = Field(description="one MORE concrete instance of the concept just taught, different surface, same mechanism. 1-3 paragraphs")


CONTENT_MODELS: dict[str, type[BaseModel]] = {
    "hook": HookContent, "anchor": AnchorContent, "picture": PictureContent,
    "model": ModelContent, "formalize": FormalizeContent, "geometry": GeometryContent,
    "practice": PracticeContent, "explain_back": ExplainBackContent,
    "evaluate": EvaluateContent,
}


# ── runtime beats (harness clamp — ADR 0002) ────────────────────

# checkpoint kind per beat, decided by grammar, not by the planner:
#   guess    — hook only; free-text guess, one-tap skip ("no idea")
#   steer    — teaching blocks; Got it / example / lost me chips
#   practice — try-one input lives inside the block; skippable
#   explain  — block's own textarea; skippable
#   evaluate — quiz submit; skippable
_TAIL_TYPES = ("practice", "explain_back", "evaluate")
_TAIL_KINDS = {"practice": "practice", "explain_back": "explain", "evaluate": "evaluate"}
MAX_TEACHING_BEATS = 3


def clamp_beats(plan: LessonPlan) -> list[dict]:
    """Planner proposes beats; the harness enforces the interaction contract:
    hook always stands alone as Beat 1 (the Guess checkpoint), the tail
    blocks (practice / explain_back / evaluate) each stand alone and in
    canonical order, and the middle collapses to at most MAX_TEACHING_BEATS
    steering beats. Returns JSON-able beat dicts for the lesson store."""
    hook = None
    tail: dict[str, PlannedBlock] = {}
    middle: list[dict] = []
    for planned in plan.beats:
        group = None
        for block in planned.blocks:
            if block.type == "hook":
                if hook is None:
                    hook = block
            elif block.type in _TAIL_TYPES:
                tail.setdefault(block.type, block)
            else:
                if group is None:
                    group = {"kind": "steer", "label": planned.label, "blocks": []}
                    middle.append(group)
                group["blocks"].append(block)

    if hook is None:
        raise ValueError("plan has no hook block — the hook is spine, always")
    for spine in ("explain_back", "evaluate"):
        if spine not in tail:
            raise ValueError(f"plan has no {spine} block — it is spine, always")

    while len(middle) > MAX_TEACHING_BEATS:
        spill = middle.pop()
        middle[-1]["blocks"].extend(spill["blocks"])

    beats = [{"kind": "guess", "label": hook.title, "blocks": [hook.model_dump()]}]
    for group in middle:
        beats.append({"kind": "steer", "label": group["label"],
                      "blocks": [b.model_dump() for b in group["blocks"]]})
    route_tail = {
        "practice": "Your turn — try one",
        "explain_back": "Explain it back in your own words",
        "evaluate": "Quick check — a couple of questions",
    }
    for block_type in _TAIL_TYPES:
        if block_type in tail:
            beats.append({"kind": _TAIL_KINDS[block_type],
                          "label": route_tail[block_type],
                          "blocks": [tail[block_type].model_dump()]})
    return beats


# ── mappers: content -> component list (the wire shape) ─────────

def _comp(cid: str, component: str, props: dict) -> dict:
    return {"id": cid, "component": component, "props": props}


def _tree(block: PlannedBlock, body: list[dict]) -> list[dict]:
    """Column root + Heading + body components, ids prefixed and unique.
    Headings carry the block title only — no loop-letter tags (learner
    feedback 2026-07-12: the grammar is the teacher's business)."""
    comps = [_comp("heading", "Heading", {"letter": None, "text": block.title})]
    comps.extend(body)
    children = [c["id"] for c in comps]
    root = _comp("root", "Column", {"children": children})
    return [root] + comps


def _prose(cid: str, paragraphs: list) -> dict:
    return _comp(cid, "Prose", {"paragraphs": paragraphs})


def _chip(label: str, action: str, value: str | None = None,
          variant: str = "chip") -> dict:
    return {"label": label, "action": action, "value": value, "variant": variant}


def map_block(block: PlannedBlock, content: BaseModel) -> list[dict]:
    t = block.type
    body: list[dict] = []
    if t == "hook":
        body = [_prose("prose", content.paragraphs)]
        if content.figure is not None:
            body.append(_comp("scene", "FigureSketch", content.figure.model_dump()))
    elif t == "anchor":
        body = [
            _prose("prose", content.paragraphs),
            _comp("definition", "Definition", {
                "label": content.definition_label, "text": content.definition_text,
                "variant": "plain"}),
        ]
    elif t == "picture":
        if content.lead_paragraph:
            body.append(_prose("prose", [content.lead_paragraph]))
        body.append(_comp("figure", "FigureSketch", content.figure.model_dump()))
    elif t == "model":
        body = [_comp("model", "Definition", {
            "label": content.model_label, "text": content.model_text, "variant": "model"})]
    elif t == "formalize":
        if content.intro_paragraph:
            body.append(_prose("prose", [content.intro_paragraph]))
        eq = content.equation
        body.append(_comp("equation", "EquationBlock", {
            "label": eq.label, "tex": eq.tex, "tag": eq.tag, "caption": eq.caption}))
        if content.figure is not None:
            body.append(_comp("figure", "FigureSketch", content.figure.model_dump()))
        if content.symbols:
            body.append(_comp("symbols", "DataTable", {
                "headers": ["Symbol", "In the mental model"],
                "rows": [[s.symbol, s.meaning] for s in content.symbols]}))
        if content.break_text:
            body.append(_comp("break", "Definition", {
                "label": content.break_label or "Where the analogy breaks",
                "text": content.break_text, "variant": "break"}))
    elif t == "geometry":
        if content.lead_paragraph:
            body.append(_prose("prose", [content.lead_paragraph]))
        body.append(_comp("graph", "GraphBlock", content.graph.model_dump()))
    elif t == "practice":
        # worked example is the teacher's turn; the near-twin input is the
        # learner's. expected_answer deliberately never enters the tree —
        # it rides the tool ack (commit-then-grade, same as quiz keys).
        body = [_prose("prose", content.worked_paragraphs)]
        if content.figure is not None:
            body.append(_comp("figure", "FigureSketch", content.figure.model_dump()))
        body.append(_comp("tryone", "PromptInput", {
            "prompt_text": content.problem_text,
            "placeholder": content.placeholder,
            "submit_label": "Send my answer",
            "action": "try_one",
            "skip_label": "Skip for now",
            "skip_action": "skip_checkpoint",
            # the lesson's ONE gentle stay-recommendation (spec 0002) —
            # the first skippable checkpoint gets it, nothing else does
            "note": "Worth the minute — trying one is what makes it stick.",
        }))
    elif t == "explain_back":
        body = [_comp("explain", "ExplainBack", {
            "prompt_text": content.prompt_text, "placeholder": content.placeholder})]
    elif t == "evaluate":
        body = [_comp(f"quiz{i}", "QuizBlock", q.model_dump())
                for i, q in enumerate(content.quizzes)]
    return _tree(block, body)


def append_skip_row(tree: list[dict], note: str | None = None) -> list[dict]:
    """Quiet skip affordance on a skippable block's own surface (spec 0002:
    Beats 4-6 only). The stay-recommendation is one gentle line, never
    repeated — callers pass note on at most one surface per lesson."""
    tree.append(_comp("skiprow", "ChipRow", {
        "chips": [_chip("Skip for now", "skip_checkpoint", variant="quiet")],
        "note": note}))
    tree[0]["props"]["children"].append("skiprow")
    return tree


def map_insert(kind: str, title: str, content: BaseModel) -> list[dict]:
    """Steering inserts: 'example' (one more concrete instance) or
    'reanchor' (fresh, smaller analogy — the original skill's re-enter-at-B).
    Cursor never moves for these."""
    if kind == "reanchor":
        block = PlannedBlock(type="anchor", title=title, brief="")
        return map_block(block, content)
    comps = [
        _comp("heading", "Heading", {"letter": None, "text": title}),
        _prose("prose", content.paragraphs),
    ]
    root = _comp("root", "Column", {"children": [c["id"] for c in comps]})
    return [root] + comps


# ── overview + checkpoint surfaces (spec 0002) ──────────────────

def overview_tree(lesson_number: int, plan: LessonPlan, beats: list[dict],
                  milestone: str | None = None) -> list[dict]:
    """The learner-facing roadmap: place, promise, why-you-care, the route
    in plain words with interactive moments marked, the running example
    teased, and the Start Gate. Loop letter codes never appear here."""
    eyebrow = f"Lesson {lesson_number:04d}"
    if milestone:
        eyebrow += f" · {milestone}"
    route = []
    for i, beat in enumerate(beats, start=1):
        label = beat["label"]
        if beat["kind"] == "guess":
            label += " — you'll take a guess"
        route.append(f"{i}. {label}")
    comps = [
        _comp("header", "LessonHeader", {
            "eyebrow": eyebrow, "title": plan.title,
            "subtitle": plan.subtitle, "loop_plan": None}),
        _prose("why", [plan.why_you_care,
                       f"We'll build everything around one example: {plan.running_example}."]),
        _comp("routehead", "Heading", {"letter": None, "text": "Where we're going"}),
        _prose("route", route),
        _comp("startgate", "ChipRow", {
            "chips": [_chip("Let's start", "start_lesson", variant="primary")],
            "note": "Press when you're ready — nothing streams until you do."}),
    ]
    root = _comp("root", "Column", {"children": [c["id"] for c in comps]})
    return [root] + comps


def guess_checkpoint_tree() -> list[dict]:
    comps = [
        _comp("guess", "PromptInput", {
            "prompt_text": "What's your guess? A wrong-but-reasonable one is exactly what we want.",
            "placeholder": "Say it however it comes to you…",
            "submit_label": "Send my guess",
            "action": "guess",
            "skip_label": "No idea — show me",
            "skip_action": "guess_skip",
        }),
    ]
    root = _comp("root", "Column", {"children": [c["id"] for c in comps]})
    return [root] + comps


def steering_tree() -> list[dict]:
    comps = [
        _comp("steer", "ChipRow", {
            "chips": [
                _chip("Got it →", "steer", "advance", variant="primary"),
                _chip("Give me an example", "steer", "example"),
                _chip("Lost me", "steer", "reanchor"),
            ],
            "note": None}),
    ]
    root = _comp("root", "Column", {"children": [c["id"] for c in comps]})
    return [root] + comps


def next_gate_tree() -> list[dict]:
    comps = [
        _comp("gate", "ChipRow", {
            "chips": [
                _chip("Next lesson →", "next_lesson", variant="primary"),
                _chip("Done for today", "done_today", variant="quiet"),
            ],
            "note": None}),
    ]
    root = _comp("root", "Column", {"children": [c["id"] for c in comps]})
    return [root] + comps

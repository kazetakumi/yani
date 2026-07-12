"""The lesson tools (spec 0002, ADR 0002): plan_lesson / start_lesson / next_block.

A lesson is a dialogue, not a document. plan_lesson runs the planner and
shows the learner the roadmap (Overview) — nothing streams until the
learner presses the Start Gate. start_lesson streams Beat 1 (the hook) and
stops at the Guess checkpoint. Each next_block streams exactly one more
beat — or composes a steering insert without moving the cursor. The
harness owns the plan and cursor (lesson_store); the mentor supplies
judgment through `steering` and `note`.

All three are generator tools (ADR 0001 protocol unchanged): they yield
surface events while running and return a compact ack. Answer keys ride
the acks (commit-then-grade): quiz keys on the evaluate beat, the practice
expected answer on the practice beat."""

from pydantic import BaseModel

from .. import lesson_store, skill_registry, surface_store
from ..agent_prompts import agent_prompt
from ..lesson_blocks import (
    CONTENT_MODELS, AnchorContent, ExampleContent, LessonPlan, PlannedBlock,
    append_skip_row, clamp_beats, guess_checkpoint_tree, map_block, map_insert,
    next_gate_tree, overview_tree, steering_tree,
)
from ..llm import LLM, DEFAULT_MODEL, get_client

STEERINGS = ("advance", "example", "reanchor", "skip", "close")

# What the harness waits for after each beat kind — echoed in acks so the
# mentor always knows whose turn it is.
_AWAITING = {
    "guess": "the learner's guess (action 'guess') or a one-tap skip ('guess_skip')",
    "steer": "a steering chip (action 'steer': advance / example / reanchor)",
    "practice": "the learner's try-one answer (action 'try_one') or 'skip_checkpoint'",
    "explain": "the learner's explain-back (action 'explain_back') or 'skip_checkpoint'",
    "evaluate": "quiz submissions (action 'quiz_result') or 'skip_checkpoint'",
}


def _llm() -> LLM:
    return LLM(get_client(), DEFAULT_MODEL)


def _emit_surface(surface_id: str, components: list):
    surface_store.create(surface_id)
    surface_store.set_components(surface_id, components)
    yield {"ui": "createSurface", "surface_id": surface_id}
    yield {"ui": "updateComponents", "surface_id": surface_id, "components": components}


def _compose(llm: LLM, plan: dict, block: PlannedBlock, learner_note: str = "") -> BaseModel:
    brief = block.brief
    if learner_note:
        # the back-edge (spec 0002): the learner's checkpoint words reach
        # composition — "aim the anchor at their guess" made literal
        brief += f"\n\nlearner context from the chat (aim the content at this): {learner_note}"
    return llm.run_structured(
        [{"role": "system", "content": agent_prompt("block-composer")},
         {"role": "user", "content": (
             f"lesson title: {plan['title']}\n"
             f"running example: {plan['running_example']}\n"
             f"block type: {block.type}\n"
             f"block title: {block.title}\n"
             f"brief: {brief}")}],
        CONTENT_MODELS[block.type],
        step="subagent.block",
    )


def _stream_beat(llm: LLM, lesson_id: str, lesson: dict, beat_index: int,
                 learner_note: str = ""):
    """Compose and emit one beat's blocks plus its checkpoint surface.
    Returns (ack_fields, surface_ids) via StopIteration value."""
    beat = lesson["beats"][beat_index]
    surface_ids, blocks_ack, failed = [], [], []
    quiz_keys, practice_key = [], None

    for i, raw in enumerate(beat["blocks"]):
        block = PlannedBlock.model_validate(raw)
        try:
            # the learner's words steer only the beat's first block — the
            # one that answers them (the anchor after a guess); the rest
            # of the beat follows the plan
            content = _compose(llm, lesson["plan"], block,
                               learner_note if i == 0 else "")
        except Exception as error:
            # one bad block must not kill the beat — skip it, tell the
            # transcript, keep streaming (blocks already on screen stand)
            failed.append({"block": block.type, "error": f"{type(error).__name__}: {error}"})
            continue

        tree = map_block(block, content)
        if beat["kind"] == "explain":
            tree = append_skip_row(tree)
        elif beat["kind"] == "evaluate":
            tree = append_skip_row(tree)
            # commit-then-grade: keys enter the transcript via this ack
            # BEFORE the learner answers; grading is lookup, not memory
            for quiz in content.quizzes:
                correct = next((o.text for o in quiz.options if o.correct), None)
                quiz_keys.append({
                    "question": quiz.question,
                    "correct_answer": correct,
                    "explanations": {o.text: o.explain for o in quiz.options},
                })
        elif beat["kind"] == "practice":
            practice_key = content.expected_answer

        surface_id = f"{lesson_id}-{beat_index:02d}-{i:02d}-{block.type}"
        yield from _emit_surface(surface_id, tree)
        surface_ids.append(surface_id)
        blocks_ack.append({"type": block.type, "title": block.title, "surface_id": surface_id})

    # the checkpoint surface, where one is separate from the blocks
    if beat["kind"] == "guess":
        cp_id = f"{lesson_id}-{beat_index:02d}-cp-guess"
        yield from _emit_surface(cp_id, guess_checkpoint_tree())
        surface_ids.append(cp_id)
    elif beat["kind"] == "steer":
        cp_id = f"{lesson_id}-{beat_index:02d}-cp-steer"
        yield from _emit_surface(cp_id, steering_tree())
        surface_ids.append(cp_id)

    ack = {
        "beat": beat_index + 1,
        "beat_kind": beat["kind"],
        "beat_label": beat["label"],
        "blocks": blocks_ack,
        "awaiting": _AWAITING[beat["kind"]],
    }
    if beat["kind"] == "practice":
        ack["practice_answer_key"] = practice_key
    if quiz_keys:
        ack["quiz_answer_keys"] = quiz_keys
    if failed:
        ack["failed_blocks"] = failed
    return ack, surface_ids


def plan_lesson(topic_brief: str):
    """Plan one Concept Loop lesson and show the learner its Overview (roadmap + Start Gate). Streams NO lesson content — teaching begins only when the learner presses "Let's start" (action 'start_lesson', then call start_lesson). topic_brief must carry the concept, the learner's mission context and level, and what earlier lessons covered."""
    if not skill_registry.is_loaded("mentor"):
        raise ValueError(
            "the mentor skill is not loaded — call load_skill(skill_name='mentor') first"
        )

    llm = _llm()
    plan = llm.run_structured(
        [{"role": "system", "content": agent_prompt("lesson-planner")},
         {"role": "user", "content": f"topic brief: {topic_brief}"}],
        LessonPlan,
        step="subagent.lesson_plan",
    )
    beats = clamp_beats(plan)

    number = surface_store.next_lesson_number()
    lesson_id = f"lesson{number:04d}"
    lesson_store.create(lesson_id, number, plan.model_dump(), beats)

    overview_id = f"{lesson_id}-overview"
    yield from _emit_surface(overview_id, overview_tree(number, plan, beats))

    return {
        "lesson_id": lesson_id,
        "lesson_number": number,
        "title": plan.title,
        "running_example": plan.running_example,
        "route": [b["label"] for b in beats],
        "surface_ids": [overview_id],
        "awaiting": "the Start Gate — say nothing beyond one short line; "
                    "wait for the learner's 'start_lesson' action",
    }


def start_lesson(lesson_id: str):
    """Begin a planned lesson after the learner pressed "Let's start": streams Beat 1 (the hook) and stops at the Guess checkpoint. Call exactly once per lesson, only in response to the 'start_lesson' UI action."""
    lesson = lesson_store.require(lesson_id)
    if lesson["status"] != "planned":
        raise ValueError(f"lesson '{lesson_id}' is {lesson['status']} — start_lesson only runs once, on a planned lesson")

    ack, surface_ids = yield from _stream_beat(_llm(), lesson_id, lesson, 0)
    lesson_store.update(lesson_id, status="teaching", cursor=1)
    ack.update({"lesson_id": lesson_id, "surface_ids": surface_ids,
                "beats_remaining": len(lesson["beats"]) - 1})
    return ack


def next_block(lesson_id: str, steering: str, note: str = ""):
    """Advance the lesson one beat, or serve a steering detour, per the learner's checkpoint signal. steering: 'advance' or 'skip' stream the next beat — after a guess, put the learner's guess in `note` so the beat is composed AT it; 'example' / 'reanchor' compose ONE insert from your `note` brief (cursor does not move — write the brief yourself: for reanchor, a SMALLER concept with a FRESH analogy aimed at what confused them); 'close' ends the lesson with the Next Gate — call it only after your chat Close. The practice and evaluate acks carry answer keys: grade by lookup, never from memory."""
    if steering not in STEERINGS:
        raise ValueError(f"steering must be one of {STEERINGS}, got {steering!r}")
    lesson = lesson_store.require(lesson_id)
    if lesson["status"] == "planned":
        raise ValueError("lesson not started — wait for the Start Gate, then call start_lesson")
    if lesson["status"] == "done":
        raise ValueError(f"lesson '{lesson_id}' is already closed")

    llm = _llm()
    cursor = lesson["cursor"]
    beats = lesson["beats"]

    if steering == "close":
        gate_id = f"{lesson_id}-next-gate"
        yield from _emit_surface(gate_id, next_gate_tree())
        lesson_store.update(lesson_id, status="done")
        return {"lesson_id": lesson_id, "lesson_complete": True,
                "surface_ids": [gate_id],
                "awaiting": "'next_lesson' or 'done_today' — the learner closes the session, never you"}

    if steering in ("example", "reanchor"):
        if not note.strip():
            raise ValueError(f"steering '{steering}' needs a note: the self-contained brief for the insert block")
        if steering == "reanchor":
            if lesson["reanchor_count"] >= lesson_store.MAX_REANCHORS:
                return {
                    "lesson_id": lesson_id,
                    "reanchor_cap_reached": True,
                    "guidance": "two re-anchors already served — move on (steering='advance'); "
                                "spaced review will catch what remains. Never re-explain the same thing louder.",
                }
            content = llm.run_structured(
                [{"role": "system", "content": agent_prompt("block-composer")},
                 {"role": "user", "content": (
                     f"lesson title: {lesson['plan']['title']}\n"
                     f"running example: {lesson['plan']['running_example']}\n"
                     "block type: anchor\n"
                     "block title: A fresh way in\n"
                     f"brief: {note}")}],
                AnchorContent, step="subagent.block",
            )
            insert_kind, count = "reanchor", lesson["reanchor_count"] + 1
            lesson_store.update(lesson_id, reanchor_count=count)
        else:
            content = llm.run_structured(
                [{"role": "system", "content": agent_prompt("block-composer")},
                 {"role": "user", "content": (
                     f"lesson title: {lesson['plan']['title']}\n"
                     f"running example: {lesson['plan']['running_example']}\n"
                     "block type: example\n"
                     "block title: Another angle\n"
                     f"brief: {note}")}],
                ExampleContent, step="subagent.block",
            )
            insert_kind = "example"

        seq = lesson.get("insert_seq", 0) + 1
        lesson_store.update(lesson_id, insert_seq=seq)
        insert_id = f"{lesson_id}-insert-{seq:02d}-{insert_kind}"
        title = "A fresh way in" if insert_kind == "reanchor" else "Another angle"
        yield from _emit_surface(insert_id, map_insert(insert_kind, title, content))
        # hand the floor back: same checkpoint again, new chips
        chips_id = f"{insert_id}-cp"
        yield from _emit_surface(chips_id, steering_tree())
        return {"lesson_id": lesson_id, "insert": insert_kind,
                "surface_ids": [insert_id, chips_id],
                "awaiting": _AWAITING["steer"],
                "cursor_unmoved": True}

    # advance | skip — stream the next beat (skip differs only in what the
    # evidence log already recorded and in what the mentor says in chat)
    if cursor >= len(beats):
        return {"lesson_id": lesson_id, "beats_exhausted": True,
                "guidance": "all beats delivered — write your chat Close (verdict or honest IOU, "
                            "then the one-line mental model), then call next_block(steering='close')"}

    ack, surface_ids = yield from _stream_beat(llm, lesson_id, lesson, cursor,
                                               learner_note=note.strip())
    lesson_store.update(lesson_id, cursor=cursor + 1)
    ack.update({"lesson_id": lesson_id, "surface_ids": surface_ids,
                "beats_remaining": len(beats) - cursor - 1})
    if steering == "skip":
        ack["skipped_previous_checkpoint"] = True
    return ack

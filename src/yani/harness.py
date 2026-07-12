import inspect
from pathlib import Path

from .llm import LLM, get_client, DEFAULT_MODEL
from dotenv import load_dotenv
from .state import State
from .tools import ToolExecutor
from .observability import Logger
import json

load_dotenv()



MODEL = DEFAULT_MODEL

# Hard ceiling on decide→act rounds per user turn. The 2026-07-10 log showed
# 50 rounds (~170K input tokens) on one weather question when the model had
# no legal way to finish — this is the fuse that makes the next unknown
# failure cost cents, not dollars. A legitimate UI turn is ~5 rounds.
MAX_STEPS = 12

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_system_prompt() -> str:
    # Read fresh on every call, deliberately not cached: the whole point of
    # pulling this out of state.json is that editing the file takes effect
    # immediately, on the very next turn — including on already-resumed
    # conversations. A few KB of markdown is nothing to re-read per turn.
    base = (PROMPTS_DIR / "system_prompt.md").read_text().strip()
    # environment block, computed at request time (the Claude Code pattern):
    # the model has no idea what day it is unless the harness tells it
    from datetime import date
    env = f"## Environment\n\nToday's date: {date.today().isoformat()}. Model: {MODEL}."
    # the deterministic session ritual (spec 0001): workspace state + this
    # session's verdict, recomputed every turn — the model executes it,
    # never chooses it
    from .workspace import ritual_prompt_block
    # Skills, two disclosure modes per the auto_enable frontmatter flag:
    # auto-enabled bodies ride whole in every prompt; the rest appear as a
    # name+description menu the model pulls from with load_skill.
    from .skill_registry import list_skills
    sections = [base, env, ritual_prompt_block()]
    lazy = []
    for skill in list_skills():
        if skill["auto_enable"]:
            sections.append(skill["body"])
        else:
            lazy.append(f"- **{skill['name']}** — {skill['description']}")
    if lazy:
        # the menu travels inside a <system-reminder> block — the tag the
        # prompt's own Skills section tells the model to look for
        sections.append(
            "<system-reminder>\n"
            "## Skills\n\n"
            "Extended capabilities, loaded on demand. Before doing a skill's "
            "job, call load_skill(skill_name=...) and follow the workflow it "
            "returns. A loaded skill stays available for the rest of the "
            "conversation.\n\n" + "\n".join(lazy) + "\n</system-reminder>"
        )
    return "\n\n".join(sections)


tool_executor = ToolExecutor()

logger = Logger()

# Single source of truth: which tools produce a client-visible UI event, and
# what that event is called on the wire. camelCase to match the ui-builder
# skill's own vocabulary — translated here, not carried by the tool itself,
# so create_surface (etc.) only ever returns its own domain data.
_UI_TOOL_ACTIONS = {
    "create_surface": "createSurface",
    "update_components": "updateComponents",
    "update_data": "updateDataModel",
}

def step(llm: LLM, state: State, tool_executor: ToolExecutor):
    """Generator version of the old bool-returning step(). Forwards each
    text.delta as it streams in, then yields exactly one trailing
    {"type": "step.done", "has_more_work": bool} — the old return value,
    smuggled out as the last item in the stream since yield and return
    don't compose here."""

    messages = [{"role": "system", "content": load_system_prompt()}] + state.get_messages()
    tools = tool_executor.get_tools()

    text_response = None
    tool_calls = None

    for event in llm.stream(messages, tools):
        if event["type"] == "text.delta":
            yield event
        elif event["type"] == "done":
            text_response = event["text_response"]
            tool_calls = event["tool_calls"]

    if tool_calls:
        for call in tool_calls:
            state.update_tool_call_request(call)
            tool_name = call.name
            args = json.loads(call.arguments)
            # announce before executing — Lesson 0026's silent-detour fix:
            # without this, a multi-tool turn is >10s of dead air client-side
            yield {"type": "tool.start", "name": tool_name}
            tool_result = tool_executor.execute(tool_name, args)
            # Streaming tool (ADR 0001): drive the generator, forwarding each
            # {"ui": EventName, ...} item as a wire event the moment the tool
            # yields it; the generator's return value is the transcript ack.
            if inspect.isgenerator(tool_result):
                gen = tool_result
                while True:
                    try:
                        item = next(gen)
                    except StopIteration as stop:
                        tool_result = stop.value if stop.value is not None else ""
                        break
                    if isinstance(item, dict) and "ui" in item:
                        payload = {k: v for k, v in item.items() if k != "ui"}
                        yield {"type": f"ui.{item['ui']}", **payload}
            state.update_tool_call_response(call.call_id, tool_result)
            # a failed tool returns an "ERROR: ..." string, not a dict — that
            # belongs in the transcript for the model to react to, never on
            # the wire as a UI event (**str would crash here anyway)
            if tool_name in _UI_TOOL_ACTIONS and isinstance(tool_result, dict):
                yield {"type": f"ui.{_UI_TOOL_ACTIONS[tool_name]}", **tool_result}
        yield {"type": "step.done", "has_more_work": True}
        return

    if text_response:
        state.update_text_response(text_response)
    yield {"type": "step.done", "has_more_work": False}

def loop(user_message: str):
    """Generator version of the old str-returning loop(). Forwards each
    step()'s text.delta events, drives the same has_more_work while-loop
    as before off the step.done marker, then yields one final
    {"type": "turn.done", "text_response": reply} once state is saved."""

    llm = LLM(get_client(), MODEL)
    state = State()
    state.load()

    state.add_user_message(user_message)
    logger.log_line(step="init", user_message=user_message)

    has_more_work = True
    steps_taken = 0
    while has_more_work:
        steps_taken += 1
        if steps_taken > MAX_STEPS:
            logger.log_line(step="max_steps_reached", max_steps=MAX_STEPS)
            yield {"type": "error", "message": f"turn aborted after {MAX_STEPS} steps"}
            break
        for event in step(llm, state, tool_executor):
            if event["type"] == "text.delta":
                yield event
            elif event["type"] == "step.done":
                has_more_work = event["has_more_work"]
            else:
                yield event

    reply = state.get_last_reply()
    state.save()
    logger.log_line(step="end", final_reponse=reply)

    yield {"type": "turn.done", "text_response": reply}






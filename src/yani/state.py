import json

from . import users


def _state_file():
    # Resolved fresh per call (multi-user-workspaces map, ticket 01): this
    # learner's chat transcript, a sibling of about.md in their learner home.
    return users.learner_home() / "state.json"


class State:

    def __init__(self):
        self.messages = []

    def load(self):
        state_file = _state_file()
        if state_file.exists():
            # system messages are no longer persisted — they're prepended fresh
            # from prompts/system_prompt.md on every call (see harness.py's
            # step()). Strip any that snuck into an older state.json so a
            # resumed conversation doesn't end up with two system messages.
            self.messages = [
                m for m in json.loads(state_file.read_text()) if m.get("role") != "system"
            ]
        else:
            self.messages = []

    def save(self):
        state_file = _state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(self.messages, indent=2))

    def add_user_message(self, user_message: str):
        self.messages.append({"role": "user", "content": user_message})

    def update_tool_call_request(self, function_call_item):
        # Deliberately minimal, not the full model_dump(): dropping `id`
        # and `status` and keeping only these four — tested with a real
        # multi-step tool call (the London weather round trip) and the
        # model reasoned correctly about its own prior request.
        self.messages.append({
            "type": function_call_item.type,
            "call_id": function_call_item.call_id,
            "name": function_call_item.name,
            "arguments": function_call_item.arguments,
        })

    def update_tool_call_response(self, call_id: str, result):
        self.messages.append({
            "type": "function_call_output",
            "call_id": call_id,
            "output": str(result),
        })

    def update_text_response(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def get_messages(self) -> list:
        return self.messages

    def get_last_reply(self) -> str:
        # A turn may legitimately end without assistant text now — a
        # UI-only reply's last message is a function_call_output, and the
        # system prompt tells the model to stay silent after it. Return ""
        # instead of KeyError-ing on a dict that has no "content".
        last = self.messages[-1] if self.messages else {}
        if last.get("role") == "assistant":
            return last.get("content", "")
        return ""

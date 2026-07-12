import json
import time
import uuid
from pathlib import Path
import os
from .session import session_id_store

LOG_FILE = Path(".yani") / "harness.log.jsonl"

class Logger:

    def __init__(self):
        pass
    
    def log_line(self, **fields) -> None:
        session_id = session_id_store.get()
        LOG_FILE.parent.mkdir(exist_ok=True)
        entry = {"timestamp": time.time(), "session_id": session_id, **fields}
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_llm_call(self, step: str, model: str, usage, latency_ms: float) -> None:
        self.log_line(
            step=step,
            **{
                "gen_ai.request.model": model,
                "gen_ai.usage.input_tokens": usage.input_tokens,
                "gen_ai.usage.output_tokens": usage.output_tokens,
            },
            latency_ms=round(latency_ms),
        )
    
    def log_tool_call(self, tool_name: str, latency_ms: float, ok: bool, args: dict | None = None) -> None:
        # args truncated, not dropped: the 2026-07-10 update_component storm
        # was diagnosable only by inference because the log had no arguments.
        args_repr = json.dumps(args)[:300] if args is not None else None
        self.log_line(step="tool_call", tool_name=tool_name, latency_ms=round(latency_ms), ok=ok, args=args_repr)

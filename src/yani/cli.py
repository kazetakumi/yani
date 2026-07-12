from dotenv import load_dotenv
from .harness import loop
import uuid
from .session import session_id_store

load_dotenv()


user_message = "What's the weather at Dubai today"

def main():
    session_id = uuid.uuid4().hex[:8]
    session_id_store.set(session_id)

    print("<<< User : ", user_message)

    # loop() is a generator now (the SSE conversion) — consume its event
    # stream the same way the server does, just printing instead of framing.
    for event in loop(user_message):
        if event["type"] == "text.delta":
            print(event["text"], end="", flush=True)
        elif event["type"].startswith("ui.") or event["type"] == "error":
            print(f"\n[{event['type']}] {event}")
        elif event["type"] == "turn.done":
            print(f"\n>>> AI Assistant :  {event['text_response']}")

if __name__ == "__main__":
    main()
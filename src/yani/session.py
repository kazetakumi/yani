import contextvars

session_id_store = contextvars.ContextVar("session_id", default=None)
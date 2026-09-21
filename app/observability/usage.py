"""Request-scoped usage accounting, including workflow nodes and RAG calls."""
from contextlib import contextmanager
from contextvars import ContextVar

_current = ContextVar("model_usage", default=None)


@contextmanager
def capture_usage():
    counters = dict(input_tokens=0, output_tokens=0, embedding_tokens=0,
                    llm_calls=0, embedding_calls=0, missing_usage=0)
    token = _current.set(counters)
    try:
        yield counters
    finally:
        _current.reset(token)


def record_usage(usage, *, embedding=False):
    counters = _current.get()
    if counters is None:
        return
    counters["embedding_calls" if embedding else "llm_calls"] += 1
    if usage is None:
        counters["missing_usage"] += 1
        return
    if embedding:
        counters["embedding_tokens"] += usage.total_tokens
    else:
        counters["input_tokens"] += usage.prompt_tokens
        counters["output_tokens"] += usage.completion_tokens

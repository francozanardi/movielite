from typing import Callable

_store = {}

def register_function(fn: Callable) -> str:
    key = f"registered_fn_{len(_store)}"
    _store[key] = fn
    return key

def get_function(key: str) -> Callable:
    return _store[key]

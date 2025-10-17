from typing import Any

from typing_extensions import LiteralString, Never


def raise_type_error(value: Any, t: type | LiteralString) -> Never:
    if isinstance(t, str):
        t_str = t
    else:
        t_str = t.__name__

    raise TypeError(f"Cannot structure {value!r} into {t_str} (type: {type(value)})")

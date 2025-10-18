from __future__ import annotations

from typing import Any

from typing_extensions import LiteralString, Never


def raise_type_error(value: Any, t: type | LiteralString) -> Never:
    t_str = t if isinstance(t, str) else t.__name__

    raise TypeError(f"Cannot structure {value!r} into {t_str} (type: {type(value)})")

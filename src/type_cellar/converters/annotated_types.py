from __future__ import annotations

from typing import Annotated

from beartype.typing import get_args, get_origin
from typing_extensions import Any


# @cbase.register_structure_hook
def res_unwrap_annotated(value, _: type[Any]) -> None:
    """TODO not yet implemented"""
    metas: list[Any] = []
    base = value
    while get_origin(base) is Annotated:
        b, *m = get_args(base)
        metas.extend(m)
        base = b

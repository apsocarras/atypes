from __future__ import annotations

import datetime as dt

from cattrs import Converter

from ._raise_util import raise_type_error


def des_datetimes(value: dt.datetime):
    return value.isoformat()


def res_datetimes(value, _: type[dt.datetime]) -> dt.datetime:
    if isinstance(value, str):
        return dt.datetime.fromisoformat(value)
    if isinstance(value, dt.datetime):
        return value
    raise_type_error(value, dt.datetime)


def register_datetime_hooks(conv: Converter) -> None:
    """Register structure/unstructure hooks for datetime.datetime."""
    conv.register_unstructure_hook(dt.datetime, des_datetimes)
    conv.register_structure_hook(dt.datetime, res_datetimes)

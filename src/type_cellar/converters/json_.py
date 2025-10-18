from __future__ import annotations

import json

import cattrs
from beartype.typing import Any
from cattrs import Converter

from ..wrappers import (
    JSON_MapString,
)


def json_mapstring_des(value: JSON_MapString) -> str:
    """Turn the mapping into a JSON *string*. Keys are stringified

    - JSON object keys must be strings.
    - Values are left as JSON types.
    """
    payload = {str(k): v for k, v in value.items()}
    return json.dumps(payload, separators=(",", ":"))


def json_mapstring_res(value: Any, _: Any) -> JSON_MapString:
    """Accept a JSON string (preferred), or a plain dict, and return a JSON_MapString."""
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise TypeError("Expected a JSON object string for JSON_MapString.")
        return JSON_MapString(parsed)
    elif isinstance(value, dict):
        return JSON_MapString(value)
    else:
        raise TypeError(
            f"Cannot structure type {type(value).__name__} into JSON_MapString; "
            + "expected JSON string or dict."
        )


def jsonify_sequences_des(conv: cattrs.Converter) -> None:
    """Destructure tuples and sets to list"""
    conv.register_unstructure_hook(tuple, list)
    conv.register_unstructure_hook(set, list)


def register_json_hooks(conv: Converter) -> None:
    conv.register_unstructure_hook(tuple, list)
    conv.register_unstructure_hook(set, list)
    conv.register_unstructure_hook(JSON_MapString, json_mapstring_des)
    conv.register_structure_hook(JSON_MapString, json_mapstring_res)


def __doctest_json_mapstring():
    """

    ```pycon
    >>> import json
    >>> import attrs
    >>> import cattrs
    >>> from wck_python_utils.types._types import JSON_MapString
    >>> from wck_python_utils.models.converters import cbase

    >>> d = JSON_MapString(data={"a": 1, "b": True})
    >>> d
    JSON_MapString({a: 1, b: True})

    >>> list(d.items())  # doctest: +ELLIPSIS
    [('a', 1), ('b', True)]
    >>> json.dumps({str(k): str(v) for k, v in d.items()})
    '{"a": "1", "b": "True"}'

    >>> @attrs.define
    ... class Example:
    ...     meta: JSON_MapString

    >>> ex = Example(d)
    >>> cbase.unstructure(ex)
    {'meta': '{"a":1,"b":true}'}

    >>> raw = {"meta": '{"a": 1, "b": true}'}
    >>> obj = cbase.structure(raw, Example)
    >>> obj.meta
    JSON_MapString({a: 1, b: True})

    ```
    """


if __name__ == "__main__":
    import doctest

    _ = doctest.testmod()

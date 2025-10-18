"""Utility class for creating de-duplication keys (e.g. for Pub/Sub)"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal, TypeVar

from cattrs import Converter
from typing_extensions import NotRequired, TypedDict, Unpack, override

from .converters._raise_util import raise_type_error


class SalientAttributes(TypedDict, total=False):
    """Attributes for creating a dedupe key

    NOTE: All the values must be JSON serializable for use in a DedupeKeyMeta

    NOTE: ``natural_key`` will override all other values if provided
    """

    natural_key: NotRequired[str]
    data: NotRequired[bytes]
    trace_id: NotRequired[str]
    request_id: NotRequired[str]


def hash_bytes(b: bytes, /) -> str:
    return hashlib.sha256(b).hexdigest()


class DedupeKeyMeta(ABC):
    """Natural key = key provided at init. Otherwise will hash payload along with provided salient attributes"""

    def __init__(self, **kwargs: Unpack[SalientAttributes]) -> None:
        natural_key: str | None = kwargs.get("natural_key")
        if natural_key:
            self._key: str = self.underlying(natural_key)
        else:
            if b := kwargs.pop("data", None):
                payload_hash = hash_bytes(b)
                salient: dict[str, str | object] | SalientAttributes = {
                    "payload_hash": payload_hash,
                    **kwargs,
                }
            else:
                salient = kwargs
            raw = json.dumps(salient, sort_keys=True).encode()
            raw_hash = hash_bytes(raw)
            self._key = raw_hash
        super().__init__()

    @classmethod
    @abstractmethod
    def prefix(cls) -> str:
        """NOTE: Includes prefix for use in firebase document stores."""
        ...

    @override
    def __str__(self) -> str:
        """NOTE: Includes prefix for use in firebase document stores."""
        return f"{self.prefix()}:{self._key}"

    @classmethod
    def underlying(cls, s: str) -> str:
        """
        ```pycon
        >>> s="alert:12345"
        >>> DedupeKeyMeta.underlying(s)
        '12345'
        >>> s2=":1234"
        >>> DedupeKeyMeta.underlying(s2)
        '1234'
        >>> s3="dedupe:9999"
        >>> DedupeKeyMeta.underlying(s3)
        '9999'

        ```
        """
        return s.split(":", 1)[-1]

    @property
    def key(self) -> str:
        return self._key

    @override
    def __eq__(self, value: object, /) -> bool:
        """NOTE: Does NOT consider the prefix"""
        if isinstance(value, DedupeKeyMeta):
            return self.key == value.key
        return False


class DedupeKey(DedupeKeyMeta):
    @override
    @classmethod
    def prefix(cls) -> str:
        return "dedupe"


class AlertKey(DedupeKeyMeta):
    @override
    @classmethod
    def prefix(cls) -> str:
        return "alert"


def dedupe_key_des_hook_factory(cls: type) -> Callable[..., str]:
    """Convert to str and keeps prefix"""
    return lambda v: str(v)


_T_Dedupe = TypeVar("_T_Dedupe", bound=DedupeKeyMeta)


def dedupe_key_res_hook_factory(cls: type[_T_Dedupe]) -> Callable[..., _T_Dedupe]:
    """Remove the prefix from the key before constructing"""

    def _wrapper(value: Any, _: _T_Dedupe) -> _T_Dedupe:
        if isinstance(value, str):
            key: str = cls.underlying(value)
            return cls(natural_key=key)
        elif isinstance(value, cls):
            return value
        raise_type_error(value, cls)

    return _wrapper


def __doctest_dedupe_key() -> None:
    """
    ```
    >>> import attr
    >>> from cattrs import Converter
    >>> from attr import define

    >>> @define
    ... class Foo:
    ...     d1: DedupeKey = attr.field(
    ...         factory=lambda: DedupeKey(
    ...             trace_id="123", request_id="456", data=b"you dropped this, king."
    ...         )
    ...     )
    ...     d2: DedupeKey = attr.field(
    ...         factory=lambda: DedupeKey(
    ...             data=b"you dropped this, king.",
    ...             request_id="456",
    ...             trace_id="123",
    ...         )
    ...     )
    >>> f = Foo()
    >>> assert f.d1 == f.d2
    >>> c = Converter()
    >>> register_dedupe_hooks(c)
    >>> des = c.unstructure(f)
    >>> d1_res = c.structure(des["d1"], DedupeKey)
    >>> d2_res = c.structure(des["d2"], DedupeKey)
    >>> assert d1_res == d2_res # note key order doesn't matter

    >>> d3 = AlertKey(natural_key=des["d1"])
    >>> assert d3 == f.d1 == f.d2

    ```
    """


def register_dedupe_hooks(conv: Converter) -> None:
    ## TODO: switching away from hardcoded values
    # c.register_unstructure_hook(DedupeKey, lambda v: str(v))
    # c.register_structure_hook(DedupeKey, lambda v, _: DedupeKey(natural_key=v))
    # c.register_unstructure_hook(AlertKey, lambda v: str(v))
    # c.register_structure_hook(AlertKey, lambda v, _: AlertKey(natural_key=v))

    pred: Callable[..., bool] = lambda t: issubclass(t, DedupeKeyMeta)

    def _reg(des_or_res: Literal["des", "res"], hook: Callable[..., Any]) -> None:
        nonlocal conv, pred
        if des_or_res == "des":
            _ = conv.register_unstructure_hook_factory(pred, hook)
        else:
            _ = conv.register_structure_hook_factory(pred, hook)

    _reg("des", dedupe_key_des_hook_factory)
    _reg("res", dedupe_key_res_hook_factory)

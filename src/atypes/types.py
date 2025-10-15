# pyright: reportPrivateUsage=false
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    SupportsIndex,
    TypeAlias,
    overload,
    runtime_checkable,
)

import useful_types as use
from typing_extensions import LiteralString, Sentinel, override

if TYPE_CHECKING:
    from .wrappers import HtmlBytes, JsonBytes, OtherBytes


logger = logging.getLogger(__name__)


JSONScalar: TypeAlias = str | int | float | bool | None
JSONType: TypeAlias = JSONScalar | Mapping[str, "JSONType"] | Sequence["JSONType"]


class HasHeaders(Protocol):
    @property
    def headers(self) -> Mapping[str, str]: ...


@runtime_checkable
class HasHeadersAndRaw(HasHeaders, Protocol):
    @property
    def raw_bytes(self) -> bytes: ...


class HasHeadersBody(HasHeaders, Protocol):
    @property
    def body(self) -> JsonBytes | HtmlBytes | OtherBytes: ...


class HasHeadersAndArgs(HasHeaders, Protocol):
    """
    Protocol representing a flask-like object with HTTP headers and url params (args)
    """

    @property
    def args(self) -> Mapping[str, Any]: ...


@runtime_checkable
class SequenceNotStr(Protocol[use._T_co]):
    """
    https://github.com/python/typing/issues/256#issuecomment-1442633430

    Cribbed from useful_types. Making it runtime_checkable.
    """

    @overload
    def __getitem__(self, index: SupportsIndex, /) -> use._T_co: ...
    @overload
    def __getitem__(self, index: slice, /) -> Sequence[use._T_co]: ...
    def __contains__(self, value: object, /) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[use._T_co]: ...
    def index(self, value: Any, start: int = 0, stop: int = ..., /) -> int: ...
    def count(self, value: Any, /) -> int: ...
    def __reversed__(self) -> Iterator[use._T_co]: ...


class SentinelMeta(ABC, Sentinel):
    @staticmethod
    @abstractmethod
    def value() -> str: ...

    @abstractmethod
    @override
    def __str__(self) -> str:
        return self.value()

    @abstractmethod
    def __bool__(self) -> Literal[True] | Literal[False]: ...


class OmittedDefaultSentinel(SentinelMeta):
    @staticmethod
    @override
    def value() -> Literal["omitted"]:  # noqa: F821
        return "omitted"

    @override
    def __str__(self) -> str:
        return super().__str__()

    @override
    def __bool__(self) -> Literal[False]:
        return False


class NotImplementSentinel(SentinelMeta):
    @staticmethod
    @override
    def value() -> Literal["not-yet-implemented"]:  # noqa: F821
        return "not-yet-implemented"

    @override
    def __str__(self) -> str:
        return super().__str__()

    @override
    def __bool__(self) -> Literal[False]:
        return False

    @override
    def __eq__(self, other: object) -> bool:
        return self.__class__ == other.__class__


class UUID_Str:
    """Main purpose is to convert a uuid to string"""

    def __init__(self, _uuid: uuid.UUID | None = None) -> None:
        self._uuid: uuid.UUID = _uuid or uuid.uuid4()

    @override
    def __str__(self) -> str:  # hyphenated canonical form
        return str(self._uuid)

    @override
    def __repr__(self) -> str:
        return str(self._uuid)

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, UUID_Str):
            return self._uuid == other._uuid
        if isinstance(other, uuid.UUID):
            return self._uuid == other
        if isinstance(other, str):
            try:
                other_uuid = uuid.UUID(hex=other)
                return self._uuid == other_uuid
            except Exception:
                return False
        raise NotImplementedError

    @override
    def __hash__(self) -> int:
        return hash(self._uuid)


class LoggerEvent(ABC):
    @property
    @abstractmethod
    def event(self) -> LiteralString | str: ...
    @property
    @abstractmethod
    def status(self) -> LiteralString | str: ...
    @property
    @abstractmethod
    def details(self) -> Mapping[str, JSONType]: ...

# pyright: reportPrivateUsage=false
from __future__ import annotations

import logging
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
from typing_extensions import LiteralString, Self, Sentinel, override

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

    @classmethod
    def make(cls) -> Self:
        return cls(cls.value())


class OmittedDefaultSentinel(SentinelMeta):
    @staticmethod
    @override
    def value() -> Literal["OMITTED"]:  # noqa: F821
        return "OMITTED"

    @override
    def __str__(self) -> str:
        return super().__str__()

    @override
    def __bool__(self) -> Literal[False]:
        return False


class NotImplementSentinel(SentinelMeta):
    @staticmethod
    @override
    def value() -> Literal["NOT-IMPLEMENTED"]:  # noqa: F821
        return "NOT-IMPLEMENTED"

    @override
    def __str__(self) -> str:
        return super().__str__()

    @override
    def __bool__(self) -> Literal[False]:
        return False

    @override
    def __eq__(self, other: object) -> bool:
        return self.__class__ == other.__class__


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


class LoggerEventProto(Protocol):
    @property
    def event(self) -> LiteralString | str: ...
    @property
    def status(self) -> LiteralString | str: ...
    @property
    def details(self) -> Mapping[str, JSONType]: ...

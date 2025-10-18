# pyright: reportPrivateUsage=false
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, MutableMapping, Sequence
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    Protocol,
    SupportsIndex,
    TypeAlias,
    overload,
    runtime_checkable,
)

import useful_types as use
from typing_extensions import LiteralString, Self, Sentinel, TypedDict, override

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


class _VersionStampErrorArgs(TypedDict):
    stamped_name: str
    raw_name: str
    unstamped_name: str


class _TableInfoKwargs(TypedDict):
    project_id: str
    dataset_id: str
    table_id: str


class HasTableInfoProto(Protocol):
    @property
    def project_id(self) -> str: ...
    @property
    def dataset_id(self) -> str: ...
    @property
    def table_id(self) -> str: ...
    @property
    def full_table_id(self) -> str: ...


@runtime_checkable
class FlaskRequestProto(Protocol):
    """
    Structural subset of flask.Request (Werkzeug Request) with the features most apps rely on.
    """

    method: str
    url: str
    path: str
    headers: Mapping[str, str]
    args: Mapping[str, str]  # query params (first value per key)
    form: Mapping[str, str]  # form fields (first value per key)
    files: Mapping[str, Any]  # e.g., werkzeug.datastructures.FileStorage
    cookies: Mapping[str, str]
    remote_addr: str | None
    content_type: str | None
    mimetype: str | None
    # WSGI environ (read-only mapping in Flask)
    environ: Mapping[str, Any]

    @overload
    def get_data(  # pyright: ignore[reportOverlappingOverload]
        self,
        cache: bool = True,
        as_text: Literal[False] = False,
        parse_form_data: bool = False,
    ) -> bytes: ...
    @overload
    def get_data(
        self,
        cache: bool = True,
        as_text: Literal[True] = ...,
        parse_form_data: bool = False,
    ) -> str: ...
    def get_data(
        self, cache: bool = True, as_text: bool = False, parse_form_data: bool = False
    ) -> bytes | str: ...

    def get_json(self, silent: bool = False, force: bool = False) -> Any | None: ...
    @property
    def is_json(self) -> bool: ...


@runtime_checkable
class FlaskResponseProto(Protocol):
    """
    Structural subset of flask.Response (Werkzeug Response).
    """

    status_code: int
    headers: MutableMapping[str, str]
    mimetype: str | None
    content_type: str | None

    # get_data(as_text=False) -> bytes | str
    @overload
    def get_data(  # pyright: ignore[reportOverlappingOverload]
        self,
        cache: bool = True,
        as_text: Literal[False] = False,
        parse_form_data: bool = False,
    ) -> bytes: ...
    @overload
    def get_data(
        self,
        cache: bool = True,
        as_text: Literal[True] = ...,
        parse_form_data: bool = False,
    ) -> str: ...
    def get_data(
        self, cache: bool = True, as_text: bool = False, parse_form_data: bool = False
    ) -> bytes | str: ...

    def set_data(self, data: bytes | str) -> None: ...

    # Cookie helpers
    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: int | None = None,
        expires: int | str | None = None,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str | None = None,
    ) -> None: ...
    def delete_cookie(
        self, key: str, path: str = "/", domain: str | None = None
    ) -> None: ...


class SupportsStr(Protocol):
    @override
    def __str__(self) -> str: ...


UrlLike = str | SupportsStr


@runtime_checkable
class HTTPXRequestProto(Protocol):
    """
    Structural subset of httpx.Request.
    """

    method: str
    url: UrlLike
    headers: Mapping[str, str]
    content: bytes | None

    def copy(self) -> HTTPXRequestProto: ...


@runtime_checkable
class HTTPXResponseProto(Protocol):
    """
    Structural subset of httpx.Response.
    """

    status_code: int
    headers: Mapping[str, str]
    reason_phrase: str
    url: UrlLike
    request: HTTPXRequestProto

    content: bytes
    text: str

    def json(self) -> Any: ...
    def iter_bytes(self) -> Iterator[bytes]: ...
    def raise_for_status(self) -> None: ...


ExternalRequest: TypeAlias = Annotated[
    FlaskRequestProto | HTTPXRequestProto, "Request from 3rd-party library"
]
ExternalResponse: TypeAlias = Annotated[
    FlaskResponseProto | HTTPXResponseProto, "Response from 3rd-party library"
]

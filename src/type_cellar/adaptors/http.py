# pyright: reportPrivateUsage = false

from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Mapping
from http import HTTPStatus
from typing import (
    Any,
    Generic,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    overload,
    runtime_checkable,
)

import attr

from .._types import (
    ExternalRequest,
    ExternalResponse,
    FlaskRequestProto,
    FlaskResponseProto,
    HTTPXRequestProto,
    HTTPXResponseProto,
)
from ..enums import HttpMethod, SerialFormatType
from ..wrappers import HtmlBytes, JsonBytes, OtherBytes, XMLBytes


def _coerce_http_method(val: str | None) -> HttpMethod:
    try:
        # If HttpMethod is a str-valued Enum: HttpMethod("GET")
        return HttpMethod(val)
    except Exception:
        return HttpMethod.UNKNOWN  # require this member in your Enum


@runtime_checkable
class _HasContent(Protocol):
    @property
    def content(self) -> bytes | None: ...


@runtime_checkable
class _HasGetData(Protocol):
    def get_data(
        self,
        cache: bool = True,
    ) -> Any: ...


def _extract_bytes(msg: ExternalRequest | ExternalResponse) -> bytes:
    if isinstance(msg, _HasContent):
        body = msg.content  # httpx.Request content can be None
    else:
        body = msg.get_data()
    return body or b""


def construct_bytewrapper(
    msg: ExternalRequest | ExternalResponse,
) -> JsonBytes | HtmlBytes | OtherBytes | XMLBytes:
    """Wrap the type of the payload based on content-type"""
    sformat = SerialFormatType.from_header(msg.headers)
    body: bytes = _extract_bytes(msg)
    match sformat:
        case SerialFormatType.APPLICATION_JSON:
            return JsonBytes(body)
        case SerialFormatType.TEXT_HTML:
            return HtmlBytes(body)
        case SerialFormatType.APPLICATION_XML:
            return XMLBytes(body)
        case _:
            return XMLBytes(body)


_T_Req = TypeVar("_T_Req", FlaskRequestProto, HTTPXRequestProto, covariant=True)
_T_Resp = TypeVar("_T_Resp")
_T_Body = TypeVar(
    "_T_Body",
)

_AnyBytes: TypeAlias = JsonBytes | HtmlBytes | OtherBytes | XMLBytes
_T_ByteWrapper = TypeVar(
    "_T_ByteWrapper",
    JsonBytes,
    HtmlBytes,
    XMLBytes,
    OtherBytes,
    _AnyBytes,
    covariant=True,
)


class _BodyHeaders(ABC, Generic[_T_ByteWrapper]):
    """Common attrs/methods for adaptors that expose headers/body."""

    _headers: Mapping[str, str]
    _body: _T_ByteWrapper

    @property
    def headers(self) -> Mapping[str, str]:
        return self._headers

    @property
    def body(self) -> _T_ByteWrapper:
        return self._body

    @property
    def raw(self) -> bytes:
        return self._body.raw


@runtime_checkable
class HttpRequestAdaptor(Protocol, Generic[_T_ByteWrapper]):
    """Normalized view over any 3rd-party HTTP request type."""

    @property
    def method(self) -> HttpMethod: ...
    @property
    def url(self) -> str: ...
    @property
    def path(self) -> str: ...
    @property
    def args(self) -> Mapping[str, str]: ...
    @property
    def headers(self) -> Mapping[str, str]: ...
    @property
    def body(self) -> _T_ByteWrapper: ...
    @property
    def raw(self) -> bytes: ...
    def get_json(self) -> Any: ...
    @property
    def remote_addr(self) -> str | None: ...


@attr.define
class SimpleHttpRequestAdaptor(
    _BodyHeaders[_T_ByteWrapper], Generic[_T_Req, _T_ByteWrapper]
):
    """A concrete, framework-agnostic request adaptor."""

    external: _T_Req
    _method: HttpMethod
    _url: str
    _path: str
    _args: Mapping[str, str]
    _headers: Mapping[str, str]
    _body: _T_ByteWrapper
    _remote_addr: str | None
    _get_json: Callable[[], Any]

    @property
    def method(self) -> HttpMethod:
        return self._method

    @property
    def url(self) -> str:
        return self._url

    @property
    def path(self) -> str:
        return self._path

    @property
    def args(self) -> Mapping[str, str]:
        return self._args

    @property
    def remote_addr(self) -> str | None:
        return self._remote_addr


_S: TypeAlias = SimpleHttpRequestAdaptor[_T_Req, _T_ByteWrapper]

_T_KnownBytes = TypeVar(
    "_T_KnownBytes",
)


@overload
def from_werkzeug_request(
    req: FlaskRequestProto, byte_t: type[JsonBytes]
) -> _S[FlaskRequestProto, JsonBytes]: ...
@overload
def from_werkzeug_request(
    req: FlaskRequestProto, byte_t: type[HtmlBytes]
) -> _S[FlaskRequestProto, HtmlBytes]: ...
@overload
def from_werkzeug_request(
    req: FlaskRequestProto, byte_t: type[XMLBytes]
) -> _S[FlaskRequestProto, XMLBytes]: ...
@overload
def from_werkzeug_request(
    req: FlaskRequestProto, byte_t: None
) -> _S[FlaskRequestProto, _AnyBytes]: ...
def from_werkzeug_request(
    req: FlaskRequestProto,
    byte_t: type[_T_ByteWrapper] | None = None,
) -> (
    SimpleHttpRequestAdaptor[FlaskRequestProto, JsonBytes]
    | SimpleHttpRequestAdaptor[FlaskRequestProto, HtmlBytes]
    | SimpleHttpRequestAdaptor[FlaskRequestProto, XMLBytes]
    | SimpleHttpRequestAdaptor[FlaskRequestProto, _AnyBytes]
):
    b: bytes = _extract_bytes(req)

    construct_args = {
        "external": req,
        "_method": _coerce_http_method(req.method),
        "_url": req.url,
        "_path": req.path,
        "_args": dict(req.args.items()),
        "_headers": dict(req.headers.items()),
        "_remote_addr": getattr(req, "remote_addr", None),
        "_get_json": req.get_json,
    }
    ## If type is known and passed in signature, narrow
    match byte_t:
        case _ if byte_t is JsonBytes:
            construct_args["_body"] = JsonBytes(b)
            return cast(
                SimpleHttpRequestAdaptor[FlaskRequestProto, JsonBytes],
                SimpleHttpRequestAdaptor(**construct_args),  # pyright: ignore[reportArgumentType]
            )
        case _ if byte_t is HtmlBytes:
            construct_args["_body"] = HtmlBytes(b)
            return cast(
                SimpleHttpRequestAdaptor[FlaskRequestProto, HtmlBytes],
                SimpleHttpRequestAdaptor(**construct_args),  # pyright: ignore[reportArgumentType]
            )

        case _ if byte_t is XMLBytes:
            construct_args["_body"] = XMLBytes(b)
            return cast(
                SimpleHttpRequestAdaptor[FlaskRequestProto, XMLBytes],
                SimpleHttpRequestAdaptor(**construct_args),  # pyright: ignore[reportArgumentType]
            )
        case _:  # if passed OtherBytes or None, construct from header
            construct_args["_body"] = construct_bytewrapper(req)
            return cast(
                SimpleHttpRequestAdaptor[FlaskRequestProto, _AnyBytes],
                SimpleHttpRequestAdaptor(**construct_args),  # pyright: ignore[reportArgumentType]
            )


@runtime_checkable
class HttpResponseAdaptor(Protocol, Generic[_T_ByteWrapper]):
    """Normalized view over any 3rd-party HTTP response type."""

    @property
    def status(self) -> HTTPStatus: ...
    @property
    def status_code(self) -> HTTPStatus: ...
    @property
    def headers(self) -> Mapping[str, str]: ...
    @property
    def body(self) -> _T_ByteWrapper: ...
    @property
    def raw(self) -> bytes: ...
    def get_json(self) -> Any: ...


class SimpleHttpResponseAdaptor(
    _BodyHeaders[_T_ByteWrapper], Generic[_T_Resp, _T_ByteWrapper]
):
    """A concrete, framework-agnostic response adaptor."""

    external: _T_Resp
    _status: HTTPStatus
    _headers: Mapping[str, str]
    _body: _T_ByteWrapper
    _get_json: Callable[[], Any]

    @property
    def status(self) -> HTTPStatus:
        return self._status

    @property
    def status_code(self) -> HTTPStatus:
        return self._status


_S_Resp: TypeAlias = SimpleHttpResponseAdaptor[_T_Resp, _T_ByteWrapper]


@overload
def from_werkzeug_response(
    resp: FlaskResponseProto, byte_t: type[JsonBytes]
) -> _S_Resp[FlaskResponseProto, JsonBytes]: ...
@overload
def from_werkzeug_response(
    resp: FlaskResponseProto, byte_t: type[HtmlBytes]
) -> _S_Resp[FlaskResponseProto, HtmlBytes]: ...
@overload
def from_werkzeug_response(
    resp: FlaskResponseProto, byte_t: type[XMLBytes]
) -> _S_Resp[FlaskResponseProto, XMLBytes]: ...
@overload
def from_werkzeug_response(
    resp: FlaskResponseProto, byte_t: None
) -> _S_Resp[FlaskResponseProto, _AnyBytes]: ...
def from_werkzeug_response(
    resp: FlaskResponseProto,
    byte_t: type[_T_ByteWrapper] | None = None,
) -> (
    SimpleHttpResponseAdaptor[FlaskResponseProto, JsonBytes]
    | SimpleHttpResponseAdaptor[FlaskResponseProto, HtmlBytes]
    | SimpleHttpResponseAdaptor[FlaskResponseProto, XMLBytes]
    | SimpleHttpResponseAdaptor[FlaskResponseProto, _AnyBytes]
):
    b: bytes = _extract_bytes(resp)

    def _safe_get_json() -> object | None:
        get_json = getattr(resp, "get_json", None)
        if callable(get_json):
            try:
                # Flask get_json supports 'silent' param on Request, not on Response.
                # On Response, it raises if not JSON; catch and return None.
                return get_json()
            except Exception:
                return None
        return None

    construct_args = {
        "external": resp,
        "_status": getattr(
            resp, "status_code", None
        ),  # keep int; adaptor can coerce to HTTPStatus
        "_headers": dict(getattr(resp, "headers", {}).items()),
        "_get_json": _safe_get_json,
    }

    match byte_t:
        case _ if byte_t is JsonBytes:
            construct_args["_body"] = JsonBytes(b)
            return cast(
                SimpleHttpResponseAdaptor[FlaskResponseProto, JsonBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )
        case _ if byte_t is HtmlBytes:
            construct_args["_body"] = HtmlBytes(b)
            return cast(
                SimpleHttpResponseAdaptor[FlaskResponseProto, HtmlBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )
        case _ if byte_t is XMLBytes:
            construct_args["_body"] = XMLBytes(b)
            return cast(
                SimpleHttpResponseAdaptor[FlaskResponseProto, XMLBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )
        case _:
            # If passed OtherBytes or None, delegate to your content-type based wrapper
            construct_args["_body"] = construct_bytewrapper(resp)
            return cast(
                SimpleHttpResponseAdaptor[FlaskResponseProto, _AnyBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )


_S_RespHttpx: TypeAlias = SimpleHttpResponseAdaptor[_T_Resp, _T_ByteWrapper]


@overload
def from_httpx_response(
    resp: HTTPXResponseProto, byte_t: type[JsonBytes]
) -> _S_RespHttpx[HTTPXResponseProto, JsonBytes]: ...
@overload
def from_httpx_response(
    resp: HTTPXResponseProto, byte_t: type[HtmlBytes]
) -> _S_RespHttpx[HTTPXResponseProto, HtmlBytes]: ...
@overload
def from_httpx_response(
    resp: HTTPXResponseProto, byte_t: type[XMLBytes]
) -> _S_RespHttpx[HTTPXResponseProto, XMLBytes]: ...
@overload
def from_httpx_response(
    resp: HTTPXResponseProto, byte_t: None
) -> _S_RespHttpx[HTTPXResponseProto, _AnyBytes]: ...
def from_httpx_response(
    resp: HTTPXResponseProto,
    byte_t: type[_T_ByteWrapper] | None = None,
) -> (
    SimpleHttpResponseAdaptor[HTTPXResponseProto, JsonBytes]
    | SimpleHttpResponseAdaptor[HTTPXResponseProto, HtmlBytes]
    | SimpleHttpResponseAdaptor[HTTPXResponseProto, XMLBytes]
    | SimpleHttpResponseAdaptor[HTTPXResponseProto, _AnyBytes]
):
    try:
        b: bytes = _extract_bytes(resp)
    except NameError:
        b = bytes(resp.content or b"")

    def _safe_get_json() -> Any:
        try:
            return resp.json()
        except Exception:
            return None

    construct_args = {
        "external": resp,
        "_status": resp.status_code,
        "_headers": dict(resp.headers.items()),
        "_get_json": _safe_get_json,
    }

    match byte_t:
        case _ if byte_t is JsonBytes:
            construct_args["_body"] = JsonBytes(b)  # pyright: ignore[reportArgumentType]
            return cast(
                SimpleHttpResponseAdaptor[HTTPXResponseProto, JsonBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )
        case _ if byte_t is HtmlBytes:
            construct_args["_body"] = HtmlBytes(b)  # pyright: ignore[reportArgumentType]
            return cast(
                SimpleHttpResponseAdaptor[HTTPXResponseProto, HtmlBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )
        case _ if byte_t is XMLBytes:
            construct_args["_body"] = XMLBytes(b)  # pyright: ignore[reportArgumentType]
            return cast(
                SimpleHttpResponseAdaptor[HTTPXResponseProto, XMLBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )
        case _:
            body_wrapped = construct_bytewrapper(resp)
            construct_args["_body"] = body_wrapped  # pyright: ignore[reportArgumentType]
            return cast(
                SimpleHttpResponseAdaptor[HTTPXResponseProto, _AnyBytes],
                SimpleHttpResponseAdaptor(**construct_args),
            )

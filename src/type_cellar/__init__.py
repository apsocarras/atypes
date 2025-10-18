from __future__ import annotations

from nobeartype import NoBearType

from ._types import (
    HasHeaders,
    HasHeadersAndArgs,
    HasHeadersAndRaw,
    HasHeadersBody,
    JSONScalar,
    JSONType,
    LoggerEvent,
    LoggerEventProto,
    NotImplementSentinel,
    OmittedDefaultSentinel,
    SentinelMeta,
    SequenceNotStr,
)
from .enums import (
    BaseStrEnum,
    HttpMethod,
    SerialFormatType,
    SuccessStatus,
)
from .wrappers import (
    ByteWrapperProto,
    HtmlBytes,
    JsonBytes,
    MapString,
    OtherBytes,
)

_nobeartype = NoBearType()
_OMITTED_DEFAULT = OmittedDefaultSentinel.make()
_NOT_IMPLEMENTED = NotImplementSentinel.make()

__all__ = [
    "BaseStrEnum",
    "ByteWrapperProto",
    "HasHeaders",
    "HasHeadersAndArgs",
    "HasHeadersAndRaw",
    "HasHeadersBody",
    "HtmlBytes",
    "HttpMethod",
    "JSONScalar",
    "JSONType",
    "JsonBytes",
    "LoggerEvent",
    "LoggerEventProto",
    "MapString",
    "NotImplementSentinel",
    "OmittedDefaultSentinel",
    "OtherBytes",
    "SentinelMeta",
    "SequenceNotStr",
    "SerialFormatType",
    "SuccessStatus",
]

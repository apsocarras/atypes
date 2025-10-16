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
    "JSONScalar",
    "JSONType",
    "HasHeaders",
    "HasHeadersAndRaw",
    "HasHeadersBody",
    "HasHeadersAndArgs",
    "SequenceNotStr",
    "SentinelMeta",
    "OmittedDefaultSentinel",
    "NotImplementSentinel",
    "LoggerEvent",
    "LoggerEventProto",
    "ByteWrapperProto",
    "JsonBytes",
    "HtmlBytes",
    "OtherBytes",
    "MapString",
    "BaseStrEnum",
    "SuccessStatus",
    "SerialFormatType",
    "HttpMethod",
]

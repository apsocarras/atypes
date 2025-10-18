"""
Enums are actually instantiated in code so they shouldn't be in the same file as non-instantiated types
"""

import logging
from enum import Enum, auto
from http import HTTPStatus
from typing import Any

from typing_extensions import Self, override

logger = logging.getLogger(__name__)


class BaseStrEnum(Enum):
    """
    - Override `__str__` so it converts to the str of its value
    - Override `auto()` creation to make the name the lowercase of the member identifier
    """

    # Multiclassing as str was a terrible idea
    # - Type checker fails to notice when you've assigned an enum to something that assumes a pure string.
    # - So you have to call str() on all enum "strings" to be safe anyways.

    @override
    def __str__(self) -> str:
        return str(self.value)

    @staticmethod
    @override
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> str:
        return name.lower()


class SuccessStatus(BaseStrEnum):
    """
    Using literals instead of auto() for type safety
    """

    SUCCESS = auto()
    ERROR = auto()
    UNKNOWN = auto()
    CRITICAL = auto()

    # Use to indicate errors we received upstream of us
    TIMEOUT = "error_timeout"  # WHERE ... LIKE %error*%
    UPSTREAM_4XX = "error_upstream_4XX"
    UPSTREAM_5XX = "error_upstream_5XX"
    UPSTREAM_AUTH_FAILED = "error_upstream_auth"
    HTTP_INVALID_URL = "error_upstream_invalid_url"

    # Use to indicate we've got errors to deal with
    INTERNAL_5XX = "critical_internal_5XX"
    VALIDATION_ERROR = "validation_error"  # some business logic violation

    @override
    def __str__(self) -> str:
        return self.value

    @staticmethod
    def from_http_response_status(
        status: HTTPStatus | int,
    ) -> "SuccessStatus":
        s = int(status)

        if s < 400:
            return SuccessStatus.SUCCESS

        if s == HTTPStatus.REQUEST_TIMEOUT:
            return SuccessStatus.TIMEOUT

        if s in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            return SuccessStatus.UPSTREAM_AUTH_FAILED

        if 400 <= s < 500:
            return SuccessStatus.UPSTREAM_4XX
        if 500 <= s < 600:
            return SuccessStatus.UPSTREAM_5XX

        return SuccessStatus.UNKNOWN


class SerialFormatType(BaseStrEnum):
    UNKNOWN = auto()

    # Textual
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSV = "text/csv"
    TEXT_XML = "text/xml"

    # JSON / XML
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"

    # Form data
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"

    # Binary
    OCTET_STREAM = "application/octet-stream"
    PDF = "application/pdf"
    ZIP = "application/zip"
    GZIP = "application/gzip"

    # Images
    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"

    # Audio
    MP3 = "audio/mpeg"
    OGG_AUDIO = "audio/ogg"
    WAV = "audio/wav"

    # Video
    MP4 = "video/mp4"
    WEBM = "video/webm"
    OGG_VIDEO = "video/ogg"

    # Structured data
    PROTOBUF = "application/protobuf"
    MSGPACK = "application/msgpack"
    AVRO = "application/avro"
    PARQUET = "application/parquet"

    @classmethod
    @override
    def _missing_(cls, value: object) -> Self:
        return cls.normalize(value)

    @classmethod
    def normalize(cls, content_type: object) -> Self:
        """
        Assign <SerialFormatType.UNKNOWN: 'unknown'> to any non-parseable values.

        ```pycon
        >>> incoming_format = 'application/json; charset=utf-8'
        >>> normalized = SerialFormatType.normalize(incoming_format)
        >>> str(normalized)
        'application/json'
        >>> SerialFormatType.normalize("application/json; charset=utf-8")
        <SerialFormatType.APPLICATION_JSON: 'application/json'>

        >>> SerialFormatType.normalize("*/*")
        <SerialFormatType.APPLICATION_JSON: 'application/json'>

        >>> SerialFormatType.normalize("text/html; charset=utf-8")
        <SerialFormatType.TEXT_HTML: 'text/html'>

        >>> SerialFormatType.normalize("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        <SerialFormatType.TEXT_HTML: 'text/html'>

        >>> SerialFormatType.normalize(42)
        <SerialFormatType.UNKNOWN: 'unknown'>

        ```
        """
        if not isinstance(content_type, str):
            logger.warning(
                f"{cls.__name__} must be initialized with str (given: {type(content_type)}). Assigning UNKNOWN."
            )
            return cls(cls.UNKNOWN)

        if (
            content_type.strip().lower() == "application/*"
            or content_type.strip() == "*/*"
        ):
            logger.debug(f"Wildcard media type: {content_type}. Assuming JSON.")
            return cls(cls.APPLICATION_JSON)

        ## application/json; charset=utf-8 -> application/json
        normalized_media_type = content_type.split(";", 1)[0].strip().lower()
        if normalized_media_type in cls._value2member_map_:
            return cls(normalized_media_type)

        ## 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -> text/html
        normalized_media_type = normalized_media_type.split(",", maxsplit=1)[0]
        if normalized_media_type in cls._value2member_map_:
            return cls(normalized_media_type)

        return cls(cls.UNKNOWN)


class HttpMethod(BaseStrEnum):
    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()
    PATCH = auto()
    HEAD = auto()
    OPTIONS = auto()
    UNKNOWN = auto()


if __name__ == "__main__":
    import doctest

    _ = doctest.testmod()

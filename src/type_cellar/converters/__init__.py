from __future__ import annotations

import cattrs

from .base_converter import get_converter

__all__ = ["get_converter"]


def _doc_test() -> None:
    """
    ```pycon
    >>> import attr, cattrs, datetime as dt, uuid
    >>> from enum import Enum
    >>> from types import NoneType
    >>> from wck_python_utils.types._types import UUID_Str
    >>> from wck_python_utils.types.enums import SerialFormatType, SuccessStatus
    >>> from wck_python_utils.cloud_functions.proxy.config import PubSub_LoggingSubTopicType
    >>> from wck_python_utils.models.converters import cbase

    >>> @attr.define
    ... class MessageAttrs:
    ...     message: str
    ...     payload_schema: str
    ...     serial_format: SerialFormatType
    ...     status: SuccessStatus
    ...     sub_topic: PubSub_LoggingSubTopicType
    ...     trace_id: UUID_Str
    ...     error: None | str
    ...     details: dict
    ...     when: dt.datetime
    ...

    >>> # --- A deterministic example payload -------------------------------------
    >>> fixed_uuid = uuid.UUID("11111111-1111-4111-8111-111111111111")
    >>> attrs_obj = MessageAttrs(
    ...     message="Hello",
    ...     payload_schema="V1",
    ...     serial_format=SerialFormatType.APPLICATION_JSON,
    ...     status=SuccessStatus.SUCCESS,
    ...     sub_topic=PubSub_LoggingSubTopicType.N8N_BAD_REQUESTS_SUBTOPIC,
    ...     trace_id=UUID_Str(fixed_uuid),
    ...     error=None,
    ...     details={"no_deets": None},
    ...     when=dt.datetime(2025, 1, 2, 3, 4, 5),
    ... )
    >>>
    >>> # --- Unstructure with the Pub/Sub converter (strings everywhere) ----------
    >>> dumped = cbase.unstructure(attrs_obj)
    >>> expected = {
    ...     "message": "Hello",
    ...     "payload_schema": "V1",
    ...     "serial_format": "application/json",
    ...     "status": "success",
    ...     "sub_topic": "n8n-proxy-bad-requests",
    ...     "trace_id": "11111111-1111-4111-8111-111111111111",
    ...     "error": None,
    ...     "details": {"no_deets": None},
    ...     "when": "2025-01-02T03:04:05",
    ... }
    >>> if dumped != expected:
    ...     dumped

    ```
    """


def __doctest_exceptions() -> None:
    """
    >>> cbase.unstructure(ValueError("bad"))
    "ValueError('bad')"
    >>> cbase.unstructure(Exception("x"))
    "Exception('x')"
    """


if __name__ == "__main__":
    import doctest

    _ = doctest.testmod()

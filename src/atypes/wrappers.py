from __future__ import annotations

import uuid
from _collections_abc import dict_items, dict_keys, dict_values
from collections.abc import Iterator, Mapping
from typing import Any, Literal, NewType, Protocol, TypeVar

from typing_extensions import override

from ._types import JSONType
from .enums import SerialFormatType

MicroSeconds = NewType("MicroSeconds", int)
MiliSeconds = NewType("MiliSeconds", int)


class ByteWrapperProto(Protocol):
    raw: bytes
    type: SerialFormatType


class JsonBytes:
    def __init__(self, raw: bytes) -> None:
        self.raw: bytes = raw
        self.type: Literal[SerialFormatType.APPLICATION_JSON] = (
            SerialFormatType.APPLICATION_JSON
        )


class HtmlBytes:
    def __init__(self, raw: bytes):
        self.raw: bytes = raw
        self.type: Literal[SerialFormatType.TEXT_HTML] = SerialFormatType.TEXT_HTML


class OtherBytes:
    def __init__(self, raw: bytes, serial_format: SerialFormatType):
        self.raw: bytes = raw
        self.type: SerialFormatType = serial_format


_T_K = TypeVar("_T_K", bound=str)
_T_V = TypeVar("_T_V", bound=JSONType)


class MapString(Mapping[_T_K, _T_V]):
    """Map type that converts to string.

    Purpose is to register with cattrs and always convert to a string
    in contexts where a JSON value has to be a string.
    """

    def __init__(self, data: dict[_T_K, _T_V] | None = None) -> None:
        self._data: dict[_T_K, _T_V] = dict(data or {})

    @override
    def __getitem__(self, key: _T_K) -> _T_V:
        # Convert looked-up value to string
        return self._data[key]

    @override
    def __iter__(self) -> Iterator[_T_K]:
        # Keys are always exposed as strings
        return (k for k in self._data)

    @override
    def __len__(self) -> int:
        return len(self._data)

    @override
    def __repr__(self) -> str:
        # Represent the stringified mapping
        items = ", ".join(f"{str(k)}: {str(v)}" for k, v in self._data.items())
        return f"{self.__class__.__name__}({{{items}}})"

    @override
    def items(self) -> dict_items[Any, Any]:
        return self._data.items()

    @override
    def keys(self) -> dict_keys[Any, Any]:
        return self._data.keys()

    @override
    def values(self) -> dict_values[Any, Any]:
        return self._data.values()


class JSON_MapString(MapString[str, JSONType]):
    """MapString with str keys"""

    pass


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

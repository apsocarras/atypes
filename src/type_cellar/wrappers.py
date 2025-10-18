## FIXME: can you tell pyright to allow using your own privates?
# pyright: reportPrivateUsage = false

from __future__ import annotations

import datetime as dt
import uuid
from _collections_abc import dict_items, dict_keys, dict_values
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from functools import cached_property
from typing import (
    Any,
    ClassVar,
    Literal,
    NewType,
    Protocol,
    TypeVar,
)

from typing_extensions import Sentinel, override

from ._types import (
    HasTableInfoProto,
    JSONType,
    _VersionStampErrorArgs,
)
from .enums import SerialFormatType
from .exceptions import VersionStampError

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


class XMLBytes:
    def __init__(self, raw: bytes) -> None:
        self.raw: bytes = raw
        self.type: Literal[SerialFormatType.APPLICATION_XML] = (
            SerialFormatType.APPLICATION_XML
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
    """Type wrapper to specify a uuid4() string"""

    def __init__(self, _uuid: str | uuid.UUID | None = None, /) -> None:
        if isinstance(_uuid, str):
            self._uuid = uuid.UUID(hex=_uuid)
        else:
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


class VersionStampedName(ABC):
    """Enforce consistency/convertibility between versioned and unversioned names"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._validate()
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def raw(self) -> str: ...

    @cached_property
    def stamped(self) -> str:
        return self.stamp(self.raw)

    @cached_property
    def unstamped(self) -> str:
        """(Does roundtrip on raw with self.stamped())"""
        return self.unstamp(self.stamped)

    @classmethod
    @abstractmethod
    def stamp(cls, name: str) -> str: ...

    @classmethod
    @abstractmethod
    def unstamp(cls, name: str) -> str: ...

    @abstractmethod
    def _validate(self, *args: Any, **kwargs: Any) -> None:
        error_args: _VersionStampErrorArgs = {
            "raw_name": self.raw,
            "stamped_name": "",
            "unstamped_name": "",
        }

        def _attempt_assign(stamped: bool) -> None:
            nonlocal error_args
            key = "stamped_name" if stamped else "unstamped_name"
            try:
                error_args[key] = self.stamped
            except Exception as e:
                error_args[key] = f"<error when calling self.{key.split('_')[0]}>"
                raise VersionStampError(info=error_args) from e

        def _valid_roundtrip() -> bool:
            return self.unstamped == self.raw

        _attempt_assign(True)
        _attempt_assign(False)

        if not _valid_roundtrip():
            raise VersionStampError(info=error_args)


class VersionStampedTableName(VersionStampedName, ABC):
    @property
    @abstractmethod
    def full_table_id(self) -> str: ...

    @override
    @abstractmethod
    def __str__(self) -> str:
        return self.full_table_id


_T = TypeVar("_T", bound=HasTableInfoProto)


def _utc_numeric_version_stamp(table_name: str) -> str:
    """Apply a numeric UTC timestamp (no letters)

    Handles fully-qualified names and base table_names.
    """

    def _stamp(name: str):
        return f"{name}_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    table_split = table_name.split(".")
    if len(table_split) == 1:
        return _stamp(table_split[0])
    else:
        return ".".join([*list(table_split[:-1]), _stamp(table_split[-1])])


FAILED_OP = Sentinel("FAILED_OP")


def _utc_numeric_version_cleaner(table_name: str) -> str | Sentinel:
    """Remove the numeric version timestamp.

    To avoid mangling names, requires that the version stamp is only numeric.
    """

    def _find_split_point(table_name: str) -> int | None:
        n = -1
        while abs(n) - 1 < len(table_name):
            if not table_name[n].isnumeric():
                return None
            if table_name[n] == "_":
                return n
            n -= 1
        return None

    if (idx := _find_split_point(table_name)) is None:
        return FAILED_OP

    return table_name[:idx]


class UtcVersionStampedTableName(VersionStampedTableName):
    """Stamp a name with a UTC datetime string suffix"""

    def __init__(
        self,
        table_info: HasTableInfoProto,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._table: HasTableInfoProto = table_info
        super().__init__(*args, **kwargs)

    @override
    def __str__(self) -> str:
        return super().__str__()

    @property
    @override
    def full_table_id(self) -> str:
        """Render the full base table id"""

        return self._table.full_table_id

    @property
    @override
    def raw(self) -> str:
        return self.full_table_id

    @override
    @classmethod
    def stamp(cls, name: str) -> str:
        return _utc_numeric_version_stamp(name)

    @override
    @classmethod
    def unstamp(cls, name: str) -> str:
        return str(_utc_numeric_version_cleaner(name))

    @override
    def _validate(self, *args: Any, **kwargs: Any) -> None:
        return super()._validate(*args, **kwargs)


class StagingTableName(VersionStampedTableName):
    _default_suffix: ClassVar[str] = "staging"

    def __init__(
        self,
        table_info: HasTableInfoProto,
        staging_suffix: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._table: HasTableInfoProto = table_info
        self._suffix: str = staging_suffix or self._default_suffix
        super().__init__(*args, **kwargs)

    @override
    def __str__(self) -> str:
        return super().__str__()

    @property
    @override
    def full_table_id(self) -> str:
        """Render the full base table id"""

        return self._table.full_table_id

    @property
    @override
    def raw(self) -> str:
        return self.full_table_id

    @override
    @classmethod
    def stamp(cls, name: str) -> str:
        return f"{name}_{cls._default_suffix}"

    @override
    @classmethod
    def unstamp(cls, name: str) -> str:
        return name.removesuffix(cls._default_suffix)

    @override
    def _validate(self, *args: Any, **kwargs: Any) -> None:
        return super()._validate(*args, **kwargs)

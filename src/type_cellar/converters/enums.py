from enum import Enum
from http import HTTPStatus
from typing import SupportsInt

from cattrs import Converter

from ..enums import BaseStrEnum
from ._raise_util import raise_type_error


def base_enum(value: Enum) -> str:
    return str(value.value)


def base_str_enum(value: BaseStrEnum) -> str:
    return str(value.value)


def res_http_status(
    value: str,
    _: type[HTTPStatus],
) -> HTTPStatus:
    if isinstance(value, SupportsInt):
        val_int = int(value)
        if val_int in HTTPStatus.__members__.values():
            new_value = HTTPStatus(val_int)
            return new_value
    raise_type_error(value, "type[HTTPStatus]")


def register_enum_hooks(conv: Converter) -> None:
    conv.register_structure_hook(HTTPStatus, lambda v, _: HTTPStatus(int(v)))
    conv.register_unstructure_hook(Enum, base_enum)
    conv.register_unstructure_hook(BaseStrEnum, base_str_enum)

from __future__ import annotations

import uuid

from cattrs import Converter

from type_cellar.wrappers import UUID_Str

from ._raise_util import raise_type_error


def res_uuid_str(value: UUID_Str) -> str:
    """
    >>> import uuid
    >>> from wck_python_utils.types._types import UUID_Str

    >>> u = uuid.uuid4()
    >>> s = res_uuid_str(UUID_Str(u))
    >>> if s != str(u):
    ...     print(s, str(u))

    """
    return str(value)


def make_uuid_str(value, _: type[UUID_Str]) -> UUID_Str:
    """
    >>> import uuid
    >>> from wck_python_utils.types._types import UUID_Str

    >>> u = uuid.uuid4()
    >>> if make_uuid_str(str(u), UUID_Str) != UUID_Str(u):
    ...     print(str(u), UUID_Str(u), make_uuid_str(str(u), UUID_Str))

    >>> if make_uuid_str(u, UUID_Str) != UUID_Str(u):
    ...     print(u, UUID_Str(u), make_uuid_str(u, UUID_Str))

    >>> make_uuid_str(123, UUID_Str)
    Traceback (most recent call last):
        ...
    TypeError: Cannot structure 123 into UUID_Str (type: <class 'int'>)
    """
    if isinstance(value, (str, uuid.UUID)):
        return UUID_Str(value)
    raise_type_error(value, UUID_Str)


def uuid_to_hex(value: uuid.UUID) -> str:
    """
    >>> import uuid
    >>> u = uuid.uuid4()
    >>> hex_str = uuid_to_hex(u)
    >>> isinstance(hex_str, str)
    True
    >>> hex_str == str(u)
    True
    """
    proc = UUID_Str(value)
    return str(proc)


def uuid_from_hex(value, _: type[uuid.UUID]) -> uuid.UUID:
    """
    >>> import uuid
    >>> u = uuid.uuid4()
    >>> if uuid_from_hex(str(u), uuid.UUID) != u:
    ...     print(str(u), u)
    >>> uuid_from_hex(str(u), uuid.UUID) == u
    True
    >>> uuid_from_hex(u, uuid.UUID) == u
    True
    >>> uuid_from_hex(123, uuid.UUID)
    Traceback (most recent call last):
        ...
    TypeError: Cannot structure 123 into UUID (type: <class 'int'>)
    """
    if isinstance(value, str):
        return uuid.UUID(value)
    if isinstance(value, uuid.UUID):
        return value
    raise_type_error(value, uuid.UUID)


def register_uuid_hooks(converter: Converter) -> None:
    conv = converter

    conv.register_structure_hook(uuid.UUID, uuid_from_hex)
    conv.register_unstructure_hook(uuid.UUID, uuid_to_hex)

    ## We want the uuid_str hooks to override the basic uuid, so we will place these after
    conv.register_structure_hook(UUID_Str, make_uuid_str)
    conv.register_unstructure_hook(UUID_Str, res_uuid_str)

# pyright: reportPrivateUsage=false
from __future__ import annotations

from typing import Any

from ._types import SequenceNotStr as Sequence
from ._types import SupportsStr, _VersionStampErrorArgs


class ValidationError(BaseException):
    """BaseException for violating class invariants"""

    pass


class VersionStampError(ValidationError):
    """Failure to reconstruct original name from stamped name"""

    def __init__(
        self,
        info: _VersionStampErrorArgs,
        *args: object,
        **kwargs: object,
    ) -> None:
        stamped_name = info["stamped_name"]
        raw_name = info["raw_name"]
        unstamped_name = info["unstamped_name"]

        msg = f"Failed to reconstruct name: 'raw'={raw_name}, 'stamped_name'={stamped_name}, 'unstamped'={unstamped_name}"
        super().__init__(msg, *args, **kwargs)


class HeaderAndValuesError(ValidationError):
    """Mismatches between headers and values"""

    def __init__(
        self, headers: Sequence[str], values: Sequence[str], *args: Any, **kwargs: Any
    ) -> None:
        msg = f"Length mismatch: 'headers'={len(headers)}, 'values'={len(values)}"
        super().__init__(msg, *args, **kwargs)


class TableIdentifierError(ValidationError):
    """Failed to construct a valid table name based on the inputs"""

    def __init__(self, *args: SupportsStr, **kwargs: str) -> None:
        msg = f"Failed to construct table id from: {', '.join(str(s) for s in args)}"
        super().__init__(msg, *args, **kwargs)


class MissingCompositeKeyColsError(ValidationError):
    """Can't form composite key because certain columns are missing"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        msg = f"Can't form composite key: {', '.join(f'{k}={v}' for k, v in kwargs.items())}"
        super().__init__(msg)


class HasColumnError(ValidationError):
    """Column already present in the row"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        msg = f"Already has primary key col: {', '.join(f'{k}={v}' for k, v in kwargs.items())}"
        super().__init__(msg)

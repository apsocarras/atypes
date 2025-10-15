"""
"Smoke tests" are tests that only check basic aspects of the package.
They point to something more fundamentally wrong in your setup.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Iterator

from beartype.claw import beartype_package

beartype_package("atypes")


def iter_modules() -> Iterator[pkgutil.ModuleInfo]:
    pkg = importlib.import_module("atypes")
    return pkgutil.walk_packages(pkg.__path__, pkg.__name__ + ".")


def test_import_all_package_modules():
    def import_error(name: str) -> Exception | None:
        try:
            _ = importlib.import_module(name)
            return None
        except Exception as e:
            return e

    import_errors = {
        mod.name: mod_error
        for mod in iter_modules()
        if (mod_error := import_error(mod.name)) is not None
    }

    assert not import_errors, f"Failed imports: {import_errors}"

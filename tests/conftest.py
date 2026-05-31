"""Pytest configuration.

The ``omnirun`` SDK is a private dependency that is not published to PyPI, so it
is not installable in CI or in a clean development environment. The package
imports ``Sandbox`` from it at module load time (``from omnirun import Sandbox``),
which means importing ``langchain_omnirun`` would fail without it.

Every test in this suite already replaces the sandbox with a mock (via
``unittest.mock.patch("langchain_omnirun.tools.Sandbox")``) and never touches a
real microVM. To make the package importable while keeping the tests genuine, we
register a minimal stub ``omnirun`` module in ``sys.modules`` before any test
imports the package. If the real SDK is installed, it is used instead.
"""

from __future__ import annotations

import sys
import types


def _install_omnirun_stub() -> None:
    try:
        import omnirun  # noqa: F401  (real SDK available)

        return
    except ImportError:
        pass

    stub = types.ModuleType("omnirun")

    class Sandbox:  # minimal placeholder; tests patch this symbol on the consumer
        """Stub stand-in for ``omnirun.Sandbox`` used only for import resolution."""

        @classmethod
        def create(cls, *args: object, **kwargs: object) -> Sandbox:
            raise RuntimeError(
                "omnirun.Sandbox stub invoked — tests must patch "
                "langchain_omnirun.tools.Sandbox"
            )

    stub.Sandbox = Sandbox  # type: ignore[attr-defined]
    sys.modules["omnirun"] = stub


_install_omnirun_stub()

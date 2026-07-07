"""Application resources (icons, stylesheets, compiled Qt resources).

Add ``.qrc`` files here and compile with::

    pyside6-rcc resources/vinylsplit.qrc -o resources/vinylsplit_rc.py

Import the generated module in :mod:`vinylsplit.app` to register resources
at startup.
"""

from pathlib import Path

RESOURCES_DIR = Path(__file__).parent

__all__ = ["RESOURCES_DIR"]

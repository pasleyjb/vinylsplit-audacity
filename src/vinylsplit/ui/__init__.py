"""Qt Designer UI definitions.

Place ``.ui`` files in this package and load them from wizard pages via
:class:`~vinylsplit.wizard.pages.base.WizardPageBase.load_ui`.

Example (future)::

    from pathlib import Path
    from vinylsplit.ui import UI_DIR

    class MyPage(WizardPageBase):
        def build_content(self) -> None:
            self.load_ui(str(UI_DIR / "my_page.ui"))

To compile resources, add a ``.qrc`` file under
:mod:`vinylsplit.resources` and run ``pyside6-rcc``.
"""

from pathlib import Path

UI_DIR = Path(__file__).parent

__all__ = ["UI_DIR"]

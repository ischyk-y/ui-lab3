from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from lab3qt.ui import TextEditor


def main() -> int:
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

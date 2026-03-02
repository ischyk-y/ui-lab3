from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCloseEvent,
    QFont,
    QKeySequence,
    QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTextEdit,
    QToolBar,
    QToolButton,
)


class TextEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._text_edit = QTextEdit()
        self.setCentralWidget(self._text_edit)
        self.resize(900, 650)

        self._current_file: Path | None = None
        self._highlight_color = QColor("#fff59d")
        self._emoji_choices = ["😀", "😂", "😍", "👍", "🔥", "💡", "✨"]

        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._text_edit.document().modificationChanged.connect(
            lambda _: self._update_window_title()
        )
        self._text_edit.cursorPositionChanged.connect(self._sync_format_actions)

        self.statusBar().showMessage("Ready")
        self._update_window_title()
        self._sync_format_actions()

    def _create_actions(self) -> None:
        # тримаю всі гарячі клавіші в одному місці, так легше щось змінювати
        self._new_action = QAction("&New", self)
        self._new_action.setShortcut(QKeySequence.StandardKey.New)
        self._new_action.triggered.connect(self.new_file)

        self._open_action = QAction("&Open...", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self.open_file)

        self._save_action = QAction("&Save", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.triggered.connect(self.save_file)

        self._save_as_action = QAction("Save &As...", self)
        self._save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._save_as_action.triggered.connect(self.save_file_as)

        self._exit_action = QAction("E&xit", self)
        self._exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self._exit_action.triggered.connect(self.close)

        self._bold_action = QAction("&Bold", self)
        self._bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self._bold_action.setCheckable(True)
        self._bold_action.triggered.connect(self.toggle_bold)

        self._italic_action = QAction("&Italic", self)
        self._italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self._italic_action.setCheckable(True)
        self._italic_action.triggered.connect(self.toggle_italic)

        self._underline_action = QAction("&Underline", self)
        self._underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self._underline_action.setCheckable(True)
        self._underline_action.triggered.connect(self.toggle_underline)

        self._highlight_action = QAction("Highlight", self)
        self._highlight_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self._highlight_action.setCheckable(True)
        self._highlight_action.triggered.connect(self.toggle_highlight)

        self._insert_link_action = QAction("Insert &Link...", self)
        self._insert_link_action.setShortcut(QKeySequence("Ctrl+K"))
        self._insert_link_action.triggered.connect(self.insert_link)

        self._emoji_menu = QMenu("Insert Emoji", self)
        for emoji in self._emoji_choices:
            emoji_action = self._emoji_menu.addAction(emoji)
            emoji_action.triggered.connect(lambda _, e=emoji: self._insert_emoji(e))

    def _create_menus(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self._new_action)
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self._exit_action)

        format_menu = menu_bar.addMenu("&Format")
        format_menu.addAction(self._bold_action)
        format_menu.addAction(self._italic_action)
        format_menu.addAction(self._underline_action)
        format_menu.addAction(self._highlight_action)
        format_menu.addSeparator()
        format_menu.addAction(self._insert_link_action)
        format_menu.addMenu(self._emoji_menu)

    def _create_toolbars(self) -> None:
        self._file_toolbar = QToolBar("File", self)
        self._file_toolbar.setMovable(False)
        self._file_toolbar.addAction(self._new_action)
        self._file_toolbar.addAction(self._open_action)
        self._file_toolbar.addAction(self._save_action)
        self._file_toolbar.addAction(self._save_as_action)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._file_toolbar)

        self._format_toolbar = QToolBar("Format", self)
        self._format_toolbar.setMovable(False)
        self._format_toolbar.addAction(self._bold_action)
        self._format_toolbar.addAction(self._italic_action)
        self._format_toolbar.addAction(self._underline_action)
        self._format_toolbar.addAction(self._highlight_action)
        self._format_toolbar.addAction(self._insert_link_action)

        emoji_button = QToolButton(self)
        emoji_button.setText("Emoji")
        emoji_button.setToolTip("Insert emoji")
        emoji_button.setMenu(self._emoji_menu)
        emoji_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._format_toolbar.addWidget(emoji_button)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._format_toolbar)

    def new_file(self) -> None:
        if not self._maybe_save():
            return

        self._text_edit.clear()
        self._current_file = None
        self._text_edit.document().setModified(False)
        self.statusBar().showMessage("New document", 2000)
        self._update_window_title()

    def open_file(self) -> None:
        if not self._maybe_save():
            return

        start_dir = str(self._current_file.parent) if self._current_file else ""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            start_dir,
            "Text Files (*.txt);;All Files (*)",
        )

        if file_name:
            self._load_from_file(Path(file_name))

    def save_file(self) -> bool:
        if self._current_file is None:
            return self.save_file_as()
        return self._save_to_file(self._current_file)

    def save_file_as(self) -> bool:
        suggested = self._current_file or Path.home() / "document.txt"
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            str(suggested),
            "Text Files (*.txt);;All Files (*)",
        )

        if not file_name:
            return False

        return self._save_to_file(Path(file_name))

    def toggle_bold(self, checked: bool) -> None:
        weight = QFont.Weight.Bold if checked else QFont.Weight.Normal
        self._apply_char_format(font_weight=weight)

    def toggle_italic(self, checked: bool) -> None:
        self._apply_char_format(italic=checked)

    def toggle_underline(self, checked: bool) -> None:
        self._apply_char_format(underline=checked)

    def toggle_highlight(self, checked: bool) -> None:
        color: QColor | Qt.GlobalColor = self._highlight_color if checked else Qt.GlobalColor.transparent
        self._apply_char_format(background=color)

    def insert_link(self) -> None:
        cursor = self._text_edit.textCursor()
        selected_text = cursor.selectedText()

        text, text_ok = QInputDialog.getText(
            self,
            "Link Text",
            "Display text:",
            text=selected_text,
        )
        if not text_ok or not text:
            return

        url, url_ok = QInputDialog.getText(self, "Link URL", "URL:")
        if not url_ok or not url:
            return

        cursor.insertHtml(f'<a href="{url}">{text}</a>')

    def _apply_char_format(
        self,
        *,
        font_weight: QFont.Weight | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        background: QColor | Qt.GlobalColor | None = None,
    ) -> None:
        fmt = QTextCharFormat()
        if font_weight is not None:
            fmt.setFontWeight(font_weight)
        if italic is not None:
            fmt.setFontItalic(italic)
        if underline is not None:
            fmt.setFontUnderline(underline)
        if background is not None:
            fmt.setBackground(background)
        self._merge_format_on_selection(fmt)

    def _merge_format_on_selection(self, char_format: QTextCharFormat) -> None:
        cursor = self._text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(char_format)
        self._text_edit.mergeCurrentCharFormat(char_format)

    def _maybe_save(self) -> bool:
        if not self._text_edit.document().isModified():
            return True

        # не хочу втрачати конспект, тому пінгую користувача перед закриттям
        ret = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "The document has been modified. Do you want to save your changes?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

        if ret == QMessageBox.StandardButton.Save:
            return self.save_file()
        if ret == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def _save_to_file(self, file_path: Path) -> bool:
        try:
            file_path.write_text(self._text_edit.toHtml(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"Cannot write file {file_path.name}:\n{exc}",
            )
            return False

        self._current_file = file_path
        self._text_edit.document().setModified(False)
        self.statusBar().showMessage("File saved", 2000)
        self._update_window_title()
        return True

    def _load_from_file(self, file_path: Path) -> None:
        try:
            data = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"Cannot read file {file_path.name}:\n{exc}",
            )
            return

        if "<" in data and ">" in data:
            self._text_edit.setHtml(data)
        else:
            self._text_edit.setPlainText(data)

        self._current_file = file_path
        self._text_edit.document().setModified(False)
        self.statusBar().showMessage("File loaded", 2000)
        self._update_window_title()

    def _insert_emoji(self, emoji: str) -> None:
        self._text_edit.insertPlainText(emoji)

    def _sync_format_actions(self) -> None:
        fmt = self._text_edit.currentCharFormat()
        bold_on = fmt.fontWeight() >= QFont.Weight.Bold
        italic_on = fmt.fontItalic()
        underline_on = fmt.fontUnderline()
        brush = fmt.background()
        color = brush.color() if brush.style() != Qt.BrushStyle.NoBrush else QColor(Qt.GlobalColor.transparent)
        highlight_on = color.isValid() and color == self._highlight_color

        for action, state in (
            (self._bold_action, bold_on),
            (self._italic_action, italic_on),
            (self._underline_action, underline_on),
            (self._highlight_action, highlight_on),
        ):
            action.blockSignals(True)
            action.setChecked(state)
            action.blockSignals(False)

    def _update_window_title(self) -> None:
        shown_name = self._current_file.name if self._current_file else "Untitled"
        if self._text_edit.document().isModified():
            shown_name += "*"
        self.setWindowTitle(f"{shown_name} - Text Editor")

    def closeEvent(self, event: QCloseEvent) -> None:  
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Qt Text Editor")
    window = TextEditor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

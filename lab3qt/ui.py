from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QKeySequence,
    QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTextEdit,
    QToolBar,
    QToolButton,
)

from lab3qt.io import default_document_path, read_text, write_text


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
        self._load_default_document()

    def _load_default_document(self) -> None:
        default_path = default_document_path()
        if default_path.exists():
            self._load_from_file(default_path)
        else:
            self._update_window_title()

    def _create_actions(self) -> None:
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
        file_toolbar = QToolBar("File", self)
        file_toolbar.setMovable(False)
        file_toolbar.addAction(self._new_action)
        file_toolbar.addAction(self._open_action)
        file_toolbar.addAction(self._save_action)
        file_toolbar.addAction(self._save_as_action)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, file_toolbar)

        format_toolbar = QToolBar("Format", self)
        format_toolbar.setMovable(False)
        format_toolbar.addAction(self._bold_action)
        format_toolbar.addAction(self._italic_action)
        format_toolbar.addAction(self._underline_action)
        format_toolbar.addAction(self._highlight_action)
        format_toolbar.addAction(self._insert_link_action)

        emoji_button = QToolButton(self)
        emoji_button.setText("Emoji")
        emoji_button.setToolTip("Insert emoji")
        emoji_button.setMenu(self._emoji_menu)
        emoji_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        format_toolbar.addWidget(emoji_button)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, format_toolbar)

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

        start_dir = self._current_file.parent if self._current_file else Path.home()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(start_dir),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_name:
            self._load_from_file(Path(file_name))

    def save_file(self) -> bool:
        if self._current_file is None:
            return self.save_file_as()
        return self._save_to_file(self._current_file)

    def save_file_as(self) -> bool:
        suggested = self._current_file or default_document_path()
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
        background = self._highlight_color if checked else QColor(Qt.GlobalColor.transparent)
        self._apply_char_format(background=background)

    def insert_link(self) -> None:
        url, okay = QInputDialog.getText(self, "Insert Link", "URL")
        if not okay or not url:
            return

        cursor = self._text_edit.textCursor()
        text = cursor.selectedText() or url
        cursor.insertHtml(f'<a href="{url}">{text}</a>')

    def _insert_emoji(self, emoji: str) -> None:
        self._text_edit.insertPlainText(emoji)

    def _maybe_save(self) -> bool:
        if not self._text_edit.document().isModified():
            return True

        response = QMessageBox.question(
            self,
            "Save document?",
            "Зберегти зміни перед тим як продовжити?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
        )

        if response == QMessageBox.StandardButton.Save:
            return self.save_file()
        if response == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _save_to_file(self, path: Path) -> bool:
        try:
            write_text(path, self._text_edit.toPlainText())
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Не вдалося зберегти файл: {exc}")
            return False

        self._current_file = path
        self._text_edit.document().setModified(False)
        self.statusBar().showMessage("File saved", 2000)
        self._update_window_title()
        return True

    def _load_from_file(self, path: Path) -> None:
        try:
            content = read_text(path)
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Не вдалося відкрити файл: {exc}")
            return

        self._text_edit.setPlainText(content)
        self._current_file = path
        self._text_edit.document().setModified(False)
        self.statusBar().showMessage(f"Opened {path.name}", 2000)
        self._update_window_title()

    def _apply_char_format(
        self,
        font_weight: QFont.Weight | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        background: QColor | None = None,
    ) -> None:
        cursor = self._text_edit.textCursor()
        format = QTextCharFormat()
        if font_weight is not None:
            format.setFontWeight(font_weight)
        if italic is not None:
            format.setFontItalic(italic)
        if underline is not None:
            format.setFontUnderline(underline)
        if background is not None:
            format.setBackground(background)

        cursor.mergeCharFormat(format)
        self._text_edit.mergeCurrentCharFormat(format)
        self._sync_format_actions()

    def _sync_format_actions(self) -> None:
        cursor = self._text_edit.textCursor()
        format = cursor.charFormat()
        self._bold_action.setChecked(format.fontWeight() == QFont.Weight.Bold)
        self._italic_action.setChecked(format.fontItalic())
        self._underline_action.setChecked(format.fontUnderline())
        self._highlight_action.setChecked(format.background().color() == self._highlight_color)

    def _update_window_title(self) -> None:
        title = self._current_file.name if self._current_file else "Нове повідомлення"
        if self._text_edit.document().isModified():
            title += "*"
        self.setWindowTitle(f"Текстовий редактор — {title}")


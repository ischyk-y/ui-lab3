from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DOCUMENT = DATA_DIR / "document.txt"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def default_document_path() -> Path:
    ensure_data_dir()
    return DEFAULT_DOCUMENT


def read_text(path: Path | None = None) -> str:
    source = (Path(path) if path else default_document_path())
    if not source.exists():
        return ""
    return source.read_text(encoding="utf-8")


def write_text(path: Path | None, content: str) -> None:
    target = Path(path if path else default_document_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

"""Predefined file-type groups for UI filtering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileTypeOption:
    """A toggleable file category shown in the GUI."""

    key: str
    label: str
    extensions: frozenset[str]
    subdir: str  # destination folder name under the user-chosen output root


FILE_TYPE_OPTIONS: tuple[FileTypeOption, ...] = (
    FileTypeOption("pdf", "PDF", frozenset({"pdf"}), "PDF"),
    FileTypeOption("word", "Word", frozenset({"doc", "docx"}), "Word"),
    FileTypeOption("excel", "Excel", frozenset({"xls", "xlsx", "csv"}), "Excel"),
    FileTypeOption("text", "Text / Markdown", frozenset({"txt", "md", "rtf"}), "Text"),
    FileTypeOption(
        "images",
        "Images",
        frozenset({"jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"}),
        "Images",
    ),
    FileTypeOption(
        "video", "Video", frozenset({"mp4", "mkv", "avi", "mov", "wmv", "webm"}), "Video"
    ),
    FileTypeOption(
        "audio", "Audio", frozenset({"mp3", "wav", "flac", "aac", "ogg", "m4a"}), "Audio"
    ),
    FileTypeOption(
        "archives",
        "Archives",
        frozenset({"zip", "rar", "7z", "tar", "gz", "bz2"}),
        "Archives",
    ),
    FileTypeOption(
        "code",
        "Code",
        frozenset({"py", "js", "ts", "html", "css", "json", "java", "cpp", "c"}),
        "Code",
    ),
    FileTypeOption("presentations", "Presentations", frozenset({"ppt", "pptx"}), "Presentations"),
    FileTypeOption("no_extension", "No extension", frozenset({""}), "Other"),
)


def extensions_for_keys(enabled_keys: set[str]) -> frozenset[str]:
    """Return the union of extensions for the given option keys."""
    out: set[str] = set()
    for opt in FILE_TYPE_OPTIONS:
        if opt.key in enabled_keys:
            out.update(opt.extensions)
    return frozenset(out)


def file_matches_extensions(file_extension: str, allowed: frozenset[str]) -> bool:
    """True if the file's extension (lowercase, no dot) is in the allowed set."""
    return file_extension in allowed

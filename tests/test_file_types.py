"""Tests for file-type filter helpers."""

from __future__ import annotations

from organizer.file_types import extensions_for_keys, file_matches_extensions


def test_extensions_for_keys_unions() -> None:
    allowed = extensions_for_keys({"pdf", "images"})
    assert "pdf" in allowed
    assert "jpg" in allowed
    assert "png" in allowed
    assert "mp3" not in allowed


def test_file_matches_extensions() -> None:
    allowed = extensions_for_keys({"pdf"})
    assert file_matches_extensions("pdf", allowed)
    assert not file_matches_extensions("txt", allowed)


def test_no_extension_option() -> None:
    allowed = extensions_for_keys({"no_extension"})
    assert file_matches_extensions("", allowed)
    assert not file_matches_extensions("pdf", allowed)

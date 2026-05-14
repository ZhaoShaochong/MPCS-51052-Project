"""Watchdog-based watcher pushing paths into an asyncio queue."""

from __future__ import annotations

import asyncio
import contextlib
import os
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _EnqueueHandler(FileSystemEventHandler):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        queue: asyncio.Queue[Path],
    ) -> None:
        self._loop = loop
        self._queue = queue

    def _enqueue(self, path: str | bytes) -> None:
        p = Path(os.fsdecode(path))
        with contextlib.suppress(RuntimeError):
            self._loop.call_soon_threadsafe(self._queue.put_nowait, p)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._enqueue(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        dest = getattr(event, "dest_path", None)
        if dest:
            self._enqueue(dest)
        else:
            self._enqueue(event.src_path)


class FileWatcher:
    """Runs a watchdog Observer in a background thread."""

    def __init__(self, root: Path, queue: asyncio.Queue[Path]) -> None:
        self._root = root.resolve()
        self._queue = queue
        self._observer: Any = None

    def start(self) -> None:
        loop = asyncio.get_running_loop()
        handler = _EnqueueHandler(loop, self._queue)
        obs = Observer()
        obs.schedule(handler, str(self._root), recursive=False)
        obs.start()
        self._observer = obs

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

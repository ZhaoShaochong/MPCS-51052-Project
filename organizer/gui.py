"""Tkinter GUI: pick folders, toggle file types, and organize without CLI rules."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from organizer.file_types import FILE_TYPE_OPTIONS, extensions_for_keys
from organizer.models import FileEvent, Rule
from organizer.rule_engine import RuleEngine
from organizer.scan import scan_directory
from organizer.ui_rules import build_rules_for_types


class OrganizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Smart File Organizer")
        self.root.minsize(520, 600)
        self._type_vars: dict[str, tk.BooleanVar] = {}

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        padx, pady = 10, 6
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        source_frame = ttk.LabelFrame(main, text="Folder to organize", padding=8)
        source_frame.pack(fill=tk.X, padx=padx, pady=pady)
        self._path_row(source_frame, self.source_var, self._browse_source)

        dest_frame = ttk.LabelFrame(main, text="Output folder", padding=8)
        dest_frame.pack(fill=tk.X, padx=padx, pady=pady)
        self._path_row(dest_frame, self.dest_var, self._browse_dest)
        ttk.Label(
            dest_frame,
            text="Each enabled type is moved into a subfolder (e.g. PDF/, Images/).",
            wraplength=480,
        ).pack(anchor=tk.W, pady=(4, 0))

        types_frame = ttk.LabelFrame(main, text="File types to organize", padding=8)
        types_frame.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)

        toggles = ttk.Frame(types_frame)
        toggles.pack(fill=tk.BOTH, expand=True)
        for i, opt in enumerate(FILE_TYPE_OPTIONS):
            var = tk.BooleanVar(value=False)
            self._type_vars[opt.key] = var
            row, col = divmod(i, 2)
            ttk.Checkbutton(toggles, text=opt.label, variable=var).grid(
                row=row, column=col, sticky=tk.W, padx=8, pady=4
            )

        btn_row = ttk.Frame(types_frame)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="Select all", command=self._select_all_types).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Clear all", command=self._clear_all_types).pack(side=tk.LEFT)

        opts = ttk.Frame(main)
        opts.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Checkbutton(opts, text="Dry run (do not move files)", variable=self.dry_run_var).pack(
            anchor=tk.W
        )

        action_row = ttk.Frame(main)
        action_row.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Button(action_row, text="Organize", command=self._run_scan).pack(side=tk.LEFT)
        ttk.Button(action_row, text="Clear log", command=self._clear_log).pack(side=tk.LEFT, padx=8)

        log_frame = ttk.LabelFrame(main, text="Log", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)
        self.log = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _path_row(
        self, parent: tk.Misc, var: tk.StringVar, browse_cmd: Callable[[], None]
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row, text="Browse...", command=browse_cmd).pack(side=tk.RIGHT)

    def _browse_source(self) -> None:
        chosen = filedialog.askdirectory(title="Select folder to organize")
        if chosen:
            self.source_var.set(chosen)

    def _browse_dest(self) -> None:
        chosen = filedialog.askdirectory(title="Select output folder")
        if chosen:
            self.dest_var.set(chosen)

    def _selected_type_keys(self) -> set[str]:
        return {key for key, var in self._type_vars.items() if var.get()}

    def _select_all_types(self) -> None:
        for var in self._type_vars.values():
            var.set(True)

    def _clear_all_types(self) -> None:
        for var in self._type_vars.values():
            var.set(False)

    def _append_log(self, line: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def _resolve_output_root(self, source: Path) -> Path | None:
        raw = self.dest_var.get().strip()
        if raw:
            dest = Path(raw)
            if not dest.is_dir():
                try:
                    dest.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    messagebox.showerror("Invalid output folder", str(exc))
                    return None
            return dest
        return source / "Organized"

    def _run_scan(self) -> None:
        raw_source = self.source_var.get().strip()
        if not raw_source:
            messagebox.showwarning("Missing folder", "Select the folder to organize.")
            return
        source = Path(raw_source)
        if not source.is_dir():
            messagebox.showerror("Invalid folder", f"Not a valid folder:\n{source}")
            return

        enabled = self._selected_type_keys()
        if not enabled:
            messagebox.showwarning(
                "No file types selected",
                "Enable at least one file type.",
            )
            return

        output_root = self._resolve_output_root(source)
        if output_root is None:
            return

        rules = build_rules_for_types(enabled, output_root)
        allowed = extensions_for_keys(enabled)
        dry_run = self.dry_run_var.get()
        engine = RuleEngine()

        self._append_log(f"Source: {source}")
        self._append_log(f"Output: {output_root}")
        self._append_log(f"Types: {', '.join(sorted(enabled))}")
        for rule in rules:
            self._append_log(f"  {rule.raw_text}")
        if dry_run:
            self._append_log("(dry run)")

        def on_skip(child: Path, exc: OSError) -> None:
            self._append_log(f"Skip {child.name}: {exc}")

        def on_result(fe: FileEvent, rule: Rule, new_path: Path | None) -> None:
            if dry_run:
                self._append_log(f"[dry run] {fe.name} -> {rule.action_target}")
            elif rule.action_kind.value == "move" and new_path is not None:
                self._append_log(f"Moved: {fe.name} -> {new_path}")
            else:
                self._append_log(f"Applied: {fe.name}")

        hits = scan_directory(
            source,
            rules,
            engine,
            allowed_extensions=allowed,
            dry_run=dry_run,
            on_skip=on_skip,
            on_result=on_result,
        )
        self._append_log(f"Done. Organized {hits} file(s).")


def run_gui() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    OrganizerApp(root)
    root.mainloop()

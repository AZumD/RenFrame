#!/usr/bin/env python3
"""Ren'Py ARM Converter — desktop GUI (Windows + Linux aarch64)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox
from urllib.parse import unquote, urlparse

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from renpy_arm.convert import FRAME_INSTRUCTIONS, ConvertError, convert_game

try:
    import customtkinter as ctk
except ImportError as e:
    raise SystemExit(
        "Missing dependency: customtkinter\n  pip install -r requirements.txt"
    ) from e

_HAS_DND = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _HAS_DND = True
except ImportError:
    TkinterDnD = None  # type: ignore

APP_NAME = "RenFrame"
APP_TAG = "PC Ren'Py → Steam Frame (Linux ARM64)"

C_BG = "#07111f"
C_PANEL = "#12233a"
C_PANEL_2 = "#1a3050"
C_BORDER = "#2a4a6a"
C_TEXT = "#f0e6d8"
C_MUTED = "#9eb0c4"
C_ACCENT = "#ff7a45"
C_ACCENT_HOVER = "#ff9466"
C_TEAL = "#3db8a8"
C_OK = "#5ecf8e"
C_ERR = "#ff6b7a"
C_GLOW = "#16304a"

ASSETS = Path(__file__).resolve().parent / "assets" / "fonts"


def _register_font_file(path: Path) -> None:
    if not path.is_file():
        return
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)  # FR_PRIVATE
        except Exception:
            pass


def _load_fonts() -> tuple[str, str]:
    display = body = "Segoe UI"
    mapping = (("Syne-Bold.ttf", "display", "Syne"), ("DMSans-Regular.ttf", "body", "DM Sans"))
    for name, slot, hint in mapping:
        path = ASSETS / name
        if not path.is_file():
            continue
        _register_font_file(path)
        try:
            fam = tkfont.Font(file=str(path)).actual("family") or hint
            if slot == "display":
                display = fam
            else:
                body = fam
        except Exception:
            if slot == "display":
                display = hint
            else:
                body = hint
    if sys.platform.startswith("linux") and display in {"Segoe UI", "Syne"}:
        for fam in ("Noto Sans", "DejaVu Sans"):
            try:
                tkfont.Font(family=fam, size=12)
                if display in {"Segoe UI", "Syne"}:
                    display = fam
                if body in {"Segoe UI", "DM Sans"}:
                    body = fam
                break
            except Exception:
                continue
    return display, body


def _make_root():
    ctk.set_appearance_mode("dark")
    if _HAS_DND:

        class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self.TkdndVersion = TkinterDnD._require(self)

        root = CTkDnD()
    else:
        root = ctk.CTk()
    root.title(APP_NAME)
    root.geometry("960x780")
    root.minsize(820, 660)
    root.configure(fg_color=C_BG)
    return root


def _open_path(path: Path) -> None:
    path = path.resolve()
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:
        pass


class ConverterApp:
    def __init__(self) -> None:
        self.root = _make_root()
        self.display_font, self.body_font = _load_fonts()
        self.source: Path | None = None
        self.last_zip: Path | None = None
        self.output_dir = Path.home() / "Desktop"
        if not self.output_dir.is_dir():
            self.output_dir = Path.home()
        self._busy = False
        self._dnd_ready = False
        self._build()

    def _build(self) -> None:
        accent = ctk.CTkFrame(self.root, fg_color=C_ACCENT, height=4, corner_radius=0)
        accent.pack(fill="x", side="top")

        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(18, 4))
        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=ctk.CTkFont(family=self.display_font, size=34, weight="bold"),
            text_color=C_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=f"{APP_TAG}  ·  drop a Ren'Py game, get a Frame-ready zip",
            font=ctk.CTkFont(family=self.body_font, size=14),
            text_color=C_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        steps = ctk.CTkFrame(self.root, fg_color=C_GLOW, corner_radius=12)
        steps.pack(fill="x", padx=28, pady=(12, 4))
        ctk.CTkLabel(
            steps,
            text="1  Drop game    →    2  Convert    →    3  Copy zip to Frame    →    4  ./add-to-steam.sh",
            font=ctk.CTkFont(family=self.body_font, size=13),
            text_color=C_TEAL,
        ).pack(padx=16, pady=10)

        self.drop = ctk.CTkFrame(
            self.root,
            fg_color=C_PANEL,
            border_width=2,
            border_color=C_BORDER,
            corner_radius=16,
            height=148,
        )
        self.drop.pack(fill="x", padx=28, pady=12)
        self.drop.pack_propagate(False)

        self.drop_label = ctk.CTkLabel(
            self.drop,
            text="Drop a Ren'Py game folder or .zip here",
            font=ctk.CTkFont(family=self.display_font, size=20, weight="bold"),
            text_color=C_TEXT,
        )
        self.drop_label.pack(expand=True, pady=(26, 2))
        self.path_label = ctk.CTkLabel(
            self.drop,
            text="or Browse — Windows / Linux PC build or archive",
            font=ctk.CTkFont(family=self.body_font, size=13),
            text_color=C_MUTED,
        )
        self.path_label.pack(pady=(0, 18))

        if _HAS_DND:
            self._dnd_ready = self._bind_drop_targets()

        actions = ctk.CTkFrame(self.root, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=4)

        ctk.CTkButton(
            actions,
            text="Browse…",
            width=120,
            height=42,
            corner_radius=10,
            fg_color=C_PANEL_2,
            hover_color=C_BORDER,
            text_color=C_TEXT,
            font=ctk.CTkFont(family=self.body_font, size=14),
            command=self._browse,
        ).pack(side="left", padx=(0, 10))

        self.convert_btn = ctk.CTkButton(
            actions,
            text="Convert",
            width=168,
            height=42,
            corner_radius=10,
            fg_color=C_ACCENT,
            hover_color=C_ACCENT_HOVER,
            text_color="#1a0f0a",
            font=ctk.CTkFont(family=self.body_font, size=15, weight="bold"),
            command=self._start_convert,
        )
        self.convert_btn.pack(side="left")

        ctk.CTkButton(
            actions,
            text="Open zip folder",
            width=140,
            height=42,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=C_BORDER,
            hover_color=C_PANEL,
            text_color=C_MUTED,
            font=ctk.CTkFont(family=self.body_font, size=13),
            command=self._open_output,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text="Output folder…",
            width=130,
            height=42,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=C_BORDER,
            hover_color=C_PANEL,
            text_color=C_MUTED,
            font=ctk.CTkFont(family=self.body_font, size=13),
            command=self._pick_output,
        ).pack(side="right")

        self.out_label = ctk.CTkLabel(
            self.root,
            text=f"Zip saves to: {self.output_dir}",
            font=ctk.CTkFont(family=self.body_font, size=12),
            text_color=C_MUTED,
        )
        self.out_label.pack(anchor="e", padx=28)

        progress_card = ctk.CTkFrame(self.root, fg_color=C_PANEL, corner_radius=12)
        progress_card.pack(fill="x", padx=28, pady=(10, 0))

        progress_head = ctk.CTkFrame(progress_card, fg_color="transparent")
        progress_head.pack(fill="x", padx=14, pady=(10, 2))
        self.progress_title = ctk.CTkLabel(
            progress_head,
            text="Ready",
            font=ctk.CTkFont(family=self.body_font, size=12, weight="bold"),
            text_color=C_TEXT,
        )
        self.progress_title.pack(side="left")
        self.progress_detail = ctk.CTkLabel(
            progress_head,
            text="0%",
            font=ctk.CTkFont(family=self.body_font, size=11),
            text_color=C_MUTED,
        )
        self.progress_detail.pack(side="right")

        self.overall_progress = ctk.CTkProgressBar(
            progress_card,
            height=10,
            corner_radius=5,
            fg_color=C_BG,
            progress_color=C_ACCENT,
        )
        self.overall_progress.pack(fill="x", padx=14, pady=(2, 6))
        self.overall_progress.set(0)

        self.stage_progress = ctk.CTkProgressBar(
            progress_card,
            height=5,
            corner_radius=3,
            fg_color=C_BG,
            progress_color=C_TEAL,
        )
        self.stage_progress.pack(fill="x", padx=14, pady=(0, 10))
        self.stage_progress.set(0)

        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=12)

        left = ctk.CTkFrame(body, fg_color=C_PANEL, corner_radius=14)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(
            left,
            text="Progress",
            font=ctk.CTkFont(family=self.body_font, size=13, weight="bold"),
            text_color=C_TEAL,
        ).pack(anchor="w", padx=16, pady=(14, 4))
        self.log_box = ctk.CTkTextbox(
            left,
            font=ctk.CTkFont(family=self.body_font, size=13),
            fg_color=C_BG,
            text_color=C_TEXT,
            corner_radius=10,
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        right = ctk.CTkFrame(body, fg_color=C_PANEL, corner_radius=14, width=340)
        right.pack(side="right", fill="both", padx=(10, 0))
        right.pack_propagate(False)

        right_head = ctk.CTkFrame(right, fg_color="transparent")
        right_head.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(
            right_head,
            text="On the Frame later",
            font=ctk.CTkFont(family=self.body_font, size=13, weight="bold"),
            text_color=C_ACCENT,
        ).pack(side="left")
        ctk.CTkButton(
            right_head,
            text="Copy",
            width=64,
            height=28,
            corner_radius=8,
            fg_color=C_PANEL_2,
            hover_color=C_BORDER,
            text_color=C_TEXT,
            font=ctk.CTkFont(family=self.body_font, size=12),
            command=self._copy_instructions,
        ).pack(side="right")

        tip = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(family=self.body_font, size=12),
            fg_color=C_BG,
            text_color=C_MUTED,
            corner_radius=10,
            wrap="word",
        )
        tip.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tip.insert("1.0", FRAME_INSTRUCTIONS)
        tip.configure(state="disabled")

        self.status = ctk.CTkLabel(
            self.root,
            text="Ready" + ("" if self._dnd_ready else "  ·  drag-drop unavailable; Browse still works"),
            font=ctk.CTkFont(family=self.body_font, size=12),
            text_color=C_MUTED,
        )
        self.status.pack(anchor="w", padx=28, pady=(0, 16))

    def _append_log(self, msg: str) -> None:
        self.root.after(0, lambda: (self.log_box.insert("end", msg + "\n"), self.log_box.see("end")))

    def _set_status(self, msg: str, color: str = C_MUTED) -> None:
        self.root.after(0, lambda: self.status.configure(text=msg, text_color=color))

    @staticmethod
    def _human_bytes(value: int) -> str:
        size = float(max(0, value))
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024.0 or unit == "TB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _set_progress(
        self,
        stage: str,
        overall: float,
        current: float | None = None,
        detail: str | None = None,
    ) -> None:
        overall = max(0.0, min(1.0, overall))

        def apply() -> None:
            self.progress_title.configure(text=stage)
            detail_text = detail or ""
            percent = f"{round(overall * 100):d}%"
            self.progress_detail.configure(
                text=f"{detail_text}  ·  {percent}" if detail_text else percent
            )
            self.overall_progress.set(overall)
            try:
                self.stage_progress.stop()
            except Exception:
                pass
            if current is None:
                self.stage_progress.configure(mode="indeterminate")
                self.stage_progress.start()
            else:
                self.stage_progress.configure(mode="determinate")
                self.stage_progress.set(max(0.0, min(1.0, current)))

        self.root.after(0, apply)

    def _reset_progress(self) -> None:
        def apply() -> None:
            try:
                self.stage_progress.stop()
            except Exception:
                pass
            self.stage_progress.configure(mode="determinate")
            self.stage_progress.set(0)
            self.overall_progress.set(0)
            self.progress_title.configure(text="Ready")
            self.progress_detail.configure(text="0%")

        self.root.after(0, apply)

    def _conversion_progress(
        self,
        stage: str,
        fraction: float | None,
        detail: str | None,
    ) -> None:
        ranges = {
            "Inspecting game": (0.18, 0.22),
            "Applying compatibility profile": (0.22, 0.36),
            "Detecting Ren'Py version": (0.36, 0.40),
            "Downloading runtime": (0.40, 0.56),
            "Verifying runtime": (0.56, 0.60),
            "Extracting ARM64 runtime": (0.60, 0.68),
            "Patching launchers": (0.68, 0.73),
            "Creating output zip": (0.73, 0.99),
            "Done": (1.0, 1.0),
        }
        start, end = ranges.get(stage, (0.18, 0.99))
        if fraction is None:
            overall = start
        else:
            overall = start + ((end - start) * max(0.0, min(1.0, fraction)))
        self._set_progress(stage, overall, fraction, detail)

    def _set_source(self, path: Path) -> None:
        self.source = path
        self.path_label.configure(text=str(path), text_color=C_TEAL)
        self.drop_label.configure(text="Ready to convert")
        self.drop.configure(border_color=C_TEAL)
        self._set_status(f"Selected: {path.name}")

    def _bind_drop_targets(self) -> bool:
        """Bind DND_FILES to the drop card and all of its real Tk child windows.

        CustomTkinter widgets are composites. Binding only the outer CTkFrame
        can stop working when the pointer is actually over its label/canvas.
        Registering the full widget tree keeps Explorer drag-and-drop reliable.
        """
        if not _HAS_DND:
            return False

        targets = []

        def collect(widget) -> None:  # noqa: ANN001
            targets.append(widget)
            try:
                for child in widget.winfo_children():
                    collect(child)
            except Exception:
                pass

        collect(self.drop)
        targets.append(self.root)

        bound = 0
        for widget in targets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
                bound += 1
            except Exception:
                continue
        return bound > 0

    def _parse_dnd_paths(self, data: str) -> list[Path]:
        try:
            raw_items = list(self.root.tk.splitlist(data))
        except Exception:
            raw_items = [data]

        paths: list[Path] = []
        for raw in raw_items:
            value = str(raw).strip().strip("{}")
            if not value:
                continue
            if value.lower().startswith("file://"):
                parsed = urlparse(value)
                value = unquote(parsed.path)
                if sys.platform.startswith("win") and re.match(r"^/[A-Za-z]:/", value):
                    value = value[1:]
            paths.append(Path(value))
        return paths

    def _on_drop(self, event) -> None:  # noqa: ANN001
        try:
            paths = self._parse_dnd_paths(event.data)
            existing = [path for path in paths if path.exists()]
            if not existing:
                raise ValueError("The dropped item could not be resolved to a local file or folder.")
            self._set_source(existing[0])
            if len(existing) > 1:
                self._set_status(
                    f"Selected {existing[0].name}; RenFrame converts one game at a time",
                    C_TEAL,
                )
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Ren'Py zip (Cancel to pick a folder)",
            filetypes=[("Zip / archives", "*.zip *.tar.gz *.tgz *.tar.bz2"), ("All", "*.*")],
        )
        if path:
            self._set_source(Path(path))
            return
        folder = filedialog.askdirectory(title="Select Ren'Py game folder")
        if folder:
            self._set_source(Path(folder))

    def _pick_output(self) -> None:
        folder = filedialog.askdirectory(title="Zip output folder", initialdir=str(self.output_dir))
        if folder:
            self.output_dir = Path(folder)
            self.out_label.configure(text=f"Zip saves to: {self.output_dir}")

    def _open_output(self) -> None:
        target = self.last_zip.parent if self.last_zip and self.last_zip.exists() else self.output_dir
        _open_path(target)

    def _copy_instructions(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(FRAME_INSTRUCTIONS)
        self._set_status("Frame instructions copied", C_TEAL)

    def _copy_game_tree(self, source: Path, destination: Path) -> None:
        ignored_dirs = {".git", "_arm_experiment", ".renpy-arm-cache"}
        files: list[Path] = []
        total_bytes = 0

        self._set_progress("Scanning game", 0.0, None, source.name)
        for root, dirs, names in os.walk(source):
            dirs[:] = [name for name in dirs if name not in ignored_dirs]
            root_path = Path(root)
            for name in names:
                path = root_path / name
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                files.append(path)
                total_bytes += size

        destination.mkdir(parents=True, exist_ok=True)
        copied = 0
        chunk_size = 16 * 1024 * 1024

        for root, dirs, _names in os.walk(source):
            dirs[:] = [name for name in dirs if name not in ignored_dirs]
            rel = Path(root).relative_to(source)
            (destination / rel).mkdir(parents=True, exist_ok=True)

        for src_path in files:
            rel = src_path.relative_to(source)
            dst_path = destination / rel
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            if src_path.is_symlink():
                try:
                    os.symlink(os.readlink(src_path), dst_path)
                    continue
                except OSError:
                    pass

            with src_path.open("rb") as src_file, dst_path.open("wb") as dst_file:
                while True:
                    chunk = src_file.read(chunk_size)
                    if not chunk:
                        break
                    dst_file.write(chunk)
                    copied += len(chunk)
                    fraction = copied / total_bytes if total_bytes else 1.0
                    self._set_progress(
                        "Copying game",
                        0.18 * fraction,
                        fraction,
                        f"{src_path.name}  ·  {self._human_bytes(copied)} / {self._human_bytes(total_bytes)}",
                    )
            try:
                shutil.copystat(src_path, dst_path)
            except OSError:
                pass

        self._set_progress("Copying game", 0.18, 1.0, self._human_bytes(total_bytes))

    def _start_convert(self) -> None:
        if self._busy:
            return
        if not self.source:
            messagebox.showinfo(APP_NAME, "Drop or browse to a Ren'Py game folder or zip first.")
            return
        self._busy = True
        self.convert_btn.configure(state="disabled", text="Working…")
        self.log_box.delete("1.0", "end")
        self._reset_progress()
        self._set_status("Converting…", C_TEAL)
        src = self.source
        out_dir = self.output_dir

        def worker() -> None:
            work = Path(tempfile.mkdtemp(prefix="renpy-arm-ui-"))
            try:
                if src.is_dir():
                    self._append_log("Copying game into a work folder (your original stays unchanged)…")
                    game_copy = work / src.name
                    self._copy_game_tree(src, game_copy)
                    convert_src = game_copy
                    zip_name = f"{src.name}-linux-aarch64.zip"
                else:
                    self._set_progress("Preparing archive", 0.18, 1.0, src.name)
                    convert_src = src
                    zip_name = f"{src.stem}-linux-aarch64.zip"

                out_zip = out_dir / zip_name
                result = convert_game(
                    convert_src,
                    output_zip=out_zip,
                    work_dir=work,
                    log=self._append_log,
                    progress=self._conversion_progress,
                )

                def done_ok() -> None:
                    self._busy = False
                    self.last_zip = result.archive_path
                    self.convert_btn.configure(state="normal", text="Convert")
                    self._set_progress("Done", 1.0, 1.0, result.archive_path.name)
                    self._set_status(f"Done → {result.archive_path}", C_OK)
                    messagebox.showinfo(
                        APP_NAME,
                        f"Created:\n{result.archive_path}\n\n"
                        f"Ren'Py {result.version}\n\n"
                        "Next: copy the zip to your Frame, unpack, then run:\n"
                        "  chmod +x add-to-steam.sh launch-steam.sh *.sh\n"
                        "  ./add-to-steam.sh\n\n"
                        "Details are in the right-hand panel and inside the zip.",
                    )

                self.root.after(0, done_ok)
            except ConvertError as e:
                err = str(e)
                self.root.after(0, lambda: self._fail(err))
            except Exception as e:
                err = f"Unexpected error: {e}"
                self.root.after(0, lambda: self._fail(err))

        threading.Thread(target=worker, daemon=True).start()

    def _fail(self, msg: str) -> None:
        self._busy = False
        self.convert_btn.configure(state="normal", text="Convert")
        self._append_log("ERROR: " + msg)
        self._set_progress("Failed", self.overall_progress.get(), 0.0, msg.splitlines()[0])
        self._set_status("Failed", C_ERR)
        messagebox.showerror(APP_NAME, msg)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    ConverterApp().run()


if __name__ == "__main__":
    main()

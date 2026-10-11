"""
سكربت إنشاء ملفات نظام التحميل — يشغل مرة واحدة.
"""

import os

FILES = {
    "core/downloader.py": '''"""
محرك التحميل — يتحكم في عملية تحميل فيديو واحد.
"""

import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import yt_dlp

from utils.logger import app_logger
from utils.helpers import format_filesize, format_speed, format_eta


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    status: DownloadStatus = DownloadStatus.PENDING
    percent: float = 0.0
    downloaded: int = 0
    total: int = 0
    speed: float = 0.0
    eta: int = 0
    filename: str = ""
    error: str = ""
    stage_text: str = ""

    @property
    def downloaded_str(self):
        return format_filesize(self.downloaded)

    @property
    def total_str(self):
        return format_filesize(self.total)

    @property
    def speed_str(self):
        return format_speed(self.speed)

    @property
    def eta_str(self):
        return format_eta(self.eta)


@dataclass
class DownloadOptions:
    quality: str = "720p"
    format_type: str = "mp4"
    output_dir: str = ""
    audio_only: bool = False


class Downloader:
    """محرك تحميل فيديو واحد — يعمل في thread منفصل."""

    def __init__(
        self,
        url: str,
        options: DownloadOptions,
        title: str = "",
        video_id: str = "",
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        self.url = url
        self.options = options
        self.title = title
        self.video_id = video_id
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error

        self._thread = None
        self._cancel_flag = False
        self.progress = DownloadProgress()
        self.output_path = ""

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._cancel_flag = False
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel_flag = True

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _worker(self):
        try:
            self.progress.status = DownloadStatus.DOWNLOADING
            self.progress.stage_text = "جاري التحميل..."
            self._emit()

            fmt = self._build_format()

            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(self.options.output_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [self._hook],
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "retries": 5,
                "socket_timeout": 30,
            }

            if self.options.audio_only or self.options.format_type in ("mp3", "m4a"):
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.options.format_type if self.options.format_type != "mp4" else "mp3",
                    "preferredquality": "192",
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if info:
                    fn = ydl.prepare_filename(info)
                    self.output_path = fn
                    self.progress.filename = os.path.basename(fn)

            if self._cancel_flag:
                self.progress.status = DownloadStatus.CANCELLED
                self.progress.stage_text = "ملغي"
                self._emit()
                return

            self.progress.status = DownloadStatus.COMPLETED
            self.progress.percent = 100.0
            self.progress.stage_text = "اكتمل"
            self._emit()

            if self.on_complete:
                self.on_complete(self.output_path)

        except yt_dlp.utils.DownloadError as e:
            if self._cancel_flag:
                self.progress.status = DownloadStatus.CANCELLED
                self._emit()
                return
            self._err(self._clean(str(e)))
        except Exception as e:
            self._err(str(e))

    def _build_format(self):
        if self.options.audio_only or self.options.format_type in ("mp3", "m4a"):
            return "bestaudio/best"
        h = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}.get(self.options.quality, 720)
        return "bestvideo[height<={}]+bestaudio/best[height<={}]/best".format(h, h)

    def _hook(self, d):
        if self._cancel_flag:
            raise yt_dlp.utils.DownloadError("cancelled")
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            dl = d.get("downloaded_bytes", 0)
            self.progress.percent = (dl / total * 100) if total > 0 else 0
            self.progress.downloaded = dl
            self.progress.total = total
            self.progress.speed = d.get("speed") or 0
            self.progress.eta = d.get("eta") or 0
            self._emit()

    def _emit(self):
        if self.on_progress:
            try:
                self.on_progress(self.progress)
            except Exception:
                pass

    def _err(self, msg):
        self.progress.status = DownloadStatus.FAILED
        self.progress.error = msg
        self.progress.stage_text = "فشل"
        self._emit()
        app_logger.error("فشل التحميل: {}".format(msg))
        if self.on_error:
            self.on_error(msg)

    @staticmethod
    def _clean(raw):
        raw = raw.replace("ERROR: ", "").strip()
        if "Video unavailable" in raw:
            return "الفيديو غير متاح"
        if "Private" in raw:
            return "الفيديو خاص"
        if "urlopen" in raw:
            return "فشل الاتصال بالإنترنت"
        return raw[:200]
''',

    "core/download_manager.py": '''"""
مدير التحميلات — يدير كل التحميلات الجارية والمكتملة.
"""

import uuid
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from core.downloader import Downloader, DownloadOptions, DownloadProgress, DownloadStatus
from utils.logger import app_logger


@dataclass
class DownloadItem:
    task_id: str
    url: str
    title: str
    video_id: str
    options: DownloadOptions
    downloader: Optional[Downloader] = None
    progress: DownloadProgress = field(default_factory=DownloadProgress)

    @property
    def status(self):
        return self.progress.status

    @property
    def is_active(self):
        return self.status in (
            DownloadStatus.PENDING,
            DownloadStatus.DOWNLOADING,
            DownloadStatus.PROCESSING,
        )

    @property
    def is_finished(self):
        return self.status in (
            DownloadStatus.COMPLETED,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        )


class DownloadManager:
    """يدير كل التحميلات."""

    def __init__(self):
        self.items = {}
        self.lock = threading.Lock()
        self.on_item_added = None
        self.on_item_updated = None
        self.on_item_removed = None

    def add_download(self, url, title, video_id, options):
        task_id = str(uuid.uuid4())[:8]
        item = DownloadItem(
            task_id=task_id,
            url=url,
            title=title,
            video_id=video_id,
            options=options,
        )
        item.progress.status = DownloadStatus.PENDING
        item.progress.stage_text = "في الانتظار"
        item.progress.filename = title

        with self.lock:
            self.items[task_id] = item

        app_logger.info("+ تحميل جديد [{}]: {}".format(task_id, title))

        if self.on_item_added:
            try:
                self.on_item_added(item)
            except Exception:
                pass

        self._start(item)
        return task_id

    def _start(self, item):
        downloader = Downloader(
            url=item.url,
            options=item.options,
            title=item.title,
            video_id=item.video_id,
            on_progress=lambda p: self._on_progress(item.task_id, p),
            on_complete=lambda path: self._on_complete(item.task_id, path),
            on_error=lambda err: self._on_error(item.task_id, err),
        )
        item.downloader = downloader
        downloader.start()

    def _on_progress(self, task_id, progress):
        with self.lock:
            item = self.items.get(task_id)
            if not item:
                return
            item.progress = progress
        if self.on_item_updated:
            try:
                self.on_item_updated(item)
            except Exception:
                pass

    def _on_complete(self, task_id, path):
        with self.lock:
            item = self.items.get(task_id)
        if not item:
            return
        if self.on_item_updated:
            try:
                self.on_item_updated(item)
            except Exception:
                pass

    def _on_error(self, task_id, error):
        with self.lock:
            item = self.items.get(task_id)
        if not item:
            return
        if self.on_item_updated:
            try:
                self.on_item_updated(item)
            except Exception:
                pass

    def cancel(self, task_id):
        with self.lock:
            item = self.items.get(task_id)
        if item and item.downloader:
            item.downloader.cancel()

    def remove(self, task_id):
        with self.lock:
            item = self.items.pop(task_id, None)
        if item and item.downloader and item.is_active:
            item.downloader.cancel()
        if self.on_item_removed:
            try:
                self.on_item_removed(task_id)
            except Exception:
                pass

    def cancel_all(self):
        with self.lock:
            for item in list(self.items.values()):
                if item.downloader and item.is_active:
                    item.downloader.cancel()

    def get_all(self):
        with self.lock:
            return list(self.items.values())

    def get_active_count(self):
        with self.lock:
            return sum(1 for i in self.items.values() if i.is_active)

    def clear_finished(self):
        with self.lock:
            finished = [tid for tid, i in self.items.items() if i.is_finished]
            for tid in finished:
                self.items.pop(tid, None)
        for tid in finished:
            if self.on_item_removed:
                try:
                    self.on_item_removed(tid)
                except Exception:
                    pass
''',

    "ui/download_modal.py": '''"""
نافذة منبثقة لاختيار جودة وصيغة التحميل.
"""

import os
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.downloader import DownloadOptions
from core.search_engine import VideoResult
from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger
from utils.helpers import format_duration, format_views


class DownloadModal(ctk.CTkToplevel):
    """نافذة اختيار الجودة والصيغة قبل التحميل."""

    def __init__(self, master, video, default_dir="", on_confirm=None):
        super().__init__(master)

        self.video = video
        self.on_confirm = on_confirm

        self.title("خيارات التحميل")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_PRIMARY)

        self.transient(master)
        self.grab_set()
        self.focus_set()

        self._center(master, 520, 620)

        self.quality_var = ctk.StringVar(value="720p")
        self.format_var = ctk.StringVar(value="mp4")

        if not default_dir:
            default_dir = str(Path.home() / "Downloads" / "YouTubeMediaHub")
        self.output_dir_var = ctk.StringVar(value=default_dir)

        self._build_ui()

    def _center(self, master, w, h):
        master.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - w) // 2
        y = master.winfo_y() + (master.winfo_height() - h) // 2
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def _build_ui(self):
        main = ctk.CTkFrame(
            self, fg_color=Colors.BG_SECONDARY,
            corner_radius=Sizes.RADIUS_LG,
            border_width=1, border_color=Colors.BORDER
        )
        main.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            main, text="خيارات التحميل",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(Sizes.SPACE_LG, Sizes.SPACE_MD))

        info = ctk.CTkFrame(main, fg_color=Colors.BG_TERTIARY, corner_radius=Sizes.RADIUS_MD)
        info.pack(fill="x", padx=Sizes.SPACE_LG, pady=(0, Sizes.SPACE_LG))

        t = self.video.title[:80]
        if len(self.video.title) > 80:
            t += "..."
        ctk.CTkLabel(
            info, text=t, font=Fonts.body_bold(),
            text_color=Colors.TEXT_PRIMARY,
            wraplength=420, justify="right", anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_MD, pady=(Sizes.SPACE_MD, 4))

        ctk.CTkLabel(
            info,
            text="{} | {} | {}".format(
                self.video.channel,
                format_duration(self.video.duration),
                format_views(self.video.views)
            ),
            font=Fonts.tiny(),
            text_color=Colors.TEXT_SECONDARY
        ).pack(anchor="e", padx=Sizes.SPACE_MD, pady=(0, Sizes.SPACE_MD))

        ctk.CTkLabel(
            main, text="الجودة",
            font=Fonts.small_bold(),
            text_color=Colors.TEXT_SECONDARY, anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(0, 6))

        qf = ctk.CTkFrame(main, fg_color="transparent")
        qf.pack(fill="x", padx=Sizes.SPACE_LG, pady=(0, Sizes.SPACE_MD))

        qualities = [("1080p", "1080p"), ("720p", "720p"), ("480p", "480p"),
                     ("360p", "360p"), ("صوت فقط", "audio")]

        for i, (label, val) in enumerate(qualities):
            rb = ctk.CTkRadioButton(
                qf, text=label, variable=self.quality_var, value=val,
                font=Fonts.body(), text_color=Colors.TEXT_PRIMARY,
                fg_color=Colors.ACCENT_START, hover_color=Colors.ACCENT_HOVER,
                border_color=Colors.BORDER,
                radiobutton_width=18, radiobutton_height=18,
                command=lambda v=val: self._on_quality(v)
            )
            rb.grid(row=i // 3, column=i % 3, padx=8, pady=4, sticky="w")

        ctk.CTkLabel(
            main, text="الصيغة",
            font=Fonts.small_bold(),
            text_color=Colors.TEXT_SECONDARY, anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(0, 6))

        self.format_menu = ctk.CTkOptionMenu(
            main, values=["mp4", "mp3", "m4a", "webm"],
            variable=self.format_var,
            height=Sizes.BUTTON_HEIGHT, corner_radius=Sizes.RADIUS_MD,
            font=Fonts.body(), fg_color=Colors.BG_TERTIARY,
            button_color=Colors.ACCENT_END, button_hover_color=Colors.ACCENT_HOVER,
            dropdown_fg_color=Colors.BG_SECONDARY,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            text_color=Colors.TEXT_PRIMARY
        )
        self.format_menu.pack(fill="x", padx=Sizes.SPACE_LG, pady=(0, Sizes.SPACE_MD))

        ctk.CTkLabel(
            main, text="مكان الحفظ",
            font=Fonts.small_bold(),
            text_color=Colors.TEXT_SECONDARY, anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(0, 6))

        pf = ctk.CTkFrame(main, fg_color="transparent")
        pf.pack(fill="x", padx=Sizes.SPACE_LG, pady=(0, Sizes.SPACE_LG))

        ctk.CTkEntry(
            pf, textvariable=self.output_dir_var,
            height=Sizes.BUTTON_HEIGHT, corner_radius=Sizes.RADIUS_MD,
            font=Fonts.small(), fg_color=Colors.BG_INPUT,
            border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY
        ).pack(side="right", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            pf, text="استعراض", width=110, height=Sizes.BUTTON_HEIGHT,
            corner_radius=Sizes.RADIUS_MD, font=Fonts.small_bold(),
            fg_color=Colors.BG_TERTIARY, hover_color=Colors.BG_HOVER,
            command=self._browse
        ).pack(side="right")

        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(fill="x", padx=Sizes.SPACE_LG, pady=(Sizes.SPACE_MD, Sizes.SPACE_LG), side="bottom")

        ctk.CTkButton(
            bf, text="إلغاء", width=120, height=Sizes.BUTTON_HEIGHT,
            corner_radius=Sizes.RADIUS_MD, font=Fonts.button(),
            fg_color=Colors.BG_TERTIARY, hover_color=Colors.BG_HOVER,
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            bf, text="بدء التحميل", height=Sizes.BUTTON_HEIGHT,
            corner_radius=Sizes.RADIUS_MD, font=Fonts.button(),
            fg_color=Colors.ACCENT_START, hover_color=Colors.ACCENT_HOVER,
            command=self._confirm
        ).pack(side="right", fill="x", expand=True)

    def _on_quality(self, val):
        if val == "audio":
            self.format_var.set("mp3")
        else:
            if self.format_var.get() in ("mp3", "m4a"):
                self.format_var.set("mp4")

    def _browse(self):
        current = self.output_dir_var.get()
        if not os.path.exists(current):
            current = str(Path.home())
        chosen = filedialog.askdirectory(title="اختر مجلد الحفظ", initialdir=current)
        if chosen:
            self.output_dir_var.set(chosen)

    def _confirm(self):
        q = self.quality_var.get()
        f = self.format_var.get()
        d = self.output_dir_var.get().strip()

        if not d:
            messagebox.showwarning("تنبيه", "اختر مجلد الحفظ", parent=self)
            return

        audio_only = (q == "audio")
        if audio_only and f not in ("mp3", "m4a"):
            f = "mp3"

        try:
            Path(d).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("خطأ", str(e), parent=self)
            return

        opts = DownloadOptions(
            quality=q if not audio_only else "audio",
            format_type=f,
            output_dir=d,
            audio_only=audio_only,
        )

        if self.on_confirm:
            self.on_confirm(opts)
        self.destroy()
''',

    "ui/download_item_widget.py": '''"""
عنصر عرض تحميل واحد في لوحة التحميلات.
"""

import os
import subprocess
import sys

import customtkinter as ctk

from core.downloader import DownloadStatus
from ui.theme import Colors, Fonts, Sizes


class DownloadItemWidget(ctk.CTkFrame):
    """عنصر تحميل واحد."""

    def __init__(self, master, item, on_cancel=None, on_remove=None, on_open_folder=None, **kwargs):
        super().__init__(
            master, fg_color=Colors.BG_TERTIARY,
            corner_radius=Sizes.RADIUS_MD,
            border_width=1, border_color=Colors.BORDER,
            height=90, **kwargs
        )
        self.pack_propagate(False)
        self.item = item
        self.on_cancel = on_cancel
        self.on_remove = on_remove
        self.on_open_folder = on_open_folder
        self._build()
        self.update_from_item(item)

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=Sizes.SPACE_MD, pady=(Sizes.SPACE_SM, 4))

        self.status_label = ctk.CTkLabel(
            top, text="", font=Fonts.tiny(),
            text_color=Colors.TEXT_SECONDARY,
        )
        self.status_label.pack(side="left")

        t = self.item.title[:70]
        if len(self.item.title) > 70:
            t += "..."
        self.title_label = ctk.CTkLabel(
            top, text=t, font=Fonts.small_bold(),
            text_color=Colors.TEXT_PRIMARY, anchor="e"
        )
        self.title_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            progress_color=Colors.ACCENT_START,
            fg_color=Colors.BG_HOVER,
        )
        self.progress_bar.pack(fill="x", padx=Sizes.SPACE_MD, pady=(0, 4))
        self.progress_bar.set(0)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=Sizes.SPACE_MD, pady=(0, Sizes.SPACE_SM))

        btn = ctk.CTkFrame(bottom, fg_color="transparent")
        btn.pack(side="left")

        self.action_btn = ctk.CTkButton(
            btn, text="X", width=32, height=28,
            corner_radius=Sizes.RADIUS_SM,
            font=Fonts.small_bold(),
            fg_color=Colors.BG_HOVER, hover_color=Colors.ERROR,
            command=self._on_action
        )
        self.action_btn.pack(side="left", padx=2)

        self.folder_btn = ctk.CTkButton(
            btn, text="فتح", width=50, height=28,
            corner_radius=Sizes.RADIUS_SM,
            font=Fonts.tiny(),
            fg_color=Colors.BG_HOVER, hover_color=Colors.SUCCESS,
            command=self._on_folder
        )

        self.details_label = ctk.CTkLabel(
            bottom, text="", font=Fonts.tiny(),
            text_color=Colors.TEXT_MUTED, anchor="e"
        )
        self.details_label.pack(side="right")

    def update_from_item(self, item):
        self.item = item
        p = item.progress
        self.progress_bar.set(p.percent / 100.0)

        cmap = {
            DownloadStatus.DOWNLOADING: Colors.ACCENT_START,
            DownloadStatus.PROCESSING: Colors.WARNING,
            DownloadStatus.COMPLETED: Colors.SUCCESS,
            DownloadStatus.FAILED: Colors.ERROR,
            DownloadStatus.CANCELLED: Colors.TEXT_MUTED,
            DownloadStatus.PAUSED: Colors.INFO,
            DownloadStatus.PENDING: Colors.TEXT_MUTED,
        }
        color = cmap.get(p.status, Colors.ACCENT_START)
        self.progress_bar.configure(progress_color=color)

        texts = {
            DownloadStatus.PENDING: "في الانتظار",
            DownloadStatus.DOWNLOADING: "{:.1f}%".format(p.percent),
            DownloadStatus.PROCESSING: "معالجة...",
            DownloadStatus.PAUSED: "متوقف",
            DownloadStatus.COMPLETED: "اكتمل",
            DownloadStatus.FAILED: "فشل",
            DownloadStatus.CANCELLED: "ملغي",
        }
        self.status_label.configure(text=texts.get(p.status, "-"), text_color=color)

        if p.status == DownloadStatus.DOWNLOADING and p.total > 0:
            details = "{} / {} | {} | {}".format(
                p.downloaded_str, p.total_str, p.speed_str, p.eta_str
            )
        elif p.status == DownloadStatus.COMPLETED:
            details = "تم الحفظ"
        elif p.status == DownloadStatus.FAILED:
            details = p.error[:50] if p.error else "خطأ"
        else:
            details = p.stage_text

        self.details_label.configure(text=details)

        if p.status == DownloadStatus.COMPLETED:
            self.folder_btn.pack(side="left", padx=2)
        else:
            self.folder_btn.pack_forget()

    def _on_action(self):
        if self.item.is_active:
            if self.on_cancel:
                self.on_cancel(self.item.task_id)
        else:
            if self.on_remove:
                self.on_remove(self.item.task_id)

    def _on_folder(self):
        if self.on_open_folder:
            self.on_open_folder(self.item.task_id)
        else:
            path = self.item.options.output_dir
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
            except Exception:
                pass
''',

    "ui/downloads_panel.py": '''"""
لوحة التحميلات السفلية.
"""

import os
import subprocess
import sys

import customtkinter as ctk

from core.download_manager import DownloadManager
from ui.download_item_widget import DownloadItemWidget
from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger


class DownloadsPanel(ctk.CTkFrame):
    """لوحة التحميلات — قابلة للطي والتوسيع."""

    COLLAPSED_HEIGHT = 50
    EXPANDED_HEIGHT = 260

    def __init__(self, master, manager, **kwargs):
        super().__init__(
            master, fg_color=Colors.BG_SECONDARY,
            corner_radius=Sizes.RADIUS_LG,
            border_width=1, border_color=Colors.BORDER,
            height=self.COLLAPSED_HEIGHT, **kwargs
        )
        self.pack_propagate(False)
        self.manager = manager
        self.is_expanded = False
        self.widgets = {}

        self._build()

        manager.on_item_added = self._on_added
        manager.on_item_updated = self._on_updated
        manager.on_item_removed = self._on_removed

    def _build(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=46, cursor="hand2")
        self.header.pack(fill="x", padx=Sizes.SPACE_LG, pady=(4, 0))
        self.header.pack_propagate(False)
        self.header.bind("<Button-1>", lambda e: self.toggle())

        self.arrow = ctk.CTkLabel(
            self.header, text="^", font=Fonts.small_bold(),
            text_color=Colors.TEXT_SECONDARY, cursor="hand2"
        )
        self.arrow.pack(side="left", padx=(0, 10))
        self.arrow.bind("<Button-1>", lambda e: self.toggle())

        ctk.CTkButton(
            self.header, text="مسح المنتهية", width=130, height=28,
            corner_radius=Sizes.RADIUS_SM, font=Fonts.tiny(),
            fg_color=Colors.BG_HOVER, hover_color=Colors.ERROR,
            command=self._clear
        ).pack(side="left", padx=4)

        self.title_label = ctk.CTkLabel(
            self.header, text="التحميلات", font=Fonts.body_bold(),
            text_color=Colors.TEXT_PRIMARY, cursor="hand2"
        )
        self.title_label.pack(side="right")
        self.title_label.bind("<Button-1>", lambda e: self.toggle())

        self.count_label = ctk.CTkLabel(
            self.header, text="", font=Fonts.tiny(),
            text_color=Colors.TEXT_MUTED, cursor="hand2"
        )
        self.count_label.pack(side="right", padx=(0, 10))
        self.count_label.bind("<Button-1>", lambda e: self.toggle())

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)

    def toggle(self):
        self.is_expanded = not self.is_expanded
        self._apply_state()

    def expand(self):
        if not self.is_expanded:
            self.is_expanded = True
            self._apply_state()

    def _apply_state(self):
        if self.is_expanded:
            self.configure(height=self.EXPANDED_HEIGHT)
            self.arrow.configure(text="v")
            self.content.pack(fill="both", expand=True, padx=Sizes.SPACE_MD, pady=(0, Sizes.SPACE_MD))
        else:
            self.configure(height=self.COLLAPSED_HEIGHT)
            self.arrow.configure(text="^")
            self.content.pack_forget()

    def _on_added(self, item):
        try:
            w = DownloadItemWidget(
                self.content, item=item,
                on_cancel=self._cancel,
                on_remove=self._remove,
                on_open_folder=self._open,
            )
            w.pack(fill="x", pady=4, padx=2)
            self.widgets[item.task_id] = w
            self.expand()
            self._update_counter()
        except Exception as e:
            app_logger.error("خطأ في إضافة widget: {}".format(e))

    def _on_updated(self, item):
        w = self.widgets.get(item.task_id)
        if w:
            try:
                w.after(0, lambda: w.update_from_item(item))
            except Exception:
                pass
        self._update_counter()

    def _on_removed(self, task_id):
        w = self.widgets.pop(task_id, None)
        if w:
            try:
                w.destroy()
            except Exception:
                pass
        self._update_counter()

    def _cancel(self, tid):
        self.manager.cancel(tid)

    def _remove(self, tid):
        self.manager.remove(tid)

    def _open(self, tid):
        for item in self.manager.get_all():
            if item.task_id == tid:
                path = item.options.output_dir
                try:
                    if sys.platform == "win32":
                        os.startfile(path)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", path])
                    else:
                        subprocess.Popen(["xdg-open", path])
                except Exception as e:
                    app_logger.error("فشل فتح المجلد: {}".format(e))
                break

    def _clear(self):
        self.manager.clear_finished()
        self._update_counter()

    def _update_counter(self):
        active = self.manager.get_active_count()
        total = len(self.manager.get_all())
        if active > 0:
            self.count_label.configure(
                text="({} نشط / {})".format(active, total),
                text_color=Colors.ACCENT_START
            )
        else:
            self.count_label.configure(
                text="({})".format(total),
                text_color=Colors.TEXT_MUTED
            )
''',
}


def main():
    print("=" * 60)
    print("  انشاء ملفات نظام التحميل")
    print("=" * 60)
    print()

    for filename, content in FILES.items():
        path = filename.replace("/", os.sep)
        try:
            # إنشاء المجلد لو مش موجود
            folder = os.path.dirname(path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

            # كتابة الملف
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            size = os.path.getsize(path)
            print("[OK] {} - {} bytes".format(filename, size))
        except Exception as e:
            print("[ERROR] {} - {}".format(filename, e))

    print()
    print("=" * 60)
    print("  تم إنشاء {} ملف بنجاح".format(len(FILES)))
    print("=" * 60)


if __name__ == "__main__":
    main()
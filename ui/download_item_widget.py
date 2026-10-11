"""
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

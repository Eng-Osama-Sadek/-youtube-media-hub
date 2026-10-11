"""
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

"""
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

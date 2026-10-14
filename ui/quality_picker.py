"""
نافذة اختيار جودة + طريقة التشغيل
"""

import customtkinter as ctk

from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger


class QualityPickerModal(ctk.CTkToplevel):
    """نافذة اختيار الجودة + طريقة التشغيل."""

    QUALITIES = [
        ("144p", "144", "سريع جداً - جودة منخفضة"),
        ("240p", "240", "سريع - جودة متوسطة"),
        ("360p", "360", "متوازن - الأفضل للتجربة"),
        ("480p", "480", "جيد - جودة أعلى"),
        ("720p", "720", "عالي الدقة HD"),
        ("1080p", "1080", "Full HD"),
    ]

    def __init__(self, master, video_title="", on_confirm=None):
        super().__init__(master)

        self.video_title = video_title
        self.on_confirm = on_confirm
        self.selected_quality = "360"
        self.streaming_mode = True  # ⚡ افتراضي: تشغيل فوري

        self.title("اختيار الجودة وطريقة التشغيل")
        self.geometry("520x700")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_PRIMARY)
        self.transient(master)
        self.grab_set()
        self.focus_set()

        self._center(master, 520, 700)
        self._build_ui()

    def _center(self, master, w, h):
        master.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - w) // 2
        y = master.winfo_y() + (master.winfo_height() - h) // 2
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def _build_ui(self):
        main = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_SECONDARY,
            corner_radius=Sizes.RADIUS_LG,
            border_width=1,
            border_color=Colors.BORDER
        )
        main.pack(fill="both", expand=True, padx=16, pady=16)

        # ═══ العنوان ═══
        ctk.CTkLabel(
            main,
            text="إعدادات التشغيل",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(Sizes.SPACE_LG, 4))

        title_text = self.video_title[:60]
        if len(self.video_title) > 60:
            title_text += "..."
        ctk.CTkLabel(
            main,
            text=title_text,
            font=Fonts.small(),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=440,
            justify="right",
            anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(0, Sizes.SPACE_MD))

        # ═══════════════════════════════════════════
        # 🎬 طريقة التشغيل (قسم جديد)
        # ═══════════════════════════════════════════
        ctk.CTkLabel(
            main,
            text="طريقة التشغيل:",
            font=Fonts.small_bold(),
            text_color=Colors.TEXT_PRIMARY,
            anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(0, 6))

        method_frame = ctk.CTkFrame(main, fg_color="transparent")
        method_frame.pack(fill="x", padx=Sizes.SPACE_LG, pady=(0, Sizes.SPACE_MD))

        self.method_var = ctk.StringVar(value="stream")

        # ⚡ تشغيل فوري
        instant_btn = ctk.CTkFrame(
            method_frame,
            fg_color=Colors.BG_TERTIARY,
            corner_radius=Sizes.RADIUS_MD,
            height=60,
            border_width=2,
            border_color=Colors.SUCCESS
        )
        instant_btn.pack(side="right", fill="x", expand=True, padx=(0, 4))
        instant_btn.pack_propagate(False)

        ctk.CTkRadioButton(
            instant_btn,
            text="",
            variable=self.method_var,
            value="stream",
            width=18,
            height=18,
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS,
            border_color=Colors.BORDER,
            command=self._on_method_change
        ).pack(side="right", padx=(12, 6), pady=16)

        txt1 = ctk.CTkFrame(instant_btn, fg_color="transparent")
        txt1.pack(side="right", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(
            txt1, text="⚡ تشغيل فوري",
            font=Fonts.body_bold(), text_color=Colors.SUCCESS, anchor="e"
        ).pack(anchor="e", pady=(12, 0))
        ctk.CTkLabel(
            txt1, text="يبدأ في ثوانٍ (بث مباشر)",
            font=Fonts.tiny(), text_color=Colors.TEXT_MUTED, anchor="e"
        ).pack(anchor="e")

        # 💾 تحميل ثم تشغيل
        download_btn = ctk.CTkFrame(
            method_frame,
            fg_color=Colors.BG_TERTIARY,
            corner_radius=Sizes.RADIUS_MD,
            height=60,
            border_width=1,
            border_color=Colors.BORDER
        )
        download_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
        download_btn.pack_propagate(False)

        ctk.CTkRadioButton(
            download_btn,
            text="",
            variable=self.method_var,
            value="download",
            width=18,
            height=18,
            fg_color=Colors.ACCENT_START,
            hover_color=Colors.ACCENT_HOVER,
            border_color=Colors.BORDER,
            command=self._on_method_change
        ).pack(side="right", padx=(12, 6), pady=16)

        txt2 = ctk.CTkFrame(download_btn, fg_color="transparent")
        txt2.pack(side="right", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(
            txt2, text="💾 تحميل ثم تشغيل",
            font=Fonts.body_bold(), text_color=Colors.TEXT_PRIMARY, anchor="e"
        ).pack(anchor="e", pady=(12, 0))
        ctk.CTkLabel(
            txt2, text="جودة أعلى - ينتظر قليلاً",
            font=Fonts.tiny(), text_color=Colors.TEXT_MUTED, anchor="e"
        ).pack(anchor="e")

        # فاصل
        ctk.CTkFrame(
            main, height=1, fg_color=Colors.BORDER
        ).pack(fill="x", padx=Sizes.SPACE_LG, pady=Sizes.SPACE_MD)

        # ═══ الجودة ═══
        ctk.CTkLabel(
            main,
            text="جودة العرض:",
            font=Fonts.small_bold(),
            text_color=Colors.TEXT_PRIMARY,
            anchor="e"
        ).pack(anchor="e", padx=Sizes.SPACE_LG, pady=(0, 6))

        self.quality_var = ctk.StringVar(value="360")

        for label, value, desc in self.QUALITIES:
            self._create_quality_option(main, label, value, desc)

        # ═══ الأزرار ═══
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(
            fill="x", padx=Sizes.SPACE_LG,
            pady=(Sizes.SPACE_MD, Sizes.SPACE_LG),
            side="bottom"
        )

        ctk.CTkButton(
            btn_frame,
            text="إلغاء",
            width=110,
            height=Sizes.BUTTON_HEIGHT,
            corner_radius=Sizes.RADIUS_MD,
            font=Fonts.button(),
            fg_color=Colors.BG_TERTIARY,
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame,
            text="▶ تشغيل الآن",
            height=Sizes.BUTTON_HEIGHT,
            corner_radius=Sizes.RADIUS_MD,
            font=Fonts.button(),
            fg_color=Colors.ACCENT_START,
            hover_color=Colors.ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_confirm
        ).pack(side="right", fill="x", expand=True)

    def _create_quality_option(self, parent, label, value, desc):
        """إنشاء زر جودة واحد."""
        frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_TERTIARY,
            corner_radius=Sizes.RADIUS_MD,
            height=48,
            border_width=1,
            border_color=Colors.BORDER
        )
        frame.pack(fill="x", padx=Sizes.SPACE_LG, pady=2)
        frame.pack_propagate(False)

        ctk.CTkRadioButton(
            frame,
            text="",
            variable=self.quality_var,
            value=value,
            width=18,
            height=18,
            fg_color=Colors.ACCENT_START,
            hover_color=Colors.ACCENT_HOVER,
            border_color=Colors.BORDER
        ).pack(side="right", padx=(Sizes.SPACE_MD, 6), pady=12)

        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="right", fill="x", expand=True, padx=(0, 6))

        ctk.CTkLabel(
            text_frame,
            text=label,
            font=Fonts.body_bold(),
            text_color=Colors.TEXT_PRIMARY,
            anchor="e"
        ).pack(anchor="e")

        ctk.CTkLabel(
            text_frame,
            text=desc,
            font=Fonts.tiny(),
            text_color=Colors.TEXT_MUTED,
            anchor="e"
        ).pack(anchor="e")

        for widget in (frame, text_frame):
            widget.bind(
                "<Double-Button-1>",
                lambda e, v=value: self._select_and_play(v)
            )

    def _on_method_change(self):
        """تحديث عند تغيير طريقة التشغيل."""
        method = self.method_var.get()
        self.streaming_mode = (method == "stream")
        app_logger.info("طريقة التشغيل: {}".format(method))

    def _select_and_play(self, value):
        """اختيار + تشغيل تلقائي."""
        self.selected_quality = value
        self.quality_var.set(value)
        self.after(200, self._on_confirm)

    def _on_confirm(self):
        """تأكيد + تشغيل."""
        quality = self.selected_quality
        streaming = self.streaming_mode

        app_logger.info("تشغيل: {}p — streaming={}".format(quality, streaming))

        self.destroy()

        if self.on_confirm:
            try:
                self.on_confirm(quality, streaming)
            except Exception as e:
                app_logger.error("فشل التشغيل: {}".format(e))
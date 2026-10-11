"""
شاشة البداية (Splash Screen) — تظهر لمدة قصيرة مع أنيميشن أنيق.
"""

import customtkinter as ctk
from ui.theme import Colors, Fonts, Sizes


class SplashScreen(ctk.CTkToplevel):
    """شاشة بداية عصرية مع شريط تحميل متحرك."""
    
    def __init__(self, duration_ms: int = 2500):
        super().__init__()
        
        self.duration_ms = duration_ms
        self.progress_value = 0
        self._animation_job = None
        
        # إعدادات النافذة
        self.title("YouTube Media Hub")
        self.geometry("560x360")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.configure(fg_color=Colors.BG_PRIMARY)
        
        # توسيط
        self._center_window(560, 360)
        
        # إبقاء في المقدمة
        self.attributes("-topmost", True)
        self.lift()
        
        # بناء الواجهة
        self._build_ui()
        
        # بدء الأنيميشن
        self._animate_progress()
    
    def _center_window(self, width: int, height: int) -> None:
        """توسيط النافذة على الشاشة."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _build_ui(self) -> None:
        """بناء عناصر الشاشة."""
        
        main = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_SECONDARY,
            corner_radius=Sizes.RADIUS_XL,
            border_width=2,
            border_color=Colors.ACCENT_END
        )
        main.pack(fill="both", expand=True, padx=12, pady=12)
        
        # الأيقونة
        self.logo_label = ctk.CTkLabel(
            main,
            text="▶",
            font=("Segoe UI Emoji", 72, "bold"),
            text_color=Colors.ACCENT_START
        )
        self.logo_label.pack(pady=(40, 0))
        
        # الاسم
        title = ctk.CTkLabel(
            main,
            text="YouTube Media Hub",
            font=Fonts.heading(),
            text_color=Colors.TEXT_PRIMARY
        )
        title.pack(pady=(10, 0))
        
        # الوصف
        subtitle = ctk.CTkLabel(
            main,
            text="ابحث • شاهد • حمّل",
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY
        )
        subtitle.pack(pady=(4, 0))
        
        # شريط التقدم
        self.progress = ctk.CTkProgressBar(
            main,
            width=380,
            height=8,
            corner_radius=4,
            progress_color=Colors.ACCENT_START,
            fg_color=Colors.BG_TERTIARY
        )
        self.progress.pack(pady=(40, 0))
        self.progress.set(0)
        
        # نص الحالة
        self.status_label = ctk.CTkLabel(
            main,
            text="جاري التحميل...",
            font=Fonts.small(),
            text_color=Colors.TEXT_MUTED
        )
        self.status_label.pack(pady=(10, 0))
        
        # حقوق النشر
        copyright_label = ctk.CTkLabel(
            main,
            text="© 2024 — للأغراض الشخصية فقط",
            font=Fonts.tiny(),
            text_color=Colors.TEXT_MUTED
        )
        copyright_label.pack(side="bottom", pady=16)
    
    def _animate_progress(self) -> None:
        """تحريك شريط التقدم تدريجياً."""
        if self.progress_value < 1.0:
            step = 0.02 if self.progress_value < 0.7 else 0.01
            self.progress_value = min(1.0, self.progress_value + step)
            self.progress.set(self.progress_value)
            
            if self.progress_value < 0.3:
                self.status_label.configure(text="جاري تهيئة التطبيق...")
            elif self.progress_value < 0.6:
                self.status_label.configure(text="فحص ffmpeg...")
            elif self.progress_value < 0.9:
                self.status_label.configure(text="تحضير الواجهة...")
            else:
                self.status_label.configure(text="جاهز! ✨")
            
            self._animation_job = self.after(50, self._animate_progress)
    
    def close_splash(self, callback=None) -> None:
        """إغلاق الشاشة."""
        if self._animation_job:
            self.after_cancel(self._animation_job)
        self.destroy()
        if callback:
            callback()
    
    def show_until_ready(self, callback) -> None:
        """إظهار الشاشة لمدة محددة، ثم استدعاء callback."""
        self.after(self.duration_ms, lambda: self.close_splash(callback))
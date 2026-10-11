"""
النافذة الرئيسية للتطبيق — النسخة الكاملة مع نظام التحميل.
"""

import customtkinter as ctk
from tkinter import messagebox

from ui.theme import Colors, Fonts, Sizes, ThemeMode
from ui.results_grid import ResultsGrid
from ui.download_modal import DownloadModal
from ui.downloads_panel import DownloadsPanel
from core.search_engine import SearchEngine, VideoResult
from core.download_manager import DownloadManager
from core.downloader import DownloadOptions
from utils.logger import app_logger, log_shutdown
from utils.ffmpeg_check import check_ffmpeg


class MainWindow(ctk.CTk):
    """النافذة الرئيسية — النسخة الكاملة."""
    
    def __init__(self):
        super().__init__()
        
        # إعدادات النافذة
        self.title("YouTube Media Hub — بحث وتحميل")
        self.geometry("{}x{}".format(Sizes.WINDOW_DEF_W, Sizes.WINDOW_DEF_H))
        self.minsize(Sizes.WINDOW_MIN_W, Sizes.WINDOW_MIN_H)
        self.configure(fg_color=Colors.BG_PRIMARY)
        
        self._center_window()
        
        try:
            self.iconbitmap("assets/icon.ico")
        except Exception:
            pass
        
        # الحالة
        self.current_theme = ThemeMode.DARK
        self.ffmpeg_available = False
        self.search_engine = SearchEngine()
        self.download_manager = DownloadManager()
        
        # بناء الواجهة
        self._build_ui()
        self.after(500, self._check_ffmpeg_on_startup)
        
        app_logger.info("تم فتح النافذة الرئيسية")
    
    def _center_window(self):
        self.update_idletasks()
        w = Sizes.WINDOW_DEF_W
        h = Sizes.WINDOW_DEF_H
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))
    
    # ═══════════════════════════════════════════
    # 🏗️ بناء الواجهة
    # ═══════════════════════════════════════════
    
    def _build_ui(self):
        self.main_container = ctk.CTkFrame(
            self, fg_color=Colors.BG_PRIMARY, corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)
        
        self._build_header()
        self._build_search_section()
        self._build_results_section()
        self._build_downloads_panel()
    
    def _build_header(self):
        header = ctk.CTkFrame(
            self.main_container, height=70,
            fg_color=Colors.BG_SECONDARY, corner_radius=0
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=Sizes.SPACE_XL)
        
        ctk.CTkLabel(
            logo_frame, text="▶",
            font=("Segoe UI Emoji", 28, "bold"),
            text_color=Colors.ACCENT_START
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            logo_frame, text="YouTube Media Hub",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")
        
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right", padx=Sizes.SPACE_XL)
        
        self.theme_btn = ctk.CTkButton(
            controls, text="🌙", width=40, height=40,
            corner_radius=Sizes.RADIUS_MD,
            font=("Segoe UI Emoji", 18),
            fg_color=Colors.BG_TERTIARY,
            hover_color=Colors.BG_HOVER,
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="right", padx=Sizes.SPACE_XS)
        
        ctk.CTkFrame(
            self.main_container, height=2,
            fg_color=Colors.ACCENT_START, corner_radius=0
        ).pack(fill="x", side="top")
    
    def _build_search_section(self):
        section = ctk.CTkFrame(self.main_container, fg_color="transparent")
        section.pack(
            fill="x", padx=Sizes.SPACE_XL,
            pady=(Sizes.SPACE_XL, Sizes.SPACE_MD)
        )
        
        self.welcome_label = ctk.CTkLabel(
            section,
            text="ابحث عن أي فيديو أو صوت من يوتيوب 🎬",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        )
        self.welcome_label.pack(anchor="e", pady=(0, Sizes.SPACE_MD))
        
        search_row = ctk.CTkFrame(section, fg_color="transparent")
        search_row.pack(fill="x")
        
        self.filter_var = ctk.StringVar(value="الكل")
        self.filter_menu = ctk.CTkOptionMenu(
            search_row,
            values=["الكل", "أفلام", "رياضة", "أخبار",
                    "كارتون", "أغاني", "تعليمي", "ترفيه"],
            variable=self.filter_var,
            width=140, height=Sizes.INPUT_HEIGHT,
            corner_radius=Sizes.RADIUS_MD,
            font=Fonts.body_bold(),
            dropdown_font=Fonts.body(),
            fg_color=Colors.BG_TERTIARY,
            button_color=Colors.ACCENT_END,
            button_hover_color=Colors.ACCENT_HOVER,
            dropdown_fg_color=Colors.BG_SECONDARY,
            dropdown_hover_color=Colors.BG_HOVER,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            text_color=Colors.TEXT_PRIMARY
        )
        self.filter_menu.pack(side="right", padx=(0, Sizes.SPACE_SM))
        
        self.search_btn = ctk.CTkButton(
            search_row,
            text="🔍 بحث", width=130, height=Sizes.INPUT_HEIGHT,
            corner_radius=Sizes.RADIUS_MD,
            font=Fonts.button(),
            fg_color=Colors.ACCENT_START,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            command=self._on_search_clicked
        )
        self.search_btn.pack(side="right", padx=(0, Sizes.SPACE_SM))
        
        self.search_entry = ctk.CTkEntry(
            search_row,
            height=Sizes.INPUT_HEIGHT,
            corner_radius=Sizes.RADIUS_MD,
            font=Fonts.body(),
            placeholder_text="اكتب اسم الفيديو... أو الصق رابط يوتيوب",
            placeholder_text_color=Colors.TEXT_MUTED,
            fg_color=Colors.BG_INPUT,
            border_color=Colors.BORDER,
            border_width=1,
            text_color=Colors.TEXT_PRIMARY
        )
        self.search_entry.pack(
            side="right", fill="x", expand=True,
            padx=(0, Sizes.SPACE_SM)
        )
        self.search_entry.bind("<Return>", lambda e: self._on_search_clicked())
    
    def _build_results_section(self):
        self.results_grid = ResultsGrid(
            self.main_container,
            on_download=self._on_download_video,
            on_copy_url=self._on_copy_url,
        )
        self.results_grid.pack(
            fill="both", expand=True,
            padx=Sizes.SPACE_XL,
            pady=(0, Sizes.SPACE_MD)
        )
        self.results_grid.show_welcome()
    
    def _build_downloads_panel(self):
        """بناء لوحة التحميلات السفلية."""
        self.downloads_panel = DownloadsPanel(
            self.main_container,
            manager=self.download_manager,
        )
        self.downloads_panel.pack(
            fill="x",
            padx=Sizes.SPACE_XL,
            pady=(0, Sizes.SPACE_MD),
            side="bottom"
        )
    
    # ═══════════════════════════════════════════
    # 🔍 البحث
    # ═══════════════════════════════════════════
    
    def _on_search_clicked(self):
        query = self.search_entry.get().strip()
        
        if not query:
            messagebox.showwarning(
                "تنبيه",
                "من فضلك اكتب كلمة للبحث عنها أو الصق رابط يوتيوب."
            )
            return
        
        filter_type = self.filter_var.get()
        app_logger.info("بحث: '{}' - الفلتر: {}".format(query, filter_type))
        
        self.search_engine.cancel()
        self.search_btn.configure(state="disabled", text="جاري...")
        self.results_grid.show_loading("جاري البحث في يوتيوب...")
        self._update_header_status("جاري البحث...")
        
        self.search_engine.search(
            query=query,
            filter_type=filter_type,
            max_results=20,
            on_success=lambda r: self.after(0, lambda: self._on_search_success(r, query)),
            on_error=lambda e: self.after(0, lambda: self._on_search_error(e)),
            on_progress=lambda m: self.after(0, lambda: self._update_header_status(m)),
        )
    
    def _on_search_success(self, results, query):
        self.search_btn.configure(state="normal", text="🔍 بحث")
        self._update_header_status("")
        self.results_grid.display_results(results, query=query)
        self.welcome_label.configure(text="نتائج البحث عن: {}".format(query))
    
    def _on_search_error(self, error):
        self.search_btn.configure(state="normal", text="🔍 بحث")
        self._update_header_status("")
        self.results_grid.show_empty(error)
        app_logger.error("خطأ بحث: {}".format(error))
    
    def _update_header_status(self, text):
        if text:
            self.title("YouTube Media Hub - {}".format(text))
        else:
            self.title("YouTube Media Hub - بحث وتحميل")
    
    # ═══════════════════════════════════════════
    # 📥 التحميل
    # ═══════════════════════════════════════════
    
    def _on_download_video(self, video):
        """فتح نافذة اختيار الجودة."""
        app_logger.info("طلب تحميل: {}".format(video.title))
        
        modal = DownloadModal(
            self,
            video=video,
            default_dir="",
            on_confirm=lambda opts: self._start_download(video, opts),
        )
        modal.focus()
    
    def _start_download(self, video, options):
        """بدء التحميل الفعلي."""
        try:
            task_id = self.download_manager.add_download(
                url=video.url,
                title=video.title,
                video_id=video.video_id,
                options=options,
            )
            app_logger.info("بدأ التحميل [{}]: {}".format(task_id, video.title))
            self._show_toast("بدأ تحميل: {}...".format(video.title[:40]))
        except Exception as e:
            messagebox.showerror("خطأ", "فشل بدء التحميل:\n{}".format(e))
            app_logger.error("فشل بدء التحميل: {}".format(e))
    
    def _on_copy_url(self, video):
        app_logger.info("تم نسخ: {}".format(video.short_url))
    
    # ═══════════════════════════════════════════
    # 🎨 Toast
    # ═══════════════════════════════════════════
    
    def _show_toast(self, message):
        """إشعار صغير يظهر ثم يختفي."""
        toast = ctk.CTkFrame(
            self,
            fg_color=Colors.ACCENT_END,
            corner_radius=Sizes.RADIUS_MD,
            border_width=1,
            border_color=Colors.ACCENT_START,
        )
        toast.place(relx=0.5, rely=0.92, anchor="center")
        
        ctk.CTkLabel(
            toast,
            text=message,
            font=Fonts.small_bold(),
            text_color="#FFFFFF"
        ).pack(padx=20, pady=10)
        
        self.after(2500, lambda: self._hide_toast(toast))
    
    def _hide_toast(self, toast):
        try:
            toast.destroy()
        except Exception:
            pass
    
    # ═══════════════════════════════════════════
    # 🎛️ التحكم
    # ═══════════════════════════════════════════
    
    def _toggle_theme(self):
        if self.current_theme == ThemeMode.DARK:
            self.current_theme = ThemeMode.LIGHT
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="☀")
        else:
            self.current_theme = ThemeMode.DARK
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="🌙")
    
    def _check_ffmpeg_on_startup(self):
        """فحص ffmpeg بدون رسالة تحذير."""
        available, message = check_ffmpeg()
        self.ffmpeg_available = available
        if not available:
            app_logger.warning("ffmpeg غير مثبت - التحميل بجودة عادية فقط")
    
    # ═══════════════════════════════════════════
    # 🚪 إغلاق
    # ═══════════════════════════════════════════
    
    def on_close(self):
        try:
            active = self.download_manager.get_active_count()
            if active > 0:
                confirm = messagebox.askyesno(
                    "تأكيد الإغلاق",
                    "هناك {} تحميل جاري. هل تريد الإغلاق؟".format(active)
                )
                if not confirm:
                    return
            
            self.search_engine.cancel()
            self.download_manager.cancel_all()
            log_shutdown()
            self.destroy()
        except Exception as e:
            app_logger.error("خطأ عند الإغلاق: {}".format(e))
            self.destroy()
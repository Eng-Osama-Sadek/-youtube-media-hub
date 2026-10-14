"""
شبكة عرض النتائج — بأزرار تمرير مرئية (تعمل دايماً)
"""

import customtkinter as ctk

from core.search_engine import VideoResult
from ui.video_card import VideoCard
from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger


class ResultsGrid(ctk.CTkFrame):
    def __init__(self, master, on_download=None, on_copy_url=None, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_SECONDARY,
            corner_radius=Sizes.RADIUS_LG,
            **kwargs
        )
        
        self.on_download = on_download
        self.on_copy_url = on_copy_url
        self.cards = []
        self._columns = 3
        
        # ═══ Header ═══
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.header.pack(fill="x", padx=Sizes.SPACE_LG, pady=(Sizes.SPACE_LG, 0))
        
        self.title_label = ctk.CTkLabel(
            self.header, text="",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY,
        )
        self.title_label.pack(side="right")
        
        self.count_label = ctk.CTkLabel(
            self.header, text="",
            font=Fonts.small(),
            text_color=Colors.TEXT_MUTED,
        )
        self.count_label.pack(side="left")
        
        # ═══ Container للـ scroll + buttons ═══
        scroll_container = ctk.CTkFrame(self, fg_color="transparent")
        scroll_container.pack(
            fill="both", expand=True,
            padx=Sizes.SPACE_SM, pady=Sizes.SPACE_SM
        )
        
        # ✅ عمود أزرار التمرير على اليسار (RTL)
        nav_frame = ctk.CTkFrame(
            scroll_container,
            fg_color=Colors.BG_TERTIARY,
            corner_radius=Sizes.RADIUS_MD,
            width=50
        )
        nav_frame.pack(side="left", fill="y", padx=(0, 6))
        nav_frame.pack_propagate(False)
        
        # زر الأعلى
        ctk.CTkButton(
            nav_frame,
            text="▲",
            width=40, height=40,
            corner_radius=Sizes.RADIUS_SM,
            font=("Segoe UI", 18, "bold"),
            fg_color=Colors.ACCENT_START,
            hover_color=Colors.ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._scroll_up
        ).pack(pady=(10, 4))
        
        # مؤشر حالة
        ctk.CTkLabel(
            nav_frame,
            text="↕",
            font=("Segoe UI", 14),
            text_color=Colors.TEXT_MUTED
        ).pack(pady=4)
        
        # زر الأسفل
        ctk.CTkButton(
            nav_frame,
            text="▼",
            width=40, height=40,
            corner_radius=Sizes.RADIUS_SM,
            font=("Segoe UI", 18, "bold"),
            fg_color=Colors.ACCENT_START,
            hover_color=Colors.ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._scroll_down
        ).pack(pady=(4, 10))
        
        # ✅ Scrollable frame على اليمين
        self.scroll_frame = ctk.CTkScrollableFrame(
            scroll_container,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(side="right", fill="both", expand=True)
        
        self.scroll_frame.bind("<Configure>", self._on_resize)
        
        # ✅ Focus على الشبكة عشان الأسهم تشتغل
        try:
            self.scroll_frame.configure(takefocus=True)
            self.scroll_frame.bind(
                "<Button-1>",
                lambda e: self.scroll_frame.focus_set()
            )
        except Exception:
            pass
        
        # ✅ ربط عجلة الماوس
        self.after(300, self._bind_mousewheel)
    
    # ═══════════════════════════════════════════
    # 🎛️ Scroll handlers
    # ═══════════════════════════════════════════
    
    def _bind_mousewheel(self):
        """ربط عجلة الماوس والأسهم."""
        try:
            toplevel = self.winfo_toplevel()
            toplevel.bind("<MouseWheel>", self._on_mousewheel, add="+")
            toplevel.bind("<Button-4>", self._on_mousewheel, add="+")
            toplevel.bind("<Button-5>", self._on_mousewheel, add="+")
            app_logger.info("تم ربط scroll events")
        except Exception as e:
            app_logger.warning("فشل ربط scroll: {}".format(e))
    
    def _on_mousewheel(self, event):
        """تحريك بعجلة الماوس."""
        try:
            canvas = self.scroll_frame._parent_canvas
            if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
                canvas.yview_scroll(3, "units")
            elif event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
                canvas.yview_scroll(-3, "units")
        except Exception:
            pass
    
    def _scroll_up(self):
        """تمرير لأعلى."""
        try:
            self.scroll_frame._parent_canvas.yview_scroll(-8, "units")
        except Exception:
            pass
    
    def _scroll_down(self):
        """تمرير لأسفل."""
        try:
            self.scroll_frame._parent_canvas.yview_scroll(8, "units")
        except Exception:
            pass
    
    # ═══════════════════════════════════════════
    # 📋 حالات العرض
    # ═══════════════════════════════════════════
    
    def show_loading(self, message="جاري البحث..."):
        self.clear()
        loading = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        loading.pack(expand=True, fill="both", pady=100)
        ctk.CTkLabel(
            loading, text=message,
            font=Fonts.subheading(), text_color=Colors.TEXT_PRIMARY
        ).pack(pady=Sizes.SPACE_MD)
        bar = ctk.CTkProgressBar(
            loading, width=260, height=6, mode="indeterminate",
            progress_color=Colors.ACCENT_START, fg_color=Colors.BG_TERTIARY
        )
        bar.pack()
        bar.start()
        self._loading_bar = bar
    
    def show_empty(self, message="لا توجد نتائج"):
        self.clear()
        empty = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        empty.pack(expand=True, fill="both", pady=100)
        ctk.CTkLabel(
            empty, text=message,
            font=Fonts.subheading(), text_color=Colors.TEXT_PRIMARY
        ).pack(pady=Sizes.SPACE_MD)
    
    def show_welcome(self):
        self.clear()
        welcome = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        welcome.pack(expand=True, fill="both", pady=100)
        ctk.CTkLabel(
            welcome, text="ابدأ البحث عن أي محتوى تحبه",
            font=Fonts.subheading(), text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(Sizes.SPACE_MD, Sizes.SPACE_XS))
        ctk.CTkLabel(
            welcome, text="اكتب في شريط البحث فوق واضغط Enter",
            font=Fonts.body(), text_color=Colors.TEXT_SECONDARY
        ).pack()
    
    def display_results(self, results, query=""):
        self.clear()
        header_text = "نتائج البحث: {}".format(query) if query else "النتائج"
        self.title_label.configure(text=header_text)
        self.count_label.configure(text="{} نتيجة".format(len(results)))
        
        for video in results:
            card = VideoCard(
                self.scroll_frame, video=video,
                on_download=self.on_download,
                on_copy_url=self.on_copy_url,
            )
            self.cards.append(card)
        
        self._layout_cards()
        app_logger.info("تم عرض {} بطاقة".format(len(results)))
    
    def _on_resize(self, event=None):
        if not self.cards:
            return
        width = self.scroll_frame.winfo_width()
        if width <= 1:
            return
        card_total_width = Sizes.CARD_WIDTH + 20
        new_columns = max(1, width // card_total_width)
        if new_columns != self._columns:
            self._columns = new_columns
            self._layout_cards()
    
    def _layout_cards(self):
        if not self.cards:
            return
        cols = max(1, self._columns)
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            card.grid(
                row=row, column=col,
                padx=Sizes.SPACE_SM, pady=Sizes.SPACE_SM,
                sticky="nsew"
            )
        for c in range(cols):
            self.scroll_frame.grid_columnconfigure(c, weight=1)
    
    def clear(self):
        if hasattr(self, "_loading_bar"):
            try:
                self._loading_bar.stop()
            except Exception:
                pass
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.cards.clear()
        self.title_label.configure(text="")
        self.count_label.configure(text="")
"""
شبكة عرض النتائج — scrollable مع توزيع ديناميكي للبطاقات.
"""

from typing import Callable, Optional
import customtkinter as ctk

from core.search_engine import VideoResult
from ui.video_card import VideoCard
from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger


class ResultsGrid(ctk.CTkFrame):
    """منطقة عرض النتائج بشكل شبكة مرنة."""
    
    def __init__(
        self, master,
        on_download: Optional[Callable] = None,
        on_copy_url: Optional[Callable] = None,
        **kwargs
    ):
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
        
        # العنوان
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
        
        # منطقة التمرير
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=Sizes.SPACE_SM, pady=Sizes.SPACE_SM)
        
        self.scroll_frame.bind("<Configure>", self._on_resize)
    
    def show_loading(self, message: str = "جاري البحث...") -> None:
        self.clear()
        
        loading = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        loading.pack(expand=True, fill="both", pady=100)
        
        ctk.CTkLabel(loading, text="🔎", font=("Segoe UI Emoji", 56)).pack()
        
        ctk.CTkLabel(
            loading, text=message,
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=Sizes.SPACE_MD)
        
        bar = ctk.CTkProgressBar(
            loading, width=260, height=6,
            mode="indeterminate",
            progress_color=Colors.ACCENT_START,
            fg_color=Colors.BG_TERTIARY
        )
        bar.pack()
        bar.start()
        
        self._loading_bar = bar
    
    def show_empty(self, message: str = "لا توجد نتائج") -> None:
        self.clear()
        
        empty = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        empty.pack(expand=True, fill="both", pady=100)
        
        ctk.CTkLabel(empty, text="😕", font=("Segoe UI Emoji", 56)).pack()
        
        ctk.CTkLabel(
            empty, text=message,
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=Sizes.SPACE_MD)
    
    def show_welcome(self) -> None:
        self.clear()
        
        welcome = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        welcome.pack(expand=True, fill="both", pady=100)
        
        ctk.CTkLabel(welcome, text="🎬", font=("Segoe UI Emoji", 64)).pack()
        
        ctk.CTkLabel(
            welcome, text="ابدأ البحث عن أي محتوى تحبه",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(Sizes.SPACE_MD, Sizes.SPACE_XS))
        
        ctk.CTkLabel(
            welcome, text="اكتب في شريط البحث فوق واضغط Enter",
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY
        ).pack()
    
    def display_results(self, results, query: str = "") -> None:
        self.clear()
        
        header_text = f"نتائج البحث: {query}" if query else "النتائج"
        self.title_label.configure(text=header_text)
        self.count_label.configure(text=f"{len(results)} نتيجة")
        
        for video in results:
            card = VideoCard(
                self.scroll_frame,
                video=video,
                on_download=self.on_download,
                on_copy_url=self.on_copy_url,
            )
            self.cards.append(card)
        
        self._layout_cards()
        app_logger.info(f"تم عرض {len(results)} بطاقة")
    
    def _on_resize(self, event=None) -> None:
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
    
    def _layout_cards(self) -> None:
        if not self.cards:
            return
        
        cols = max(1, self._columns)
        
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            card.grid(
                row=row, column=col,
                padx=Sizes.SPACE_SM,
                pady=Sizes.SPACE_SM,
                sticky="nsew"
            )
        
        for c in range(cols):
            self.scroll_frame.grid_columnconfigure(c, weight=1)
    
    def clear(self) -> None:
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
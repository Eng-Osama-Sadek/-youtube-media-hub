"""
نظام التصميم المركزي — كل الألوان والخطوط والقياسات في مكان واحد.
"""

import customtkinter as ctk
from enum import Enum


class ThemeMode(Enum):
    """أوضاع الثيم المتاحة."""
    DARK = "dark"
    LIGHT = "light"


# ═══════════════════════════════════════════
# 🎨 لوحة الألوان
# ═══════════════════════════════════════════

class Colors:
    """كل ألوان التطبيق — بنظام Dark Mode احترافي."""
    
    # === الخلفيات ===
    BG_PRIMARY     = "#0F0F14"
    BG_SECONDARY   = "#1A1A24"
    BG_TERTIARY    = "#242430"
    BG_HOVER       = "#2A2A38"
    BG_INPUT       = "#1E1E2A"
    
    # === لون التمييز ===
    ACCENT_START   = "#FF0055"
    ACCENT_END     = "#7B2FF7"
    ACCENT_HOVER   = "#FF3377"
    ACCENT_PRESSED = "#CC0044"
    
    # === النصوص ===
    TEXT_PRIMARY   = "#FFFFFF"
    TEXT_SECONDARY = "#B0B0C0"
    TEXT_MUTED     = "#6C6C80"
    TEXT_ACCENT    = "#FF0055"
    
    # === الحالات ===
    SUCCESS        = "#22C55E"
    WARNING        = "#F59E0B"
    ERROR          = "#EF4444"
    INFO           = "#3B82F6"
    
    # === الحدود ===
    BORDER         = "#2D2D3D"
    BORDER_FOCUS   = "#7B2FF7"
    
    @staticmethod
    def accent_gradient():
        return (Colors.ACCENT_START, Colors.ACCENT_END)


# ═══════════════════════════════════════════
# 🔤 الخطوط
# ═══════════════════════════════════════════

class Fonts:
    """كل الخطوط المستخدمة في التطبيق."""
    
    FAMILY          = "Cairo"
    FAMILY_FALLBACK = "Segoe UI"
    
    SIZE_XS    = 11
    SIZE_SM    = 12
    SIZE_BASE  = 14
    SIZE_MD    = 16
    SIZE_LG    = 20
    SIZE_XL    = 26
    SIZE_XXL   = 34
    SIZE_TITLE = 44
    
    @classmethod
    def title(cls):      return (cls.FAMILY, cls.SIZE_TITLE, "bold")
    @classmethod
    def heading(cls):    return (cls.FAMILY, cls.SIZE_XXL, "bold")
    @classmethod
    def subheading(cls): return (cls.FAMILY, cls.SIZE_XL, "bold")
    @classmethod
    def body(cls):       return (cls.FAMILY, cls.SIZE_BASE, "normal")
    @classmethod
    def body_bold(cls):  return (cls.FAMILY, cls.SIZE_BASE, "bold")
    @classmethod
    def small(cls):      return (cls.FAMILY, cls.SIZE_SM, "normal")
    @classmethod
    def small_bold(cls): return (cls.FAMILY, cls.SIZE_SM, "bold")
    @classmethod
    def tiny(cls):       return (cls.FAMILY, cls.SIZE_XS, "normal")
    @classmethod
    def button(cls):     return (cls.FAMILY, cls.SIZE_MD, "bold")


# ═══════════════════════════════════════════
# 📐 القياسات
# ═══════════════════════════════════════════

class Sizes:
    """كل القياسات في مكان واحد."""
    
    SPACE_XS  = 4
    SPACE_SM  = 8
    SPACE_MD  = 12
    SPACE_LG  = 16
    SPACE_XL  = 24
    SPACE_XXL = 32
    
    RADIUS_SM = 8
    RADIUS_MD = 12
    RADIUS_LG = 16
    RADIUS_XL = 24
    
    INPUT_HEIGHT  = 48
    BUTTON_HEIGHT = 48
    BUTTON_SMALL  = 36
    
    CARD_WIDTH  = 280
    CARD_HEIGHT = 320
    THUMBNAIL_H = 158
    
    WINDOW_MIN_W = 1100
    WINDOW_MIN_H = 700
    WINDOW_DEF_W = 1280
    WINDOW_DEF_H = 800


# ═══════════════════════════════════════════
# 🚀 إعداد CustomTkinter
# ═══════════════════════════════════════════

def apply_theme(mode: ThemeMode = ThemeMode.DARK) -> None:
    """تطبيق الثيم على التطبيق بالكامل."""
    ctk.set_appearance_mode(mode.value)
    ctk.set_default_color_theme("dark-blue")
    
    ctk.ThemeManager.theme["CTkButton"]["corner_radius"] = Sizes.RADIUS_MD
    ctk.ThemeManager.theme["CTkEntry"]["corner_radius"] = Sizes.RADIUS_MD
    ctk.ThemeManager.theme["CTkFrame"]["corner_radius"] = Sizes.RADIUS_LG
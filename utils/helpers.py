"""
دوال مساعدة عامة — تنسيق الوقت، الأحجام، النصوص، إلخ.
"""

import re
from pathlib import Path
from typing import Optional


def format_duration(seconds: Optional[int]) -> str:
    """
    تحويل الثواني إلى صيغة (HH:MM:SS) أو (MM:SS).
    """
    if not seconds or seconds < 0:
        return "00:00"
    
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_filesize(bytes_size: Optional[int]) -> str:
    """
    تحويل الحجم بالبايت إلى صيغة مقروءة (KB, MB, GB).
    """
    if not bytes_size or bytes_size < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def format_views(views: Optional[int]) -> str:
    """
    تنسيق عدد المشاهدات بشكل مختصر (1.2M, 350K).
    """
    if not views:
        return "0"
    
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


def sanitize_filename(filename: str) -> str:
    """
    تنظيف اسم الملف من الرموز غير المسموح بها في أنظمة الملفات.
    """
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename[:200]


def format_speed(bytes_per_sec: Optional[float]) -> str:
    """
    تنسيق سرعة التحميل (MB/s, KB/s).
    """
    if not bytes_per_sec or bytes_per_sec <= 0:
        return "0 KB/s"
    
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    return f"{bytes_per_sec / 1024:.1f} KB/s"


def format_eta(seconds: Optional[int]) -> str:
    """
    تنسيق الوقت المتبقي للتحميل.
    """
    if not seconds or seconds <= 0:
        return "غير معروف"
    
    if seconds < 60:
        return f"{seconds} ثانية"
    if seconds < 3600:
        return f"{seconds // 60} دقيقة"
    return f"{seconds // 3600} ساعة"


def ensure_directory(path: str) -> Path:
    """
    التأكد من وجود مجلد معين، وإنشائه إذا لم يكن موجوداً.
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
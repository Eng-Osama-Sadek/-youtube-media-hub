"""
فحص وجود ffmpeg على النظام — ضروري لدمج الصوت مع الفيديو.
متوافق مع Python 3.7+
"""

import shutil
import subprocess
from typing import Tuple

from utils.logger import app_logger


def is_ffmpeg_installed() -> bool:
    """
    التحقق من تثبيت ffmpeg على النظام.
    """
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_version() -> str:
    """
    جلب إصدار ffmpeg المثبت.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            first_line = result.stdout.split("\n")[0]
            return first_line
        return "غير معروف"
    except Exception as e:
        app_logger.error(f"خطأ في قراءة إصدار ffmpeg: {e}")
        return "خطأ في القراءة"


def check_ffmpeg() -> Tuple[bool, str]:
    """
    فحص شامل لـ ffmpeg وإرجاع النتيجة مع رسالة مناسبة.
    """
    if is_ffmpeg_installed():
        version = get_ffmpeg_version()
        app_logger.info(f"✅ ffmpeg مثبت: {version}")
        return True, "ffmpeg مثبت بنجاح"
    
    app_logger.warning("⚠️ ffmpeg غير موجود على النظام")
    message = (
        "⚠️ ffmpeg غير مثبت على جهازك!\n\n"
        "بدون ffmpeg، لن يمكنك دمج الصوت مع الفيديو بجودة عالية.\n\n"
        "للتثبيت:\n"
        "  • Windows: حمّله من https://ffmpeg.org/download.html وأضفه للـ PATH\n"
        "  • Linux: sudo apt install ffmpeg\n"
        "  • Mac: brew install ffmpeg"
    )
    return False, message


def needs_ffmpeg(format_type: str, quality: str) -> bool:
    """
    تحديد هل العملية تحتاج ffmpeg أم لا.
    """
    if format_type == "mp3":
        return True
    return True
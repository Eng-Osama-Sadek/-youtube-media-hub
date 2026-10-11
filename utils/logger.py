"""
نظام التسجيل (Logging) — يسجل كل الأحداث في ملف logs.txt
مع إظهارها أيضاً في الـ Console أثناء التطوير.
"""

import logging
from datetime import datetime
from pathlib import Path


# مسار ملف السجلات (بجانب التطبيق)
LOG_FILE = Path(__file__).parent.parent / "logs.txt"


def setup_logger(name: str = "YouTubeMediaHub") -> logging.Logger:
    """
    إنشاء وتكوين logger جاهز للاستخدام.
    
    Args:
        name: اسم الـ logger
        
    Returns:
        logging.Logger: كائن الـ logger المكون
    """
    logger = logging.getLogger(name)
    
    # لو تم تكوينه قبل كده، رجّعه كما هو
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # === الصيغة الموحدة للرسائل ===
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] → %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # === Handler 1: الكتابة في ملف ===
    try:
        file_handler = logging.FileHandler(
            LOG_FILE, 
            mode="a", 
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️ لم نتمكن من إنشاء ملف السجلات: {e}")
    
    # === Handler 2: الطباعة في الـ Console ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# إنشاء logger عام يستخدم في كل المشروع
app_logger = setup_logger()


def log_separator(message: str = "") -> None:
    """يضيف فاصل واضح في ملف السجلات لتسهيل القراءة."""
    separator = "═" * 60
    app_logger.info(f"\n{separator}\n  {message}\n{separator}")


def log_startup() -> None:
    """تسجيل بداية تشغيل التطبيق."""
    log_separator(f"🚀 بدء تشغيل التطبيق — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def log_shutdown() -> None:
    """تسجيل إغلاق التطبيق."""
    log_separator(f"🛑 إغلاق التطبيق — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
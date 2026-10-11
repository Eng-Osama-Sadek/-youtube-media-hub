"""
إشعارات سطح المكتب عند اكتمال التحميلات.
"""

from plyer import notification
from utils.logger import app_logger


def send_notification(
    title: str,
    message: str,
    timeout: int = 5
) -> None:
    """
    إرسال إشعار لسطح المكتب.
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="YouTube Media Hub",
            timeout=timeout
        )
        app_logger.info(f"📢 إشعار: {title} — {message}")
    except Exception as e:
        app_logger.warning(f"فشل إرسال الإشعار: {e}")


def notify_download_complete(filename: str) -> None:
    """إشعار اكتمال تحميل."""
    send_notification(
        title="✅ اكتمل التحميل",
        message=f"تم تحميل: {filename}"
    )


def notify_download_failed(filename: str, error: str = "") -> None:
    """إشعار فشل تحميل."""
    send_notification(
        title="❌ فشل التحميل",
        message=f"فشل تحميل: {filename}\n{error}"
    )
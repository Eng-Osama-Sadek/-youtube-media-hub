"""
محرك التحميل — يتحكم في عملية تحميل فيديو واحد.
يدعم: ffmpeg، H.264، تخطي قيود يوتيوب.
"""

import os
import shutil
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import yt_dlp

from utils.logger import app_logger
from utils.helpers import format_filesize, format_speed, format_eta


# ═══════════════════════════════════════════
# 🔍 اكتشاف ffmpeg
# ═══════════════════════════════════════════

def _find_ffmpeg():
    try:
        import imageio_ffmpeg
        path = imageio_ffmpeg.get_ffmpeg_exe()
        if path and os.path.exists(path):
            app_logger.info("ffmpeg: {}".format(path))
            return path
    except Exception:
        pass

    path = shutil.which("ffmpeg")
    if path:
        return path

    for c in [r"C:\ffmpeg\bin\ffmpeg.exe", os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe")]:
        if os.path.exists(c):
            return c

    app_logger.warning("ffmpeg not found")
    return None


FFMPEG_PATH = _find_ffmpeg()


# ═══════════════════════════════════════════
# 🍪 ملف Cookies (لو موجود)
# ═══════════════════════════════════════════

def _find_cookies():
    """ابحث عن ملف cookies.txt في المشروع."""
    for name in ["cookies.txt", "youtube_cookies.txt", "www.youtube.com_cookies.txt"]:
        if os.path.exists(name):
            app_logger.info("cookies: {}".format(name))
            return name
    return None


COOKIES_FILE = _find_cookies()


# ═══════════════════════════════════════════
# 📊 الحالات
# ═══════════════════════════════════════════

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    status: DownloadStatus = DownloadStatus.PENDING
    percent: float = 0.0
    downloaded: int = 0
    total: int = 0
    speed: float = 0.0
    eta: int = 0
    filename: str = ""
    error: str = ""
    stage_text: str = ""

    @property
    def downloaded_str(self):
        return format_filesize(self.downloaded)

    @property
    def total_str(self):
        return format_filesize(self.total)

    @property
    def speed_str(self):
        return format_speed(self.speed)

    @property
    def eta_str(self):
        return format_eta(self.eta)


@dataclass
class DownloadOptions:
    quality: str = "720p"
    format_type: str = "mp4"
    output_dir: str = ""
    audio_only: bool = False


# ═══════════════════════════════════════════
# 🎯 محرك التحميل
# ═══════════════════════════════════════════

class Downloader:
    """محرك تحميل فيديو واحد."""

    def __init__(
        self,
        url: str,
        options: DownloadOptions,
        title: str = "",
        video_id: str = "",
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        self.url = url
        self.options = options
        self.title = title
        self.video_id = video_id
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error

        self._thread = None
        self._cancel_flag = False
        self.progress = DownloadProgress()
        self.output_path = ""

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._cancel_flag = False
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel_flag = True

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    # ═══════════════════════════════════════════
    # 🔧 العمل الفعلي
    # ═══════════════════════════════════════════

    def _worker(self):
        try:
            self.progress.status = DownloadStatus.DOWNLOADING
            self.progress.stage_text = "جاري التحميل..."
            self._emit()

            fmt = self._build_format()

            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(self.options.output_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [self._hook],
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "retries": 10,
                "fragment_retries": 10,
                "socket_timeout": 30,
                "concurrent_fragment_downloads": 4,
                "merge_output_format": "mp4",
                "windowsfilenames": True,
                "age_limit": 99,
                "geo_bypass": True,
                "noplaylist": True,
                
                # ✅ تخطي قيود يوتيوب (مهم!)
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "web_safari", "tv_embedded"],
                        "skip": ["hls", "dash"],
                    }
                },
                
                # ✅ تجنب 403
                "http_headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                },
            }

            # ✅ ffmpeg
            if FFMPEG_PATH:
                ydl_opts["ffmpeg_location"] = FFMPEG_PATH
                app_logger.info("استخدام ffmpeg: {}".format(FFMPEG_PATH))

            # ✅ cookies (لو موجود)
            if COOKIES_FILE:
                ydl_opts["cookiefile"] = COOKIES_FILE
                app_logger.info("استخدام cookies: {}".format(COOKIES_FILE))

            # صوت فقط
            if self.options.audio_only or self.options.format_type in ("mp3", "m4a"):
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.options.format_type if self.options.format_type != "mp4" else "mp3",
                    "preferredquality": "192",
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if info:
                    fn = ydl.prepare_filename(info)
                    base, _ = os.path.splitext(fn)
                    for ext in ("mp4", "mkv", "webm", "mp3", "m4a"):
                        c = base + "." + ext
                        if os.path.exists(c):
                            fn = c
                            break
                    self.output_path = fn
                    self.progress.filename = os.path.basename(fn)

            if self._cancel_flag:
                self.progress.status = DownloadStatus.CANCELLED
                self.progress.stage_text = "ملغي"
                self._emit()
                return

            self.progress.status = DownloadStatus.COMPLETED
            self.progress.percent = 100.0
            self.progress.stage_text = "اكتمل"
            self._emit()

            if self.on_complete:
                self.on_complete(self.output_path)

        except yt_dlp.utils.DownloadError as e:
            if self._cancel_flag:
                self.progress.status = DownloadStatus.CANCELLED
                self._emit()
                return
            self._err(self._clean(str(e)))
        except Exception as e:
            self._err(str(e))

    def _build_format(self):
        """صيغة التحميل — H.264 للموافقة مع Windows."""
        if self.options.audio_only or self.options.format_type in ("mp3", "m4a"):
            return "bestaudio/best"

        h = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}.get(
            self.options.quality, 720
        )

        fmt = (
            "bestvideo[height<={h}][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
            "bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<={h}][vcodec^=avc1]+bestaudio/"
            "bestvideo[height<={h}]+bestaudio/"
            "best[height<={h}]/"
            "best"
        ).format(h=h)
        return fmt

    def _hook(self, d):
        if self._cancel_flag:
            raise yt_dlp.utils.DownloadError("cancelled")

        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            dl = d.get("downloaded_bytes", 0)
            self.progress.percent = (dl / total * 100) if total > 0 else 0
            self.progress.downloaded = dl
            self.progress.total = total
            self.progress.speed = d.get("speed") or 0
            self.progress.eta = d.get("eta") or 0
            self._emit()
        elif d.get("status") == "finished":
            self.progress.status = DownloadStatus.PROCESSING
            self.progress.percent = 100.0
            self.progress.stage_text = "جاري المعالجة..."
            self._emit()

    def _emit(self):
        if self.on_progress:
            try:
                self.on_progress(self.progress)
            except Exception:
                pass

    def _err(self, msg):
        self.progress.status = DownloadStatus.FAILED
        self.progress.error = msg
        self.progress.stage_text = "فشل"
        self._emit()
        app_logger.error("فشل التحميل: {}".format(msg))
        if self.on_error:
            self.on_error(msg)

    @staticmethod
    def _clean(raw):
        raw = raw.replace("ERROR: ", "").strip()
        if "Please sign in" in raw:
            return "يوتيوب يطلب تسجيل دخول — جرب تحميل فيديو آخر"
        if "403" in raw:
            return "خطأ 403 — جرب مرة أخرى أو غيّر الشبكة"
        if "Video unavailable" in raw:
            return "الفيديو غير متاح"
        if "Private" in raw:
            return "الفيديو خاص"
        if "urlopen" in raw or "getaddrinfo" in raw:
            return "فشل الاتصال بالإنترنت"
        if "ffmpeg" in raw.lower():
            return "خطأ في ffmpeg"
        return raw[:200]
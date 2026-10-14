"""
مشغل فيديو يوتيوب مدمج — يستخدم VLC للصوت المضمون
"""

import os
import threading
import tempfile
import subprocess
import sys

import customtkinter as ctk
import yt_dlp

from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger


def find_vlc():
    """البحث عن VLC على النظام."""
    paths = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\VideoLAN\VLC\vlc.exe"),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


VLC_PATH = find_vlc()


class VideoPlayerModal(ctk.CTkToplevel):
    def __init__(self, master, video_url, video_title="",
                 quality="360", streaming=True):
        super().__init__(master)
        self.video_url = video_url
        self.video_title = video_title
        self.quality = str(quality) if quality else "360"
        self.streaming = streaming
        self.video_file = None
        self.stream_url = None

        self.title("مشغل الفيديو")
        self.geometry("600x400")
        self.configure(fg_color=Colors.BG_PRIMARY)
        self.transient(master)

        self.update_idletasks()
        w = 600
        h = 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))

        self._build_ui()
        self._load_video()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=Colors.BG_SECONDARY, height=50)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=self.video_title[:80] or "مشغل الفيديو",
            font=Fonts.body_bold(),
            text_color=Colors.TEXT_PRIMARY,
            anchor="e"
        ).pack(side="right", padx=Sizes.SPACE_LG, fill="x", expand=True)

        ctk.CTkButton(
            header, text="X", width=40, height=36,
            corner_radius=Sizes.RADIUS_MD,
            fg_color=Colors.BG_TERTIARY,
            hover_color=Colors.ERROR,
            command=self._close
        ).pack(side="left", padx=Sizes.SPACE_MD)

        main = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        main.pack(fill="both", expand=True)

        mode = "فوري" if self.streaming else "تحميل"
        self.status_label = ctk.CTkLabel(
            main,
            text="جاري التحضير ({})...\nالجودة: {}p\n\nسيتم التشغيل في VLC".format(mode, self.quality),
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY,
            justify="center"
        )
        self.status_label.pack(expand=True)

        self.progress_bar = ctk.CTkProgressBar(
            main, width=400, height=8,
            progress_color=Colors.ACCENT_START,
            fg_color=Colors.BG_TERTIARY
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        if self.streaming:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()

    def _load_video(self):
        t = threading.Thread(target=self._worker, daemon=True)
        t.start()

    def _worker(self):
        error_msg = None
        try:
            if self.streaming:
                self._stream_worker()
            else:
                self._download_worker()
        except Exception as e:
            error_msg = str(e)
            app_logger.error("فشل: {}".format(e))

        if error_msg:
            self.after(0, lambda m=error_msg: self._show_error(m))

    def _stream_worker(self):
        try:
            q = int(self.quality)
        except Exception:
            q = 360

        opts = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "skip_download": True,
            "format": "best",
        }

        try:
            import imageio_ffmpeg
            opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

        if os.path.exists("cookies.txt"):
            opts["cookiefile"] = "cookies.txt"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(self.video_url, download=False)
            stream_url = None
            if info.get("url"):
                stream_url = info["url"]
            elif info.get("formats"):
                formats = info.get("formats", [])
                progressive = [
                    f for f in formats
                    if f.get("url")
                    and f.get("acodec") not in (None, "none")
                    and f.get("vcodec") not in (None, "none")
                ]
                if progressive:
                    progressive.sort(key=lambda x: x.get("height") or 0, reverse=True)
                    stream_url = progressive[0]["url"]
                else:
                    for f in reversed(formats):
                        if f.get("url"):
                            stream_url = f["url"]
                            break

            if not stream_url:
                raise Exception("لا يوجد رابط بث متاح")

            self.stream_url = stream_url

        self.after(0, self._play_in_vlc)

    def _download_worker(self):
        try:
            q = int(self.quality)
        except Exception:
            q = 360

        qf = q + 240
        temp_dir = tempfile.gettempdir()
        output_template = os.path.join(temp_dir, "yt_video_%(id)s.%(ext)s")

        opts = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "outtmpl": output_template,
            "progress_hooks": [self._progress_hook],
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "concurrent_fragment_downloads": 10,
        }

        try:
            import imageio_ffmpeg
            opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

        if os.path.exists("cookies.txt"):
            opts["cookiefile"] = "cookies.txt"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(self.video_url, download=True)
            if info:
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                for ext in ("mp4", "mkv", "webm"):
                    candidate = base + "." + ext
                    if os.path.exists(candidate):
                        self.video_file = candidate
                        break
                if not self.video_file and os.path.exists(filename):
                    self.video_file = filename

        if self.video_file and os.path.exists(self.video_file):
            self.after(0, self._play_in_vlc)
        else:
            raise Exception("لم يتم العثور على الملف")

    def _progress_hook(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            dl = d.get("downloaded_bytes", 0)
            if total > 0:
                percent = dl / total
                speed = d.get("speed") or 0
                speed_mb = speed / (1024 * 1024) if speed else 0
                try:
                    self.after(0, lambda p=percent, s=speed_mb: self._update_ui(p, s))
                except Exception:
                    pass

    def _update_ui(self, percent, speed):
        try:
            self.progress_bar.set(percent)
            self.status_label.configure(
                text="جاري التحميل... ({}p)\nسرعة: {:.1f} MB/s".format(
                    self.quality, speed
                )
            )
        except Exception:
            pass

    def _play_in_vlc(self):
        target = self.stream_url if self.streaming else self.video_file

        if not VLC_PATH:
            self._show_error(
                "VLC Player غير مثبت!\n\n"
                "حمله من: https://www.videolan.org/vlc/"
            )
            return

        try:
            subprocess.Popen([VLC_PATH, target])
            app_logger.info("تم التشغيل في VLC")
            self.after(500, self.destroy)
        except Exception as e:
            app_logger.error("فشل VLC: {}".format(e))
            self._show_error(str(e))

    def _show_error(self, error):
        try:
            self.status_label.configure(
                text="خطأ: {}".format(error),
                text_color=Colors.ERROR
            )
            self.progress_bar.pack_forget()
        except Exception:
            pass

    def _close(self):
        try:
            self.destroy()
        except Exception:
            pass
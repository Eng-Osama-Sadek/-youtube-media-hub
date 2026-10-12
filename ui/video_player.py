"""مشغل فيديو يوتيوب مدمج  بحل مشكلة الصوت."""
import os
import threading
import tempfile
import customtkinter as ctk
import yt_dlp
from ui.theme import Colors, Fonts, Sizes
from utils.logger import app_logger


class VideoPlayerModal(ctk.CTkToplevel):
    def __init__(self, master, video_url, video_title=""):
        super().__init__(master)
        self.video_url = video_url
        self.video_title = video_title
        self.video_file = None
        self.title("مشغل الفيديو")
        self.geometry("900x600")
        self.configure(fg_color=Colors.BG_PRIMARY)
        self.transient(master)
        self.update_idletasks()
        w = 900
        h = 600
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
            header,
            text="X",
            width=40,
            height=36,
            corner_radius=Sizes.RADIUS_MD,
            fg_color=Colors.BG_TERTIARY,
            hover_color=Colors.ERROR,
            command=self._close
        ).pack(side="left", padx=Sizes.SPACE_MD)

        self.player_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self.player_frame.pack(fill="both", expand=True)

        # شريط الحالة + التقدم
        self.status_label = ctk.CTkLabel(
            self.player_frame,
            text=" جاري تحضير الفيديو...\nقد يأخذ بضع ثوان حسب سرعة الإنترنت",
            font=Fonts.subheading(),
            text_color=Colors.TEXT_PRIMARY,
            justify="center"
        )
        self.status_label.pack(expand=True)

        self.progress_bar = ctk.CTkProgressBar(
            self.player_frame,
            width=400,
            height=8,
            progress_color=Colors.ACCENT_START,
            fg_color=Colors.BG_TERTIARY
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

    def _load_video(self):
        t = threading.Thread(target=self._worker, daemon=True)
        t.start()

    def _worker(self):
        """تحميل الفيديو + الصوت مدمجين في ملف مؤقت."""
        try:
            # ملف مؤقت للإخراج
            temp_dir = tempfile.gettempdir()
            output_template = os.path.join(temp_dir, "yt_video_%(id)s.%(ext)s")

            # خيارات التحميل
            opts = {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "outtmpl": output_template,
                "progress_hooks": [self._progress_hook],
                #  الحل: تحميل أفضل فيديو + أفضل صوت ودمجهم
                "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "merge_output_format": "mp4",
            }

            # ffmpeg للدمج
            try:
                import imageio_ffmpeg
                opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass

            # cookies
            if os.path.exists("cookies.txt"):
                opts["cookiefile"] = "cookies.txt"

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.video_url, download=True)

                # إيجاد اسم الملف النهائي
                if info:
                    filename = ydl.prepare_filename(info)
                    # الملف قد يتحول mp4 بعد الدمج
                    base, _ = os.path.splitext(filename)
                    for ext in ("mp4", "mkv", "webm"):
                        candidate = base + "." + ext
                        if os.path.exists(candidate):
                            self.video_file = candidate
                            break

                    # fallback
                    if not self.video_file and os.path.exists(filename):
                        self.video_file = filename

            if self.video_file and os.path.exists(self.video_file):
                app_logger.info(" تم تحضير الفيديو: {}".format(self.video_file))
                self.after(0, self._start_player)
            else:
                self.after(0, lambda: self._show_error("لم يتم العثور على الملف"))

        except Exception as e:
            error_msg = str(e)
            app_logger.error("فشل التحميل: {}".format(e))
            self.after(0, lambda m=error_msg: self._show_error(m))

    def _progress_hook(self, d):
        """تحديث شريط التقدم."""
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            dl = d.get("downloaded_bytes", 0)
            if total > 0:
                percent = dl / total
                # تحديث الواجهة بأمان
                try:
                    self.after(0, lambda p=percent: self.progress_bar.set(p))
                    speed = d.get("speed") or 0
                    speed_mb = speed / (1024 * 1024) if speed else 0
                    try:
                        self.after(0, lambda s=speed_mb: self.status_label.configure(
                            text=" جاري التحميل...\nسرعة: {:.1f} MB/s".format(s)
                        ))
                    except Exception:
                        pass
                except Exception:
                    pass

        elif d.get("status") == "finished":
            try:
                self.after(0, lambda: self.status_label.configure(
                    text=" جاري دمج الفيديو مع الصوت..."
                ))
            except Exception:
                pass

    def _start_player(self):
        """تشغيل الفيديو من الملف المحلي."""
        self.status_label.pack_forget()
        self.progress_bar.pack_forget()

        # تحويل المسار إلى file:// URL
        video_url = "file:///" + self.video_file.replace("\\", "/").replace(" ", "%20")

        html = (
            '<!DOCTYPE html><html><head><meta charset="UTF-8">'
            '<style>'
            '*{margin:0;padding:0;box-sizing:border-box}'
            'body{background:#000;overflow:hidden}'
            'video{width:100vw;height:100vh;object-fit:contain}'
            '</style></head><body>'
            '<video controls autoplay src="' + video_url + '"></video>'
            '</body></html>'
        )

        temp_html = os.path.join(tempfile.gettempdir(), "yt_player.html")
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html)

        try:
            import webview
            webview.create_window(
                title=self.video_title[:80] or "مشغل الفيديو",
                url="file:///" + temp_html.replace("\\", "/"),
                width=900,
                height=560,
                background_color="#000000"
            )
            self.destroy()
            webview.start()
        except ImportError:
            self._show_error("ثبت pywebview: pip install pywebview")
        except Exception as e:
            app_logger.error("فشل: {}".format(e))
            self._show_error(str(e))

    def _show_error(self, error):
        try:
            self.status_label.configure(
                text=" خطأ: {}\n\nجرب مرة أخرى".format(error),
                text_color=Colors.ERROR
            )
            self.progress_bar.pack_forget()
        except Exception:
            pass

    def _close(self):
        """إغلاق + حذف الملف المؤقت."""
        try:
            if self.video_file and os.path.exists(self.video_file):
                os.remove(self.video_file)
        except Exception:
            pass
        self.destroy()
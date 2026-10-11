"""
محرك البحث في يوتيوب — يستخدم yt-dlp لجلب النتائج بسرعة وبدون API key.
"""

import threading
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import urlparse, parse_qs

import yt_dlp
from utils.logger import app_logger


# ═══════════════════════════════════════════
# 📦 نموذج البيانات
# ═══════════════════════════════════════════

@dataclass
class VideoResult:
    """يمثل فيديو واحد من نتائج البحث."""
    video_id: str
    title: str
    channel: str
    duration: int
    views: int
    upload_date: str
    thumbnail: str
    url: str
    description: str = ""
    
    @property
    def short_url(self) -> str:
        return f"https://youtu.be/{self.video_id}"
    
    @property
    def formatted_upload_date(self) -> str:
        if not self.upload_date or len(self.upload_date) != 8:
            return "غير معروف"
        y, m, d = self.upload_date[:4], self.upload_date[4:6], self.upload_date[6:8]
        return f"{d}/{m}/{y}"


# ═══════════════════════════════════════════
# 🎯 الفلاتر
# ═══════════════════════════════════════════

FILTER_KEYWORDS = {
    "الكل":     "",
    "أفلام":    "فيلم كامل",
    "رياضة":    "مباراة رياضية",
    "أخبار":    "أخبار",
    "كارتون":   "كرتون أطفال",
    "أغاني":    "أغنية",
    "تعليمي":   "شرح تعليمي",
    "ترفيه":    "ترفيه",
}


def extract_video_id(url: str) -> Optional[str]:
    """استخراج معرّف الفيديو من رابط يوتيوب."""
    try:
        parsed = urlparse(url)
        
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/").split("/")[0]
        
        if "youtube.com" in parsed.netloc:
            if "/shorts/" in parsed.path:
                return parsed.path.split("/shorts/")[1].split("/")[0]
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [None])[0]
        
        return None
    except Exception:
        return None


def is_youtube_url(text: str) -> bool:
    return extract_video_id(text) is not None


# ═══════════════════════════════════════════
# 🔍 محرك البحث
# ═══════════════════════════════════════════

class SearchEngine:
    """محرك البحث — بيلف في Thread منفصل."""
    
    def __init__(self):
        self._current_thread = None
        self._cancel_flag = False
    
    def _build_ydl_options(self, extract_flat: bool = True) -> dict:
        return {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": extract_flat,
            "skip_download": True,
            "ignoreerrors": True,
            "nocheckcertificate": True,
            "socket_timeout": 15,
            "default_search": "ytsearch",
        }
    
    def search(
        self,
        query: str,
        filter_type: str = "الكل",
        max_results: int = 20,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_progress: Optional[Callable] = None,
    ) -> None:
        """بدء البحث في Thread منفصل."""
        self._cancel_flag = False
        
        self._current_thread = threading.Thread(
            target=self._search_worker,
            args=(query, filter_type, max_results, on_success, on_error, on_progress),
            daemon=True
        )
        self._current_thread.start()
    
    def _search_worker(
        self, query, filter_type, max_results,
        on_success, on_error, on_progress,
    ) -> None:
        try:
            if on_progress:
                on_progress("جاري الاتصال بيوتيوب...")
            
            results = []
            
            # حالة 1: رابط مباشر
            video_id = extract_video_id(query)
            if video_id:
                if on_progress:
                    on_progress("جاري تحميل بيانات الفيديو...")
                
                video = self._fetch_single_video(query)
                if video:
                    results.append(video)
                else:
                    if on_error:
                        on_error("تعذّر جلب بيانات هذا الرابط.")
                    return
            else:
                # حالة 2: بحث عادي
                keyword = FILTER_KEYWORDS.get(filter_type, "")
                search_query = f"{query} {keyword}".strip()
                
                if on_progress:
                    on_progress("جاري البحث في يوتيوب...")
                
                results = self._search_youtube(search_query, max_results)
            
            if self._cancel_flag:
                app_logger.info("تم إلغاء البحث")
                return
            
            if not results:
                if on_error:
                    on_error("لا توجد نتائج مطابقة لبحثك.")
                return
            
            app_logger.info(f"✅ تم العثور على {len(results)} نتيجة")
            if on_success:
                on_success(results)
        
        except Exception as e:
            app_logger.error(f"خطأ أثناء البحث: {e}")
            if on_error:
                on_error(f"حدث خطأ: {str(e)}")
    
    def _search_youtube(self, query: str, max_results: int) -> list:
        """تنفيذ البحث الفعلي."""
        results = []
        
        options = self._build_ydl_options(extract_flat=True)
        options["playlistend"] = max_results
        
        search_url = f"ytsearch{max_results}:{query}"
        
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(search_url, download=False)
                
                if not info or "entries" not in info:
                    return []
                
                for entry in info["entries"]:
                    if self._cancel_flag:
                        break
                    if not entry:
                        continue
                    
                    thumb = self._pick_thumbnail(entry)
                    
                    video = VideoResult(
                        video_id=entry.get("id", ""),
                        title=entry.get("title", "بدون عنوان"),
                        channel=entry.get("uploader") or entry.get("channel") or "قناة غير معروفة",
                        duration=int(entry.get("duration") or 0),
                        views=int(entry.get("view_count") or 0),
                        upload_date=self._format_upload_date(entry.get("upload_date", "")),
                        thumbnail=thumb,
                        url=f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        description=(entry.get("description") or "")[:200],
                    )
                    results.append(video)
        
        except Exception as e:
            app_logger.error(f"خطأ في البحث: {e}")
            raise
        
        return results
    
    def _fetch_single_video(self, url: str):
        """جلب بيانات فيديو واحد من رابط مباشر."""
        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "nocheckcertificate": True,
        }
        
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                
                thumb = self._pick_thumbnail(info)
                
                return VideoResult(
                    video_id=info.get("id", ""),
                    title=info.get("title", "بدون عنوان"),
                    channel=info.get("uploader") or "غير معروف",
                    duration=int(info.get("duration") or 0),
                    views=int(info.get("view_count") or 0),
                    upload_date=self._format_upload_date(info.get("upload_date", "")),
                    thumbnail=thumb,
                    url=info.get("webpage_url", url),
                    description=(info.get("description") or "")[:200],
                )
        except Exception as e:
            app_logger.error(f"فشل جلب الفيديو: {e}")
            return None
    
    @staticmethod
    def _pick_thumbnail(entry: dict) -> str:
        thumbnails = entry.get("thumbnails") or []
        if thumbnails:
            valid = [t for t in thumbnails if t.get("url")]
            if valid:
                valid.sort(key=lambda x: x.get("width") or 0, reverse=True)
                return valid[0]["url"]
        
        if entry.get("thumbnail"):
            return entry["thumbnail"]
        
        vid = entry.get("id", "")
        if vid:
            return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        
        return ""
    
    @staticmethod
    def _format_upload_date(date_str: str) -> str:
        if date_str and len(date_str) == 8 and date_str.isdigit():
            return date_str
        return ""
    
    def cancel(self) -> None:
        self._cancel_flag = True
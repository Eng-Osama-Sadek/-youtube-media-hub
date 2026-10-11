"""
مدير التحميلات — يدير كل التحميلات الجارية والمكتملة.
"""

import uuid
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from core.downloader import Downloader, DownloadOptions, DownloadProgress, DownloadStatus
from utils.logger import app_logger


@dataclass
class DownloadItem:
    task_id: str
    url: str
    title: str
    video_id: str
    options: DownloadOptions
    downloader: Optional[Downloader] = None
    progress: DownloadProgress = field(default_factory=DownloadProgress)

    @property
    def status(self):
        return self.progress.status

    @property
    def is_active(self):
        return self.status in (
            DownloadStatus.PENDING,
            DownloadStatus.DOWNLOADING,
            DownloadStatus.PROCESSING,
        )

    @property
    def is_finished(self):
        return self.status in (
            DownloadStatus.COMPLETED,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        )


class DownloadManager:
    """يدير كل التحميلات."""

    def __init__(self):
        self.items = {}
        self.lock = threading.Lock()
        self.on_item_added = None
        self.on_item_updated = None
        self.on_item_removed = None

    def add_download(self, url, title, video_id, options):
        task_id = str(uuid.uuid4())[:8]
        item = DownloadItem(
            task_id=task_id,
            url=url,
            title=title,
            video_id=video_id,
            options=options,
        )
        item.progress.status = DownloadStatus.PENDING
        item.progress.stage_text = "في الانتظار"
        item.progress.filename = title

        with self.lock:
            self.items[task_id] = item

        app_logger.info("+ تحميل جديد [{}]: {}".format(task_id, title))

        if self.on_item_added:
            try:
                self.on_item_added(item)
            except Exception:
                pass

        self._start(item)
        return task_id

    def _start(self, item):
        downloader = Downloader(
            url=item.url,
            options=item.options,
            title=item.title,
            video_id=item.video_id,
            on_progress=lambda p: self._on_progress(item.task_id, p),
            on_complete=lambda path: self._on_complete(item.task_id, path),
            on_error=lambda err: self._on_error(item.task_id, err),
        )
        item.downloader = downloader
        downloader.start()

    def _on_progress(self, task_id, progress):
        with self.lock:
            item = self.items.get(task_id)
            if not item:
                return
            item.progress = progress
        if self.on_item_updated:
            try:
                self.on_item_updated(item)
            except Exception:
                pass

    def _on_complete(self, task_id, path):
        with self.lock:
            item = self.items.get(task_id)
        if not item:
            return
        if self.on_item_updated:
            try:
                self.on_item_updated(item)
            except Exception:
                pass

    def _on_error(self, task_id, error):
        with self.lock:
            item = self.items.get(task_id)
        if not item:
            return
        if self.on_item_updated:
            try:
                self.on_item_updated(item)
            except Exception:
                pass

    def cancel(self, task_id):
        with self.lock:
            item = self.items.get(task_id)
        if item and item.downloader:
            item.downloader.cancel()

    def remove(self, task_id):
        with self.lock:
            item = self.items.pop(task_id, None)
        if item and item.downloader and item.is_active:
            item.downloader.cancel()
        if self.on_item_removed:
            try:
                self.on_item_removed(task_id)
            except Exception:
                pass

    def cancel_all(self):
        with self.lock:
            for item in list(self.items.values()):
                if item.downloader and item.is_active:
                    item.downloader.cancel()

    def get_all(self):
        with self.lock:
            return list(self.items.values())

    def get_active_count(self):
        with self.lock:
            return sum(1 for i in self.items.values() if i.is_active)

    def clear_finished(self):
        with self.lock:
            finished = [tid for tid, i in self.items.items() if i.is_finished]
            for tid in finished:
                self.items.pop(tid, None)
        for tid in finished:
            if self.on_item_removed:
                try:
                    self.on_item_removed(tid)
                except Exception:
                    pass

# -*- coding: utf-8 -*-

from asyncio import Queue, QueueEmpty, QueueFull, TimeoutError, wait_for
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

from av import AudioFrame, VideoFrame  # noqa
from av.frame import Frame
from numpy import ndarray

from avplayer.media.media_kind import MediaKind
from avplayer.variables import INFINITE_FRAME_QUEUE_SIZE


@dataclass
class FrameItem:

    frame: Frame

    @property
    def pts(self) -> int:
        return self.frame.pts

    @property
    def time_base(self) -> Fraction:
        return self.frame.time_base


class FrameCollectionClosedError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class FrameCollection:
    def __init__(self, kind: MediaKind, max_size=INFINITE_FRAME_QUEUE_SIZE):
        self._kind = kind
        self._queue = Queue(max_size)  # type: ignore[var-annotated]

        self._newest: Optional[ndarray] = None
        self._newest_pts = 0
        self._newest_time_base = 0

        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self):
        self._closed = True

    def exists_newest(self) -> bool:
        return self._newest is not None

    def update_newest(self, frame: Frame) -> ndarray:
        if self._closed:
            raise FrameCollectionClosedError

        if self._kind == MediaKind.Video:
            # [swscaler @ 0x5562636b2d80]
            # deprecated pixel format used, make sure you did set range correctly
            self._newest = frame.to_ndarray(format="bgr24")  # noqa
        elif self._kind == MediaKind.Audio:
            self._newest = frame.to_ndarray(format="s16")  # noqa
        else:
            raise RuntimeError(f"Unsupported kind: {self._kind}")

        assert self._newest is not None
        self._newest_pts = frame.pts
        self._newest_time_base = frame.time_base
        return self._newest

    def put(self, item: FrameItem) -> None:
        if self._closed:
            raise FrameCollectionClosedError

        while self._queue.full():
            try:
                self._queue.get_nowait()
            except QueueEmpty:
                pass
        try:
            self._queue.put_nowait(item)
        except QueueFull:
            pass

    def update_newest_array_and_put(self, frame: Frame) -> ndarray:
        newest = self.update_newest(frame)
        self.put(FrameItem(frame))
        return newest

    def create_newest_frame(self) -> Frame:
        if self._kind == MediaKind.Video:
            new_frame = VideoFrame.from_ndarray(self._newest, format="bgr24")
        elif self._kind == MediaKind.Audio:
            new_frame = AudioFrame.from_ndarray(self._newest, format="s16")  # noqa
        else:
            raise RuntimeError(f"Unsupported kind: {self._kind}")

        new_frame.pts = self._newest_pts
        new_frame.time_base = self._newest_time_base
        return new_frame

    async def get(self, timeout: Optional[float] = None) -> FrameItem:
        if self._closed:
            return self._queue.get_nowait()
        try:
            return await wait_for(self._queue.get(), timeout=timeout)
        except TimeoutError:
            raise

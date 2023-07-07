# -*- coding: utf-8 -*-

from typing import Final, Tuple

# noinspection SpellCheckingInspection
REALTIME_FORMATS = (
    "alsa",
    "android_camera",
    "avfoundation",
    "bktr",
    "decklink",
    "dshow",
    "fbdev",
    "gdigrab",
    "iec61883",
    "jack",
    "kmsgrab",
    "openal",
    "oss",
    "pulse",
    "sndio",
    "rtsp",
    "v4l2",
    "vfwcap",
    "x11grab",
)

# noinspection SpellCheckingInspection
DEFAULT_RTSP_OPTIONS = {
    "rtsp_transport": "tcp",
    "fflags": "nobuffer",
}

INFINITE_FRAME_QUEUE_SIZE: Final[int] = 0

DEFAULT_FRAME_QUEUE_MAX: Final[int] = 4
"""The size of the queue for transferring frames inter-threads.
"""

DEFAULT_IO_BUFFER_SIZE: Final[int] = 24_883_200
"""Size of buffer for Python input/output operations in bytes.
Honored only when file is a file-like object.
Make it a buffer size for 4k RGB images.
3840 * 2160 * 3 = 24883200 byte
"""

DEFAULT_AV_OPEN_TIMEOUT: Final[float] = 20.0
DEFAULT_AV_READ_TIMEOUT: Final[float] = 8.0

DEFAULT_AV_TIMEOUT: Final[Tuple[float, float]] = (
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
)

HLS_MASTER_FILENAME: Final[str] = "master.m3u8"
HLS_SEGMENT_FILENAME: Final[str] = "%Y-%m-%d_%H-%M-%S.ts"

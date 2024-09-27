# -*- coding: utf-8 -*-

from typing import Final, Sequence, Tuple

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

BUFFER_SIZE_4K = 3840 * 2160 * 3
"""Make it a buffer size for 4k RGB images.
3840 * 2160 * 3 = 24883200 byte
"""

DEFAULT_IO_BUFFER_SIZE: Final[int] = BUFFER_SIZE_4K
"""Size of buffer for Python input/output operations in bytes.
Honored only when file is a file-like object.
"""

DEFAULT_DROP_THRESHOLD: Final[int] = 3
"""Threshold for the number of buffering to drop waiting frames.
If the consumption rate is slower than the production rate, frames are dropped.
The smaller this value, the closer it is to live video.
"""

DEFAULT_AV_OPEN_TIMEOUT: Final[float] = 32.0
DEFAULT_AV_READ_TIMEOUT: Final[float] = 16.0

DEFAULT_AV_TIMEOUT: Final[Tuple[float, float]] = (
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
)

HLS_MASTER_FILENAME: Final[str] = "master.m3u8"
HLS_SEGMENT_FILENAME: Final[str] = "%Y-%m-%d_%H-%M-%S.ts"

PRINTER_NAMESPACE_ATTR_KEY: Final[str] = "_printer"

VERBOSE_LEVEL_0: Final[int] = 0
VERBOSE_LEVEL_1: Final[int] = 1
VERBOSE_LEVEL_2: Final[int] = 2

DEFAULT_LOGGING_STEP: Final[int] = 1000

DEFAULT_WIN_GEOMETRY: Final[str] = "640x360+0+0"
DEFAULT_WIN_TITLE: Final[str] = "AvPlayer"
DEFAULT_WIN_FPS: Final[int] = 60
DEFAULT_WIN_QUEUE_SIZE: Final[int] = 128

DEFAULT_CV_EXIT_KEYS: Final[Sequence[str]] = "Q", "q"

IO_APP: Final[str] = "io"
AIO_APP: Final[str] = "aio"
AIOTK_APP: Final[str] = "aiotk"
CV_APP: Final[str] = "aiotk"
DEFAULT_APP: Final[str] = IO_APP
APP_TYPES: Final[Sequence[str]] = IO_APP, AIO_APP, AIOTK_APP, CV_APP

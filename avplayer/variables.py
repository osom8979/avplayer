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

BUFFER_SIZE_4K = 3840 * 2160 * 3
"""Make it a buffer size for 4k RGB images.
3840 * 2160 * 3 = 24883200 byte
"""

DEFAULT_IO_BUFFER_SIZE: Final[int] = BUFFER_SIZE_4K
"""Size of buffer for Python input/output operations in bytes.
Honored only when file is a file-like object.
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

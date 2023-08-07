# -*- coding: utf-8 -*-

from ctypes import CDLL

from av.logging import ERROR
from avplayer.av.av_modules import find_libavutil_path


def av_log_set_level(level: int) -> None:
    libavutil = CDLL(find_libavutil_path())
    try:
        libavutil.av_log_set_level(level)
    finally:
        del libavutil


def av_log_get_level() -> int:
    libavutil = CDLL(find_libavutil_path())
    try:
        return libavutil.av_log_get_level()
    finally:
        del libavutil


def silent_av_warnings() -> None:
    # e.g.
    # [swscaler @ 0x5569f73ced40]
    # deprecated pixel format used, make sure you did set range correctly
    av_log_set_level(ERROR)

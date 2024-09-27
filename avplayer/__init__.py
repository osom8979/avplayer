# -*- coding: utf-8 -*-

from avplayer.apps import av_main
from avplayer.apps.defaults import AioApp, AioCv, AioTk, IoApp
from avplayer.av.av_io import AvIo
from avplayer.avconfig import AvConfig

__version__ = "1.8.2"
__all__ = [
    "__version__",
    "AioApp",
    "AioCv",
    "AioTk",
    "AvConfig",
    "AvIo",
    "IoApp",
    "av_main",
]

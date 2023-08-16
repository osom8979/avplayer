# -*- coding: utf-8 -*-

from avplayer.apps.default import AioApp, AioWebApp, IoApp
from avplayer.apps.default import default_main as av_main
from avplayer.av.av_io import AvIo
from avplayer.config import Config as AvConfig

__version__ = "1.3.0"
__all__ = [
    "AioApp",
    "AioWebApp",
    "AvConfig",
    "AvIo",
    "IoApp",
    "av_main",
]

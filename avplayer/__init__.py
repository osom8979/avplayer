# -*- coding: utf-8 -*-

from avplayer.apps.default import AioApp, IoApp
from avplayer.apps.default import default_main as av_main
from avplayer.apps.interface.av_interface import AsyncAvInterface, AvInterface
from avplayer.av.av_io import AvIo
from avplayer.avconfig import AvConfig

__version__ = "1.7.0"
__all__ = [
    "__version__",
    "AioApp",
    "AsyncAvInterface",
    "AvConfig",
    "AvInterface",
    "AvIo",
    "IoApp",
    "av_main",
]

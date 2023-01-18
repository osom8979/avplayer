# -*- coding: utf-8 -*-

from enum import Enum, unique


@unique
class MediaKind(Enum):
    Video = 0
    Audio = 1
    Subtitle = 2

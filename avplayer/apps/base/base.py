# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from overrides import override

from avplayer.avconfig import AvConfig
from avplayer.ffmpeg.ffmpeg import (
    AUTOMATIC_DETECT_FILE_FORMAT,
    DEFAULT_FILE_FORMAT,
    DEFAULT_PIXEL_FORMAT,
    detect_file_format,
    find_bits_per_pixel,
)


class AppInterface(metaclass=ABCMeta):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError


class AppBase(AppInterface):
    def __init__(self, config: AvConfig):
        self._config = config

    @property
    def config(self) -> AvConfig:
        return self._config

    def inspect_channels(self, pixel_format=DEFAULT_PIXEL_FORMAT) -> int:
        bits_per_pixel = find_bits_per_pixel(pixel_format, self._config.ffmpeg_path)
        if bits_per_pixel % 8 != 0:
            raise ValueError("The pixel format only supports multiples of 8 bits")
        return bits_per_pixel // 8

    def inspect_format(self, file: str, file_format=DEFAULT_FILE_FORMAT) -> str:
        if file and file_format.lower() == AUTOMATIC_DETECT_FILE_FORMAT.lower():
            return detect_file_format(file, self._config.ffmpeg_path)
        else:
            return file_format

    def inspect_output_format(self) -> str:
        try:
            if self._config.output:
                return self.inspect_format(self._config.output)
        except:  # noqa
            pass
        return AUTOMATIC_DETECT_FILE_FORMAT

    @override
    def start(self) -> None:
        raise NotImplementedError

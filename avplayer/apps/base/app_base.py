# -*- coding: utf-8 -*-

from avplayer.config import Config
from avplayer.ffmpeg.ffmpeg import (
    AUTOMATIC_DETECT_FILE_FORMAT,
    DEFAULT_FILE_FORMAT,
    DEFAULT_PIXEL_FORMAT,
    detect_file_format,
    find_bits_per_pixel,
)


class AppBase:
    def __init__(self, config: Config):
        self._config = config

    @property
    def config(self) -> Config:
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

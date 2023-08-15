# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Optional, Tuple

from avplayer.ffmpeg.ffmpeg import (
    AUTOMATIC_DETECT_FILE_FORMAT,
    DEFAULT_FILE_FORMAT,
    DEFAULT_PIXEL_FORMAT,
    detect_file_format,
    find_bits_per_pixel,
)
from avplayer.variables import PRINTER_NAMESPACE_ATTR_KEY


class AppBase:
    def __init__(self, args: Namespace):
        self._args = args

        assert isinstance(args.debug, bool)
        assert isinstance(args.verbose, int)
        assert isinstance(args.use_uvloop, bool)
        assert isinstance(args.ffmpeg_path, str)
        assert isinstance(args.ffprobe_path, str)
        assert isinstance(args.logging_step, int)
        assert isinstance(args.bind, str)
        assert isinstance(args.port, int)
        assert isinstance(args.timeout, float)
        assert isinstance(args.output, str)
        assert isinstance(args.input, str)

        self._debug = args.debug
        self._verbose = args.verbose
        self._use_uvloop = args.use_uvloop
        self._ffmpeg_path = args.ffmpeg_path
        self._ffprobe_path = args.ffprobe_path
        self._logging_step = args.logging_step
        self._bind = args.bind
        self._port = args.port
        self._timeout = args.timeout
        self._output = args.output
        self._input = args.input

        assert hasattr(args, PRINTER_NAMESPACE_ATTR_KEY)
        self._printer = getattr(args, PRINTER_NAMESPACE_ATTR_KEY)

    @property
    def args(self) -> Namespace:
        return self._args

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def verbose(self) -> int:
        return self._verbose

    @property
    def use_uvloop(self) -> bool:
        return self._use_uvloop

    @property
    def ffmpeg_path(self) -> str:
        return self._ffmpeg_path

    @property
    def ffprobe_path(self) -> str:
        return self._ffprobe_path

    @property
    def logging_step(self) -> int:
        return self._logging_step

    @property
    def bind(self) -> str:
        return self._bind

    @property
    def port(self) -> int:
        return self._port

    @property
    def timeout(self) -> float:
        return self._timeout

    @property
    def output(self) -> str:
        return self._output

    @property
    def input(self) -> str:
        return self._input

    @property
    def input_size(self) -> Optional[Tuple[int, int]]:
        if self._args.input_size is not None:
            assert isinstance(self._args.input_size, str)
            x, y = self._args.input_size.split("x")
            return int(x), int(y)
        else:
            return None

    @property
    def output_size(self) -> Optional[Tuple[int, int]]:
        if self._args.output_size is not None:
            assert isinstance(self._args.output_size, str)
            x, y = self._args.output_size.split("x")
            return int(x), int(y)
        else:
            return None

    def print(self, *args, **kwargs) -> None:
        self._printer(*args, **kwargs)

    def inspect_channels(self, pixel_format=DEFAULT_PIXEL_FORMAT) -> int:
        bits_per_pixel = find_bits_per_pixel(pixel_format, self._ffmpeg_path)
        if bits_per_pixel % 8 != 0:
            raise ValueError("The pixel format only supports multiples of 8 bits")
        return bits_per_pixel // 8

    def inspect_format(self, file: str, file_format=DEFAULT_FILE_FORMAT) -> str:
        if file and file_format.lower() == AUTOMATIC_DETECT_FILE_FORMAT.lower():
            return detect_file_format(file, self._ffmpeg_path)
        else:
            return file_format

    def inspect_output_format(self) -> str:
        try:
            if self.output:
                return self.inspect_format(self.output)
        except:  # noqa
            pass
        return AUTOMATIC_DETECT_FILE_FORMAT

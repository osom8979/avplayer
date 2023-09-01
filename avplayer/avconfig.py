# -*- coding: utf-8 -*-

from argparse import Namespace
from copy import deepcopy
from enum import Enum, auto, unique
from re import split as re_split
from typing import List, Optional, Tuple

from avplayer.logging.logging import logger
from avplayer.variables import (
    AIO_APP,
    AIOTK_APP,
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
    DEFAULT_HTTP_BIND,
    DEFAULT_HTTP_PORT,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_IO_BUFFER_SIZE,
    DEFAULT_LOGGING_STEP,
    DEFAULT_WIN_FPS,
    DEFAULT_WIN_GEOMETRY,
    DEFAULT_WIN_QUEUE_SIZE,
    DEFAULT_WIN_TITLE,
    IO_APP,
    PRINTER_NAMESPACE_ATTR_KEY,
)


@unique
class AvAppType(Enum):
    IO = auto()
    AIO = auto()
    AIOTK = auto()


class AvConfig:
    def __init__(
        self,
        input_file,
        output_file: Optional[str] = None,
        input_size: Optional[Tuple[int, int]] = None,
        output_size: Optional[Tuple[int, int]] = None,
        bind=DEFAULT_HTTP_BIND,
        port=DEFAULT_HTTP_PORT,
        timeout=DEFAULT_HTTP_TIMEOUT,
        timeout_open=DEFAULT_AV_OPEN_TIMEOUT,
        timeout_read=DEFAULT_AV_READ_TIMEOUT,
        buffer_size=DEFAULT_IO_BUFFER_SIZE,
        ffmpeg_path="ffmpeg",
        printer=print,
        logging_step=DEFAULT_LOGGING_STEP,
        use_uvloop=False,
        app_type=AvAppType.IO,
        win_geometry=DEFAULT_WIN_GEOMETRY,
        win_title=DEFAULT_WIN_TITLE,
        win_fps=DEFAULT_WIN_FPS,
        win_queue_size=DEFAULT_WIN_QUEUE_SIZE,
        debug=False,
        verbose=0,
        *,
        args: Optional[Namespace] = None,
    ):
        self._input_file = input_file
        self._output_file = output_file if output_file else str()
        self._input_size = input_size
        self._output_size = output_size
        self._bind = bind
        self._port = port
        self._timeout = timeout
        self._timeout_open = timeout_open
        self._timeout_read = timeout_read
        self._buffer_size = buffer_size
        self._ffmpeg_path = ffmpeg_path
        self._printer = printer
        self._logging_step = logging_step
        self._use_uvloop = use_uvloop
        self._app_type = app_type
        self._win_geometry = win_geometry
        self._win_title = win_title
        self._win_fps = win_fps
        self._win_queue_size = win_queue_size
        self._debug = debug
        self._verbose = verbose
        self._args = deepcopy(args) if args is not None else Namespace()

    @staticmethod
    def size_parse(text: Optional[str], separator="x") -> Optional[Tuple[int, int]]:
        if text is None:
            return None
        try:
            x, y = text.split(separator)
            return int(x), int(y)
        except:  # noqa
            return None

    @staticmethod
    def get_app_type(choice: str) -> AvAppType:
        if choice == IO_APP:
            return AvAppType.IO
        elif choice == AIO_APP:
            return AvAppType.AIO
        elif choice == AIOTK_APP:
            return AvAppType.AIOTK
        else:
            raise NotImplementedError

    @classmethod
    def from_namespace(cls, args: Namespace):
        assert isinstance(args.debug, bool)
        assert isinstance(args.verbose, int)
        assert isinstance(args.use_uvloop, bool)
        assert isinstance(args.app_type, str)
        assert isinstance(args.ffmpeg_path, str)
        assert isinstance(args.logging_step, int)
        assert isinstance(args.bind, str)
        assert isinstance(args.port, int)
        assert isinstance(args.timeout, float)
        assert isinstance(args.output, str)
        assert isinstance(args.input, str)
        assert isinstance(args.input_size, (type(None), str))
        assert isinstance(args.output_size, (type(None), str))
        assert isinstance(args.timeout_open, float)
        assert isinstance(args.timeout_read, float)
        assert isinstance(args.buffer_size, int)
        assert isinstance(args.win_geometry, str)
        assert isinstance(args.win_title, str)
        assert isinstance(args.win_fps, int)
        assert isinstance(args.win_queue_size, int)

        debug = args.debug
        verbose = args.verbose
        use_uvloop = args.use_uvloop
        app_type = cls.get_app_type(args.app_type)
        ffmpeg_path = args.ffmpeg_path
        logging_step = args.logging_step
        bind = args.bind
        port = args.port
        timeout = args.timeout
        output_file = args.output
        input_file = args.input
        input_size = cls.size_parse(args.input_size)
        output_size = cls.size_parse(args.output_size)
        timeout_open = args.timeout_open
        timeout_read = args.timeout_read
        buffer_size = args.buffer_size
        win_geometry = args.win_geometry
        win_title = args.win_title
        win_fps = args.win_fps
        win_queue_size = args.win_queue_size

        assert hasattr(args, PRINTER_NAMESPACE_ATTR_KEY)
        printer = getattr(args, PRINTER_NAMESPACE_ATTR_KEY)

        return cls(
            input_file=input_file,
            output_file=output_file,
            input_size=input_size,
            output_size=output_size,
            bind=bind,
            port=port,
            timeout=timeout,
            timeout_open=timeout_open,
            timeout_read=timeout_read,
            buffer_size=buffer_size,
            ffmpeg_path=ffmpeg_path,
            printer=printer,
            logging_step=logging_step,
            use_uvloop=use_uvloop,
            app_type=app_type,
            win_geometry=win_geometry,
            win_title=win_title,
            win_fps=win_fps,
            win_queue_size=win_queue_size,
            debug=debug,
            verbose=verbose,
            args=args,
        )

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
    def app_type(self) -> AvAppType:
        return self._app_type

    @property
    def ffmpeg_path(self) -> str:
        return self._ffmpeg_path

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
    def timeout_open(self) -> float:
        return self._timeout_open

    @property
    def timeout_read(self) -> float:
        return self._timeout_read

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

    @property
    def output(self) -> str:
        return self._output_file

    @property
    def input(self) -> str:
        return self._input_file

    @property
    def input_size(self) -> Optional[Tuple[int, int]]:
        return self._input_size

    @property
    def output_size(self) -> Optional[Tuple[int, int]]:
        return self._output_size

    @property
    def win_geometry(self) -> str:
        return self._win_geometry

    @property
    def tk_geometry(self) -> Tuple[int, int, int, int]:
        w, h, x, y = re_split(r"x|\+", self._win_geometry)
        return int(w), int(h), int(x), int(y)

    @property
    def win_title(self) -> str:
        return self._win_title

    @property
    def win_fps(self) -> int:
        return self._win_fps

    @property
    def win_queue_size(self) -> int:
        return self._win_queue_size

    def print(self, *args, **kwargs) -> None:
        self._printer(*args, **kwargs)

    def as_logging_lines(self) -> List[str]:
        return [
            f"Input file: '{self._input_file}'",
            f"Output file: '{self._output_file}'",
            f"Input size: {self._input_size}",
            f"Output size: {self._output_size}",
            f"Web bind: '{self._bind}'",
            f"Web port number: {self._port}",
            f"Web timeout: {self._timeout:.3f}s",
            f"AV IO open timeout: {self._timeout_open:.3f}s",
            f"AV IO read timeout: {self._timeout_read:.3f}s",
            f"Buffer size: {self._buffer_size} bytes",
            f"FFmpeg path: '{self._ffmpeg_path}'",
            f"Logging step: {self._logging_step}",
            f"Use uvloop: {self._use_uvloop}",
            f"App type: '{self._app_type.name}'",
            f"Win geometry: '{self._win_geometry}'",
            f"Win title: '{self._win_title}'",
            f"Win fps: {self._win_fps:.2f}",
            f"Debug: {self._debug}",
            f"Verbose: {self._verbose}",
        ]

    def logging_params(self) -> None:
        for line in self.as_logging_lines():
            logger.info(line)

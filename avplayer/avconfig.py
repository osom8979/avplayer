# -*- coding: utf-8 -*-

from argparse import Namespace
from copy import deepcopy
from enum import Enum, auto, unique
from re import split as re_split
from typing import List, Optional, Sequence, Tuple

from avplayer.logging.logging import logger
from avplayer.variables import (
    AIO_APP,
    AIOTK_APP,
    CV_APP,
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
    DEFAULT_CV_EXIT_KEYS,
    DEFAULT_DROP_THRESHOLD,
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
    CV = auto()


class AvConfig:
    def __init__(
        self,
        input_file,
        output_file: Optional[str] = None,
        input_size: Optional[Tuple[int, int]] = None,
        output_size: Optional[Tuple[int, int]] = None,
        timeout_open=DEFAULT_AV_OPEN_TIMEOUT,
        timeout_read=DEFAULT_AV_READ_TIMEOUT,
        buffer_size=DEFAULT_IO_BUFFER_SIZE,
        drop_slow_frame=False,
        drop_threshold=DEFAULT_DROP_THRESHOLD,
        ffmpeg_path="ffmpeg",
        printer=print,
        logging_step=DEFAULT_LOGGING_STEP,
        use_uvloop=False,
        app_type=AvAppType.IO,
        win_geometry=DEFAULT_WIN_GEOMETRY,
        win_title=DEFAULT_WIN_TITLE,
        win_fps=DEFAULT_WIN_FPS,
        win_queue_size=DEFAULT_WIN_QUEUE_SIZE,
        cv_flags: Optional[int] = None,
        cv_exit_keys: Optional[Sequence[str]] = DEFAULT_CV_EXIT_KEYS,
        cv_infinity=False,
        cv_headless=False,
        debug=False,
        verbose=0,
        *,
        args: Optional[Namespace] = None,
    ):
        self.input_file = input_file
        self.output_file = output_file if output_file else str()
        self.input_size = input_size
        self.output_size = output_size
        self.timeout_open = timeout_open
        self.timeout_read = timeout_read
        self.buffer_size = buffer_size
        self.drop_slow_frame = drop_slow_frame
        self.drop_threshold = drop_threshold
        self.ffmpeg_path = ffmpeg_path
        self.logging_step = logging_step
        self.use_uvloop = use_uvloop
        self.app_type = app_type
        self.win_geometry = win_geometry
        self.win_title = win_title
        self.win_fps = win_fps
        self.win_queue_size = win_queue_size
        self.cv_flags = cv_flags
        self.cv_exit_keys = cv_exit_keys
        self.cv_infinity = cv_infinity
        self.cv_headless = cv_headless
        self.debug = debug
        self.verbose = verbose
        self.args = deepcopy(args) if args is not None else Namespace()
        self._printer = printer

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
        elif choice == CV_APP:
            return AvAppType.CV
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
        assert isinstance(args.output, str)
        assert isinstance(args.input, str)
        assert isinstance(args.input_size, (type(None), str))
        assert isinstance(args.output_size, (type(None), str))
        assert isinstance(args.timeout_open, float)
        assert isinstance(args.timeout_read, float)
        assert isinstance(args.buffer_size, int)
        assert isinstance(args.drop_slow_frame, bool)
        assert isinstance(args.drop_threshold, int)
        assert isinstance(args.win_geometry, str)
        assert isinstance(args.win_title, str)
        assert isinstance(args.win_fps, int)
        assert isinstance(args.win_queue_size, int)
        assert isinstance(args.cv_flags, (type(None), int))
        assert isinstance(args.cv_exit_keys, (type(None), list))
        assert isinstance(args.cv_infinity, bool)
        assert isinstance(args.cv_headless, bool)

        debug = args.debug
        verbose = args.verbose
        use_uvloop = args.use_uvloop
        app_type = cls.get_app_type(args.app_type)
        ffmpeg_path = args.ffmpeg_path
        logging_step = args.logging_step
        output_file = args.output
        input_file = args.input
        input_size = cls.size_parse(args.input_size)
        output_size = cls.size_parse(args.output_size)
        timeout_open = args.timeout_open
        timeout_read = args.timeout_read
        buffer_size = args.buffer_size
        drop_slow_frame = args.drop_slow_frame
        win_geometry = args.win_geometry
        win_title = args.win_title
        win_fps = args.win_fps
        win_queue_size = args.win_queue_size
        cv_flags = args.cv_flags
        cv_exit_keys = args.cv_exit_keys
        cv_infinity = args.cv_infinity
        cv_headless = args.cv_headless

        assert hasattr(args, PRINTER_NAMESPACE_ATTR_KEY)
        printer = getattr(args, PRINTER_NAMESPACE_ATTR_KEY)

        return cls(
            input_file=input_file,
            output_file=output_file,
            input_size=input_size,
            output_size=output_size,
            timeout_open=timeout_open,
            timeout_read=timeout_read,
            buffer_size=buffer_size,
            drop_slow_frame=drop_slow_frame,
            ffmpeg_path=ffmpeg_path,
            printer=printer,
            logging_step=logging_step,
            use_uvloop=use_uvloop,
            app_type=app_type,
            win_geometry=win_geometry,
            win_title=win_title,
            win_fps=win_fps,
            win_queue_size=win_queue_size,
            cv_flags=cv_flags,
            cv_exit_keys=cv_exit_keys,
            cv_infinity=cv_infinity,
            cv_headless=cv_headless,
            debug=debug,
            verbose=verbose,
            args=args,
        )

    @property
    def output(self) -> str:
        return self.output_file

    @property
    def input(self) -> str:
        return self.input_file

    @property
    def tk_geometry(self) -> Tuple[int, int, int, int]:
        w, h, x, y = re_split(r"[x+]", self.win_geometry)
        return int(w), int(h), int(x), int(y)

    @property
    def cv_exit_codes(self) -> Sequence[int]:
        if self.cv_exit_keys:
            keys = self.cv_exit_keys
        else:
            keys = DEFAULT_CV_EXIT_KEYS
        return tuple(ord(k) for k in keys)

    def print(self, *args, **kwargs) -> None:
        self._printer(*args, **kwargs)

    def as_logging_lines(self) -> List[str]:
        return [
            f"Input file: '{self.input_file}'",
            f"Output file: '{self.output_file}'",
            f"Input size: {self.input_size}",
            f"Output size: {self.output_size}",
            f"AV IO open timeout: {self.timeout_open:.3f}s",
            f"AV IO read timeout: {self.timeout_read:.3f}s",
            f"Buffer size: {self.buffer_size} bytes",
            f"FFmpeg path: '{self.ffmpeg_path}'",
            f"Logging step: {self.logging_step}",
            f"Use uvloop: {self.use_uvloop}",
            f"App type: '{self.app_type.name}'",
            f"Win geometry: '{self.win_geometry}'",
            f"Win title: '{self.win_title}'",
            f"Win fps: {self.win_fps:.2f}",
            f"Cv flags: {self.cv_flags}",
            f"Cv exit codes: {self.cv_exit_keys}",
            f"Cv infinity: {self.cv_infinity}",
            f"Cv headless: {self.cv_headless}",
            f"Debug: {self.debug}",
            f"Verbose: {self.verbose}",
        ]

    def logging_params(self) -> None:
        for line in self.as_logging_lines():
            logger.info(line)

# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from avplayer.variables import (
    DEFAULT_AV_TIMEOUT,
    DEFAULT_FRAME_QUEUE_MAX,
    DEFAULT_IO_BUFFER_SIZE,
    INFINITE_FRAME_QUEUE_SIZE,
)


@dataclass
class CommonMediaOptions:
    format: Optional[str] = None
    """Specific format to use.
    Defaults to 'autodect'.
    """

    options: Optional[Dict[str, Any]] = None
    """Options to pass to the container and all streams.
    """

    container_options: Optional[Dict[str, Any]] = None
    """Options to pass to the container.
    """

    stream_options: Optional[List[str]] = None
    """Options to pass to each stream.
    """

    metadata_encoding: Optional[str] = None
    """Encoding to use when reading or writing file metadata.
    Defaults to 'utf-8'.
    """

    metadata_errors: Optional[str] = None
    """Specifies how to handle encoding errors; behaves like str.encode parameter.
    Defaults to 'strict'.
    """

    buffer_size: Optional[int] = None
    """Size of buffer for Python input/output operations in bytes.
    Honored only when file is a file-like object.
    Defaults to 32768 (32k).
    """

    timeout: Optional[Union[float, Tuple[float, float]]] = None
    """How many seconds to wait for data before giving up, as a float,
    or a (open timeout, read timeout) tuple.
    """

    def get_metadata_encoding(self) -> str:
        if self.metadata_encoding:
            return self.metadata_encoding
        else:
            return "utf-8"

    def get_metadata_errors(self) -> str:
        if self.metadata_errors:
            return self.metadata_errors
        else:
            return "strict"

    def get_buffer_size(self) -> int:
        if self.buffer_size is not None:
            if self.buffer_size >= 0:
                return self.buffer_size
        return DEFAULT_IO_BUFFER_SIZE

    def get_timeout(self) -> Union[float, Tuple[float, float]]:
        if self.timeout is not None:
            return self.timeout
        else:
            return DEFAULT_AV_TIMEOUT

    def get_format_name(self) -> str:
        return f"format={self.format}" if self.format else "format=autodect"

    def get_timeout_argument_message(self) -> str:
        timeout = self.get_timeout()
        if isinstance(timeout, tuple):
            assert len(timeout) == 2
            return f"timeout.open={timeout[0]}s,timeout.read={timeout[1]}s"
        else:
            return f"timeout={timeout}s"


@dataclass
class InputMediaOptions(CommonMediaOptions):
    video_index: Optional[int] = 0
    """The video index of the InputContainer.
    """

    audio_index: Optional[int] = None
    """The audio index of the InputContainer.
    """


@dataclass
class OutputMediaOptions(CommonMediaOptions):
    enable_video: bool = True
    """Use video input container
    """

    enable_audio: bool = True
    """Use audio input container
    """


@dataclass
class MediaOptions:
    input: InputMediaOptions = field(default_factory=InputMediaOptions)
    """Input file options.
    """

    output: OutputMediaOptions = field(default_factory=OutputMediaOptions)
    """Output file options.
    """

    max_frame_queue: Optional[int] = None
    """Maximum AV frame queue size.
    """

    name: Optional[str] = None
    """A unique, human-readable name.
    """

    go_faster: bool = True
    """Thread type is frame+slice.
    """

    low_delay: bool = True
    """Flag is low delay. This flag is force low delay.
    """

    speedup_tricks: bool = False
    """Flag2 is fast. This flag2 is allow non-spec compliant speedup tricks.
    """

    def get_max_frame_queue(self) -> int:
        if self.max_frame_queue is not None:
            if self.max_frame_queue >= 1:
                return self.max_frame_queue
            else:
                return INFINITE_FRAME_QUEUE_SIZE
        else:
            return DEFAULT_FRAME_QUEUE_MAX

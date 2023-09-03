# -*- coding: utf-8 -*-

from errno import EAGAIN
from threading import Event
from time import sleep
from typing import Final, Optional, Sequence, Tuple

from numpy import uint8
from numpy.typing import NDArray

from avplayer.av.av_open import open_input_container, open_output_container
from avplayer.av.av_options import CommonAvOptions
from avplayer.debug.avg_stat import AvgStat
from avplayer.ffmpeg.ffmpeg import (
    AUTOMATIC_DETECT_FILE_FORMAT,
    CRF_SANE_RANGE_MAX,
    PRESET_ULTRAFAST,
    TUNE_FASTDECODE,
)
from avplayer.logging.logging import logger
from avplayer.variables import (
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
    DEFAULT_IO_BUFFER_SIZE,
)
from avplayer.variables import VERBOSE_LEVEL_0 as VL0
from avplayer.variables import VERBOSE_LEVEL_1 as VL1
from avplayer.variables import VERBOSE_LEVEL_2 as VL2

BROKEN_PIPE: Final[int] = 32
CONNECTION_REFUSED: Final[int] = 111
SKIP_FLUSH_ERRORS: Final[Sequence[int]] = BROKEN_PIPE, CONNECTION_REFUSED


class AlreadyLatestException(RuntimeError):
    def __init__(self):
        super().__init__("An exception has already been specified")


class AvIo:
    def __init__(
        self,
        source: str,
        output: Optional[str] = None,
        done: Optional[Event] = None,
        file_format=AUTOMATIC_DETECT_FILE_FORMAT,
        buffer_size=DEFAULT_IO_BUFFER_SIZE,
        open_timeout=DEFAULT_AV_OPEN_TIMEOUT,
        read_timeout=DEFAULT_AV_READ_TIMEOUT,
        source_size: Optional[Tuple[int, int]] = None,
        destination_size: Optional[Tuple[int, int]] = None,
        logging_step=100,
        verbose=0,
    ):
        from av import AVError, FFmpegError, VideoFrame  # noqa
        from av.container import InputContainer, OutputContainer  # noqa
        from av.error import BrokenPipeError, ConnectionRefusedError  # noqa
        from av.stream import Stream  # noqa

        self.AVError = AVError
        self.FFmpegError = FFmpegError
        self.VideoFrame = VideoFrame
        self.BrokenPipeError = BrokenPipeError
        self.ConnectionRefusedError = ConnectionRefusedError

        assert isinstance(self.AVError, type)
        assert isinstance(self.FFmpegError, type)
        assert isinstance(self.VideoFrame, type)
        assert isinstance(self.BrokenPipeError, type)
        assert isinstance(self.ConnectionRefusedError, type)

        self._input_container: Optional[InputContainer] = None
        self._input_stream: Optional[Stream] = None
        self._output_container: Optional[OutputContainer] = None
        self._output_stream: Optional[Stream] = None
        self._latest_exception: Optional[BaseException] = None

        self._output_container = None
        self._output_stream = None

        self._source = source
        self._output = output if output else str()
        self._done = done if done else Event()
        self._file_format = file_format

        self._input_options = {
            "rtsp_transport": "tcp",
            "fflags": "nobuffer",
            "turn": TUNE_FASTDECODE,
        }
        self._output_stream_pix_format = "yuv420p"
        self._output_stream_options = {
            "preset": PRESET_ULTRAFAST,
            "crf": str(CRF_SANE_RANGE_MAX),
        }
        self._latest_exception = None

        self._buffer_size = buffer_size
        self._timeout = open_timeout, read_timeout
        self._source_size = source_size
        self._output_size = destination_size
        self._eagain_wait = 0.001
        self._flush_down_threshold = 10
        self._flush_down_count = 0
        self._verbose = verbose

        logger.info(f"Input file: '{self._source}'")
        logger.info(f"Input container options: {self._input_options}")

        if self._output:
            logger.info(f"Output file: '{self._output}'")
            logger.info(f"Output file format: {self._file_format}")
            logger.info(f"Output stream pixel format: {self._output_stream_pix_format}")
            logger.info(f"Output stream options: {self._output_stream_options}")

        logger.info(f"Buffer size: {self._buffer_size} bytes")
        logger.info(f"Open timeout: {self._timeout[0]:.3f}s")
        logger.info(f"Read timeout: {self._timeout[1]:.3f}s")

        self._iter_stat = AvgStat("Iter", logger, logging_step, verbose, VL0)
        self._coro_stat = AvgStat("Coro", logger, logging_step, verbose, VL1)
        self._read_stat = AvgStat("Read", logger, logging_step, verbose, VL2)
        self._decode_stat = AvgStat("Decode", logger, logging_step, verbose, VL2)
        self._encode_stat = AvgStat("Encode", logger, logging_step, verbose, VL2)
        self._write_stat = AvgStat("Write", logger, logging_step, verbose, VL2)

    @property
    def verbose(self) -> int:
        return self._verbose

    @property
    def skip_flush(self) -> bool:
        if self._latest_exception is None:
            return False

        if not isinstance(self._latest_exception, self.AVError):
            return False

        return getattr(self._latest_exception, "errno") in SKIP_FLUSH_ERRORS

    @property
    def latest_exception(self):
        return self._latest_exception

    @latest_exception.setter
    def latest_exception(self, e: BaseException) -> None:
        self._latest_exception = e

    @property
    def is_done_enabled(self) -> bool:
        return self._done.is_set()

    def done(self) -> None:
        logger.info("Enable avio 'done' flag")
        return self._done.set()

    def _open_input_container(self):
        options = CommonAvOptions(
            options=self._input_options,
            buffer_size=self._buffer_size,
            timeout=self._timeout,
        )
        return open_input_container(self._source, options)

    def _open_output_container(self):
        options = CommonAvOptions(
            format=self._file_format,
            buffer_size=self._buffer_size,
            timeout=self._timeout,
        )
        return open_output_container(self._output, options)

    def open(self) -> None:
        from av.container import InputContainer, OutputContainer
        from av.stream import Stream

        input_container: Optional[InputContainer] = None
        input_stream: Optional[Stream] = None

        output_container: Optional[OutputContainer] = None
        output_stream: Optional[Stream] = None

        try:
            input_container = self._open_input_container()
            for stream in input_container.streams:
                if stream.type == "video":
                    input_stream = stream
                    break
            if input_stream is None:
                raise IndexError("Not found video stream from source")

            input_stream.thread_type = "AUTO"
            input_stream.codec_context.low_delay = True

            if self._output:
                output_container = self._open_output_container()
                output_stream_pix_format = self._output_stream_pix_format
                output_stream_options = self._output_stream_options

                output_stream = output_container.add_stream("libx264")

                if self._output_size is not None:
                    output_stream.width = self._output_size[0]
                    output_stream.height = self._output_size[1]
                elif self._source_size is not None:
                    output_stream.width = self._source_size[0]
                    output_stream.height = self._source_size[1]
                else:
                    output_stream.width = input_stream.width
                    output_stream.height = input_stream.height

                output_stream.pix_fmt = output_stream_pix_format
                output_stream.options = output_stream_options

        except BaseException as e:
            if input_container:
                input_container.close()
            if output_container:
                output_container.close()
            logger.exception(e)
            raise
        else:
            assert input_container is not None
            assert input_stream is not None
            self._input_container = input_container
            self._output_container = output_container
            self._input_stream = input_stream
            self._output_stream = output_stream
            self._done.clear()
            logger.info("Successfully opened the I/O container")

    def close(self) -> None:
        self._done.is_set()

        if self._input_container is not None:
            self._input_container.close()

        if self._output_container is not None:
            assert self._output_stream is not None

            try:
                if not self.skip_flush:
                    self._output_container.mux(self._output_stream.encode(None))
            except BaseException as e:  # noqa
                logger.warning(f"Flush error: {e}")

            self._output_container.close()

        self._input_container = None
        self._output_container = None
        self._input_stream = None
        self._output_stream = None
        logger.info("The I/O container was successfully closed")

    def recv(self):
        while self.is_play_or_raise():
            try:
                while self.is_play_or_raise():
                    with self._read_stat:
                        packet = next(self._input_container.demux(self._input_stream))

                    # We need to skip the "flushing" packets that `demux` generates.
                    if packet.dts is None:
                        self._flush_down_count += 1
                        logger.warning(
                            "Skip the flushing packet, shutdown count: "
                            f"{self._flush_down_count}/{self._flush_down_threshold}"
                        )
                        if self._flush_down_count >= self._flush_down_threshold:
                            raise EOFError("The flush count has reached its maximum")
                        continue
                    else:
                        self._flush_down_count = 0

                    with self._decode_stat:
                        frames = packet.decode()

                    assert isinstance(frames, list)
                    for frame in frames:
                        if frame is None:
                            logger.warning("Empty frame has been detected")
                            continue
                        yield frame
            except self.AVError as e:
                if isinstance(e, self.FFmpegError) and e.errno == EAGAIN:
                    logger.warning(
                        "Resource temporarily unavailable. "
                        f"Temporarily waiting {self._eagain_wait:.2f}s ..."
                    )
                    sleep(self._eagain_wait)
                    continue
                else:
                    raise
            else:
                assert False, "Inaccessible section"
        assert False, "Inaccessible section"

    def send(self, image: Optional[NDArray[uint8]]) -> None:
        if image is None:
            return

        if not self._output:
            return

        assert self._output_container is not None
        assert self._output_stream is not None

        with self._encode_stat:
            next_frame = self.VideoFrame.from_ndarray(image, format="bgr24")
            output_packets = self._output_stream.encode(next_frame)

        for output_packet in output_packets:
            with self._write_stat:
                self._output_container.mux(output_packet)

    def frame_to_ndarray(self, frame) -> NDArray[uint8]:
        assert isinstance(frame, self.VideoFrame)
        if self._source_size is not None:
            width, height = self._source_size
            return frame.reformat(width, height, "bgr24").to_ndarray()
        else:
            return frame.to_ndarray(format="bgr24")

    def iter(self, coro) -> None:
        frame = next(self.recv())
        with self._coro_stat:
            image = self.frame_to_ndarray(frame)
            result = coro(image) if coro else image
        self.send(result)

    def is_play_or_raise(self) -> bool:
        if self._latest_exception is not None:
            raise AlreadyLatestException from self._latest_exception
        if self._done.is_set():
            raise InterruptedError
        return True

    def run(self, coro) -> None:
        try:
            logger.info("Start avio streaming ...")
            while self.is_play_or_raise():
                with self._iter_stat:
                    self.iter(coro)
        except self.AVError as e:
            self._latest_exception = e
            logger.error(f"AV error: {e}")
        except self.BrokenPipeError as e:
            self._latest_exception = e
            logger.error(f"Broken pipe error: {e}")
        except self.ConnectionRefusedError as e:
            self._latest_exception = e
            logger.error(f"Connection refused error: {e}")
        except AlreadyLatestException:
            assert self._latest_exception is not None
            logger.error(f"Already latest exception: {self._latest_exception}")
        except StopIteration as e:
            logger.warning(f"Stop iteration: {e}")
        except KeyboardInterrupt as e:
            logger.warning(f"Keyboard interrupt signal detected: {e}")
        except InterruptedError as e:
            logger.warning(f"Interrupt signal detected: {e}")
        except EOFError as e:
            logger.warning(f"End of file: {e}")

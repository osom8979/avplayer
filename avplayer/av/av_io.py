# -*- coding: utf-8 -*-

from errno import EAGAIN
from threading import Event
from time import sleep
from typing import Optional, Tuple

from numpy import uint8
from numpy.typing import NDArray

from av import AVError, FFmpegError, VideoFrame  # noqa
from av import open as av_open  # noqa
from av.container import InputContainer, OutputContainer  # noqa
from av.stream import Stream  # noqa
from avplayer.debug.step_avg import StepAvg
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


class AvIo:
    _input_container: InputContainer
    _input_stream: Stream

    _output_container: Optional[OutputContainer]
    _output_stream: Optional[Stream]

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

        self._buffer_size = buffer_size
        self._timeout = open_timeout, read_timeout
        self._source_size = source_size
        self._output_size = destination_size
        self._re_request_wait_seconds = 0.001
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

        self._iter_step = StepAvg("Iter", logger, logging_step, verbose, VL0)
        self._callback_step = StepAvg("Callback", logger, logging_step, verbose, VL1)
        self._demux_step = StepAvg("Demux", logger, logging_step, verbose, VL2)
        self._decode_step = StepAvg("Decode", logger, logging_step, verbose, VL2)
        self._encode_step = StepAvg("Encode", logger, logging_step, verbose, VL2)
        self._mux_step = StepAvg("Mux", logger, logging_step, verbose, VL2)

    @property
    def verbose(self) -> int:
        return self._verbose

    def shutdown(self) -> None:
        return self._done.set()

    def _open_input_container(self) -> InputContainer:
        logger.debug(f"Open the input container: '{self._source}'")
        return av_open(
            self._source,
            mode="r",
            options=self._input_options,
            buffer_size=self._buffer_size,
            timeout=self._timeout,
        )

    def _open_output_container(self) -> OutputContainer:
        logger.debug(f"Open the output container: '{self._output}'")
        return av_open(
            self._output,
            mode="w",
            format=self._file_format,
            buffer_size=self._buffer_size,
            timeout=self._timeout,
        )

    def open(self) -> None:
        input_container: Optional[OutputContainer] = None
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
            logger.info("Successfully opened the I/O container")

    def close(self) -> None:
        self._input_container.close()
        if self._output_container:
            assert self._output_stream is not None
            self._output_container.mux(self._output_stream.encode(None))
            self._output_container.close()
        logger.info("The I/O container was successfully closed")

    def recv(self):
        while True:
            try:
                while True:
                    self._demux_step.do_enter()
                    packet = next(self._input_container.demux(self._input_stream))
                    self._demux_step.do_exit()

                    # We need to skip the "flushing" packets that `demux` generates.
                    if packet.dts is None:
                        logger.warning("Skip the flushing packet")
                        self._flush_down_count += 1
                        if self._flush_down_count >= self._flush_down_threshold:
                            raise EOFError("The flush count has reached its maximum")
                        continue
                    else:
                        self._flush_down_count = 0

                    self._decode_step.do_enter()
                    frames = packet.decode()
                    self._decode_step.do_exit()

                    assert isinstance(frames, list)
                    for frame in frames:
                        if frame is None:
                            logger.warning("Empty frame")
                            continue
                        yield frame
            except AVError as e:
                if isinstance(e, FFmpegError) and e.errno == EAGAIN:
                    logger.warning("Resource temporarily unavailable")
                    sleep(self._re_request_wait_seconds)
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

        self._encode_step.do_enter()
        next_frame = VideoFrame.from_ndarray(image, format="bgr24")
        output_packets = self._output_stream.encode(next_frame)
        self._encode_step.do_exit()

        for output_packet in output_packets:
            with self._mux_step:
                self._output_container.mux(output_packet)

    def frame_to_ndarray(self, frame: VideoFrame) -> NDArray[uint8]:
        if self._source_size is not None:
            width, height = self._source_size
            return frame.reformat(width, height, "bgr24").to_ndarray()
        else:
            return frame.to_ndarray(format="bgr24")

    def iter(self, coro) -> None:
        frame = next(self.recv())

        self._callback_step.do_enter()
        image = self.frame_to_ndarray(frame)
        result = coro(image) if coro else image
        self._callback_step.do_exit()

        self.send(result)

    def run(self, coro) -> None:
        try:
            logger.info("Start streaming ...")
            while True:
                if self._done.is_set():
                    raise InterruptedError

                with self._iter_step:
                    self.iter(coro)
        except AVError as e:
            logger.exception(e)
            raise
        except StopIteration as e:
            logger.warning(f"Stop iteration: {e}")
        except InterruptedError as e:
            logger.warning(f"Interrupt signal detected: {e}")
        except KeyboardInterrupt as e:
            logger.warning(f"Keyboard interrupt signal detected: {e}")
        except EOFError as e:
            logger.warning(f"End of file: {e}")

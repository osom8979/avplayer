# -*- coding: utf-8 -*-

import os
from asyncio import AbstractEventLoop, run_coroutine_threadsafe
from copy import deepcopy
from datetime import datetime
from errno import EAGAIN
from fractions import Fraction
from inspect import iscoroutinefunction
from threading import Event
from time import sleep, time
from typing import Final, List, Optional, Union

from av import AudioFifo, AudioFrame, AudioResampler, AVError
from av import FFmpegError as AvFFmpegError  # noqa
from av import VideoFrame as AvVideoFrame  # noqa
from av.container import InputContainer, OutputContainer
from av.frame import Frame
from av.packet import Packet
from av.stream import Stream
from numpy import ndarray

from avplayer.chrono.datetime_filename import parse_dirname_and_filename
from avplayer.collections.frame_collection import FrameCollection
from avplayer.logging.logging import logger
from avplayer.media.hls_output_options import HlsOutputOptions
from avplayer.media.media_callbacks import (
    AsyncMediaCallbacksInterface,
    MediaCallbacks,
    MediaCallbacksInterface,
)

PACKET_TYPE_VIDEO: Final[str] = "video"
PACKET_TYPE_AUDIO: Final[str] = "audio"

AUDIO_PTIME: Final[float] = 0.020  # 20ms audio packetization


class MediaWorker:
    def __init__(
        self,
        loop: Optional[AbstractEventLoop],
        thread_quit: Event,
        input_container: InputContainer,
        output_container: Optional[OutputContainer],
        streams: List[Stream],
        video_queue: Optional[FrameCollection] = None,
        audio_queue: Optional[FrameCollection] = None,
        throttle_playback=False,
        destination: Optional[Union[str, HlsOutputOptions]] = None,
        callbacks: Optional[MediaCallbacks] = None,
    ):
        self._loop = loop
        self._thread_quit = thread_quit
        self._input_container = input_container
        self._output_container = output_container
        self._streams = streams
        self._video_queue = video_queue
        self._audio_queue = audio_queue
        self._throttle_playback = throttle_playback
        self._destination = destination
        self._callbacks = callbacks
        self._re_request_wait_seconds = 0.001

        self._audio_fifo = AudioFifo()
        self._audio_format_name = "s16"
        self._audio_layout_name = "stereo"
        self._audio_sample_rate = 48000
        self._audio_samples = 0
        self._audio_samples_per_frame = int(self._audio_sample_rate * AUDIO_PTIME)
        self._audio_resampler = AudioResampler(
            format=self._audio_format_name,
            layout=self._audio_layout_name,
            rate=self._audio_sample_rate,
        )

        self._start_time = time()
        self._packet_first_dts = None
        self._packet_first_pts = None
        self._video_first_pts = None

        # The presentation time in seconds for this frame.
        # This is the time at which the frame should be shown to the user.
        self._prev_frame_time: Optional[float] = None

        # Did you remove the first segment file?
        self._remove_first_segment_file = False

    @property
    def hls_output_mode(self) -> bool:
        if self._destination is None:
            return False
        else:
            return isinstance(self._destination, HlsOutputOptions)

    @property
    def hls_options(self) -> HlsOutputOptions:
        assert self._destination is not None
        assert isinstance(self._destination, HlsOutputOptions)
        return self._destination

    @property
    def drop_first_segment_file(self) -> bool:
        if not self.hls_output_mode:
            return False
        return self.hls_options.drop_first_segment_file

    def call_on_container_begin(self) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_container_begin):
            if not self._loop:
                return
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            run_coroutine_threadsafe(self._callbacks.on_container_begin(), self._loop)
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_container_begin()

    def call_on_container_end(self) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_container_end):
            if not self._loop:
                return
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            run_coroutine_threadsafe(self._callbacks.on_container_end(), self._loop)
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_container_end()

    def call_on_video_frame(
        self, frame: ndarray, start: datetime, last: datetime
    ) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_video_frame):
            if not self._loop:
                return
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            run_coroutine_threadsafe(
                self._callbacks.on_video_frame(frame, start, last),
                self._loop,
            )
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_video_frame(frame, start, last)

    def call_on_audio_frame(
        self, frame: ndarray, start: datetime, last: datetime
    ) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_audio_frame):
            if not self._loop:
                return
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            run_coroutine_threadsafe(
                self._callbacks.on_audio_frame(frame, start, last),
                self._loop,
            )
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_audio_frame(frame, start, last)

    def call_on_segment(
        self, directory: str, filename: str, start: datetime, last: datetime
    ) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_segment):
            if not self._loop:
                return
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            run_coroutine_threadsafe(
                self._callbacks.on_segment(directory, filename, start, last),
                self._loop,
            )
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_segment(directory, filename, start, last)

    def put_video_frame(self, frame: Frame) -> ndarray:
        assert self._video_queue is not None
        assert not self._video_queue.closed
        return self._video_queue.update_newest_array_and_put(frame)

    def put_audio_frame(self, frame: Frame) -> ndarray:
        assert self._audio_queue is not None
        assert not self._audio_queue.closed
        return self._audio_queue.update_newest_array_and_put(frame)

    def remove_hls_cached_files(self) -> None:
        assert self.hls_output_mode
        for filename in os.listdir(self.hls_options.cache_dir):
            filepath = os.path.join(self.hls_options.cache_dir, filename)
            os.remove(filepath)
            logger.warning(f"Remove HLS cache file: {filepath}")

    def find_hls_cached_filename(self) -> Optional[str]:
        assert self.hls_output_mode
        files = os.listdir(self.hls_options.cache_dir)
        if files:
            return files[0]
        else:
            return None

    def remove_hls_cached_filename(self, filename: str) -> None:
        assert self.hls_output_mode
        path = os.path.join(self.hls_options.cache_dir, filename)
        os.remove(path)

    def get_classname(self) -> str:
        return type(self).__name__

    def run(self) -> None:
        try:
            self.call_on_container_begin()

            if self.hls_output_mode:
                self.remove_hls_cached_files()

            logger.debug(f"{self.get_classname()} Run the main loop ...")

            while not self._thread_quit.is_set():
                try:
                    self._main_loop()
                except (AVError, StopIteration) as e:
                    if isinstance(e, AvFFmpegError) and e.errno == EAGAIN:
                        sleep(self._re_request_wait_seconds)
                        continue
                    else:
                        raise
                except InterruptedError:
                    logger.info(f"{self.get_classname()} Interrupt signal detected")
                    break
        finally:
            try:
                self.call_on_container_end()
            except BaseException as e:
                logger.exception(e)
            finally:
                if self._video_queue:
                    self._video_queue.close()
                if self._audio_queue:
                    self._audio_queue.close()
            logger.debug(f"{self.get_classname()} The main loop is complete")

    def _main_loop(self) -> None:
        start = datetime.now().astimezone()

        for packet in self._input_container.demux(*self._streams):
            if self._thread_quit.is_set():
                raise InterruptedError

            last = datetime.now().astimezone()
            assert isinstance(packet, Packet)

            # We need to skip the `flushing` packets that `demux` generates.
            if packet.dts is None:
                return

            if self._packet_first_dts is None:
                self._packet_first_dts = packet.dts
            if self._packet_first_pts is None:
                self._packet_first_pts = packet.pts

            output_stream = None

            if packet.stream.type == PACKET_TYPE_VIDEO:
                self._on_video_packet(packet, start, last)
                if self._output_container is not None:
                    output_streams = self._output_container.streams.video
                    output_stream = output_streams[0]
            elif packet.stream.type == PACKET_TYPE_AUDIO:
                self._on_audio_packet(packet, start, last)
                if self._output_container is not None:
                    output_streams = self._output_container.streams.audio
                    output_stream = output_streams[0]
            else:
                assert False, "Inaccessible section"

            if output_stream is not None:
                assert self._output_container is not None
                packet.dts -= self._packet_first_dts
                packet.pts -= self._packet_first_pts
                packet.stream = output_stream
                try:
                    self._output_container.mux(packet)
                except BaseException as e:
                    logger.error(f"A muxing error in the output container: {e}")

                if self.hls_output_mode:
                    segment_filename = self.find_hls_cached_filename()
                    if segment_filename:
                        self._process_hls_segment_caching(segment_filename, start, last)
                        start = last

    def _process_hls_segment_caching(
        self,
        segment_filename: str,
        start: datetime,
        last: datetime,
    ) -> None:
        assert segment_filename.endswith(".ts")
        assert self.hls_output_mode

        if self.drop_first_segment_file:
            if not self._remove_first_segment_file:
                logger.debug(f"Remove the first segment file: {segment_filename}")
                self.remove_hls_cached_filename(segment_filename)
                self._remove_first_segment_file = True
                return

        cached_path = os.path.join(self.hls_options.cache_dir, segment_filename)
        assert os.path.isfile(cached_path)

        directory, filename = parse_dirname_and_filename(start)
        filename += ".ts"

        record_directory = os.path.join(self.hls_options.destination_dir, directory)
        if not os.path.isdir(record_directory):
            os.mkdir(record_directory)

        assert os.path.isdir(record_directory)
        archive_path = os.path.join(record_directory, filename)
        assert not os.path.exists(archive_path)

        # TODO: Test different filesystems: `shutil.move()`

        os.replace(cached_path, archive_path)

        self.call_on_segment(
            directory=directory,
            filename=filename,
            start=deepcopy(start),
            last=deepcopy(last),
        )

    def _adjust_presentation_time(self):
        if self._throttle_playback and self._prev_frame_time is not None:
            elapsed_time = time() - self._start_time
            if self._prev_frame_time > elapsed_time + 1:
                sleep(0.1)

    def _on_video_packet(self, packet: Packet, start: datetime, last: datetime) -> None:
        for frame in packet.decode():
            assert isinstance(frame, AvVideoFrame)
            self._adjust_presentation_time()
            self._on_video_frame(frame, start, last)

            if self._thread_quit.is_set():
                raise InterruptedError

    def _on_audio_packet(self, packet: Packet, start: datetime, last: datetime) -> None:
        for frame in packet.decode():
            assert isinstance(frame, AudioFrame)
            self._adjust_presentation_time()
            self._on_audio_frame(frame, start, last)

            if self._thread_quit.is_set():
                raise InterruptedError

    def _on_video_frame(
        self, frame: AvVideoFrame, start: datetime, last: datetime
    ) -> None:
        if self._video_queue is None:
            raise RuntimeError("Video Queue is None")
        if self._video_queue.closed:
            raise RuntimeError("Video Queue is closed")

        if frame.pts is None:
            logger.warning(
                f"MediaWorker[{self._input_container.name}]"
                " Skipping video frame with no pts"
            )
            return

        # Video from a webcam doesn't start at pts 0, cancel out offset
        if self._video_first_pts is None:
            self._video_first_pts = frame.pts
        frame.pts -= self._video_first_pts

        self._prev_frame_time = frame.time

        newest_video_data = self.put_video_frame(frame)
        self.call_on_video_frame(
            newest_video_data,
            deepcopy(start),
            deepcopy(last),
        )

    def _on_audio_frame(
        self, frame: AudioFrame, start: datetime, last: datetime
    ) -> None:
        if self._audio_queue is None:
            raise RuntimeError("Audio Queue is None")
        if self._audio_queue.closed:
            raise RuntimeError("Audio Queue is closed")

        if (
            frame.format.name != self._audio_format_name
            or frame.layout.name != self._audio_layout_name
            or frame.sample_rate != self._audio_sample_rate
        ):
            frame.pts = None
            frame = self._audio_resampler.resample(frame)

        # Fix timestamps
        frame.pts = self._audio_samples
        frame.time_base = Fraction(1, self._audio_sample_rate)
        self._audio_samples += frame.samples

        self._audio_fifo.write(frame)
        while True:
            frame = self._audio_fifo.read(self._audio_samples_per_frame)
            if not frame:
                break

            self._prev_frame_time = frame.time
            newest_audio_data = self.put_audio_frame(frame)
            self.call_on_audio_frame(
                newest_audio_data,
                deepcopy(start),
                deepcopy(last),
            )


def media_worker_main(*args, **kwargs) -> None:
    worker = MediaWorker(*args, **kwargs)
    worker.run()

# -*- coding: utf-8 -*-

import os
from asyncio import AbstractEventLoop
from io import StringIO
from threading import Event, Thread
from typing import List, Optional, Union

from av import open as av_open  # noqa
from av.container import InputContainer, OutputContainer
from av.stream import Stream

from avplayer.collections.frame_collection import FrameCollection
from avplayer.logging.logging import logger
from avplayer.media.av_helper import init_stream
from avplayer.media.hls_output_options import HlsOutputOptions
from avplayer.media.media_callbacks import MediaCallbacks
from avplayer.media.media_kind import MediaKind
from avplayer.media.media_options import MediaOptions
from avplayer.media.media_worker import media_worker_main
from avplayer.variables import REALTIME_FORMATS, UNKNOWN_DEVICE_UID


class MediaPlayer:

    _address: Union[str, int]
    _destination: Optional[Union[str, HlsOutputOptions]]
    _callbacks: Optional[MediaCallbacks]
    _options: MediaOptions

    _thread: Optional[Thread]
    _thread_quit: Optional[Event]

    _input_container: Optional[InputContainer]
    _output_container: Optional[OutputContainer]
    _streams: List[Stream]

    _video_queue: Optional[FrameCollection]
    _audio_queue: Optional[FrameCollection]

    _throttle_playback: bool

    def __init__(
        self,
        address: Union[str, int],
        destination: Optional[Union[str, HlsOutputOptions]] = None,
        callbacks: Optional[MediaCallbacks] = None,
        options: Optional[MediaOptions] = None,
    ):
        self._address = address
        self._destination = destination
        self._callbacks = callbacks
        self._options = options if options else MediaOptions()

        self._thread = None
        self._thread_quit = None

        self._input_container = None
        self._output_container = None
        self._streams = list()

        self._video_queue = None
        self._audio_queue = None

        self._throttle_playback = False

    @property
    def throttle_playback(self) -> bool:
        return self._throttle_playback

    @property
    def is_realtime(self) -> bool:
        return not self._throttle_playback

    @property
    def name(self) -> str:
        return self._options.name if self._options.name else str()

    @property
    def device_uid(self) -> int:
        return self._options.device if self._options.device else UNKNOWN_DEVICE_UID

    @property
    def group_name(self) -> str:
        return self._options.group if self._options.group else str()

    @property
    def project_name(self) -> str:
        return self._options.project if self._options.project else str()

    @property
    def class_name(self) -> str:
        buffer = StringIO()
        buffer.write(f"{type(self).__name__}[name='{self.name}'")
        device_uid = self.device_uid
        if device_uid != UNKNOWN_DEVICE_UID:
            buffer.write(f",device={self.device_uid}")
        buffer.write("]")
        return buffer.getvalue()

    @property
    def video_queue(self) -> Optional[FrameCollection]:
        return self._video_queue

    @property
    def audio_queue(self) -> Optional[FrameCollection]:
        return self._audio_queue

    def __repr__(self) -> str:
        return self.class_name

    def __str__(self) -> str:
        return self.class_name

    def is_unknown_device_uid(self) -> bool:
        return self.device_uid == UNKNOWN_DEVICE_UID

    def is_open(self) -> bool:
        return self._input_container is not None

    def open(self, loop: Optional[AbstractEventLoop] = None) -> None:
        try:
            assert self._input_container is None
            self._create_media()

            assert self._thread is None
            assert self._thread_quit is None
            self._start_thread(loop)
        except BaseException as e:
            logger.error(e)
            if self._thread:
                self._stop_thread()
            if self._input_container:
                self._destroy_media()
            raise

    def close(self) -> None:
        assert self._thread is not None
        assert self._thread_quit is not None
        self._stop_thread()

        assert self._input_container is not None
        self._destroy_media()

    def _create_input_container(self) -> InputContainer:
        av_address = self._address
        av_format = self._options.format
        av_input_options = self._options.input_options
        av_container_options = self._options.container_options
        av_stream_options = self._options.stream_options
        av_metadata_encoding = self._options.get_metadata_encoding()
        av_metadata_errors = self._options.get_metadata_errors()
        av_buffer_size = self._options.get_buffer_size()
        av_timeout = self._options.get_timeout()
        av_timeout_message = self._options.get_timeout_argument_message()

        _args_message = f"address='{av_address}',{av_timeout_message}"
        logger.debug(f"Input container opening ... ({_args_message})")

        input_container = av_open(
            file=av_address,
            mode="r",
            format=av_format,
            options=av_input_options,
            container_options=av_container_options,
            stream_options=av_stream_options,
            metadata_encoding=av_metadata_encoding,
            metadata_errors=av_metadata_errors,
            buffer_size=av_buffer_size,
            timeout=av_timeout,
        )
        assert isinstance(input_container, InputContainer)
        logger.info("Input container opened successfully")

        return input_container

    def _create_output_container(
        self,
        video_stream: Optional[Stream] = None,
        audio_stream: Optional[Stream] = None,
    ) -> OutputContainer:
        av_output_options = self._options.output_options
        av_metadata_encoding = self._options.get_metadata_encoding()
        av_metadata_errors = self._options.get_metadata_errors()
        av_buffer_size = self._options.get_buffer_size()
        av_timeout = self._options.get_timeout()

        assert self._destination is not None
        if isinstance(self._destination, str):
            output_filename = self._destination
            output_options = av_output_options
        elif isinstance(self._destination, HlsOutputOptions):
            output_filename = self._destination.get_hls_filename()
            output_options = self._destination.get_hls_options()
            if av_output_options is not None:
                assert isinstance(av_output_options, dict)
                output_options.update(av_output_options)
        else:
            assert False, "Inaccessible section"

        assert output_filename is not None
        assert output_options is not None
        assert isinstance(output_filename, str)
        assert isinstance(output_options, dict)

        logger.debug(f"Output container opening ... ({output_filename})")
        output_container = av_open(
            file=output_filename,
            mode="w",
            options=output_options,
            metadata_encoding=av_metadata_encoding,
            metadata_errors=av_metadata_errors,
            buffer_size=av_buffer_size,
            timeout=av_timeout,
        )
        assert isinstance(output_container, OutputContainer)
        logger.info("Output container opened successfully")

        if video_stream is not None:
            output_container.add_stream(template=video_stream)  # noqa
        if audio_stream is not None:
            output_container.add_stream(template=audio_stream)  # noqa

        return output_container

    def _create_media(self) -> None:
        destination = self._destination
        if destination and isinstance(destination, HlsOutputOptions):
            cache_dir = destination.cache_dir
            if not os.path.isdir(cache_dir):
                raise NotADirectoryError(f"Not found cache directory: '{cache_dir}'")
            if not os.access(cache_dir, os.W_OK):
                raise PermissionError(f"Write permission is required: '{cache_dir}'")

        video_index = self._options.video_index
        audio_index = self._options.audio_index
        go_faster = self._options.go_faster
        low_delay = self._options.low_delay
        max_frame_queue = self._options.get_max_frame_queue()

        input_container = self._create_input_container()
        output_container: Optional[OutputContainer] = None

        try:
            video_stream = init_stream(
                kind=MediaKind.Video,
                index=video_index,
                streams=input_container.streams.video,
                max_queue=max_frame_queue,
                go_faster=go_faster,
                low_delay=low_delay,
            )
            audio_stream = init_stream(
                kind=MediaKind.Audio,
                index=audio_index,
                streams=input_container.streams.audio,
                max_queue=max_frame_queue,
                go_faster=go_faster,
                low_delay=low_delay,
            )

            if video_stream is not None or audio_stream is not None:
                if self._destination is not None:
                    output_container = self._create_output_container(
                        video_stream[0] if video_stream is not None else None,
                        audio_stream[0] if audio_stream is not None else None,
                    )

            streams: List[Stream] = list()
            video_queue: Optional[FrameCollection] = None
            audio_queue: Optional[FrameCollection] = None

            if video_stream is not None:
                streams.append(video_stream[0])
                video_queue = video_stream[1]
            if audio_stream is not None:
                streams.append(audio_stream[0])
                audio_queue = audio_stream[1]

            # Check whether we need to throttle playback
            container_format = set(input_container.format.name.split(","))
            throttle_playback = not container_format.intersection(REALTIME_FORMATS)
        except:  # noqa
            input_container.close()
            if output_container is not None:
                output_container.close()
            raise
        else:
            self._input_container = input_container
            self._output_container = output_container
            self._streams = streams
            self._video_queue = video_queue
            self._audio_queue = audio_queue
            self._throttle_playback = throttle_playback

    def _destroy_media(self) -> None:
        if self._input_container:
            self._input_container.close()
            self._input_container = None
        if self._output_container:
            for output_stream in self._output_container.streams:
                assert isinstance(output_stream, Stream)
                for output_packet in output_stream.encode(None):
                    self._output_container.mux(output_packet)
            self._output_container.close()
            self._output_container = None
        self._streams.clear()
        if self._video_queue is not None:
            self._video_queue.close()
            self._video_queue = None
        if self._audio_queue is not None:
            self._audio_queue.close()
            self._audio_queue = None
        self._throttle_playback = False

    def _start_thread(self, loop: Optional[AbstractEventLoop] = None) -> None:
        logger.debug("Starting worker thread ...")
        assert self._input_container is not None
        self._thread_quit = Event()
        self._thread = Thread(
            name=self.class_name,
            target=media_worker_main,
            args=(
                loop,
                self._thread_quit,
                self._input_container,
                self._output_container,
                self._streams,
                self._video_queue,
                self._audio_queue,
                self._throttle_playback,
                self._destination,
                self._callbacks,
            ),
        )
        self._thread.start()
        logger.info("The worker thread is started.")

    def _stop_thread(self) -> None:
        logger.debug("Stopping worker thread ...")
        if self._thread_quit:
            self._thread_quit.set()
        if self._thread:
            self._thread.join()
        self._thread_quit = None  # Must be assigned as `None` after join.
        self._thread = None
        logger.info("The worker thread is stopped.")

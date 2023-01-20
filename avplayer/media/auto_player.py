# -*- coding: utf-8 -*-

from asyncio import Event, get_running_loop
from asyncio import sleep as asyncio_sleep
from copy import deepcopy
from datetime import datetime
from enum import Enum, auto, unique
from inspect import iscoroutinefunction
from io import StringIO
from typing import Optional, Union

from numpy import ndarray
from overrides import overrides

from avplayer.logging.logging import logger
from avplayer.media.hls_output_options import HlsOutputOptions
from avplayer.media.media_callbacks import (
    AsyncMediaCallbacksInterface,
    MediaCallbacks,
    MediaCallbacksInterface,
)
from avplayer.media.media_options import MediaOptions
from avplayer.media.media_player import MediaPlayer
from avplayer.variables import UNKNOWN_DEVICE_UID


class IllegalStateError(RuntimeError):
    pass


@unique
class AutoPlayerState(Enum):
    Closed = auto()
    Opening = auto()
    Running = auto()
    Closing = auto()


class AutoPlayer(AsyncMediaCallbacksInterface):

    _player: Optional[MediaPlayer]

    def __init__(
        self,
        address: Union[str, int],
        destination: Optional[Union[str, HlsOutputOptions]] = None,
        callbacks: Optional[MediaCallbacks] = None,
        options: Optional[MediaOptions] = None,
    ):
        self._address = deepcopy(address)
        self._destination = deepcopy(destination)
        self._callbacks = deepcopy(callbacks)
        self._options = deepcopy(options)

        self._reconnect_wait_seconds = 4.0
        self._state = AutoPlayerState.Closed
        self._exit = True
        self._event = Event()
        self._player = None

    @property
    def state(self) -> AutoPlayerState:
        return self._state

    @property
    def exiting(self) -> bool:
        return self._exit

    @property
    def name(self) -> str:
        if self._options and self._options.name:
            return self._options.name
        else:
            return str()

    @property
    def device_uid(self) -> int:
        if self._options and self._options.device:
            return self._options.device
        else:
            return UNKNOWN_DEVICE_UID

    @property
    def group_name(self) -> str:
        if self._options and self._options.group:
            return self._options.group
        else:
            return str()

    @property
    def project_name(self) -> str:
        if self._options and self._options.project:
            return self._options.project
        else:
            return str()

    @property
    def class_name(self) -> str:
        buffer = StringIO()
        buffer.write(f"{type(self).__name__}[name='{self.name}'")
        device_uid = self.device_uid
        if device_uid != UNKNOWN_DEVICE_UID:
            buffer.write(f",device={self.device_uid}")
        buffer.write("]")
        return buffer.getvalue()

    def __repr__(self) -> str:
        return self.class_name

    def __str__(self) -> str:
        return self.class_name

    def is_unknown_device_uid(self) -> bool:
        return self.device_uid == UNKNOWN_DEVICE_UID

    def is_open(self) -> bool:
        return self._player is not None

    @overrides
    async def on_container_begin(self) -> None:
        if self._callbacks:
            if iscoroutinefunction(self._callbacks.on_container_begin):
                assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
                await self._callbacks.on_container_begin()
            else:
                assert isinstance(self._callbacks, MediaCallbacksInterface)
                self._callbacks.on_container_begin()

        self._state = AutoPlayerState.Running

    @overrides
    async def on_container_end(self) -> None:
        self._state = AutoPlayerState.Closing

        try:
            if self._callbacks:
                if iscoroutinefunction(self._callbacks.on_container_end):
                    assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
                    await self._callbacks.on_container_end()
                else:
                    assert isinstance(self._callbacks, MediaCallbacksInterface)
                    self._callbacks.on_container_end()
        finally:
            self._event.set()

    @overrides
    async def on_video_frame(
        self, frame: ndarray, start: datetime, last: datetime
    ) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_video_frame):
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            await self._callbacks.on_video_frame(frame, start, last)
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_video_frame(frame, start, last)

    @overrides
    async def on_audio_frame(
        self, frame: ndarray, start: datetime, last: datetime
    ) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_audio_frame):
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            await self._callbacks.on_audio_frame(frame, start, last)
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_audio_frame(frame, start, last)

    @overrides
    async def on_segment(
        self, directory: str, filename: str, start: datetime, last: datetime
    ) -> None:
        if not self._callbacks:
            return

        if iscoroutinefunction(self._callbacks.on_segment):
            assert isinstance(self._callbacks, AsyncMediaCallbacksInterface)
            await self._callbacks.on_segment(directory, filename, start, last)
        else:
            assert isinstance(self._callbacks, MediaCallbacksInterface)
            self._callbacks.on_segment(directory, filename, start, last)

    async def run(self) -> None:
        if self._state != AutoPlayerState.Closed:
            raise IllegalStateError

        self._exit = False

        while not self._exit:
            self._player = MediaPlayer(
                address=self._address,
                destination=self._destination,
                callbacks=self,
                options=self._options,
            )
            self._event.clear()

            try:
                self._state = AutoPlayerState.Opening
                self._player.open(loop=get_running_loop())
                await self._event.wait()
            except BaseException as e:
                logger.exception(e)
            finally:
                try:
                    self._player.close()
                except BaseException as e:
                    logger.exception(e)
                finally:
                    sec_text = f"{self._reconnect_wait_seconds:.2}"
                    logger.debug(f"Reconnect waiting ... {sec_text}s")
                    await asyncio_sleep(self._reconnect_wait_seconds)

        self._state = AutoPlayerState.Closed

    async def close(self) -> None:
        if self._state == AutoPlayerState.Closed:
            raise IllegalStateError

        self._exit = True
        self._event.set()

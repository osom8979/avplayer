# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union

from numpy import ndarray


class MediaCallbacksInterface(metaclass=ABCMeta):
    @abstractmethod
    def on_container_begin(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_container_end(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_video_frame(self, frame: ndarray, start: datetime, last: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_audio_frame(self, frame: ndarray, start: datetime, last: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_segment(
        self, directory: str, filename: str, start: datetime, last: datetime
    ) -> None:
        raise NotImplementedError


class AsyncMediaCallbacksInterface(metaclass=ABCMeta):
    @abstractmethod
    async def on_container_begin(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_container_end(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_video_frame(
        self, frame: ndarray, start: datetime, last: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_audio_frame(
        self, frame: ndarray, start: datetime, last: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_segment(
        self, directory: str, filename: str, start: datetime, last: datetime
    ) -> None:
        raise NotImplementedError


MediaCallbacks = Union[
    MediaCallbacksInterface,
    AsyncMediaCallbacksInterface,
]

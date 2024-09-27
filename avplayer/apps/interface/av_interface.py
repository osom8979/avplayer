# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray


class AvInterface(ABC):
    @abstractmethod
    def on_open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        raise NotImplementedError


class AsyncAvInterface(ABC):
    @abstractmethod
    async def on_open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        raise NotImplementedError


class AsyncAvTckInterface(AsyncAvInterface):
    @abstractmethod
    async def on_resize(self, width: int, height: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_key(self, keysym: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_grap(self, image: NDArray[uint8]) -> NDArray[uint8]:
        raise NotImplementedError


class AsyncCvInterface(AsyncAvInterface):
    @abstractmethod
    def on_reboot(self, reason: Optional[BaseException]) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_frame(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        raise NotImplementedError

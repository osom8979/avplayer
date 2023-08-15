# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray


class AsyncAvInterface(metaclass=ABCMeta):
    @abstractmethod
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        raise NotImplementedError


class AsyncAvWebInterface(AsyncAvInterface):
    @abstractmethod
    async def on_key_pressed(
        self, keycode: str, shift: bool, ctrl: bool, alt: bool
    ) -> None:
        raise NotImplementedError

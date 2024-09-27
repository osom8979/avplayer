# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.async_av_tk import AsyncAvTk
from avplayer.apps.interface.av_interface import AsyncAvTckInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger


class AioTk(AsyncAvTk, AsyncAvTckInterface):
    def __init__(self, config: AvConfig, coro=None):
        super().__init__(config, self)
        self._is_coroutine = iscoroutinefunction(coro)
        self._coro = coro

    @override
    async def on_open(self) -> None:
        logger.info("on_open()")

    @override
    async def on_close(self) -> None:
        logger.info("on_close()")

    @override
    async def on_resize(self, width: int, height: int) -> None:
        logger.info(f"on_resize(width={width},height={height})")

    @override
    async def on_key(self, keysym: str) -> None:
        logger.info(f"on_key(keysym='{keysym}')")
        if keysym in ("Q", "q", "Escape"):
            self.quit()

    @override
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            if self._is_coroutine:
                return await self._coro(image)
            else:
                return self._coro(image)
        else:
            return image

    @override
    def on_grap(self, image: NDArray[uint8]) -> NDArray[uint8]:
        return image

# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.async_av_app import AsyncAvApp
from avplayer.apps.interface.av_interface import AsyncAvInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger


class AioApp(AsyncAvApp, AsyncAvInterface):
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
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            if self._is_coroutine:
                return await self._coro(image)
            else:
                return self._coro(image)
        else:
            return image

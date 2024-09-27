# -*- coding: utf-8 -*-

from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.async_cv_app import AsyncCvApp
from avplayer.apps.interface.av_interface import AsyncCvInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger


class AioCv(AsyncCvApp, AsyncCvInterface):
    def __init__(self, config: AvConfig, coro=None):
        super().__init__(config, self)
        self._coro = coro

    @override
    async def on_open(self) -> None:
        logger.info("on_open()")

    @override
    async def on_close(self) -> None:
        logger.info("on_close()")

    @override
    def on_reboot(self, reason: Optional[BaseException]) -> None:
        logger.info(f"on_reboot(reason='{str(reason)}')")

    @override
    def on_frame(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            return self._coro(image)
        else:
            return image

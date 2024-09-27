# -*- coding: utf-8 -*-

from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.av_app import AvApp
from avplayer.apps.interface.av_interface import AvInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger


class IoApp(AvApp, AvInterface):
    def __init__(self, config: AvConfig, coro=None):
        super().__init__(config, self)
        self._coro = coro

    @override
    def on_open(self) -> None:
        logger.info("on_open()")

    @override
    def on_close(self) -> None:
        logger.info("on_close()")

    @override
    def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            return self._coro(image)
        else:
            return image

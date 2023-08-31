# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio.exceptions import CancelledError
from inspect import iscoroutinefunction
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.async_av_app import AsyncAvApp
from avplayer.apps.base.async_av_tk import AsyncAvTk
from avplayer.apps.base.av_app import AvApp
from avplayer.apps.base.base import AppInterface
from avplayer.apps.interface.av_interface import AsyncAvInterface, AvInterface
from avplayer.avconfig import AvAppType, AvConfig
from avplayer.logging.logging import logger


class IoApp(AvApp, AvInterface):
    def __init__(self, config: AvConfig, coro=None):
        super().__init__(config, self)
        self._coro = coro

    @override
    def on_open(self) -> None:
        pass

    @override
    def on_close(self) -> None:
        pass

    @override
    def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            return self._coro(image)
        else:
            return image


class AioApp(AsyncAvApp, AsyncAvInterface):
    def __init__(self, config: AvConfig, coro=None):
        super().__init__(config, self)
        self._is_coroutine = iscoroutinefunction(coro)
        self._coro = coro

    @override
    async def on_open(self) -> None:
        pass

    @override
    async def on_close(self) -> None:
        pass

    @override
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            if self._is_coroutine:
                return await self._coro(image)
            else:
                return self._coro(image)
        else:
            return image


class AioTk(AsyncAvTk, AsyncAvInterface):
    def __init__(self, config: AvConfig, coro=None):
        super().__init__(config, self)
        self._is_coroutine = iscoroutinefunction(coro)
        self._coro = coro

    @override
    async def on_open(self) -> None:
        pass

    @override
    async def on_close(self) -> None:
        pass

    @override
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            if self._is_coroutine:
                return await self._coro(image)
            else:
                return self._coro(image)
        else:
            return image


def create_app(config: AvConfig, coro=None) -> AppInterface:
    app_type = config.app_type
    if app_type == AvAppType.IO:
        return IoApp(config, coro)
    elif app_type == AvAppType.AIO:
        return AioApp(config, coro)
    elif app_type == AvAppType.AIOTK:
        return AioTk(config, coro)
    else:
        raise ValueError(f"Unknown app type: {app_type}")


def default_main_with_config(config: AvConfig, coro=None) -> int:
    app = create_app(config, coro)
    try:
        app.start()
    except CancelledError:
        logger.debug("An cancelled signal was detected")
        return 0
    except KeyboardInterrupt:
        logger.warning("An interrupt signal was detected")
        return 0
    except Exception as e:
        logger.exception(e)
        return 1
    except BaseException as e:
        logger.exception(e)
        return 1
    else:
        return 0


def default_main(args: Namespace, coro=None) -> int:
    config = AvConfig.from_namespace(args)
    config.logging_params()
    return default_main_with_config(config, coro)

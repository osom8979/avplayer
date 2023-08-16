# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio.exceptions import CancelledError
from inspect import iscoroutinefunction
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.aio.run import aio_run
from avplayer.apps.base.async_av_app_base import AsyncAvAppBase
from avplayer.apps.base.async_av_web_app_base import AsyncAvWebAppBase
from avplayer.apps.base.av_app_base import AvAppBase
from avplayer.apps.interface.async_av_interface import (
    AsyncAvInterface,
    AsyncAvWebInterface,
)
from avplayer.apps.interface.av_interface import AvInterface
from avplayer.config import Config
from avplayer.logging.logging import logger


class IoApp(AvAppBase, AvInterface):
    def __init__(self, config: Config, coro=None):
        super().__init__(config, self)
        self._coro = coro

    @override
    def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            return self._coro(image)
        else:
            return image


class AioApp(AsyncAvAppBase, AsyncAvInterface):
    def __init__(self, config: Config, coro=None):
        super().__init__(config, self)
        self._is_coroutine = iscoroutinefunction(coro)
        self._coro = coro

    @override
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._coro is not None:
            if self._is_coroutine:
                return await self._coro(image)
            else:
                return self._coro(image)
        else:
            return image


class AioWebApp(AsyncAvWebAppBase, AsyncAvWebInterface):
    def __init__(self, config: Config, coro=None, keydown=None):
        super().__init__(config, self)
        self._is_coroutine = iscoroutinefunction(coro)
        self._coro = coro
        self._is_coroutine_keydown = iscoroutinefunction(keydown)
        self._keydown = keydown

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
    async def on_key_pressed(
        self, keycode: str, shift: bool, ctrl: bool, alt: bool
    ) -> None:
        if self._keydown is None:
            return
        if self._is_coroutine_keydown:
            await self._keydown(keycode, shift, ctrl, alt)
        else:
            self._keydown(keycode, shift, ctrl, alt)


def default_main(args: Namespace, coro=None, keydown=None) -> int:
    config = Config.from_namespace(args)
    config.logging_params()

    try:
        if config.is_io:
            IoApp(config, coro).start_app()
        elif config.is_aio:
            aio_run(AioApp(config, coro).start_async_app())
        elif config.is_aioweb:
            AioWebApp(config, coro, keydown).start_webserver_with_avio()
        else:
            raise NotImplementedError
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

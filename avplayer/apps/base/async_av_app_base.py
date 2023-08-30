# -*- coding: utf-8 -*-

from asyncio import AbstractEventLoop, get_running_loop, run_coroutine_threadsafe
from asyncio.exceptions import CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.aio.run import aio_run
from avplayer.apps.base.av_app_base import AvAppBase
from avplayer.apps.interface.av_interface import AsyncAvInterface
from avplayer.avconfig import AvConfig
from avplayer.debug.step_avg import StepAvg
from avplayer.logging.logging import logger
from avplayer.variables import VERBOSE_LEVEL_2


class AsyncAvAppBase(AvAppBase):
    _callback: Optional[AsyncAvInterface]  # type: ignore[assignment]

    def __init__(self, config: AvConfig, callback: Optional[AsyncAvInterface] = None):
        super().__init__(config, None)
        self._callback = callback

        self._async_enqueue_step = StepAvg(
            "AsyncEnqueue",
            logger,
            self.config.logging_step,
            self.config.verbose,
            VERBOSE_LEVEL_2,
        )
        self._async_imgproc_step = StepAvg(
            "AsyncImgproc",
            logger,
            self.config.logging_step,
            self.config.verbose,
            VERBOSE_LEVEL_2,
        )

    async def _call_async_image(self, image: NDArray[uint8], begin: datetime) -> None:
        self._async_enqueue_step.do_enter(begin)
        self._async_enqueue_step.do_exit()

        self._async_imgproc_step.do_enter()
        try:
            if self._callback is not None:
                next_image = await self._callback.on_image(image)
            else:
                next_image = image
        except BaseException as e:
            self._avio.latest_exception = e
            return
        else:
            try:
                self.avio.send(next_image)
            except BaseException as e:
                self._avio.latest_exception = e
                return
        finally:
            self._async_imgproc_step.do_exit()

    def _enqueue_on_image_coroutine(
        self, loop: AbstractEventLoop, image: NDArray[uint8]
    ) -> None:
        run_coroutine_threadsafe(self._call_async_image(image, datetime.now()), loop)

    async def _until_thread_complete(self) -> None:
        self._avio.open()

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            loop = get_running_loop()
            await loop.run_in_executor(
                executor,
                self._avio.run,
                partial(self._enqueue_on_image_coroutine, loop),
            )
        except CancelledError:
            logger.warning("An cancelled signal was detected")
            logger.warning("Enable streamer shutdown flag")
            self._avio.shutdown()

            logger.warning("Wait for the executor to exit ...")
            executor.shutdown(wait=True)
        finally:
            self._avio.close()

    async def _event_context_with_until_thread_complete(self) -> None:
        if self._callback:
            await self._callback.on_open()
            try:
                await self._until_thread_complete()
            finally:
                await self._callback.on_close()
        else:
            await self._until_thread_complete()

    @override
    def start(self) -> None:
        aio_run(
            self._event_context_with_until_thread_complete(),
            self.config.use_uvloop,
        )

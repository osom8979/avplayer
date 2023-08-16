# -*- coding: utf-8 -*-

from asyncio import AbstractEventLoop, get_running_loop, run_coroutine_threadsafe
from asyncio.exceptions import CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray

from avplayer.apps.base.av_app_base import AvAppBase
from avplayer.apps.interface.async_av_interface import AsyncAvInterface
from avplayer.config import Config
from avplayer.debug.step_avg import StepAvg
from avplayer.logging.logging import logger
from avplayer.variables import VERBOSE_LEVEL_2


class AsyncAvAppBase(AvAppBase):
    _callback: Optional[AsyncAvInterface]  # type: ignore[assignment]

    def __init__(self, config: Config, callback: Optional[AsyncAvInterface] = None):
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
            logger.exception(e)
        else:
            self.avio.send(next_image)
        finally:
            self._async_imgproc_step.do_exit()

    def _enqueue_on_image_coroutine(
        self, loop: AbstractEventLoop, image: NDArray[uint8]
    ) -> None:
        run_coroutine_threadsafe(self._call_async_image(image, datetime.now()), loop)

    async def start_async_app(self) -> None:
        executor = ThreadPoolExecutor(max_workers=1)
        self.open_avio()
        try:
            loop = get_running_loop()
            await loop.run_in_executor(
                executor,
                self.run_avio,
                partial(self._enqueue_on_image_coroutine, loop),
            )
        except CancelledError:
            logger.warning("An cancelled signal was detected")
            logger.warning("Enable streamer shutdown flag")
            self.shutdown_avio()

            logger.warning("Wait for the executor to exit ...")
            executor.shutdown(wait=True)
        finally:
            self.close_avio()

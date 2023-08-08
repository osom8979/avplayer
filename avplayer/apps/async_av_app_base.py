# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import AbstractEventLoop, get_running_loop, run_coroutine_threadsafe
from asyncio.exceptions import CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import partial

from numpy import uint8
from numpy.typing import NDArray

from avplayer.apps.async_av_interface import AsyncAvEmptyInterface
from avplayer.apps.av_app_base import AvAppBase
from avplayer.debug.step_avg import StepAvg
from avplayer.logging.logging import logger
from avplayer.variables import VERBOSE_LEVEL_2


class AsyncAvAppBase(AvAppBase, AsyncAvEmptyInterface):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._async_enqueue_step = StepAvg(
            "AsyncEnqueue",
            logger,
            self.logging_step,
            self.verbose,
            VERBOSE_LEVEL_2,
        )
        self._async_imgproc_step = StepAvg(
            "AsyncImgproc",
            logger,
            self.logging_step,
            self.verbose,
            VERBOSE_LEVEL_2,
        )

    async def _call_async_image(self, image: NDArray[uint8], begin: datetime) -> None:
        self._async_enqueue_step.do_enter(begin)
        self._async_enqueue_step.do_exit()

        self._async_imgproc_step.do_enter()
        try:
            next_image = await self.on_image(image)
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

    async def async_run_avio(self) -> None:
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

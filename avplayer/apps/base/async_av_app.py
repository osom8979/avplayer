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
from avplayer.apps.base.av_app import AvApp
from avplayer.apps.interface.av_interface import AsyncAvInterface
from avplayer.avconfig import AvConfig
from avplayer.debug.avg_stat import AvgStat
from avplayer.logging.logging import logger
from avplayer.variables import VERBOSE_LEVEL_1 as VL1
from avplayer.variables import VERBOSE_LEVEL_2 as VL2


class AsyncAvApp(AvApp):
    _callback: Optional[AsyncAvInterface]  # type: ignore[assignment]

    def __init__(self, config: AvConfig, callback: Optional[AsyncAvInterface] = None):
        super().__init__(config, None)
        self._callback = callback

        self._pub = 0
        self._sub = 0
        self._pubsub_threshold = 10
        self._frame_drop = False
        # If the consumption rate is slower than the production rate,
        # frames are dropped.

        step = self.config.logging_step
        verbose = self.config.verbose
        self._enqueue_step = AvgStat("Enqueue", logger, step, verbose, VL2)
        self._call_step = AvgStat("Call", logger, step, verbose, VL2)
        self._grab_stat = AvgStat("Grab", logger, step, verbose, VL2)

    async def _after(self, image: NDArray[uint8], begin: datetime) -> None:
        """
        [IMPORTANT]
        await function calls should be reduced as much as possible.
        """

        try:
            self._enqueue_step.do_enter(begin)
            self._enqueue_step.do_exit()

            with self._call_step:
                try:
                    if self._callback:
                        # [IMPORTANT] --------------------------------------#
                        # The callback must be the only await function call #
                        next_image = await self._callback.on_image(image)
                        # --------------------------------------------------#
                    else:
                        next_image = image
                except BaseException as e:
                    self._avio.latest_exception = e
                else:
                    if next_image is None:
                        return

                    with self._grab_stat:
                        try:
                            self.on_grab(next_image)
                        except BaseException as e:
                            logger.exception(e)

                    try:
                        self.avio.send(next_image)
                    except BaseException as e:
                        self._avio.latest_exception = e
        except BaseException as e:
            logger.exception(e)
        finally:
            self._sub += 1

    def on_grab(self, image: NDArray[uint8]) -> None:
        pass

    def _enqueue_on_image_coroutine(
        self, loop: AbstractEventLoop, image: NDArray[uint8]
    ) -> None:
        assert self._pub >= self._sub
        remain = self._pub - self._sub

        slow_consumption = remain >= self._pubsub_threshold
        if slow_consumption and self.config.verbose >= VL1:
            logger.warning("Frame consumption is slow ...")

        if slow_consumption and self.config.drop_slow_frame:
            return

        run_coroutine_threadsafe(self._after(image, datetime.now()), loop)
        self._pub += 1

    async def _run_avio(self) -> None:
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            loop = get_running_loop()
            await loop.run_in_executor(
                executor,
                self._avio.run,
                partial(self._enqueue_on_image_coroutine, loop),
            )
        except CancelledError:
            logger.debug("A 'cancel' signal was detected in the thread pool.")
        finally:
            if not self._avio.is_done_enabled:
                self._avio.done()

            logger.debug("Wait for the executor to exit ...")
            executor.shutdown(wait=True)
            logger.debug("Executor has terminated")

    async def _until_avio_complete(self) -> None:
        self._avio.open()
        try:
            await self._run_avio()
        finally:
            self._avio.close()

    async def _until_complete(self) -> None:
        if self._callback:
            await self._callback.on_open()
            try:
                await self._until_avio_complete()
            finally:
                await self._callback.on_close()
        else:
            await self._until_avio_complete()

    @override
    def start(self) -> None:
        aio_run(self._until_complete(), self.config.use_uvloop)

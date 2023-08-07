# -*- coding: utf-8 -*-

from abc import abstractmethod
from argparse import Namespace
from asyncio import AbstractEventLoop, get_running_loop, run_coroutine_threadsafe
from asyncio.exceptions import CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import Callable

from numpy import uint8
from numpy.typing import NDArray

from avplayer.apps.app_base import AppBase
from avplayer.av.av_io import AvIo
from avplayer.debug.step_avg import StepAvg
from avplayer.ffmpeg.ffmpeg import AUTOMATIC_DETECT_FILE_FORMAT
from avplayer.logging.logging import logger


class AsyncAvAppBase(AppBase):
    def __init__(self, args: Namespace, printer: Callable[..., None] = print):
        super().__init__(args, printer)

        destination = args.destination if args.destination else None
        file_format = self.inspect_format(destination) if destination else None

        self._streamer = AvIo(
            self.source,
            destination,
            file_format=file_format if file_format else AUTOMATIC_DETECT_FILE_FORMAT,
            source_size=self.source_size,
            destination_size=self.destination_size,
            logging_step=self.logging_step,
            verbose=self.verbose,
        )

        self._async_event_delay_step = StepAvg(
            "AsyncEventDelay",
            logger,
            self.logging_step,
            self.verbose,
            2,
        )
        self._async_event_imgproc_step = StepAvg(
            "AsyncEventImgproc",
            logger,
            self.logging_step,
            self.verbose,
            2,
        )

    @abstractmethod
    async def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        raise NotImplementedError

    async def _call_async_image(self, image: NDArray[uint8], begin: datetime) -> None:
        self._async_event_delay_step.do_enter(begin)
        self._async_event_delay_step.do_exit()

        self._async_event_imgproc_step.do_enter()
        try:
            next_image = await self.on_image(image)
        except BaseException as e:
            logger.exception(e)
        else:
            self._streamer.send(next_image)
        finally:
            self._async_event_imgproc_step.do_exit()

    def _async_image_wrapper(
        self, loop: AbstractEventLoop, image: NDArray[uint8]
    ) -> None:
        run_coroutine_threadsafe(self._call_async_image(image, datetime.now()), loop)

    def shutdown_streaming(self):
        self._streamer.shutdown()

    async def async_run_streamer(self) -> None:
        executor = ThreadPoolExecutor(max_workers=1)
        self._streamer.open()
        try:
            loop = get_running_loop()
            await loop.run_in_executor(
                executor,
                self._streamer.run,
                partial(self._async_image_wrapper, loop),
            )
        except CancelledError:
            logger.warning("An cancelled signal was detected")
            logger.warning("Enable streamer shutdown flag")
            self._streamer.shutdown()

            logger.warning("Wait for the executor to exit ...")
            executor.shutdown(wait=True)
        finally:
            self._streamer.close()

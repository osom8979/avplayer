# -*- coding: utf-8 -*-

from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.async_av_app import AsyncAvApp
from avplayer.apps.base.base import AppBase
from avplayer.apps.interface.av_interface import AsyncAvInterface, AsyncCvInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger


class AsyncCvApp(AppBase, AsyncAvInterface):
    _callback: Optional[AsyncCvInterface]  # type: ignore[assignment]
    _app: Optional[AsyncAvApp]

    def __init__(
        self,
        config: AvConfig,
        callback: Optional[AsyncCvInterface] = None,
    ):
        super().__init__(config)
        self._callback = callback

        import cv2

        self._cv2 = cv2
        self._exit_codes = self._config.cv_exit_codes
        self._manually_done = False
        self._app = None

    @property
    def config(self):
        return self._config

    @property
    def app(self):
        return self._app

    @property
    def title(self) -> str:
        return self._config.win_title

    @property
    def flags(self) -> int:
        if self._config.cv_flags:
            return self._config.cv_flags
        else:
            return self._cv2.WINDOW_NORMAL

    def done(self) -> None:
        self._manually_done = True
        if self._app is not None:
            self._app.avio.done()

    def show_image(self, image: NDArray[uint8]) -> None:
        self._cv2.imshow(self.title, image)

    def wait_key(self) -> int:
        return self._cv2.waitKey(1)

    def run_av_app(self) -> None:
        self._app = AsyncAvApp(config=self._config, callback=self)
        try:
            self._app.start()
        finally:
            self._app = None

    def run_av_app_infinitely(self) -> None:
        while not self._manually_done:
            reason: Optional[BaseException] = None

            try:
                self.run_av_app()
            except KeyboardInterrupt:
                self.done()
                return
            except BaseException as e:
                logger.exception(e)
                reason = e

            if self._callback is not None:
                self._callback.on_reboot(reason)

    @override
    def start(self) -> None:
        if not self._config.cv_headless:
            # [IMPORTANT]
            # You must call cv2's highgui before avplayer.
            self._cv2.namedWindow(self.title, self.flags)

        try:
            if self._config.cv_infinity:
                self.run_av_app_infinitely()
            else:
                self.run_av_app()
        finally:
            if not self._config.cv_headless:
                self._cv2.destroyWindow(self.title)

    @override
    async def on_open(self):
        if self._callback is not None:
            await self._callback.on_open()

    @override
    async def on_close(self):
        if self._callback is not None:
            await self._callback.on_close()

    @override
    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._callback is not None:
            preview = self._callback.on_frame(image)
        else:
            preview = image

        if not self._config.cv_headless and preview is not None:
            self.show_image(preview)
            if self._exit_codes:
                keycode = self.wait_key() & 0xFF
                if keycode in self._exit_codes:
                    self.done()

        return preview

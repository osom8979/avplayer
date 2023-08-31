# -*- coding: utf-8 -*-

from asyncio import create_task
from asyncio import sleep as asyncio_sleep
from asyncio import Event as AsyncEvent
from threading import Lock
from tkinter import NW, Canvas, Event, TclError, Tk
from typing import Optional, Tuple
from _tkinter import DONT_WAIT

from overrides import override

from avplayer.aio.run import aio_run
from avplayer.apps.base.async_av_app import AsyncAvApp
from avplayer.apps.interface.av_interface import AsyncAvInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger
from numpy import uint8, zeros
from numpy.typing import NDArray
from PIL.Image import Image, fromarray
from PIL.ImageTk import PhotoImage


class AsyncAvTk(AsyncAvApp):
    _callback: Optional[AsyncAvInterface]  # type: ignore[assignment]
    _exception: Optional[BaseException]

    _array: NDArray
    _image: Image
    _resized: Image
    _photo: PhotoImage

    def __init__(
        self,
        config: AvConfig,
        callback: Optional[AsyncAvInterface] = None,
    ):
        super().__init__(config, callback)

        self._done = AsyncEvent()

        self._tk = Tk()
        self._tk.title(config.win_title)
        self._tk.geometry(config.win_geometry)
        self._tk.resizable(True, True)

        self._exception = None
        self._update_interval = 1.0 / config.win_fps

        width, height = config.tk_geometry[0:2]
        self._canvas = Canvas(self._tk, width=width, height=height, bg="white")
        self._canvas.pack(fill="both", expand=True)
        self.update_canvas(zeros((width, height, 3), dtype=uint8))

        self._tk.bind("<Configure>", self._configure)
        self._tk.bind("<Escape>", self._escape)
        self._tk.bind("<Key>", self._key)

    @property
    def tk(self) -> Tk:
        return self._tk

    @property
    def width(self) -> int:
        return self._tk.winfo_width()

    @property
    def height(self) -> int:
        return self._tk.winfo_height()

    @property
    def size(self) -> Tuple[int, int]:
        return self.width, self.height

    @staticmethod
    def array_mode(image: NDArray) -> str:
        """
        https://pillow.readthedocs.io/en/latest/handbook/concepts.html#modes
        """
        dims = len(image.shape)
        if dims == 2:
            return "L"
        elif dims == 3:
            channels = image.shape[2]
            if channels == 1:
                return "L"
            elif channels == 3:
                return "RGB"
            elif channels == 4:
                return "RGBA"
            else:
                raise ValueError(f"Unsupported channels: {channels}")
        else:
            raise ValueError(f"Unsupported dims: {dims}")

    def update_canvas(self, image: NDArray) -> None:
        try:
            self._array = image
            self._image = fromarray(self._array, mode=self.array_mode(image))
            self._resized = self._image.resize(self.size)
            self._photo = PhotoImage(image=self._resized)
            self._canvas.create_image(0, 0, image=self._photo, anchor=NW)
        except BaseException as e:
            self._exception = e

    def mainloop(self, shield_exception=False) -> None:
        self._tk.mainloop()  # Holding
        if not shield_exception and self._exception is not None:
            raise RuntimeError from self._exception

    def _configure(self, event: Event) -> None:
        pass

    def _escape(self, event: Event) -> None:
        assert event is not None
        self.on_escape()

    def _key(self, event: Event) -> None:
        assert self._exception is None
        try:
            self.on_keydown(event.char)
        except BaseException as e:
            self._exception = e

    def on_grab(self) -> NDArray:
        return zeros((self.width, self.height, 3), dtype=uint8)

    def on_escape(self) -> None:
        self._done.set()
        print("on_escape")

    def on_keydown(self, code: str) -> None:
        pass

    async def _tk_main(self) -> None:
        avtask = create_task(self._until_complete())
        try:
            while not self._done.is_set():
                # self._tk.update()

                # Process all pending events
                while self._tk.dooneevent(DONT_WAIT) > 0:
                    pass

                try:
                    self._tk.winfo_exists()
                except TclError as e:
                    logger.exception(e)
                    break

                await asyncio_sleep(self._update_interval)
        finally:
            print("1")
            self._avio.shutdown()
            print("2")
            self._tk.quit()
            print("3")
            await avtask
            print("4")

    async def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        print("on_image2")
        if self._callback:
            next_image = await self._callback.on_image(image)
        else:
            next_image = image
        self.update_canvas(next_image)
        return next_image

    @override
    def start(self) -> None:
        aio_run(self._tk_main(), self.config.use_uvloop)

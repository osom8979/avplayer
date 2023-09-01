# -*- coding: utf-8 -*-

from asyncio import Event as AsyncioEvent
from asyncio import (
    Queue,
    QueueEmpty,
    QueueFull,
    create_task,
    get_running_loop,
    run_coroutine_threadsafe,
)
from asyncio import sleep as asyncio_sleep
from functools import partial
from tkinter import NW, Canvas, Event, TclError, Tk
from typing import Final, Optional, Sequence, Tuple

from _tkinter import DONT_WAIT
from numpy import uint8, zeros
from numpy.typing import NDArray
from overrides import override
from PIL.Image import fromarray
from PIL.ImageTk import PhotoImage

from avplayer.aio.run import aio_run
from avplayer.apps.base.async_av_app import AsyncAvApp
from avplayer.apps.interface.av_interface import AsyncAvTckInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger

KEY_RETURN: Final[str] = "<Return>"
KEY_BACKSPACE: Final[str] = "<BackSpace>"
KEY_ESCAPE: Final[str] = "<Escape>"
KEY_INSERT: Final[str] = "<Insert>"
KEY_DELETE: Final[str] = "<Delete>"
KEY_HOME: Final[str] = "<Home>"
KEY_END: Final[str] = "<End>"
KEY_PAGE_UP: Final[str] = "<Prior>"
KEY_PAGE_DOWN: Final[str] = "<Next>"
KEY_UP: Final[str] = "<Up>"
KEY_DOWN: Final[str] = "<Down>"
KEY_LEFT: Final[str] = "<Left>"
KEY_RIGHT: Final[str] = "<Right>"

SPECIAL_KEYS: Final[Sequence[str]] = (
    KEY_RETURN,
    KEY_BACKSPACE,
    KEY_ESCAPE,
    KEY_INSERT,
    KEY_DELETE,
    KEY_HOME,
    KEY_END,
    KEY_PAGE_UP,
    KEY_PAGE_DOWN,
    KEY_UP,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
)


class AsyncAvTk(AsyncAvApp):
    _callback: Optional[AsyncAvTckInterface]  # type: ignore[assignment]
    _exception: Optional[BaseException]
    _latest_size: Tuple[int, int]
    _photo: PhotoImage
    _image_queue: Queue[NDArray]

    def __init__(
        self,
        config: AvConfig,
        callback: Optional[AsyncAvTckInterface] = None,
    ):
        super().__init__(config, callback)

        self._tk = Tk()
        self._tk.title(config.win_title)
        self._tk.geometry(config.win_geometry)
        self._tk.resizable(True, True)

        self._exception = None
        self._update_interval = 1.0 / config.win_fps

        width, height = config.tk_geometry[0:2]
        self._latest_size = width, height
        self._canvas = Canvas(self._tk, width=width, height=height, bg="white")
        self._canvas.pack(fill="both", expand=True)
        self.update_canvas(zeros((height, width, 3), dtype=uint8))

        self._tk.bind("<Configure>", self._configure)

        self._tk.bind("<Enter>", self._mouse_enter)
        self._tk.bind("<Leave>", self._mouse_leave)
        self._tk.bind("<Motion>", self._mouse_move)

        self._tk.bind("<FocusIn>", self._focus_in)
        self._tk.bind("<FocusOut>", self._focus_out)

        self._tk.bind("<Double-Button-1>", self._lbutton_double)
        self._tk.bind("<Double-Button-2>", self._mbutton_double)
        self._tk.bind("<Double-Button-3>", self._rbutton_double)

        self._tk.bind("<ButtonRelease-1>", self._lbutton_up)
        self._tk.bind("<ButtonRelease-2>", self._mbutton_up)
        self._tk.bind("<ButtonRelease-3>", self._rbutton_up)

        self._tk.bind("<B1-Motion>", self._lbutton_move)
        self._tk.bind("<B2-Motion>", self._mbutton_move)
        self._tk.bind("<B3-Motion>", self._rbutton_move)

        self._tk.bind("<Button-1>", self._lbutton_down)
        self._tk.bind("<Button-2>", self._mbutton_down)
        self._tk.bind("<Button-3>", self._rbutton_down)
        self._tk.bind("<Button-4>", self._wheel_up)
        self._tk.bind("<Button-5>", self._wheel_down)
        self._tk.bind("<MouseWheel>", self._wheel_move)

        self._tk.bind("<Key>", self._key)

        for key in SPECIAL_KEYS:
            self._tk.bind(key, partial(self._special_key, key))

        self._tk_done = AsyncioEvent()
        self._image_queue = Queue(maxsize=config.win_queue_size)

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
            pil_image = fromarray(image, self.array_mode(image))
            if self.size != pil_image.size:
                pil_image = pil_image.resize(self.size)
            self._photo = PhotoImage(image=pil_image)
            self._canvas.create_image(0, 0, image=self._photo, anchor=NW)
        except BaseException as e:
            self._exception = e

    def mainloop(self, shield_exception=False) -> None:
        self._tk.mainloop()  # Holding
        if not shield_exception and self._exception is not None:
            raise RuntimeError from self._exception

    def quit(self) -> None:
        self._avio.done()
        self._tk_done.set()

    @staticmethod
    def call_event(coro) -> None:
        run_coroutine_threadsafe(coro, get_running_loop())

    def _configure(self, event: Event) -> None:
        if self._latest_size != (event.width, event.height):
            self._latest_size = event.width, event.height
            if self._callback:
                self.call_event(self._callback.on_resize(event.width, event.height))

    def _mouse_enter(self, event: Event) -> None:
        pass

    def _mouse_leave(self, event: Event) -> None:
        pass

    def _mouse_move(self, event: Event) -> None:
        pass

    def _focus_in(self, event: Event) -> None:
        pass

    def _focus_out(self, event: Event) -> None:
        pass

    def _lbutton_double(self, event: Event) -> None:
        pass

    def _mbutton_double(self, event: Event) -> None:
        pass

    def _rbutton_double(self, event: Event) -> None:
        pass

    def _lbutton_up(self, event: Event) -> None:
        pass

    def _mbutton_up(self, event: Event) -> None:
        pass

    def _rbutton_up(self, event: Event) -> None:
        pass

    def _lbutton_move(self, event: Event) -> None:
        pass

    def _mbutton_move(self, event: Event) -> None:
        pass

    def _rbutton_move(self, event: Event) -> None:
        pass

    def _lbutton_down(self, event: Event) -> None:
        pass

    def _mbutton_down(self, event: Event) -> None:
        pass

    def _rbutton_down(self, event: Event) -> None:
        pass

    def _wheel_up(self, event: Event) -> None:
        pass

    def _wheel_down(self, event: Event) -> None:
        pass

    def _wheel_move(self, event: Event) -> None:
        pass

    def _key(self, event: Event) -> None:
        logger.debug(f"[tk] event <Key> code={event.keycode},sym={event.keysym}")
        if self._callback:
            self.call_event(self._callback.on_key(event.keysym))

    def _special_key(self, bind: str, event: Event) -> None:
        logger.debug(f"[tk] event {bind} code={event.keycode},sym={event.keysym}")
        if self._callback:
            self.call_event(self._callback.on_key(event.keysym))

    async def _run_tk_with_avio(self) -> None:
        avtask = create_task(self._run_avio(), name="avtask")

        try:
            logger.info("Start tk event loop ...")
            while not self._tk_done.is_set():
                # self._tk.update()

                try:
                    frame = self._image_queue.get_nowait()
                except QueueEmpty:
                    if self.config.verbose >= 2:
                        logger.debug(
                            "The image queue is empty. Skip the current frame."
                        )
                else:
                    self.update_canvas(frame)

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
            if not self._avio.is_done_enabled:
                self._avio.done()

            logger.debug("[avtask] waiting ...")
            await avtask
            logger.debug("[avtask] complete !!")

            logger.debug("[tk] quitting ...")
            self._tk.quit()
            logger.debug("[tk] quit !!")

    @override
    async def _until_avio_complete(self) -> None:
        self._avio.open()
        try:
            await self._run_tk_with_avio()
        finally:
            self._avio.close()

    @override
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
    def on_grab(self, image: NDArray[uint8]) -> NDArray[uint8]:
        if not self._avio.is_done_enabled:
            try:
                frame = (image[:, :, ::-1] if len(image.shape) == 3 else image).copy()
                self._image_queue.put_nowait(frame)
            except QueueFull:
                logger.warning("The image queue is full. Drop the current frame")
        return image

    @override
    def start(self) -> None:
        aio_run(self._until_complete(), self.config.use_uvloop)

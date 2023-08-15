# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray

from avplayer.apps.base.app_base import AppBase
from avplayer.apps.interface.av_interface import AvInterface
from avplayer.av.av_io import AvIo


class AvAppBase(AppBase):
    _callback: Optional[AvInterface]

    def __init__(self, args: Namespace, callback: Optional[AvInterface] = None):
        super().__init__(args)
        self._callback = callback

        self._avio = AvIo(
            self.input,
            self.output,
            file_format=self.inspect_output_format(),
            source_size=self.input_size,
            destination_size=self.output_size,
            logging_step=self.logging_step,
            verbose=self.verbose,
        )

    def _callback_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        if self._callback is not None:
            return self._callback.on_image(image)
        else:
            return image

    @property
    def avio(self):
        return self._avio

    def shutdown_avio(self):
        self._avio.shutdown()

    def open_avio(self):
        self._avio.open()

    def close_avio(self):
        self._avio.close()

    def run_avio(self, coro) -> None:
        self._avio.run(coro)

    def start_app(self):
        self.open_avio()
        try:
            self.run_avio(self._callback_image)
        finally:
            self.close_avio()

# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Callable

from avplayer.apps.app_base import AppBase
from avplayer.av.av_io import AvIo


class AvAppBase(AppBase):
    def __init__(self, args: Namespace, printer: Callable[..., None] = print):
        super().__init__(args, printer)
        self._avio = AvIo(
            self.input,
            self.output,
            file_format=self.inspect_output_format,
            source_size=self.input_size,
            destination_size=self.output_size,
            logging_step=self.logging_step,
            verbose=self.verbose,
        )

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

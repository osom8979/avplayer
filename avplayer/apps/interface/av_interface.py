# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray


class AvInterface(metaclass=ABCMeta):
    @abstractmethod
    def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        raise NotImplementedError

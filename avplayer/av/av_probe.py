# -*- coding: utf-8 -*-

from typing import NamedTuple, Optional, Tuple, Union

from av import open as av_open  # noqa
from av._core import time_base  # noqa
from av.container import InputContainer


class AvProbe(NamedTuple):
    width: int
    height: int
    duration: float


def get_av_probe(
    file: str,
    timeout: Optional[Union[float, Tuple[float, float]]] = None,
) -> AvProbe:
    # Elapsed seconds 0.04s ~ 0.07s in `AMD Ryzen 7 4700u` (10sec duration `.ts` file)
    input_container = av_open(file=file, mode="r", timeout=timeout)
    assert isinstance(input_container, InputContainer)

    duration = input_container.duration / time_base
    width = input_container.width
    height = input_container.height

    return AvProbe(width=width, height=height, duration=duration)

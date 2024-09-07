# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-overload, operator"

from typing import NamedTuple, Optional, Tuple, Union


class AvProbe(NamedTuple):
    width: int
    height: int
    duration: float


def get_av_probe(
    file: str,
    timeout: Optional[Union[float, Tuple[float, float]]] = None,
) -> AvProbe:
    from av import open as av_open  # noqa
    from av._core import time_base  # noqa
    from av.container import InputContainer

    # Elapsed seconds 0.04s ~ 0.07s in `AMD Ryzen 7 4700u` (10sec duration `.ts` file)
    input_container = av_open(file=file, mode="r", timeout=timeout)
    assert isinstance(input_container, InputContainer)

    duration = input_container.duration / time_base
    width = input_container.width  # type: ignore[attr-defined]
    height = input_container.height  # type: ignore[attr-defined]

    return AvProbe(width=width, height=height, duration=duration)

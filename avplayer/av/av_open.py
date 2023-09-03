# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional, Tuple, Union

from avplayer.av.av_options import CommonAvOptions
from avplayer.logging.logging import logger


def open_input_container(
    file: str,
    file_format: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    container_options: Optional[Dict[str, Any]] = None,
    stream_options: Optional[List[str]] = None,
    metadata_encoding: Optional[str] = None,
    metadata_errors: Optional[str] = None,
    buffer_size: Optional[int] = None,
    timeout: Optional[Union[float, Tuple[float, float]]] = None,
):
    from av import open as av_open  # noqa
    from av.container import InputContainer

    logger.debug(f"Open the input container: '{file}'")
    result = av_open(
        file,
        mode="r",
        format=file_format,
        options=options,
        container_options=container_options,
        stream_options=stream_options,
        metadata_encoding=metadata_encoding,
        metadata_errors=metadata_errors,
        buffer_size=buffer_size,
        timeout=timeout,
    )

    assert isinstance(result, InputContainer)
    return result


def open_output_container(
    file: str,
    file_format: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    container_options: Optional[Dict[str, Any]] = None,
    stream_options: Optional[List[str]] = None,
    metadata_encoding: Optional[str] = None,
    metadata_errors: Optional[str] = None,
    buffer_size: Optional[int] = None,
    timeout: Optional[Union[float, Tuple[float, float]]] = None,
):
    from av import open as av_open  # noqa
    from av.container import OutputContainer

    logger.debug(f"Open the output container: '{file}'")
    result = av_open(
        file,
        mode="w",
        format=file_format,
        options=options,
        container_options=container_options,
        stream_options=stream_options,
        metadata_encoding=metadata_encoding,
        metadata_errors=metadata_errors,
        buffer_size=buffer_size,
        timeout=timeout,
    )

    assert isinstance(result, OutputContainer)
    return result


def open_input(file: str, options: CommonAvOptions):
    return open_input_container(
        file,
        file_format=options.get_format(),
        options=options.options,
        container_options=options.container_options,
        stream_options=options.stream_options,
        metadata_encoding=options.get_metadata_encoding(),
        metadata_errors=options.get_metadata_errors(),
        buffer_size=options.get_buffer_size(),
        timeout=options.get_timeout(),
    )


def open_output(file: str, options: CommonAvOptions):
    return open_output_container(
        file,
        file_format=options.get_format(),
        options=options.options,
        container_options=options.container_options,
        stream_options=options.stream_options,
        metadata_encoding=options.get_metadata_encoding(),
        metadata_errors=options.get_metadata_errors(),
        buffer_size=options.get_buffer_size(),
        timeout=options.get_timeout(),
    )

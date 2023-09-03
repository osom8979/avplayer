# -*- coding: utf-8 -*-

from avplayer.av.av_options import CommonAvOptions
from avplayer.logging.logging import logger


def open_input_container(file: str, options: CommonAvOptions):
    from av import open as av_open  # noqa
    from av.container import InputContainer

    logger.debug(f"Open the input container: '{file}'")
    result = av_open(
        file,
        mode="r",
        format=options.format,
        options=options.options,
        container_options=options.container_options,
        stream_options=options.stream_options,
        metadata_encoding=options.get_metadata_encoding(),
        metadata_errors=options.get_metadata_errors(),
        buffer_size=options.get_buffer_size(),
        timeout=options.get_timeout(),
    )

    assert isinstance(result, InputContainer)
    return result


def open_output_container(file: str, options: CommonAvOptions):
    from av import open as av_open  # noqa
    from av.container import OutputContainer

    logger.debug(f"Open the output container: '{file}'")
    result = av_open(
        file,
        mode="w",
        format=options.format,
        options=options.options,
        container_options=options.container_options,
        stream_options=options.stream_options,
        metadata_encoding=options.get_metadata_encoding(),
        metadata_errors=options.get_metadata_errors(),
        buffer_size=options.get_buffer_size(),
        timeout=options.get_timeout(),
    )

    assert isinstance(result, OutputContainer)
    return result

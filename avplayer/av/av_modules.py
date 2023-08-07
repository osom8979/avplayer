# -*- coding: utf-8 -*-

import os
import re
from importlib import import_module
from types import ModuleType


def get_module_directory(module: ModuleType) -> str:
    module_path = getattr(module, "__path__", None)
    if module_path:
        assert isinstance(module_path, list)
        return module_path[0]

    module_file = getattr(module, "__file__", None)
    if module_file:
        assert isinstance(module_file, str)
        return os.path.dirname(module_file)

    raise RuntimeError(f"The '{module.__name__}' module path is unknown")


def find_ffmpeg_library_path(library_name: str) -> str:
    av_module = import_module("av")
    av_core_module = import_module("av._core")

    av_module_dir = get_module_directory(av_module)
    if av_module_dir[-1] == "/":
        av_module_dir = av_module_dir[:-1]
    av_lib_module_dir = av_module_dir + ".libs"
    if not os.path.isdir(av_lib_module_dir):
        raise FileNotFoundError(f"Not found module directory: {av_lib_module_dir}")

    versions = getattr(av_core_module, "library_versions")
    assert isinstance(versions, dict)
    if library_name not in versions:
        raise ValueError(f"Unknown library name: {library_name}")

    major = versions[library_name][0]
    minor = versions[library_name][1]
    patch = versions[library_name][2]
    assert isinstance(major, int)
    assert isinstance(minor, int)
    assert isinstance(patch, int)

    regex_pattern = r"^{name}-(.*)\.so\.{major}\.{minor}\.{patch}$".format(
        name=library_name, major=major, minor=minor, patch=patch
    )
    matcher = re.compile(regex_pattern)

    for file in os.listdir(av_lib_module_dir):
        if matcher.match(file):
            return os.path.join(av_lib_module_dir, file)

    raise FileNotFoundError(f"Not found ffmpeg library: {library_name}")


# noinspection SpellCheckingInspection
def find_libavutil_path() -> str:
    return find_ffmpeg_library_path("libavutil")

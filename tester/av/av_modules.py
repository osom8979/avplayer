# -*- coding: utf-8 -*-

from os import path
from unittest import TestCase, main

from avplayer.av.av_modules import find_libavutil_path


class AvModulesTestCase(TestCase):
    def test_find_libavutil_path(self):
        self.assertTrue(path.isfile(find_libavutil_path()))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

from unittest import TestCase, main

from avplayer.av.av_logging import av_log_get_level, av_log_set_level


class AvLoggingTestCase(TestCase):
    def test_log_level(self):
        test_level = 12
        av_log_set_level(test_level)
        self.assertEqual(test_level, av_log_get_level())


if __name__ == "__main__":
    main()

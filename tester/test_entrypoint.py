# -*- coding: utf-8 -*-

from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase, main

from avplayer.arguments import version
from avplayer.entrypoint import main as entrypoint_main


class EntrypointTestCase(TestCase):
    def test_version(self):
        buffer = StringIO()
        code = -1
        with redirect_stdout(buffer):
            try:
                entrypoint_main(["--version"])
            except SystemExit as e:
                code = e.code
        self.assertEqual(0, code)
        self.assertEqual(version(), buffer.getvalue().strip())


if __name__ == "__main__":
    main()

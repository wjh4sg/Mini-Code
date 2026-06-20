import unittest

import main
import minicode_cli


class MainTests(unittest.TestCase):
    def test_main_is_compatibility_wrapper(self):
        self.assertIs(main.main, minicode_cli.main)

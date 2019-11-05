# Misc tests.

import unittest

from context import sedparse
from utils import parse_string


class TestSedparseMisc(unittest.TestCase):  # pylint: disable=unused-variable
    def test_string_expr_count(self):
        """Calling compile_string() should increase by one the expression count."""
        before = sedparse.cur_input.string_expr_count
        _ = parse_string("p")
        _ = parse_string("p")
        _ = parse_string("p")
        after = sedparse.cur_input.string_expr_count
        self.assertEqual(before + 3, after)


if __name__ == "__main__":
    unittest.main()

# Misc tests.

import os
import tempfile
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

    def test_global_data_cleanup(self):
        """
        Global variables should be reset after an error and after the end of
        normal execution, to avoid leaking and affecting the next run.
        """

        # After compile_string(), prog.* should be NULL
        script = ["p", "x", "s/foo/bar/g"]
        sedparse.compile_string([], "\n".join(script))
        self.assertIsNone(sedparse.prog.base)
        self.assertIsNone(sedparse.prog.cur)
        self.assertIsNone(sedparse.prog.end)
        self.assertIsNone(sedparse.prog.text)

        # After compile_file(), prog.file should be NULL
        script = ["p", "x", "s/foo/bar/g"]
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as file:
            file.write("\n".join(script))
            filename = file.name
        sedparse.compile_file([], filename)
        self.assertIsNone(sedparse.prog.file)
        os.remove(filename)

        # After normal execution, blocks is back to zero and old_text_buf will
        # still hold some contents.
        script = ["{", "i\\", "foo", "}"]
        _ = parse_string("\n".join(script))
        self.assertEqual(0, sedparse.blocks)
        self.assertIsNone(sedparse.pending_text)

        # After an error, every global should be reset
        script = ["{", "i\\", "foo", "XXX"]
        try:
            _ = parse_string("\n".join(script))
        except sedparse.ParseError:
            pass
        self.assertEqual(0, sedparse.blocks)
        self.assertIsNone(sedparse.old_text_buf)
        self.assertIsNone(sedparse.pending_text)


if __name__ == "__main__":
    unittest.main()

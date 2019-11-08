# Misc tests.
# coding: utf-8

import json
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
        self.assertIsNone(sedparse.prog.base)
        self.assertIsNone(sedparse.prog.cur)
        self.assertIsNone(sedparse.prog.end)
        self.assertIsNone(sedparse.prog.text)
        self.assertIsNone(sedparse.prog.file)

    def test_expressions_and_files(self):
        """
        In the commmand line, the sed script to be parsed can be informed using
        a string `-e` and/or a file `-f`. Both options can be used multiple
        times to compose a larger script in smaller chunks. The original option
        order is respected. This mimics how GNU sed itself works.

        Option `-e` is mapped to `compile_string()` and option `-f` is mapped to
        `compile_file()`. Both are called here in different combinations to make
        sure they work as expected.
        """

        # Create a script file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as file:
            file.write("x\n")
            filename = file.name

        data = [
            # @ means the file must be loaded (-f file)
            (["@"], ["x"]),
            (["p"], ["p"]),
            (["p", "d", "q"], ["p", "d", "q"]),
            (["@", "p"], ["x", "p"]),
            (["p", "@"], ["p", "x"]),
            (["p", "@", "d", "@", "q"], ["p", "x", "d", "x", "q"]),
        ]
        for scripts, expected_commands in data:
            args = []
            for script in scripts:
                if script == "@":
                    args.extend(["-f", filename])
                else:
                    args.extend(["-e", script])
            the_json = sedparse.main(args)
            the_program = json.loads(the_json)
            self.assertEqual(
                expected_commands, [x["cmd"] for x in the_program], msg=scripts
            )
        os.remove(filename)

    def test_savchar_with_unicode(self):
        """
        savchar() should handle Unicode characters correctly. That means going
        back N bytes when the input is a file, where N is the lenght in bytes of
        the current Unicode character (i.e., ★ is composed of 3 bytes).

        In this test, while reading the numeric argument for the "q" command in
        `in_integer()`, it will detect the "9" and then a non-number "★". At
        this point `savchar()` will be called to go back before the "★". Then
        the parser will read "★" again and complain about "extra characters
        after command". If Unicode backtracking is not supported, the parser
        error would be different.
        """
        script = "q9★\n"

        # Create a script file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as file:
            file.write(script)
            filename = file.name

        # Test reading from a file (-f)
        with self.assertRaises(sedparse.ParseError) as manager:
            sedparse.compile_file([], filename)
        self.assertTrue(
            manager.exception.message.endswith("extra characters after command")
        )
        os.remove(filename)

        # Test reading from a string (-e)
        with self.assertRaises(sedparse.ParseError) as manager:
            sedparse.compile_string([], script)
        self.assertTrue(
            manager.exception.message.endswith("extra characters after command")
        )


if __name__ == "__main__":
    unittest.main()

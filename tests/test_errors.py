# Test all error messages.

import contextlib
import io
import sys
import unittest

from context import sedparse

TEST_DATA = [
    # pylint: disable=bad-whitespace
    # fmt: off

    # Note: Not all possible error messages are tested, those that were left
    #       out are not available in the port.
    # Format: (sed script, char nr, constant, error message)

    #                 ANCIENT_VERSION  expected newer version of sed
    ("!!p",       2, "BAD_BANG", "multiple `!'s"),
    ("1,p",       3, "BAD_COMMA", "unexpected `,'"),
    ("s★a★b★",    2, "BAD_DELIM",
                            "delimiter character is not a single-byte character"),
    ("+1p",       2, "BAD_STEP", "invalid usage of +N or ~N as first address"),
    ("~1p",       2, "BAD_STEP", "invalid usage of +N or ~N as first address"),
    (":",         1, "COLON_LACKS_LABEL", '":" lacks a label'),
    #                 DISALLOWED_CMD  e/r/w commands disabled in sandbox mode
    ("}",         1, "EXCESS_CLOSE_BRACE", "unexpected `}'"),
    ("s/a/b/gg",  8, "EXCESS_G_OPT", "multiple `g' options to `s' command"),
    ("dp",        2, "EXCESS_JUNK", "extra characters after command"),
    ("xx",        2, "EXCESS_JUNK", "extra characters after command"),
    ("s/a/b/2p2", 9, "EXCESS_N_OPT", "multiple number options to `s' command"),
    ("{",         1, "EXCESS_OPEN_BRACE", "unmatched `{'"),  # GNU sed is "char 0"
    ("s/a/b/pp",  8, "EXCESS_P_OPT", "multiple `p' options to `s' command"),
    ("a",         1, "EXPECTED_SLASH", "expected \\ after `a', `c' or `i'"),
    #                 INCOMPLETE_CMD  incomplete command
    ("0p",        2, "INVALID_LINE_0", "invalid usage of line address 0"),
    ("0,5p",      4, "INVALID_LINE_0", "invalid usage of line address 0"),
    ("s/a/b/w",   7, "MISSING_FILENAME", "missing filename in r/R/w/W commands"),
    ("r",         1, "MISSING_FILENAME", "missing filename in r/R/w/W commands"),
    ("{p;$}",     5, "NO_CLOSE_BRACE_ADDR", "`}' doesn't want any addresses"),
    #                 NO_COLON_ADDR  : doesn't want any addresses
    ("1",         1, "NO_COMMAND", "missing command"),
    ("1\n",       2, "NO_COMMAND", "missing command"),
    #                 NO_SHARP_ADDR  comments don't accept any addresses
    #                 ONE_ADDR  command only uses one address
    #                 RECURSIVE_ESCAPE_C  recursive escaping after \\c not allowed
    ("u",         1, "UNKNOWN_CMD", "unknown command: `u'"),
    ("s/a/b/z",   7, "UNKNOWN_S_OPT", "unknown option to `s'"),
    ("s/a/b/\r",  7, "UNKNOWN_S_OPT", "unknown option to `s'"),
    ("/a",        2, "UNTERM_ADDR_RE", "unterminated address regex"),
    ("s/a/b",     5, "UNTERM_S_CMD", "unterminated `s' command"),
    ("y/a/",      4, "UNTERM_Y_CMD", "unterminated `y' command"),
    #                 Y_CMD_LEN  strings for `y' command are different lengths
    ("s/a/b/0",   7, "ZERO_N_OPT", "number option to `s' command may not be zero"),
]

# Capture stdout and stderr for the asserts
# https://stackoverflow.com/a/17981937
@contextlib.contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestSedparseErrors(unittest.TestCase):  # pylint: disable=unused-variable
    def test_errors(self):
        for script, char_nr, _, message in TEST_DATA:
            expected = "sed: -e expression #%d, char %d: %s" % (
                sedparse.cur_input.string_expr_count + 1,
                char_nr,
                message,
            )

            with captured_output() as (_, err):
                try:
                    parsed = []
                    sedparse.compile_string(parsed, script)
                    sedparse.check_final_program()
                except SystemExit:
                    pass
                with self.subTest(script=script):
                    self.assertEqual(expected, err.getvalue().rstrip())


if __name__ == "__main__":
    unittest.main()

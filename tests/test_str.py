# Test the str() output from the structs.
# Note: test_repr.py uses the same tests, keep both in sync.

import unittest

from context import sedparse
from utils import parse_string


class TestSedparsestr(unittest.TestCase):  # pylint: disable=unused-variable
    def test_str_struct_addr(self):
        """Check str for all kinds of addresses"""
        data = [
            ("$", "$", "None"),
            ("91,92", "91", "92"),
            ("91~992", "91~992", "None"),
            ("91,~992", "91", "~992"),
            ("91,+992", "91", "+992"),
            ("/foo/IM", "/foo/IM", "None"),
        ]
        for address, str_a1, str_a2 in data:
            script = address + "p"
            parsed = parse_string(script)
            self.assertEqual(str_a1, str(parsed[0].a1), msg=script)
            self.assertEqual(str_a2, str(parsed[0].a2), msg=script)

    def test_str_struct_text_buf(self):
        script = "a L1\\\nL2"
        expected = "L1\\\nL2"
        self.assertEqual(expected, str(parse_string(script)[0].x.cmd_txt))

    def test_str_struct_text_buf_raw(self):
        """Test using the struct only, not the parser"""
        struct = sedparse.struct_text_buf()
        struct.text = ["f", "o", "o"]
        expected = "fo"  # last char (usually a \n) is chopped
        self.assertEqual(expected, str(struct))

    def test_str_struct_misc(self):
        """Check str for struct_{regex,replacement,output}"""
        script = "s/foo/bar/igw file"
        parsed = parse_string(script)
        self.assertEqual("/foo/igw", str(parsed[0].x.cmd_subst.regx))
        self.assertEqual("bar", str(parsed[0].x.cmd_subst.replacement))
        self.assertEqual("file", str(parsed[0].x.cmd_subst.outf))


if __name__ == "__main__":
    unittest.main()

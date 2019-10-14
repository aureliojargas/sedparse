# Test the repr() output from the structs.

import unittest

from context import sedparse


def parse_string(script):
    parsed = []
    sedparse.compile_string(parsed, script)
    return parsed


class TestSedparseRepr(unittest.TestCase):  # pylint: disable=unused-variable
    def test_repr_struct_addr(self):
        """Check repr for all kinds of addresses"""
        data = [
            # pylint: disable=line-too-long
            (
                "$",
                "struct_addr(addr_type=7, addr_number=0, addr_step=0, addr_regex=None)",
                "None",
            ),
            (
                "91,92",
                "struct_addr(addr_type=3, addr_number=91, addr_step=0, addr_regex=None)",
                "struct_addr(addr_type=3, addr_number=92, addr_step=0, addr_regex=None)",
            ),
            (
                "91~992",
                "struct_addr(addr_type=4, addr_number=91, addr_step=992, addr_regex=None)",
                "None",
            ),
            (
                "91,~992",
                "struct_addr(addr_type=3, addr_number=91, addr_step=0, addr_regex=None)",
                "struct_addr(addr_type=6, addr_number=0, addr_step=992, addr_regex=None)",
            ),
            (
                "91,+992",
                "struct_addr(addr_type=3, addr_number=91, addr_step=0, addr_regex=None)",
                "struct_addr(addr_type=5, addr_number=0, addr_step=992, addr_regex=None)",
            ),
            (
                "/foo/IM",
                "struct_addr(addr_type=2, addr_number=0, addr_step=0,"
                " addr_regex=struct_regex(slash='/', pattern='foo', flags='IM'))",
                "None",
            ),
        ]
        for address, repr_a1, repr_a2 in data:
            script = address + "p"
            with self.subTest(script=script):
                parsed = parse_string(script)
                self.assertEqual(repr_a1, repr(parsed[0].a1))
                self.assertEqual(repr_a2, repr(parsed[0].a2))

    def test_repr_struct_text_buf(self):
        script = "a L1\\\nL2"
        expected = "struct_text_buf(text=['L', '1', '\\\\', '\\n', 'L', '2', '\\n'])"
        self.assertEqual(expected, repr(parse_string(script)[0].x.cmd_txt))

    def test_repr_struct_text_buf_raw(self):
        """Test using the struct only, not the parser"""
        struct = sedparse.struct_text_buf()
        struct.text = ["f", "o", "o"]
        expected = "struct_text_buf(text=['f', 'o', 'o'])"
        self.assertEqual(expected, repr(struct))

    def test_repr_struct_misc(self):
        """Check repr for struct_{regex,replacement,output}"""
        script = "s/foo/bar/igw file"
        with self.subTest(script=script):
            parsed = parse_string(script)
            self.assertEqual(
                "struct_regex(slash='/', pattern='foo', flags='')",
                repr(parsed[0].x.cmd_subst.regx),
            )
            self.assertEqual(
                "struct_replacement(text='bar')",
                repr(parsed[0].x.cmd_subst.replacement),
            )
            self.assertEqual(
                "struct_output(name='file')", repr(parsed[0].x.cmd_subst.outf)
            )


if __name__ == "__main__":
    unittest.main()

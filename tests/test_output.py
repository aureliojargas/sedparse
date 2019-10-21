# Test output from struct.to_dict() and struct.to_json().

import json
import unittest

from context import sedparse


def parse_string(script):
    parsed = []
    sedparse.compile_string(parsed, script)
    return parsed


class TestSedparseOutput(unittest.TestCase):  # pylint: disable=unused-variable
    def test_diet(self):
        data = [
            (
                "0~2p",
                {
                    "a1": {"addr_type": 4, "addr_number": 0, "addr_step": 2},
                    "cmd": "p",
                    "line": 1,
                },
            ),
            (
                "1,~2p",
                {
                    "a1": {"addr_type": 3, "addr_number": 1},
                    "a2": {"addr_type": 6, "addr_number": 0, "addr_step": 2},
                    "cmd": "p",
                    "line": 1,
                },
            ),
            (
                "1,+2p",
                {
                    "a1": {"addr_type": 3, "addr_number": 1},
                    "a2": {"addr_type": 5, "addr_number": 0, "addr_step": 2},
                    "cmd": "p",
                    "line": 1,
                },
            ),
            (
                "/x/p",
                {
                    "a1": {
                        "addr_type": 2,
                        "addr_regex": {"pattern": "x", "slash": "/"},
                    },
                    "cmd": "p",
                    "line": 1,
                },
            ),
            (
                "s/x/y/",
                {
                    "cmd": "s",
                    "x": {
                        "cmd_subst": {
                            "regx": {"pattern": "x", "slash": "/"},
                            "replacement": {"text": "y"},
                        }
                    },
                    "line": 1,
                },
            ),
            ("$p", {"a1": {"addr_type": 7}, "cmd": "p", "line": 1}),
            ("q0", {"cmd": "q", "x": {"int_arg": 0}, "line": 1}),
            ("!p", {"addr_bang": True, "cmd": "p", "line": 1}),
            ("p", {"cmd": "p", "line": 1}),
        ]
        for script, output in data:
            parsed = parse_string(script)
            self.assertEqual(output, parsed[0].to_dict(), msg=script)
            self.assertEqual(output, json.loads(parsed[0].to_json()), msg=script)

    def test_full(self):
        script = "p"
        output = {
            "a1": None,
            "a2": None,
            "addr_bang": False,
            "cmd": "p",
            "x": {
                "cmd_txt": {"text": []},
                "int_arg": -1,
                "fname": "",
                "cmd_subst": {
                    "regx": {"pattern": "", "flags": "", "slash": ""},
                    "replacement": {"text": ""},
                    "outf": {"name": ""},
                },
                "label_name": "",
                "comment": "",
            },
            "line": 1,
        }
        parsed = parse_string(script)
        self.assertEqual(output, parsed[0].to_dict(remove_empty=False), msg=script)
        self.assertEqual(
            output, json.loads(parsed[0].to_json(remove_empty=False)), msg=script
        )


if __name__ == "__main__":
    unittest.main()

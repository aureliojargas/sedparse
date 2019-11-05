# Utilities for testing

from context import sedparse


def parse_string(script):  # pylint: disable=unused-variable
    parsed = []
    sedparse.compile_string(parsed, script)
    sedparse.check_final_program()
    return parsed

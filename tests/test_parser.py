# Test the parser, feeding it with tricky sed scripts.
# coding: utf-8

import unittest

from utils import parse_string


# The global holder for all the test data
TEST_DATA = {}

# Aligning test cases makes them way more readable
# -----------------------------------------------------------------------------
# Test data for ADDRESSES

TEST_DATA["address"] = [
    # Test cases for addresses: numeric, $, /regex/
    # Source: compile_address(), match_slash()
    # fmt: off

    # sed script       !       addr1         addr2
    # --------------------------------------------

    # no address
    ("p",              False,  None,         None),
    ("!p",             True,   None,         None),
    ("{}",             False,  None,         None),
    ("!{}",            True,   None,         None),

    # last line
    ("$p",             False,  "$",          None),
    ("${}",            False,  "$",          None),
    ("$!p",            True,   "$",          None),
    (" $ p",           False,  "$",          None),
    (" $ {}",          False,  "$",          None),
    (" $ ! p",         True,   "$",          None),

    # numeric
    ("5p",             False,  "5",          None),
    ("5{}",            False,  "5",          None),
    ("5!p",            True,   "5",          None),
    (" 5 p",           False,  "5",          None),
    (" 5 {}",          False,  "5",          None),
    (" 5 ! p",         True,   "5",          None),

    # numeric range
    ("1,5p",           False,  "1",          "5"),
    ("1,5{}",          False,  "1",          "5"),
    ("1,5!p",          True,   "1",          "5"),
    (" 1 , 5 p",       False,  "1",          "5"),
    (" 1 , 5 {}",      False,  "1",          "5"),
    (" 1 , 5 ! p",     True,   "1",          "5"),

    # inverted range
    ("5,1p",           False,  "5",          "1"),
    ("$,1p",           False,  "$",          "1"),

    # zero is allowed if second address is a regex
    ("0,/x/p",         False,  "0",          "/x/"),

    # steps ~ and +
    ("1~2p",           False,  "1~2",        None),
    ("0~2p",           False,  "0~2",        None),
    ("5~0p",           False,  "5",          None),  # source change
    ("1,~2p",          False,  "1",          "~2"),
    ("1,+2p",          False,  "1",          "+2"),
    ("1,~0p",          False,  "1",          "~0"),
    ("1,+0p",          False,  "1",          "+0"),

    # regex with /
    ("/x/p",           False,  "/x/",        None),
    ("/x/{}",          False,  "/x/",        None),
    ("/x/!p",          True,   "/x/",        None),
    (" /x/ p",         False,  "/x/",        None),
    (" /x/ {}",        False,  "/x/",        None),
    (" /x/ ! p",       True,   "/x/",        None),

    ("/x/,/y/p",       False,  "/x/",        "/y/"),
    ("/x/,/y/{}",      False,  "/x/",        "/y/"),
    ("/x/,/y/!p",      True,   "/x/",        "/y/"),
    (" /x/ , /y/ p",   False,  "/x/",        "/y/"),
    (" /x/ , /y/ {}",  False,  "/x/",        "/y/"),
    (" /x/ , /y/ ! p", True,   "/x/",        "/y/"),

    # flags (GNU extension)
    ("/x/Ip",          False,  "/x/I",       None),
    ("/x/I{}",         False,  "/x/I",       None),
    ("/x/I!p",         True,   "/x/I",       None),
    (" /x/ I p",       False,  "/x/I",       None),
    (" /x/ I {}",      False,  "/x/I",       None),
    (" /x/ I ! p",     True,   "/x/I",       None),

    # combining flags
    ("/x/IMp",         False,  "/x/IM",      None),
    ("/x/MIp",         False,  "/x/MI",      None),
    ("/x/ M I p",      False,  "/x/MI",      None),

    # repeated flags are not removed
    ("/x/MMIIMIp",     False,  "/x/MMIIMI",  None),

    # escaped / delimiter will loose the escape
    (r"\/x/p",         False,  r"/x/",       None),  # source change

    # regex with other delimiter (\n and non-ASCII not allowed)
    (r"\;x;p",         False,  r"\;x;",      None),
    (r"\,x,p",         False,  r"\,x,",      None),
    (r"\(x(p",         False,  r"\(x(",      None),
    (r"\[x[p",         False,  r"\[x[",      None),
    (r"\ x p",         False,  r"\ x ",      None),
    ( "\\\tx\tp",      False,  "\\\tx\t",    None),  # tab
    (r"\\x\p",         False,  "\\\\x\\",    None),  # \
    #(r"\★x★p",         False,  "\\★x★",      None),  # ★

    # regex: command as delimiter
    (r"\pxpp",         False,  r"\pxp",      None),
    (r"\=x==",         False,  r"\=x=",      None),
    (r"\{x{{}",        False,  r"\{x{",      None),

    # regex: bang as delimiter
    (r"\!x!p",         False,  r"\!x!",      None),
    (r"\!x!!p",        True,   r"\!x!",      None),

    # regex: flag letter as delimiter
    (r"\IxIp",         False,  r"\IxI",      None),
    (r"\IxIIp",        False,  r"\IxII",     None),

    # empty regex
    (r"//p",           False,  r"//",        None),
    (r"\ppp",          False,  r"\pp",       None),
    (r"//,//p",        False,  r"//",        r"//"),
    (r"\,,,\ppp",      False,  r"\,,",       r"\pp"),
    (r"\III,\MMMp",    False,  r"\III",      r"\MMM"),

    # same address repeated
    ("5,5p",           False,  "5",          "5"),
    ("$,$p",           False,  "$",          "$"),
    ("/x/,/x/p",       False,  "/x/",        "/x/"),
    ("//,//p",         False,  "//",         "//"),

    # Non-ASCII chars are allowed
    ("/★/,/★/p",       False,  "/★/",        "/★/"),

    # regex that looks numeric or last line
    ("/0/p",           False,  "/0/",        None),
    ("/5/p",           False,  "/5/",        None),
    ("/1,5/p",         False,  "/1,5/",      None),
    ("/$/p",           False,  "/$/",        None),

    # mixed extra tabs and spaces
    (" 1\t ,\t 5\t p", False,  "1",          "5"),
    ("\t /x/\t !\t p", True,   "/x/",        None),
    ("\t /x/\t I\t p", False,  "/x/I",       None),

    # regex: escaped delimiter (start, middle, end)
    (r"/\/\/\//p",     False,  r"/\/\/\//",  None),
    (r"\|\|\|\||p",    False,  r"\|\|\|\||", None),

    # Delimiter inside a regex character class
    ("/[/]/p",         False,  "/[/]/",      None),
]


# -----------------------------------------------------------------------------
# Test data for FILENAME commands

TEST_DATA["r"] = [
    # Test cases for command: r, R, w, W
    # Note that "s///w filename" is tested in the "s" tests.
    # Note: all scripts end in EOF. At run time the \n ending is also tested.
    # Source: read_filename()
    # Format: (sed script, expected filename)
    # fmt: off

    ("rname", "name"),

    # Leading spaces are ignored
    ("r space", "space"),
    ("r\ttab", "tab"),
    ("r \t \t mixed", "mixed"),

    # Every char is valid (it reads until \n), so ;}# are not special
    ("r;", ";"),
    ("r}", "}"),
    ("r#", "#"),
    ("r\\", "\\"),
    ("r foo}; \t#\\", "foo}; \t#\\"),

    # Non-ASCII chars are allowed
    ("r★", "★"),
]

# Copy all "r" tests to: R, w, W
TEST_DATA["R"] = [("R" + script[1:], filename) for script, filename in TEST_DATA["r"]]
TEST_DATA["w"] = [("w" + script[1:], filename) for script, filename in TEST_DATA["r"]]
TEST_DATA["W"] = [("W" + script[1:], filename) for script, filename in TEST_DATA["r"]]

# Filename is the command name
TEST_DATA["r"].append(("rr", "r"))
TEST_DATA["R"].append(("RR", "R"))
TEST_DATA["w"].append(("ww", "w"))
TEST_DATA["W"].append(("WW", "W"))


# -----------------------------------------------------------------------------
# Test data for LABEL commands

TEST_DATA[":"] = [
    # Test cases for commands: :, b, t, T, v
    # Note: all scripts end in EOF. At run time the \n ending is also tested.
    # Source: read_label()
    # Format: (sed script, expected label name)
    # fmt: off

    (":name", "name"),

    # Leading spaces are ignored
    (": space", "space"),
    (":\ttab", "tab"),
    (": \t \t mixed", "mixed"),

    # Those chars end a label: tab space ; #
    # Note that } also ends a label, but it will be tested later
    (":label\t", "label"),
    (":label ", "label"),
    (":label;", "label"),
    (":label#", "label"),

    # All other chars are valid as labels
    (":!", "!"),
    (":{", "{"),
    (":\\", "\\"),

    # Non-ASCII chars are allowed
    (":★", "★"),
]

# Copy all ":" tests to: b, t, T, v
TEST_DATA["b"] = [("b" + script[1:], label) for script, label in TEST_DATA[":"]]
TEST_DATA["t"] = [("t" + script[1:], label) for script, label in TEST_DATA[":"]]
TEST_DATA["T"] = [("T" + script[1:], label) for script, label in TEST_DATA[":"]]
TEST_DATA["v"] = [("v" + script[1:], label) for script, label in TEST_DATA[":"]]

# Label name is the command name
TEST_DATA[":"].append(("::", ":"))
TEST_DATA["b"].append(("bb", "b"))
TEST_DATA["t"].append(("tt", "t"))
TEST_DATA["T"].append(("TT", "T"))
TEST_DATA["v"].append(("vv", "v"))

# Labels are ended by the } command
TEST_DATA[":"].append(("{:label}", "label"))
TEST_DATA["b"].append(("{blabel}", "label"))
TEST_DATA["t"].append(("{tlabel}", "label"))
TEST_DATA["T"].append(("{Tlabel}", "label"))
TEST_DATA["v"].append(("{vlabel}", "label"))

# Empty labels are allowed when jumping
TEST_DATA["b"].append(("b", ""))
TEST_DATA["t"].append(("t", ""))
TEST_DATA["T"].append(("T", ""))

# The v command can also be empty
TEST_DATA["v"].append(("v", ""))

# Those chars end an empty label: tab space ; } #
TEST_DATA["b"].append(("b\t", ""))
TEST_DATA["b"].append(("b ", ""))
TEST_DATA["b"].append(("b;", ""))
TEST_DATA["b"].append(("{b}", ""))
TEST_DATA["b"].append(("b#", ""))


# -----------------------------------------------------------------------------
# Test data for TEXT commands

TEST_DATA["a"] = [
    # Test cases for commands: a, i, c, e
    # Source: read_text()
    # Format: (sed script, expected text)
    # fmt: off

    # Traditional sed requires a line break after \
    ("a\\\ntext", "text"),

    # GNU sed allows no line break
    ("a\\text", "text"),

    # GNU sed allows no \ either
    ("atext", "text"),

    # Multiline texts with leading a\\n, a\, a should produce the same output
    ("a\\\n1\\\n2\\\n3", "1\\\n2\\\n3"),
    (  "a\\1\\\n2\\\n3", "1\\\n2\\\n3"),
    (    "a1\\\n2\\\n3", "1\\\n2\\\n3"),

    # Empty text at EOF is allowed (when having \ and/or \n)
    ("a\\\n", ""),
    ("a\\", ""),
    ("a\n", ""),
    #("a", ""),  # Error: expected \ after `a', `c' or `i'

    # Leading spaces before \ are ignored
    ("a \\space", "space"),
    ("a\t\\tab", "tab"),
    ("a \t \t \\mixed", "mixed"),

    # Leading spaces after \ are preserved
    ("a\\ text", " text"),
    ("a\\\ttext", "\ttext"),
    ("a\\ \t \t text", " \t \t text"),

    # Leading spaces are ignored when no \ is used
    ("a space", "space"),
    ("a\ttab", "tab"),
    ("a \t \t mixed", "mixed"),

    # Trailing spaces are always preserved
    ("atext ", "text "),
    ("atext\t", "text\t"),
    ("atext \t \t ", "text \t \t "),

    # From second line on, leading and trailing spaces are always preserved
    ("a\\\n1\\\n 2 \\\n\t3\t", "1\\\n 2 \\\n\t3\t"),
    (  "a\\1\\\n 2 \\\n\t3\t", "1\\\n 2 \\\n\t3\t"),
    (    "a1\\\n 2 \\\n\t3\t", "1\\\n 2 \\\n\t3\t"),

    # Literal escape at beginning and middle of the line
    ("a\\\n\\text\\text", "\\text\\text"),
    (  "a\\\\text\\text", "\\text\\text"),
    (      "atext\\text",   "text\\text"),

    # Literal escape at EOL is allowed except in the last line
    #XXX why only odd numbers work?
    ("a\\\n1" + "\\"*1 + "\n2", "1" + "\\"*1 + "\n2"),
    # ("a\\\n1" + "\\"*2 + "\n2p", "1" + "\\"*2 + "\n2p"),
    ("a\\\n1" + "\\"*3 + "\n2", "1" + "\\"*3 + "\n2"),
    # ("a\\\n1" + "\\"*4 + "\n2", "1" + "\\"*4 + "\n2"),
    ("a\\\n1" + "\\"*5 + "\n2", "1" + "\\"*5 + "\n2"),

    # Every char is valid (it reads until \n), so ;}# are not special
    ("a;", ";"),
    ("a}", "}"),
    ("a#", "#"),
    ("a\\ foo}; \t#", " foo}; \t#"),

    # Non-ASCII chars are allowed
    ("a★", "★"),
]

# Copy all "a" tests to: i, c, e
TEST_DATA["i"] = [("i" + script[1:], text) for script, text in TEST_DATA["a"]]
TEST_DATA["c"] = [("c" + script[1:], text) for script, text in TEST_DATA["a"]]
TEST_DATA["e"] = [("e" + script[1:], text) for script, text in TEST_DATA["a"]]

# Empty bare "e" is allowed (but forbidden for a, i, c)
TEST_DATA["e"].append(("e", ""))


# -----------------------------------------------------------------------------
# Test data for "y" and "s" commands

TEST_DATA["y"] = [
    # Test cases for commands: y, s
    # Source: match_slash()
    # Format: (sed script, delimiter, source, dest)
    # fmt: off

    # Simple usage
    ("y/a/A/", "/", "a", "A"),

    # Empty source and dest
    ("y///", "/", "", ""),

    # Source and dest are equal
    ("y/a/a/", "/", "a", "a"),

    # Space and tab in source and dest
    ("y/ /\t/", "/", " ", "\t"),
    ("y/\t/ /", "/", "\t", " "),

    # Otherwise special chars as delimiter
    ("y;a;A;",    ";",  "a", "A"),
    ("y[a[A[",    "[",  "a", "A"),
    ("y{a{A{",    "{",  "a", "A"),
    ("y}a}A}",    "}",  "a", "A"),
    ("y#a#A#",    "#",  "a", "A"),
    ("y a A ",    " ",  "a", "A"),
    ("y\ta\tA\t", "\t", "a", "A"),
    ("y\\a\\A\\", "\\", "a", "A"),

    # Literal / must be escaped as \/ in source and dest
    ("y/\\/a/\\/A/", "/", "\\/a", "\\/A"),

    # Literal x must be escaped as \x in source and dest when delim=x
    ("y#\\#a#\\#A#", "#", "\\#a", "\\#A"),

    # Literal \ must be escaped as \\ in source and dest
    ("y/\\\\/\\\\/", "/", "\\\\", "\\\\"),

    # Literal \n must be escaped as \\n in source and dest
    ("y/\\\n/\\\n/", "/", "\\\n", "\\\n"),

    # Literal \ is not allowed when \ is the delimiter
    #("y\\\\\\a\\\\\\A\\", "\\", "\\\\a", "\\\\A"),

    # Non-ASCII chars are NOT allowed as delimiter
    #("y★a★A★", "★", "a", "A"),

    # Non-ASCII chars are allowed as source and dest
    ("y/★/★/", "/", "★", "★"),
]

# Copy all "y" tests to: s
TEST_DATA["s"] = [
    ("s" + script[1:], delimiter, source, dest)
    for script, delimiter, source, dest in TEST_DATA["y"]
]

# y: source and dest are allowed to have different lengths
# Note: This differs from the GNU sed parser. Since we do not perform the
#       de-escaping of \/, \\ and \\n, the length check is turned off.
TEST_DATA["y"].append(("y/a/aa/", "/", "a", "aa"))

# Command name as delimiter
TEST_DATA["y"].append(("yyayAy", "y", "a", "A"))
TEST_DATA["s"].append(("ssasAs", "s", "a", "A"))

# Delimiter inside a regex character class
TEST_DATA["s"].append(("s/[/]//", "/", "[/]", ""))


# -----------------------------------------------------------------------------
# Test data for using flags in the "s" command

TEST_DATA["s-flags"] = [
    # Source: match_slash(), mark_subst_opts()
    # Format: (sed script, delimiter, pattern, replacement, flags, flag_arg)
    # fmt: off

    # Flags: traditional sed
    ("s/a/A/g",     "/", "a", "A", "g",   ""),
    ("s/a/A/p",     "/", "a", "A", "p",   ""),
    ("s/a/A/1",     "/", "a", "A", "1",   ""),
    ("s/a/A/99",    "/", "a", "A", "99",  ""),
    ("s/a/A/999",   "/", "a", "A", "999", ""),
    ("s/a/A/wfile", "/", "a", "A", "w",   "file"),

    # Flags: GNU sed extensions
    ("s/a/A/e", "/", "a", "A", "e", ""),
    ("s/a/A/m", "/", "a", "A", "m", ""),
    ("s/a/A/i", "/", "a", "A", "i", ""),
    ("s/a/A/M", "/", "a", "A", "M", ""),
    ("s/a/A/I", "/", "a", "A", "I", ""),

    # Flags: trailing \r\n is allowed
    ("s/a/A/g\r\n", "/", "a", "A", "g", ""),

    # Flags mixed (note that the order is preserved)
    ("s/a/A/gpemiMIwfile", "/", "a", "A", "gpemiMIw", "file"),

    # Flags: GNU sed extensions can be repeated
    ("s/a/A/eemmiiMMII", "/", "a", "A", "eemmiiMMII", ""),
    ("s/a/A/emiMIemiMI", "/", "a", "A", "emiMIemiMI", ""),

    # Flag w: must be the last flag (everything is a filename after it)
    ("s/a/A/wfile gp", "/", "a", "A", "w", "file gp"),

    # Flag w: leading spaces are ignored
    ("s/a/A/w space",       "/", "a", "A", "w", "space"),
    ("s/a/A/w\ttab",        "/", "a", "A", "w", "tab"),
    ("s/a/A/w \t \t mixed", "/", "a", "A", "w", "mixed"),

    # Flag w: every char is valid (it reads until \n), so ;}# are not special
    ("s/a/A/w;",  "/", "a", "A", "w", ";"),
    ("s/a/A/w}",  "/", "a", "A", "w", "}"),
    ("s/a/A/w#",  "/", "a", "A", "w", "#"),
    ("s/a/A/w\\", "/", "a", "A", "w", "\\"),
    ("s/a/A/w foo}; \t#\\", "/", "a", "A", "w", "foo}; \t#\\"),

    # Flag w: non-ASCII chars are allowed
    ("s/a/A/w★", "/", "a", "A", "w", "★"),
]


# -----------------------------------------------------------------------------

TEST_DATA["#"] = [
    # Test cases for comments
    # Preserving comments is a sedparse extension. GNU sed discards them.
    # Note: all scripts end in EOF. At run time the \n ending is also tested.
    # Note: result_index identifies # command index in the parsing results list.
    # Source: read_comment()
    # Format: (result_index, sed script, comment)
    # fmt: off

    # Empty comment
    (0, "#", ""),
    (1, "p#", ""),
    (1, "p;#", ""),

    # No spaces around #
    (0, "#foo", "foo"),
    (1, "p#foo", "foo"),
    (1, "p;#foo", "foo"),

    # Leading spaces before # are ignored
    (0, " \t#foo", "foo"),
    (1, "p \t#foo", "foo"),
    (1, "p; \t#foo", "foo"),

    # Leading and trailing spaces in the comment contents are preserved
    (0, "#  foo  ", "  foo  "),
    (0, "#\t\tfoo\t\t", "\t\tfoo\t\t"),

    # Extra leading # are treated as comment content
    (0, "##foo", "#foo"),
    (0, "####foo", "###foo"),

    # An escape at line end is not special inside comments
    (0, "#foo\\", "foo\\"),

    # Command-ending characters are not special inside comments
    (0, "#foo;", "foo;"),
    (0, "#foo}", "foo}"),

    # Comment right after a label command
    (1, ":a#foo", "foo"),
    (1, "ba#foo", "foo"),
    (1, "b #foo", "foo"),
    (1, "b#foo",  "foo"),

    # Comment right after y and s
    (1, "y/a/A/#foo",  "foo"),
    (1, "s/a/A/g#foo", "foo"),

    # Comment right after blocks
    # Note: "{#foo" is the only allowed partial comment in BSD sed (no ; before)
    (1, "{#foo\n}", "foo"),
    (2, "{}#foo",   "foo"),

    # The special #n at first line is treated as a normal comment by the parser.
    # After parsing, the calling code can make it special if desired.
    (0, "#n", "n"),
]


# -----------------------------------------------------------------------------

TEST_DATA["\n"] = [
    # Test cases for blank lines
    # Preserving blank lines is a sedparse extension. GNU sed discards them.
    # Source: ignore_trailing_fluff() and also search for "sedparse" comments.
    # Format: (sed script, *expected_parsed_commands)
    # fmt: off

    # 100% blank lines script
    ("\n", "\n"),
    ("\n\n", "\n", "\n"),
    ("\n\n\n", "\n", "\n", "\n"),

    # blank lines at the top and bottom should be preserved
    ("\n\np",   "\n", "\n", "p"),
    ("p\n\n\n", "p", "\n", "\n"),

    # blank lines between solo commands should be preserved
    ("p\nq",     "p", "q"),
    ("p\n\nq",   "p", "\n", "q"),
    ("p\n\n\nq", "p", "\n", "\n", "q"),

    # blank lines between label commands should be preserved
    ("b\nq",     "b", "q"),
    ("b\n\nq",   "b", "\n", "q"),
    ("b\n\n\nq", "b", "\n", "\n", "q"),

    # blank lines between filename commands should be preserved
    ("rfoo\nq",     "r", "q"),
    ("rfoo\n\nq",   "r", "\n", "q"),
    ("rfoo\n\n\nq", "r", "\n", "\n", "q"),

    # blank lines between text commands should be preserved
    ("a\\\nfoo\nq",     "a", "q"),
    ("a\\\nfoo\n\nq",   "a", "\n", "q"),
    ("a\\\nfoo\n\n\nq", "a", "\n", "\n", "q"),

    # blank lines between consecutive blocks should be preserved
    ("{\n}\n{}",         "{", "}", "{", "}"),
    ("{\n\n}\n\n{}",     "{", "\n", "}", "\n", "{", "}"),
    ("{\n\n\n}\n\n\n{}", "{", "\n", "\n", "}", "\n", "\n", "{", "}"),

    # blank lines between nested blocks should be preserved
    ("{\n{}\n}",         "{", "{", "}", "}"),
    ("{\n\n{}\n\n}",     "{", "\n", "{", "}", "\n", "}"),
    ("{\n\n\n{}\n\n\n}", "{", "\n", "\n", "{", "}", "\n", "\n", "}"),

    # blank lines between comments should be preserved
    ("#foo\n#bar",     "#", "#"),
    ("#foo\n\n#bar",   "#", "\n", "#"),
    ("#foo\n\n\n#bar", "#", "\n", "\n", "#"),
]


# -----------------------------------------------------------------------------

TEST_DATA["block"] = [
    # Test cases for blocks
    # Note: all scripts end in EOF. At run time the \n ending is also tested.
    # Format: (sed script, *expected_parsed_commands)
    # fmt: off

    # Empty blocks are allowed
    ("{}", "{", "}"),

    # Nested empty blocks are allowed
    ("{{}}", "{", "{", "}", "}"),

    # Using ; is optional around { and }
    ("{p}",   "{", "p", "}"),
    ("{p;}",  "{", "p", "}"),
    ("{;p}",  "{", "p", "}"),
    ("{;p;}", "{", "p", "}"),
    ("{p;};", "{", "p", "}"),
]


# -----------------------------------------------------------------------------

TEST_DATA["gotcha"] = [
    # Test cases for some gotchas
    # Note: all scripts end in EOF. At run time the \n ending is also tested.
    # Format: (sed script, *expected_parsed_commands)
    # fmt: off

    # Test read_label() detection for the next command
    ("blabel\t", "b"),
    ("blabel ", "b"),
    ("blabel;", "b"),
    ("{blabel}", "{", "b", "}"),
    ("blabel#", "b", "#"),
    ("blabel;;; #", "b", "#"),

    # Same tests repeated, now with an empty label
    ("b\t", "b"),
    ("b ", "b"),
    ("b;", "b"),
    ("{b}", "{", "b", "}"),
    ("b#", "b", "#"),
    ("b;;; #", "b", "#"),
]


# -----------------------------------------------------------------------------

TEST_DATA["trailing_fluff"] = [
    # Test cases for ignore_trailing_fluff()
    # Note: all scripts end in EOF. At run time the \n ending is also tested.
    # Format: (sed script, *expected_parsed_commands)
    # fmt: off

    # Ignore trailing spaces and tabs
    ("p      ", "p"),
    ("p\t\t\t", "p"),
    ("p\t \t ", "p"),

    # Ignore trailing semicolons
    ("p;",      "p"),
    ("p;;;;;",  "p"),
    ("p;;;;;x", "p", "x"),

    # Mixing spaces and semicolons
    ("p ;\t; ", "p"),
    ("p ;;\tx", "p", "x"),
]


class TestSedparseParser(unittest.TestCase):  # pylint: disable=unused-variable
    def _assert_defaults(self, data, skip=None, msg=""):
        """Assert that all command attributes are set to their default values.
        Use `skip=["foo"]` to skip checking the `foo` attribute.
        """
        # pylint: disable=too-many-branches
        if skip is None:
            skip = []
        if "a1" not in skip:
            self.assertEqual(None, data.a1, msg=msg)
        if "a2" not in skip:
            self.assertEqual(None, data.a2, msg=msg)
        if "addr_bang" not in skip:
            self.assertEqual(False, data.addr_bang, msg=msg)
        if "int_arg" not in skip:
            self.assertEqual(-1, data.x.int_arg, msg=msg)
        if "fname" not in skip:
            self.assertEqual("", data.x.fname, msg=msg)
        if "label_name" not in skip:
            self.assertEqual("", data.x.label_name, msg=msg)
        if "cmd_txt" not in skip:
            self.assertEqual("", str(data.x.cmd_txt), msg=msg)
        if "comment" not in skip:
            self.assertEqual("", data.x.comment, msg=msg)
        if "slash" not in skip:
            self.assertEqual("", data.x.cmd_subst.regx.slash, msg=msg)
        if "pattern" not in skip:
            self.assertEqual("", data.x.cmd_subst.regx.pattern, msg=msg)
        if "replacement" not in skip:
            self.assertEqual("", data.x.cmd_subst.replacement.text, msg=msg)
        if "flags" not in skip:
            self.assertEqual("", data.x.cmd_subst.regx.flags, msg=msg)
        if "outf" not in skip:
            self.assertEqual("", data.x.cmd_subst.outf.name, msg=msg)

    def test_address(self):
        for script, bang, addr1, addr2 in TEST_DATA["address"]:
            expected = [bang, addr1, addr2]

            # only the first command matters, i.e., { when {}
            parsed = parse_string(script)[0]
            self.assertListEqual(
                expected,
                [
                    parsed.addr_bang,
                    str(parsed.a1) if parsed.a1 else None,
                    str(parsed.a2) if parsed.a2 else None,
                ],
                msg=script,
            )

    def test_commands_with_no_args(self):
        commands = (
            "=",
            "d",
            "D",
            "F",
            "g",
            "G",
            "h",
            "H",
            "l",
            "L",
            "n",
            "N",
            "p",
            "P",
            "q",
            "Q",
            "x",
            "z",
        )
        for command in commands:
            for template in ("%s", "%s;", "{%s}", "%s#foo", "{ \t%s \t}"):
                script = template % command
                parsed = parse_string(script)
                parsed = parsed[1] if "{" in script else parsed[0]
                self.assertEqual(command, parsed.cmd, msg=script)
                self._assert_defaults(parsed, skip=None, msg=script)

    def test_commands_with_numeric_arg(self):
        # Note that those commands "solo", with no numeric arguments,
        # are already tested in test_commands_with_no_args().
        for command in ("l", "L", "q", "Q"):
            for arg in (0, 5, 99):
                for template in (
                    "%s%d",
                    "%s%d;",
                    "{%s%d}",
                    "%s%d#foo",
                    "{ \t%s \t%d \t}",
                ):
                    script = template % (command, arg)
                    parsed = parse_string(script)
                    parsed = parsed[1] if "{" in script else parsed[0]
                    self.assertEqual(command, parsed.cmd, msg=script)
                    self.assertEqual(arg, parsed.x.int_arg, msg=script)
                    self._assert_defaults(parsed, skip=["int_arg"], msg=script)

    def test_commands_with_filename(self):
        for command in ("r", "R", "w", "W"):
            for script_end in ("", "\n"):  # empty=EOF
                for script, filename in TEST_DATA[command]:
                    script = script + script_end
                    parsed = parse_string(script)[0]
                    self.assertEqual(command, parsed.cmd, msg=script)
                    self.assertEqual(filename, parsed.x.fname, msg=script)
                    self._assert_defaults(parsed, skip=["fname"], msg=script)

    def test_commands_with_label(self):
        for command in (":", "b", "t", "T", "v"):
            for script_end in ("", "\n"):  # empty=EOF
                for script, label in TEST_DATA[command]:
                    script = script + script_end
                    parsed = parse_string(script)
                    if parsed[0].cmd == "{":
                        parsed = parsed[1]
                    else:
                        parsed = parsed[0]
                    self.assertEqual(command, parsed.cmd, msg=script)
                    self.assertEqual(label, parsed.x.label_name, msg=script)
                    self._assert_defaults(parsed, skip=["label_name"], msg=script)

    def test_commands_with_text(self):
        for command in ("a", "i", "c", "e"):
            for script, text in TEST_DATA[command]:
                parsed = parse_string(script)[0]
                self.assertEqual(command, parsed.cmd, msg=script)
                self.assertEqual(text, str(parsed.x.cmd_txt), msg=script)
                self._assert_defaults(parsed, skip=["cmd_txt"], msg=script)

    def test_commands_y_and_s(self):
        for command in ("y", "s"):
            for script, delimiter, arg1, arg2 in TEST_DATA[command]:
                parsed = parse_string(script)[0]
                self.assertEqual(command, parsed.cmd, msg=script)
                self.assertEqual(delimiter, parsed.x.cmd_subst.regx.slash, msg=script)
                self.assertEqual(arg1, parsed.x.cmd_subst.regx.pattern, msg=script)
                self.assertEqual(arg2, parsed.x.cmd_subst.replacement.text, msg=script)
                self._assert_defaults(
                    parsed, skip=["slash", "pattern", "replacement"], msg=script
                )

    def test_command_s_flags(self):
        command = "s"
        for script, delimiter, pattern, replacement, flags, flag_arg in TEST_DATA[
            "s-flags"
        ]:
            parsed = parse_string(script)[0]
            self.assertEqual(command, parsed.cmd, msg=script)
            self.assertEqual(delimiter, parsed.x.cmd_subst.regx.slash, msg=script)
            self.assertEqual(pattern, parsed.x.cmd_subst.regx.pattern, msg=script)
            self.assertEqual(
                replacement, parsed.x.cmd_subst.replacement.text, msg=script
            )
            self.assertEqual(flags, parsed.x.cmd_subst.regx.flags, msg=script)
            self.assertEqual(flag_arg, parsed.x.cmd_subst.outf.name, msg=script)
            self._assert_defaults(
                parsed,
                skip=["slash", "pattern", "replacement", "flags", "outf"],
                msg=script,
            )

    def test_comments(self):  # sedparse extension
        command = "#"
        for script_end in ("", "\n"):  # empty=EOF
            for index, script, comment in TEST_DATA[command]:
                script = script + script_end
                parsed = parse_string(script)[index]
                self.assertEqual(command, parsed.cmd, msg=script)
                self.assertEqual(comment, parsed.x.comment, msg=script)
                self._assert_defaults(parsed, skip=["comment"], msg=script)

    def test_blank_lines(self):  # sedparse extension
        for data in TEST_DATA["\n"]:
            script = data[0]
            expected_commands = list(data[1:])
            self.assertEqual(
                expected_commands, [x.cmd for x in parse_string(script)], msg=script
            )

    def test_blocks(self):
        for script_end in ("", "\n"):  # empty=EOF
            for data in TEST_DATA["block"]:
                script = data[0] + script_end
                expected_commands = list(data[1:])
                self.assertEqual(
                    expected_commands, [x.cmd for x in parse_string(script)], msg=script
                )

    def test_gotchas(self):
        for script_end in ("", "\n"):  # empty=EOF
            for data in TEST_DATA["gotcha"]:
                script = data[0] + script_end
                expected_commands = list(data[1:])
                self.assertEqual(
                    expected_commands, [x.cmd for x in parse_string(script)], msg=script
                )

    def test_ignore_trailing_fluff(self):
        for script_end in ("", "\n"):  # empty=EOF
            for data in TEST_DATA["trailing_fluff"]:
                script = data[0] + script_end
                expected_commands = list(data[1:])
                self.assertEqual(
                    expected_commands, [x.cmd for x in parse_string(script)], msg=script
                )

    def test_command_data_cleanup(self):
        """
        All data from the previous command must be cleared when reading
        the next one. Those tests check that the last bare "p" command
        should be using the default values for all the data fields.
        """
        # a1, a2, bang, slash, pattern, replacement, flags, outf
        script = ["/a1/I, /a2/M ! s/foo/bar/igw file", "p"]
        p_data = parse_string("\n".join(script))[-1]
        self._assert_defaults(p_data, skip=None, msg=script)

        # int_arg
        script = ["q99", "p"]
        p_data = parse_string("\n".join(script))[-1]
        self._assert_defaults(p_data, skip=None, msg=script)

        # fname
        script = ["r file", "p"]
        p_data = parse_string("\n".join(script))[-1]
        self._assert_defaults(p_data, skip=None, msg=script)

        # label_name
        script = [":label", "p"]
        p_data = parse_string("\n".join(script))[-1]
        self._assert_defaults(p_data, skip=None, msg=script)

        # cmd_txt
        script = ["a", "text", "p"]
        p_data = parse_string("\n".join(script))[-1]
        self._assert_defaults(p_data, skip=None, msg=script)


if __name__ == "__main__":
    unittest.main()

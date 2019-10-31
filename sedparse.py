# sedparse
# GNU sed's parser translated from C to Python
# https://github.com/aureliojargas/sedparse

# TODO
# - identify and document all sedparse additions
# - document how it works
#
# WONTDO
# - Check if command only accepts one address
#   if (cur_cmd->a2) bad_prog (_(ONE_ADDR))
# - Check POSIX compatibility, all GNU sed extensions are supported
#   if (posixicity == POSIXLY_BASIC)

# Since sedparse is a literal translation, maintaining the same code, variables
# and method names, I have to disable the following checks.
# pylint: disable=global-statement
# pylint: disable=invalid-name
# pylint: disable=no-else-break
# pylint: disable=no-else-return
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-branches
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from __future__ import print_function  # pylint: disable=unused-variable
import argparse
import json
import sys

# Adapt some C entities to Python
NULL = None
EOF = "<EOF>"

# Default options when dumping JSON
# The separators argument is required in python2 https://bugs.python.org/issue16333
JSON_OPTS = {"indent": 4, "sort_keys": True, "separators": (",", ": ")}


# Base class to handle translated C structs
class struct:
    def to_dict(self, remove_empty=True):
        """
        Return the struct data as a dict.

        Using plain self.__dict__ works only for a single level. This function
        is recursive and converts all the nested structs.

        When using remove_empty, keys that have empty or default values are removed.

        Note that the structs use no dictionaries to store their data, so we
        don't need to check for it in this code.
        """
        d = {}
        for key, val in self.__dict__.items():
            if isinstance(val, struct):
                val = val.to_dict(remove_empty)
            if remove_empty:
                if val is None or val in ("", (), [], {}):
                    continue
                if key == "int_arg" and val == -1:
                    continue
                if key == "addr_bang" and not val:
                    continue
                if key == "addr_step" and val == 0:
                    continue
                if (
                    key == "addr_number"
                    and val == 0
                    and self.__dict__["addr_type"] in (ADDR_IS_REGEX, ADDR_IS_LAST)
                ):
                    continue
            d[key] = val
        return d

    def to_json(self, remove_empty=True):
        return json.dumps(self, default=lambda x: x.to_dict(remove_empty), **JSON_OPTS)


class ParseError(Exception):
    # pylint: disable=too-many-arguments
    def __init__(self, message="", file="", line=0, column=0, expression=0, exitcode=1):
        # https://stackoverflow.com/a/38857736
        super(ParseError, self).__init__(message)
        self.message = message
        self.file = file
        self.line = line
        self.column = column
        self.expression = expression
        self.exitcode = exitcode


######################################## translated from sed.c

program_name = "sedparse"

######################################## translated from basicdefs.h


def ISBLANK(c):
    return c in (" ", "\t")


def ISDIGIT(ch):
    return ch in "0123456789"


def ISSPACE(c):
    return c in (" ", "\t", "\n", "\v", "\f", "\r")


######################################## translated from sed.h

# sedparse: The original code handles file open/read/write/close operations,
# but here we only care about the filename.
class struct_output(struct):
    def __init__(self):
        self.name = ""

        # sedparse: not used
        # missing_newline = False
        # fp = None
        # link = None

    def __repr__(self):
        return "%s(name=%r)" % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name


class struct_text_buf(struct):
    def __init__(self):
        self.text = []
        # text_length = 0  # sedparse: not used

    def __repr__(self):
        return "%s(text=%r)" % (self.__class__.__name__, self.text)

    def __str__(self):
        return "".join(self.text)[:-1]  # remove trailing \n


class struct_regex(struct):
    def __init__(self):
        self.pattern = ""

        # In the original this was an integer, a bitwise OR for address flags.
        # In sedparse it is a string with all the found flags, in their
        # original order, and even repetition is preserved. It is also used
        # to save both regex address flags and "s" command flags.
        self.flags = ""  # sedparse: was 0 in the original

        # This is used to save the slash char used as delimiter in: regex
        # addresses (/foo/p) and in "s" and "y" commands (s///).
        self.slash = ""  # sedparse extension

        # sedparse: not used
        # sz = 0
        # dfa = None  # struct_dfa()
        # begline = False
        # endline = False
        # re = ""

    def __repr__(self):
        return "%s(slash=%r, pattern=%r, flags=%r)" % (
            self.__class__.__name__,
            self.slash,
            self.pattern,
            self.flags,
        )

    def __str__(self):
        return self.escape() + self.slash + self.pattern + self.slash + self.flags

    def escape(self):  # sedparse extension
        return "\\" if self.slash != "/" else ""


# sedparse: not used
# # enum replacement_types {
# REPL_ASIS = 0
# REPL_UPPERCASE = 1
# REPL_LOWERCASE = 2
# REPL_UPPERCASE_FIRST = 4
# REPL_LOWERCASE_FIRST = 8
# REPL_MODIFIERS = REPL_UPPERCASE_FIRST | REPL_LOWERCASE_FIRST
# # These are given to aid in debugging
# REPL_UPPERCASE_UPPERCASE = REPL_UPPERCASE_FIRST | REPL_UPPERCASE
# REPL_UPPERCASE_LOWERCASE = REPL_UPPERCASE_FIRST | REPL_LOWERCASE
# REPL_LOWERCASE_UPPERCASE = REPL_LOWERCASE_FIRST | REPL_UPPERCASE
# REPL_LOWERCASE_LOWERCASE = REPL_LOWERCASE_FIRST | REPL_LOWERCASE

# sedparse: not used
# # enum text_types {
# TEXT_BUFFER = 1
# TEXT_REPLACEMENT = 2
# TEXT_REGEX = 3

# sedparse: not used
# # enum addr_state {
# RANGE_INACTIVE = 1           # never been active
# RANGE_ACTIVE = 2             # between first and second address
# RANGE_CLOSED = 3             # like RANGE_INACTIVE, but range has ended once

# enum addr_types {
# fmt: off
ADDR_IS_NULL = 1             # null address
ADDR_IS_REGEX = 2            # a.addr_regex is valid
ADDR_IS_NUM = 3              # a.addr_number is valid
ADDR_IS_NUM_MOD = 4          # a.addr_number is valid, addr_step is modulo
ADDR_IS_STEP = 5             # address is +N (only valid for addr2)
ADDR_IS_STEP_MOD = 6         # address is ~N (only valid for addr2)
ADDR_IS_LAST = 7             # address is $
# fmt: on


class struct_addr(struct):
    def __init__(self):
        self.addr_type = ADDR_IS_NULL  # enum addr_types
        self.addr_number = 0
        self.addr_step = 0
        self.addr_regex = struct_regex()

    def __repr__(self):
        return "%s(addr_type=%r, addr_number=%r, addr_step=%r, addr_regex=%r)" % (
            self.__class__.__name__,
            self.addr_type,
            self.addr_number,
            self.addr_step,
            self.addr_regex,
        )

    def __str__(self):
        ret = ""
        if self.addr_type == ADDR_IS_REGEX:
            ret = str(self.addr_regex)
        elif self.addr_type == ADDR_IS_NUM:
            ret = str(self.addr_number)
        elif self.addr_type == ADDR_IS_NUM_MOD:
            ret = "%s~%s" % (self.addr_number, self.addr_step)
        elif self.addr_type == ADDR_IS_STEP:
            ret = "+%s" % self.addr_step
        elif self.addr_type == ADDR_IS_STEP_MOD:
            ret = "~%s" % self.addr_step
        elif self.addr_type == ADDR_IS_LAST:
            ret = "$"
        else:  # sedparse: this condition should not happen
            ret = "<unknown address type '%s'>" % self.addr_type
        return ret


class struct_replacement(struct):
    def __init__(self):
        self.text = ""  # sedparse extension

        # sedparse: not used
        # prefix = ""
        # prefix_length = 0
        # subst_id = 0
        # repl_type = REPL_ASIS  # enum replacement_types
        # next_ = None  # struct_replacement

    def __repr__(self):
        return "%s(text=%r)" % (self.__class__.__name__, self.text)

    def __str__(self):
        return self.text


class struct_subst(struct):
    def __init__(self):
        self.regx = struct_regex()
        self.replacement = struct_replacement()
        self.outf = struct_output()  # "w" option given

        # sedparse: not used
        # Note that instead of using those attributes to save the found flags,
        # sedparse saves them to self.regx.flags as a single string, preserving
        # the original order and possible repetition.
        # numb = 0  # if >0, only substitute for match number "numb"
        # global_ = False  # "g" option given
        # print_ = False  # "p" option given (before/after eval)
        # eval_ = False  # "e" option given
        # max_id = 0  # maximum backreference on the RHS
        # replacement_buffer = ""  # ifdef lint

    def __repr__(self):
        return "%s(regx=%r, replacement=%r, outf=%r)" % (
            self.__class__.__name__,
            self.regx,
            self.replacement,
            self.outf,
        )

    def __str__(self):
        return (
            self.regx.slash
            + str(self.regx.pattern)
            + self.regx.slash
            + str(self.replacement.text)
            + self.regx.slash
            + self.regx.flags
            + (" " + self.outf.name if "w" in self.regx.flags else "")
        )


# sedparse: In the original this was a 'union' inside 'struct sed_cmd'
class struct_sed_cmd_x(struct):
    "auxiliary data for various commands"

    def __init__(self):
        # This structure is used for a, i, and c commands.
        self.cmd_txt = struct_text_buf()

        # This is used for the l, q and Q commands.
        self.int_arg = -1

        # This is used for the r command. (sedparse: and R w W)
        self.fname = ""

        # This is used for the hairy s command. (sedparse: and y)
        self.cmd_subst = struct_subst()

        # This is used for the ":" command.
        self.label_name = ""

        # This is used for the command comment.
        self.comment = ""  # sedparse extension

        # sedparse: not used
        # # This is used for the {}, b, and t commands.
        # jump_index = 0
        # # This is used for the w command.
        # outf = struct_output()
        # # This is used for the R command.
        # # (despite the struct name, it is used for both in and out files).
        # inf = struct_output()
        # # This is used for the y command.
        # translate = ""
        # translatemb = ""

    def __repr__(self):
        return (
            "%s(int_arg=%r, label_name=%r, fname=%r, comment=%r,"
            " cmd_txt=%r, cmd_subst=%r)"
            % (
                self.__class__.__name__,
                self.int_arg,
                self.label_name,
                self.fname,
                self.comment,
                self.cmd_txt,
                self.cmd_subst,
            )
        )


class struct_sed_cmd(struct):
    def __init__(self):
        # Command addresses
        self.a1 = struct_addr()
        self.a2 = struct_addr()

        # Non-zero if command is to be applied to non-matches.
        self.addr_bang = False  # sedparse: using bool

        # The actual command character.
        self.cmd = ""

        # auxiliary data for various commands
        self.x = struct_sed_cmd_x()

        # The original line number where this command was found
        self.line = 0  # sedparse extension

        # sedparse: not used
        # range_state = RANGE_INACTIVE  # See enum addr_state

    def __repr__(self):
        return "%s(line=%r, cmd=%r, addr_bang=%r, a1=%r, a2=%r, x=%r)" % (
            self.__class__.__name__,
            self.line,
            self.cmd,
            self.addr_bang,
            self.a1,
            self.a2,
            self.x,
        )

    def __str__(self):
        ret = []

        if self.a1:
            ret.append(str(self.a1))
        if self.a2:
            ret.append(",%s" % self.a2)
        if ret:
            ret.append(" ")

        if self.addr_bang:
            ret.append("!")

        ret.append(self.cmd)

        if self.cmd == "\n":
            pass
        elif self.cmd == "#":
            ret.append(self.x.comment)
        elif self.cmd == ":":
            ret.append(self.x.label_name)
        elif self.cmd in ("s", "y"):
            ret.append(str(self.x.cmd_subst))
        elif self.x.label_name:
            ret.append(" " + self.x.label_name)
        elif self.x.fname:
            ret.append(" " + self.x.fname)
        elif self.x.int_arg and self.x.int_arg > -1:
            ret.append(" %s" % self.x.int_arg)
        elif self.x.cmd_txt.text:  # a i c
            ret.append("\\\n%s" % self.x.cmd_txt)

        return "".join(ret)


# sedparse: This is probably from regex.c, but I'll fake it here
# just saving the collected strings
def compile_regex(pattern, flags):
    r = struct_regex()
    r.pattern = "".join(pattern)
    r.flags = "".join(flags)
    return r


def IS_MB_CHAR(ch):
    return ch != EOF and ord(ch) > 127
    # sedparse: This exception is because I chose to store EOF as "<EOF>"


######################################## translated from utils.h

# enum exit_codes
EXIT_SUCCESS = 0
EXIT_BAD_USAGE = 1  # bad program syntax, invalid command-line options
# EXIT_BAD_INPUT = 2  # failed to open some of the input files (sedparse: not used)
EXIT_PANIC = 4  # PANIC during program execution

######################################## translated from utils.c

# Print an error message and exit
def panic(msg):
    raise ParseError(exitcode=EXIT_PANIC, message="%s: %s" % (program_name, msg))


def init_buffer():
    return []


def add1_buffer(buffer, ch):
    if ch != EOF:
        buffer.append(ch)  # in-place
    # the return is never used


def free_buffer(b):
    del b


######################################## translated from compile.c

OPEN_BRACKET = "["
CLOSE_BRACKET = "]"
# OPEN_BRACE = "{"
CLOSE_BRACE = "}"

# struct prog_info {
#   /* When we're reading a script command from a string, `prog.base'
#      points to the first character in the string, 'prog.cur' points
#      to the current character in the string, and 'prog.end' points
#      to the end of the string.  This allows us to compile script
#      strings that contain nulls. */
#   const unsigned char *base;
#   const unsigned char *cur;
#   const unsigned char *end;

#   /* This is the current script file.  If it is NULL, we are reading
#      from a string stored at `prog.cur' instead.  If both `prog.file'
#      and `prog.cur' are NULL, we're in trouble! */
#   FILE *file;
# };
class prog_info:
    base = None  # int
    cur = None  # int
    end = None  # int
    file = None  # file descriptor
    text = None  # str
    # Using None because some code checks for "is not None" to detect unset state


# Information used to give out useful and informative error messages.
# struct error_info {
#   /* This is the name of the current script file. */
#   const char *name;

#   /* This is the number of the current script line that we're compiling. */
#   countT line;

#   /* This is the index of the "-e" expressions on the command line. */
#   countT string_expr_count;
# };
class error_info:
    name = ""
    line = 0
    string_expr_count = 0


# Where we are in the processing of the input.
class prog(prog_info):
    pass


class cur_input(error_info):
    pass


# sedparse: not used
# /* We wish to detect #n magic only in the first input argument;
#   this flag tracks when we have consumed the first file of input. */
# static bool first_script = true;
# first_script = True

# Allow for scripts like "sed -e 'i\' -e foo":
# static struct buffer *pending_text = NULL;
# static struct text_buf *old_text_buf = NULL;
pending_text = NULL
old_text_buf = NULL

# /* Information about block start positions.  This is used to backpatch
#   block end positions. */
# static struct sed_label *blocks = NULL;
blocks = 0

# Various error messages we may want to print
# sedparse: not used messages are commented
BAD_BANG = "multiple `!'s"
BAD_COMMA = "unexpected `,'"
BAD_STEP = "invalid usage of +N or ~N as first address"
EXCESS_OPEN_BRACE = "unmatched `{'"
EXCESS_CLOSE_BRACE = "unexpected `}'"
EXCESS_JUNK = "extra characters after command"
EXPECTED_SLASH = "expected \\ after `a', `c' or `i'"
NO_CLOSE_BRACE_ADDR = "`}' doesn't want any addresses"
# NO_COLON_ADDR = ": doesn't want any addresses"
# NO_SHARP_ADDR = "comments don't accept any addresses"
NO_COMMAND = "missing command"
# ONE_ADDR = "command only uses one address"
UNTERM_ADDR_RE = "unterminated address regex"
UNTERM_S_CMD = "unterminated `s' command"
UNTERM_Y_CMD = "unterminated `y' command"
UNKNOWN_S_OPT = "unknown option to `s'"
EXCESS_P_OPT = "multiple `p' options to `s' command"
EXCESS_G_OPT = "multiple `g' options to `s' command"
EXCESS_N_OPT = "multiple number options to `s' command"
ZERO_N_OPT = "number option to `s' command may not be zero"
# Y_CMD_LEN = "strings for `y' command are different lengths"
BAD_DELIM = "delimiter character is not a single-byte character"
# ANCIENT_VERSION = "expected newer version of sed"
INVALID_LINE_0 = "invalid usage of line address 0"
UNKNOWN_CMD = "unknown command: `%c'"
# INCOMPLETE_CMD = "incomplete command"
COLON_LACKS_LABEL = '":" lacks a label'
# RECURSIVE_ESCAPE_C = "recursive escaping after \\c not allowed"
# DISALLOWED_CMD = "e/r/w commands disabled in sandbox mode"
MISSING_FILENAME = "missing filename in r/R/w/W commands"

# Complain about an unknown command and exit.
def bad_command(ch):
    bad_prog(UNKNOWN_CMD % ch)


# Complain about a programming error and exit.
def bad_prog(why):
    if cur_input.name:
        msg = "%s: file %s line %d: %s" % (
            program_name,
            cur_input.name,
            cur_input.line,
            why,
        )
    else:
        msg = "%s: -e expression #%d, char %d: %s" % (
            program_name,
            cur_input.string_expr_count,
            prog.cur - prog.base,
            why,
        )
    raise ParseError(
        message=msg,
        file=cur_input.name,
        expression=cur_input.string_expr_count,
        line=cur_input.line,
        column=(prog.cur - prog.base) if prog.cur else 0,
        exitcode=EXIT_BAD_USAGE,
    )


# /* Read the next character from the program.  Return EOF if there isn't
#   anything to read.  Keep cur_input.line up to date, so error messages
#   can be meaningful. */
def inchar():
    ch = EOF
    if prog.cur is not None:
        if prog.cur < prog.end:
            prog.cur += 1
            ch = prog.text[prog.cur]
    elif prog.file:
        # https://stackoverflow.com/a/15599780
        ch = prog.file.read(1)
        if not ch:
            ch = EOF
    if ch == "\n":
        cur_input.line += 1
    debug(ch, stats=True)
    return ch


# unget `ch' so the next call to inchar will return it.
def savchar(ch):
    debug("savchar(%s)" % ch, stats=True)
    if ch == EOF:
        return
    if ch == "\n" and cur_input.line > 0:
        cur_input.line -= 1
    if prog.cur:
        prog.cur -= 1
        # XXX not sure about cur+1
        if prog.cur <= prog.base or prog.text[prog.cur + 1] != ch:
            # panic("Called savchar with unexpected pushback (%s)" % ch)
            panic(
                "Called savchar with unexpected pushback (curr=%s %s!=%s)"
                % (prog.cur, prog.text[prog.cur], ch)
            )
    else:
        try:
            # Go back one position in prog.file file descriptor pointer
            prog.file.seek(prog.file.tell() - 1)  # ungetc(ch, prog.file)
        except ValueError:  # negative seek position -1
            pass


# Read the next non-blank character from the program.
def in_nonblank():
    while True:
        ch = inchar()
        if not ISBLANK(ch):
            break
    return ch


# sedparse extension
# Ignore multiple trailing blanks and ; until EOC/EOL/EOF. Skipping those chars
# avoids \n incorrectly being considered a new command and producing a new
# undesired blank line in the output.
def ignore_trailing_fluff():
    while True:
        ch = in_nonblank()
        if ch == ";":  # skip it
            pass
        elif ch in (EOF, "\n"):  # EOF, EOL
            return
        else:  # start of a new command
            savchar(ch)
            return


# /* Consume script input until a valid end of command marker is found:
#      comment, closing brace, newline, semicolon or EOF.
#   If any other character is found, die with 'extra characters after command'
#   error.
# */
def read_end_of_cmd():
    ch = in_nonblank()
    if ch in (CLOSE_BRACE, "#"):
        savchar(ch)
    elif ch not in (EOF, "\n", ";"):
        bad_prog(EXCESS_JUNK)

    # sedparse: Ignore multiple trailing blanks and ; until EOC/EOL/EOF
    elif ch == ";":
        ignore_trailing_fluff()


# Read an integer value from the program.
def in_integer(ch):
    num = []
    while ISDIGIT(ch):
        num.append(ch)
        ch = inchar()
    savchar(ch)
    return int("".join(num))


def add_then_next(buffer, ch):
    add1_buffer(buffer, ch)
    return inchar()


# sedparse extension
# This is a copy of read_filename, but preserving blanks.
def read_comment():
    b = init_buffer()
    ch = inchar()
    while ch not in (EOF, "\n"):
        ch = add_then_next(b, ch)
    return b


# Read in a filename for a `r', `w', or `s///w' command.
def read_filename():
    b = init_buffer()
    ch = in_nonblank()
    while ch not in (EOF, "\n"):
        ch = add_then_next(b, ch)
    # add1_buffer(b, "\0");  # not necessary in Python
    return b


def next_cmd_entry(vector):
    cmd = struct_sed_cmd()
    cmd.a1 = NULL
    cmd.a2 = NULL
    # cmd.range_state = RANGE_INACTIVE  # sedparse: not used
    cmd.addr_bang = False
    cmd.cmd = "\0"  # something invalid, to catch bugs early
    vector.append(cmd)
    return cmd


def snarf_char_class(b):  # , cur_stat):
    state = 0
    delim = None  # delim IF_LINT( = 0)

    ch = inchar()
    if ch == "^":
        ch = add_then_next(b, ch)
    if ch == CLOSE_BRACKET:
        ch = add_then_next(b, ch)

    # States are:
    #   0 outside a collation element, character class or collation class
    #   1 after the bracket
    #   2 after the opening ./:/=
    #   3 after the closing ./:/=

    # for (;; ch = add_then_next(b, ch)) {
    first_loop_run = True
    while True:
        if not first_loop_run:
            ch = add_then_next(b, ch)
        first_loop_run = False

        mb_char = IS_MB_CHAR(ch)  # , cur_stat)

        if ch in (EOF, "\n"):
            return ch

        if ch in (".", ":", "="):
            if mb_char:
                continue

            if state == 1:
                delim = ch
                state = 2
            elif state == 2 and ch == delim:
                state = 3
            # else:
            #     break  # break from C-switch

            continue

        if ch == OPEN_BRACKET:
            if mb_char:
                continue

            if state == 0:
                state = 1
            continue

        if ch == CLOSE_BRACKET:
            if mb_char:
                continue

            if state in (0, 1):
                return ch

            if state == 3:
                state = 0

        # Getting a character different from .=: whilst in state 1
        # goes back to state 0, getting a character different from ]
        # whilst in state 3 goes back to state 2.
        if ch not in (".", ":", "=") and state == 1:
            state = 0
        elif ch != CLOSE_BRACKET and state == 3:
            state = 2

        # state &= ~1  # please, no magic


def match_slash(slash, regex):  # char, bool
    # struct buffer *b
    # mbstate_t cur_stat = { 0, }

    # We allow only 1 byte characters for a slash.
    if IS_MB_CHAR(slash):  # , &cur_stat):
        bad_prog(BAD_DELIM)

    # memset(&cur_stat, 0, sizeof cur_stat)

    b = init_buffer()

    # while ((ch = inchar ()) != EOF && ch != '\n')
    while True:
        ch = inchar()
        if ch in (EOF, "\n"):
            break

        # const mb_char = IS_MB_CHAR(ch, &cur_stat)

        if not IS_MB_CHAR(ch):
            if ch == slash:
                return b

            elif ch == "\\":
                ch = inchar()
                if ch == EOF:
                    break
                # sedparse
                # # GNU sed interprets \n here, we don't
                # elif ch == "n" and regex:
                #     ch = "\n"
                # # Those exceptions remove the leading \ from known situations
                # # For example, s/a\/b/.../ becomes "a/b" not "a\/b"
                # # Since I want to keep the original user text, this is disabled
                # elif (ch != "\n" and (ch != slash or (not regex and ch == "&"))):
                else:
                    add1_buffer(b, "\\")
            elif ch == OPEN_BRACKET and regex:
                add1_buffer(b, ch)
                ch = snarf_char_class(b)  # , &cur_stat)
                if ch != CLOSE_BRACKET:
                    break

        add1_buffer(b, ch)

    if ch == "\n":
        savchar(ch)  # for proper line number in error report
    free_buffer(b)
    return NULL


# sedparse: this function works differently from the original.
# In gsed, there's no return, since it just sets all the flags as properties of
# "cmd_s". Here it collects and returns the flags as a list.
def mark_subst_opts(cmd_s):
    flags = []
    numb = False

    while True:
        ch = in_nonblank()
        debug("s flag candidate: %r" % ch)

        if ch in ("i", "I", "m", "M", "e"):  # GNU extensions
            flags.append(ch)

        elif ch == "p":
            if ch in flags:
                bad_prog(EXCESS_P_OPT)
            flags.append(ch)

        elif ch == "g":
            if ch in flags:
                bad_prog(EXCESS_G_OPT)
            flags.append(ch)

        elif ch in "0123456789":
            if numb:
                bad_prog(EXCESS_N_OPT)
            n = in_integer(ch)
            if int(n) == 0:
                bad_prog(ZERO_N_OPT)
            flags.append(str(n))
            numb = True

        elif ch == "w":
            flags.append(ch)
            # This flag will always be at the end of the list, since after w
            # cannot exist any other flag because the filename consumes
            # everything until the end of the line.
            b = read_filename()
            if not b:
                bad_prog(MISSING_FILENAME)
            cmd_s.outf.name = "".join(b)
            debug("s flag filename: %r" % cmd_s.outf.name)
            return flags

        elif ch == "#":
            savchar(ch)
            return flags

        elif ch == CLOSE_BRACE:
            savchar(ch)
            return flags

        # sedparse: Ignore multiple trailing blanks and ; until EOC/EOL/EOF
        elif ch == ";":
            ignore_trailing_fluff()
            return flags

        elif ch in (EOF, "\n"):
            return flags

        elif ch == "\r":
            if inchar() == "\n":
                return flags
            bad_prog(UNKNOWN_S_OPT)

        else:
            bad_prog(UNKNOWN_S_OPT)
        # NOTREACHED


# read in a label for a `:', `b', or `t' command
def read_label():
    b = init_buffer()
    ch = in_nonblank()

    while ch not in (EOF, "\n", ";", CLOSE_BRACE, "#") and not ISBLANK(ch):
        ch = add_then_next(b, ch)

    savchar(ch)

    # sedparse extension: Ignore trailing blanks and ; until EOC/EOL/EOF
    ignore_trailing_fluff()

    # add1_buffer(b, "\0")  # not necessary in Python
    ret = "".join(b)
    free_buffer(b)
    return ret


def read_text(buf, leadin_ch):
    global pending_text
    global old_text_buf

    if buf:
        if pending_text:
            free_buffer(pending_text)
        pending_text = init_buffer()
        buf.text = []
        # buf.text_length = 0  # sedparse: not used
        old_text_buf = buf

    if leadin_ch == EOF:
        return

    if leadin_ch != "\n":
        add1_buffer(pending_text, leadin_ch)

    ch = inchar()
    while ch not in (EOF, "\n"):
        if ch == "\\":
            ch = inchar()
            if ch != EOF:
                add1_buffer(pending_text, "\\")

        if ch == EOF:
            add1_buffer(pending_text, "\n")
            return

        ch = add_then_next(pending_text, ch)

    add1_buffer(pending_text, "\n")

    if not buf:
        buf = old_text_buf
    # buf.text_length = normalize_text(get_buffer (pending_text),
    #                                  size_buffer (pending_text), TEXT_BUFFER)
    buf.text = pending_text
    free_buffer(pending_text)
    pending_text = NULL


# Try to read an address for a sed command.  If it succeeds,
#   return non-zero and store the resulting address in `*addr'.
#   If the input doesn't look like an address read nothing
#   and return zero.
def compile_address(addr, ch):  # struct_addr, str
    addr.addr_type = ADDR_IS_NULL
    addr.addr_step = 0
    addr.addr_number = 0  # extremely unlikely to ever match
    addr.addr_regex = NULL

    if ch in ("/", "\\"):
        # sedparse: Instead of using bit flags as regex.c, I'll just save the
        # flags as text
        flags = []
        # flags = 0
        # struct buffer *b

        addr.addr_type = ADDR_IS_REGEX
        if ch == "\\":
            ch = inchar()
        b = match_slash(ch, True)
        if b == NULL:
            bad_prog(UNTERM_ADDR_RE)
        slash = ch

        while True:
            ch = in_nonblank()
            # if posixicity == POSIXLY_BASIC:
            #     goto posix_address_modifier
            if ch == "I":  # GNU extension
                # flags |= REG_ICASE
                flags.append(ch)
            elif ch == "M":  # GNU extension
                # flags |= REG_NEWLINE
                flags.append(ch)
            else:
                #   posix_address_modifier:  # GOTO label
                savchar(ch)
                addr.addr_regex = compile_regex(b, flags)
                addr.addr_regex.slash = slash
                free_buffer(b)
                return True

    elif ISDIGIT(ch):
        addr.addr_number = in_integer(ch)
        addr.addr_type = ADDR_IS_NUM
        ch = in_nonblank()
        if ch != "~":  # or posixicity == POSIXLY_BASIC:
            savchar(ch)
        else:
            step = in_integer(in_nonblank())
            if step > 0:
                addr.addr_step = step
                addr.addr_type = ADDR_IS_NUM_MOD

    elif ch in ("+", "~"):  # and posixicity != POSIXLY_BASIC:
        addr.addr_step = in_integer(in_nonblank())
        # sedparse: skipping this to match and save 1,~0p and 1,+0p
        # if addr.addr_step == 0:
        #     pass  # default to ADDR_IS_NULL; forces matching to stop on next line
        # elif ch == "+":
        if ch == "+":
            addr.addr_type = ADDR_IS_STEP
        else:
            addr.addr_type = ADDR_IS_STEP_MOD

    elif ch == "$":
        addr.addr_type = ADDR_IS_LAST

    else:
        return False
    return True


# Read a program (or a subprogram within `{' `}' pairs) in and store
# the compiled form in `*vector'.  Return a pointer to the new vector.
def compile_program(vector):
    global blocks

    if pending_text:
        read_text(NULL, "\n")

    while True:

        a = struct_addr()

        # while ((ch=inchar ()) == ';' || ISSPACE (ch))
        #   ;
        # if (ch == EOF)
        #   break;
        while True:
            ch = inchar()

            # sedparse:
            # GNU sed parser discards the \n used as command separator.
            # Sedsed keeps all cosmetic line breaks (i.e. \n\n) when formatting
            # code. So here sedparse creates the concept of the \n command, to
            # identify and preserve those breaks.
            if ch == "\n":
                break

            if ch != ";" and not ISSPACE(ch):
                break

        if ch == EOF:
            break

        cur_cmd = next_cmd_entry(vector)
        cur_cmd.line = cur_input.line

        if compile_address(a, ch):
            if a.addr_type == ADDR_IS_STEP or a.addr_type == ADDR_IS_STEP_MOD:
                bad_prog(BAD_STEP)

            cur_cmd.a1 = a  # MEMDUP(&a, 1, struct addr)
            debug("----- Found address 1: %r" % cur_cmd.a1)

            a = struct_addr()  # reset a
            ch = in_nonblank()
            if ch == ",":
                if not compile_address(a, in_nonblank()):
                    bad_prog(BAD_COMMA)

                cur_cmd.a2 = a  # MEMDUP(&a, 1, struct addr)
                debug("----- Found address 2: %r" % cur_cmd.a2)
                ch = in_nonblank()

            # sedparse: removed: or posixicity == POSIXLY_BASIC)):
            if cur_cmd.a1.addr_type == ADDR_IS_NUM and cur_cmd.a1.addr_number == 0:
                if not cur_cmd.a2 or cur_cmd.a2.addr_type != ADDR_IS_REGEX:
                    bad_prog(INVALID_LINE_0)

        if ch == "!":
            cur_cmd.addr_bang = True
            debug("----- Found negation: !")
            ch = in_nonblank()
            if ch == "!":
                bad_prog(BAD_BANG)

        # Do not accept extended commands in --posix mode.  Also,
        # a few commands only accept one address in that mode.
        # SKIPPED

        cur_cmd.cmd = ch
        debug("----- Found command: %r" % ch)

        # sedparse
        if ch == "\n":
            # Adjust the line number for the empty lines, because they're just
            # detected in the next line
            cur_cmd.line -= 1

            # Detect cases like 1\n, an address with no "real" command
            if cur_cmd.a1:
                bad_prog(NO_COMMAND)

        elif ch == "#":
            # if (cur_cmd->a1)
            #     bad_prog (_(NO_SHARP_ADDR));

            # sedparse: no #n detection, it will be considered a normal comment
            # ch = inchar()
            # if ch == "n" and first_script and cur_input.line < 2:
            #     if (prog.base and prog.cur == 2 + prog.base):
            #     # or (prog.file and not prog.base and 2 == ftell(prog.file)):
            #       no_default_output = true

            # sedparse: GNU sed discards the comment contents, but we must save it
            b = read_comment()
            cur_cmd.x.comment = "".join(b)
            debug("comment: %r" % cur_cmd.x.comment)
            free_buffer(b)
            # while ch != EOF and ch != "\n":
            #     ch = inchar()
            # continue

        elif ch == "v":
            argument = read_label()
            cur_cmd.x.label_name = argument
            debug("argument: %s" % argument)

        elif ch == "{":
            blocks += 1

            # sedparse: Ignore multiple trailing blanks and ; until EOC/EOL/EOF
            ignore_trailing_fluff()

            # cur_cmd.addr_bang = not cur_cmd.addr_bang  # ?

        elif ch == "}":
            if not blocks:
                bad_prog(EXCESS_CLOSE_BRACE)
            if cur_cmd.a1:
                bad_prog(NO_CLOSE_BRACE_ADDR)

            read_end_of_cmd()
            blocks -= 1  # done with this entry

        # sedparse: "e" handling was moved here (original code uses GOTO)
        elif ch in ("a", "i", "c", "e"):
            ch = in_nonblank()

            # GOTO read_text_to_slash:
            # sedparse: Empty "e" at EOF is allowed
            if ch == EOF and cur_cmd.cmd == "e":
                break

            if ch == EOF:
                bad_prog(EXPECTED_SLASH)

            if ch == "\\":
                ch = inchar()
            else:
                # if posixicity == POSIXLY_BASIC:
                #     bad_prog(EXPECTED_SLASH)
                savchar(ch)
                ch = "\n"

            read_text(cur_cmd.x.cmd_txt, ch)
            debug("text: %r" % cur_cmd.x.cmd_txt)
        # END GOTO

        elif ch in (":", "T", "b", "t"):
            # if (cur_cmd->a1)
            #   bad_prog (_(NO_COLON_ADDR));
            label = read_label()
            cur_cmd.x.label_name = label
            debug("label: %r" % label)
            if ch == ":" and not label:
                bad_prog(COLON_LACKS_LABEL)
            # labels = setup_label (labels, vector->v_length, label, NULL);

        elif ch in ("Q", "q", "L", "l"):
            ch = in_nonblank()
            if ISDIGIT(ch):
                cur_cmd.x.int_arg = in_integer(ch)
                debug("int_arg: %r" % in_integer(ch))
            else:
                cur_cmd.x.int_arg = -1
                debug("int_arg: -1")
                savchar(ch)
            read_end_of_cmd()

        elif ch in (
            "=",
            "d",
            "D",
            "F",
            "g",
            "G",
            "h",
            "H",
            "n",
            "N",
            "p",
            "P",
            "z",
            "x",
        ):
            read_end_of_cmd()

        elif ch in ("r", "R", "w", "W"):
            b = read_filename()
            if not b:
                bad_prog(MISSING_FILENAME)
            cur_cmd.x.fname = "".join(b)
            debug("filename: %r" % cur_cmd.x.fname)
            free_buffer(b)

        elif ch == "s":
            slash = inchar()
            b = match_slash(slash, True)
            if b == NULL:
                bad_prog(UNTERM_S_CMD)
            cur_cmd.x.cmd_subst.regx.slash = slash
            cur_cmd.x.cmd_subst.regx.pattern = "".join(b)
            debug("s pattern: %r" % cur_cmd.x.cmd_subst.regx.pattern)

            b2 = match_slash(slash, False)
            if b2 == NULL:
                bad_prog(UNTERM_S_CMD)
            cur_cmd.x.cmd_subst.replacement.text = "".join(b2)
            debug("s replacement: %r" % cur_cmd.x.cmd_subst.replacement.text)

            # setup_replacement(cur_cmd.x.cmd_subst, b2)
            free_buffer(b2)

            flags = "".join(mark_subst_opts(cur_cmd.x.cmd_subst))
            cur_cmd.x.cmd_subst.regx.flags = flags
            debug("s flags: %r" % flags)
            # cur_cmd.x.cmd_subst.regx = compile_regex(
            #     b, flags, cur_cmd.x.cmd_subst.max_id + 1
            # )
            free_buffer(b)

            # if cur_cmd.x.cmd_subst.eval and sandbox:
            #     bad_prog(_(DISALLOWED_CMD))

        elif ch == "y":
            slash = inchar()
            b = match_slash(slash, False)
            if b == NULL:
                bad_prog(UNTERM_Y_CMD)
            cur_cmd.x.cmd_subst.regx.slash = slash
            cur_cmd.x.cmd_subst.regx.pattern = "".join(b)
            debug("y pattern: %r" % cur_cmd.x.cmd_subst.regx.pattern)

            b2 = match_slash(slash, False)
            if b2 == NULL:
                bad_prog(UNTERM_Y_CMD)
            cur_cmd.x.cmd_subst.replacement.text = "".join(b2)
            debug("y replacement: %r" % cur_cmd.x.cmd_subst.replacement.text)

            # sedparse: Since we do not perform the de-escaping of \/, \\ and \\n
            # (see match_slash()), the length check is turned off.
            #
            # if len(normalize_text(b)) != len(normalize_text(b2)):
            #     bad_prog(Y_CMD_LEN)

            read_end_of_cmd()
            free_buffer(b)
            free_buffer(b2)

        elif ch == EOF:
            bad_prog(NO_COMMAND)
            # /*NOTREACHED*/
        else:
            bad_command(ch)
            # /*NOTREACHED*/
    # no return, vector edited in place


# /* `str' is a string (from the command line) that contains a sed command.
#   Compile the command, and add it to the end of `cur_program'. */
def compile_string(cur_program, string):  # pylint: disable=unused-variable
    # global first_script

    # string_expr_count = 0

    # prog and cur_input are global classes

    prog.file = NULL
    prog.base = 0  # first char of the string (will be 1-based)
    prog.cur = prog.base
    prog.end = prog.cur + len(string)
    prog.text = "@" + string  # the leading @ is ignored, it's a 1-based index

    cur_input.line = 1  # sedparse: original was zero
    cur_input.name = NULL
    # string_expr_count += 1
    cur_input.string_expr_count += 1

    compile_program(cur_program)

    # Reseting here breaks check_final_program() error messages (bad_prog())
    # prog.base = NULL
    # prog.cur = NULL
    # prog.end = NULL

    # first_script = False
    # no return, cur_program edited in place


# `cmdfile' is the name of a file containing sed commands.
#   Read them in and add them to the end of `cur_program'.
#
def compile_file(cur_program, cmdfile):
    # prog and cur_input are global classes
    # global first_script

    prog.file = sys.stdin
    if cmdfile[0] != "-":  # or cmdfile[1] != "\0":
        prog.file = open(cmdfile, "r")

    cur_input.line = 1
    cur_input.name = cmdfile
    cur_input.string_expr_count = 0

    compile_program(cur_program)

    if prog.file != sys.stdin:
        prog.file.close()
    # Reseting here breaks check_final_program() error messages (bad_prog())
    # prog.file = NULL

    # first_script = False
    # no return, cur_program edited in place


# Make any checks which require the whole program to have been read.
#   In particular: this backpatches the jump targets.
#   Any cleanup which can be done after these checks is done here also.
def check_final_program():  # program):  # pylint: disable=unused-variable
    global pending_text

    # do all "{"s have a corresponding "}"?
    if blocks:
        bad_prog(EXCESS_OPEN_BRACE)

    # was the final command an unterminated a/c/i command?
    if pending_text:
        debug("pending_text: %r" % pending_text)
        old_text_buf.text = pending_text
        free_buffer(pending_text)
        pending_text = NULL


######################################## end of translations

# From now on it's all sedparse exclusive code

PARSER_DEBUG = False


def debug(msg, stats=False):
    if PARSER_DEBUG:
        if stats:
            print(
                "exp=%s line=%s cur=%s end=%s text=%r ch=%r"
                % (
                    cur_input.string_expr_count,
                    cur_input.line,
                    prog.cur,
                    prog.end,
                    prog.text,
                    msg,
                ),
                file=sys.stderr,
            )
        else:
            print(msg, file=sys.stderr)


def to_json(obj, remove_empty=True):
    return json.dumps(obj, default=lambda x: x.to_dict(remove_empty), **JSON_OPTS)


def print_program(compiled_program):  # pylint: disable=unused-variable
    indent_level = 0
    indent_prefix = " " * 4
    for x in compiled_program:
        if x.cmd == "}":
            indent_level -= 1

        if x.cmd == "\n":
            print()
        else:
            print("%s%s" % ((indent_prefix * indent_level), x))

        if x.cmd == "{":
            indent_level += 1


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Parse a sed script file and dump the results as JSON in STDOUT."
    )
    argparser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    argparser.add_argument(
        "--full", action="store_true", help="show full JSON (has empty values)"
    )
    argparser.add_argument("sed_file", nargs="?", default="-")
    args = argparser.parse_args()

    PARSER_DEBUG = args.verbose

    debug("Will parse file: %s" % args.sed_file)
    the_program = []
    try:
        compile_file(the_program, args.sed_file)
    except ParseError as err:
        print(err.message, file=sys.stderr)
        sys.exit(err.exitcode)
    print(to_json(the_program, not args.full))
    sys.exit(EXIT_SUCCESS)

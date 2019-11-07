# sedparse command line tests

Just run `clitest --prefix 4 tests/test_cmdline.md` to test this file.

Note that tests for combining `-e` and `-f` in the same command are made in `test_misc.py`.

## Help message

    $ python sedparse.py -h | sed 1q
    usage: sedparse.py [-h] [-e script] [-f script-file] [--full] [-v]
    $

## No sed script informed

    $ python sedparse.py
    sedparse: No sed script to be parsed. Use -e and/or -f.
    $ python sedparse.py --full --verbose
    sedparse: No sed script to be parsed. Use -e and/or -f.
    $

## Error message when using an expression

    $ python sedparse.py -e k
    sedparse: -e expression #1, char 1: unknown command: `k'
    $

## Error message when using a file

    $ echo k > k.sed
    $ echo k | python sedparse.py -f k.sed
    sedparse: file k.sed line 1: unknown command: `k'
    $ rm k.sed

## Error message when using STDIN

    $ echo k | python sedparse.py -f -
    sedparse: file - line 1: unknown command: `k'
    $

## Runtime errors are sent to STDERR and return 1

    $ python sedparse.py >/dev/null; echo $?
    sedparse: No sed script to be parsed. Use -e and/or -f.
    1
    $

Parse errors are already well tested in `test_errors.py`.

## Normal execution should print to STDOUT and return zero

    $ python sedparse.py -e x 2>/dev/null; echo $?
    [
        {
            "cmd": "x",
            "line": 1
        }
    ]
    0
    $

## Empty sed script

    $ python sedparse.py -e ''
    []
    $ touch empty.sed
    $ python sedparse.py -f empty.sed
    []
    $ cat empty.sed | python sedparse.py -f -
    []
    $ rm empty.sed
    $

## Both -e and --expression should work

    $ python sedparse.py -e x
    [
        {
            "cmd": "x",
            "line": 1
        }
    ]
    $ python sedparse.py --expression x
    [
        {
            "cmd": "x",
            "line": 1
        }
    ]
    $

## Both -f and --file should work

    $ echo x > x.sed
    $ python sedparse.py -f x.sed
    [
        {
            "cmd": "x",
            "line": 1
        }
    ]
    $ python sedparse.py --file x.sed
    [
        {
            "cmd": "x",
            "line": 1
        }
    ]
    $ rm x.sed
    $

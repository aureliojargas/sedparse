# sedparse

This is a work in progress, not yet officially released.

I'm still force pushing and doing wild west cowboy dev.

For now, I do not recommend investing any time on it.

----

- Author: Aurelio Jargas
- Requires: Python 3.4
- License: GPLv3

A translation from C to Python of GNU sed's parser for sed scripts.

After running sedparse in your sed script, the resulting "[AST](https://en.wikipedia.org/wiki/Abstract_syntax_tree)" is available in different formats:

- List of objects (translated C structs)
- List of dictionaries
- JSON

> Note that this is not a full GNU sed implementation.
> Only the parser for sed scripts was translated.
> Check https://github.com/GillesArcas/PythonSed for a working sed in Python.


## About the translation

To make it feasable to keep this code updated with future GNU sed code, this is a literal translation, trying to mimic as much as possible of the original code. That includes using the same API, same logic, same variable and method names and same data structures. Pythonic code? Sorry, not here.

Sedparse was translated from this GNU sed version:

    commit a9cb52bcf39f0ee307301ac73c11acb24372b9d8
    Author: Assaf Gordon <assafgordon@gmail.com>
    Date:   Sun Jun 2 01:14:00 2019 -0600

http://git.savannah.gnu.org/cgit/sed.git/commit/?id=a9cb52bcf39f0ee307301ac73c11acb24372b9d8


## Sedparse extensions to the original parser

- Preserves comments
- Preserves blank lines between commands
- Preserves original flags for the `s` command
- Preserves original flags for regex addresses


## Usage from the command line

```console
$ python sedparse.py script.sed > script.json
$
```

Given the following `script.sed` file:

```sed
7,/foo/ {
  $!N
  s/\n/-/gi
}

# Comments and blank lines are preserved
```

This is the generated JSON:

```json
[
    {
        "a1": {
            "addr_number": 7,
            "addr_type": 3
        },
        "a2": {
            "addr_number": 0,
            "addr_regex": {
                "pattern": "foo",
                "slash": "/"
            },
            "addr_type": 2
        },
        "cmd": "{",
        "line": 1
    },
    {
        "a1": {
            "addr_number": 0,
            "addr_type": 7
        },
        "addr_bang": true,
        "cmd": "N",
        "line": 2
    },
    {
        "cmd": "s",
        "line": 3,
        "x": {
            "cmd_subst": {
                "regx": {
                    "flags": "gi",
                    "pattern": "\\n",
                    "slash": "/"
                },
                "replacement": {
                    "text": "-"
                }
            }
        }
    },
    {
        "cmd": "}",
        "line": 4
    },
    {
        "cmd": "\n",
        "line": 5
    },
    {
        "cmd": "#",
        "line": 6,
        "x": {
            "comment": " Comments and blank lines are preserved"
        }
    }
]
```


## Usage as a Python module

```python
>>> import pprint
>>> import sedparse
>>> sedscript = r'7,/foo/{$!N;s/\n/-/gi;}'
>>>
>>> # Use compile_string() to parse a string as a sed script.
>>> # The result is a list of sed commands.
>>>
>>> parsed = []
>>> sedparse.compile_string(parsed, sedscript)
>>>
>>> pprint.pprint(parsed)  # doctest:+ELLIPSIS
[struct_sed_cmd(line=1, cmd='{', ...),
 struct_sed_cmd(line=1, cmd='N', ...),
 struct_sed_cmd(line=1, cmd='s', ...),
 struct_sed_cmd(line=1, cmd='}', ...)]
>>>
>>> # Use .to_dict() to convert each command to a Python dict.
>>>
>>> pprint.pprint(parsed[0].to_dict())
{'a1': {'addr_number': 7, 'addr_type': 3},
 'a2': {'addr_number': 0,
        'addr_regex': {'pattern': 'foo', 'slash': '/'},
        'addr_type': 2},
 'cmd': '{',
 'line': 1}
>>>
>>> # Use .to_json() to convert each command to JSON.
>>>
>>> print(parsed[0].to_json())
{
    "a1": {
        "addr_number": 7,
        "addr_type": 3
    },
    "a2": {
        "addr_number": 0,
        "addr_regex": {
            "pattern": "foo",
            "slash": "/"
        },
        "addr_type": 2
    },
    "cmd": "{",
    "line": 1
}
>>>
>>> # Or use the global sedparse.to_json() to convert
>>> # the whole parsed script to JSON.
>>>
>>> print(sedparse.to_json(parsed))  # doctest:+ELLIPSIS
[
    {
        "a1": {...
>>>
>>> # You can print the commands.
>>>
>>> [str(x) for x in parsed]
['7,/foo/ {', '$ !N', 's/\\n/-/gi', '}']
>>>
>>> # You can inspect the parsed sed commands.
>>>
>>> [x.cmd for x in parsed]
['{', 'N', 's', '}']
>>>
>>> # The first command has two addresses.
>>>
>>> str(parsed[0])
'7,/foo/ {'
>>> str(parsed[0].a1)
'7'
>>> str(parsed[0].a2)
'/foo/'
>>> repr(parsed[0].a1)
'struct_addr(addr_type=3, addr_number=7, addr_step=0, addr_regex=None)'
>>> repr(parsed[0].a2)
"struct_addr(addr_type=2, addr_number=0, addr_step=0, addr_regex=struct_regex(slash='/', pattern='foo', flags=''))"
>>>
>>> # The second command has only one (negated) address.
>>>
>>> str(parsed[1])
'$ !N'
>>> str(parsed[1].a1)
'$'
>>> parsed[1].a2 is None  # no second address
True
>>> parsed[1].addr_bang  # has !
True
>>> parsed[1].cmd
'N'
>>>
>>> # The third command is s/// and has no address.
>>>
>>> str(parsed[2])
's/\\n/-/gi'
>>> parsed[2].a1 is None  # no addresses
True
>>> parsed[2].cmd
's'
>>> parsed[2].x.cmd_subst.regx.slash
'/'
>>> parsed[2].x.cmd_subst.regx.pattern
'\\n'
>>> parsed[2].x.cmd_subst.replacement.text
'-'
>>> parsed[2].x.cmd_subst.regx.flags
'gi'
>>>
```

As you can see, the information is split in lots of different places. Here are some of the most important ones:

```python
>>> dir(parsed[0])  # doctest:+ELLIPSIS
[..., 'a1', 'a2', 'addr_bang', 'cmd', 'line',... 'x']
>>>
>>> dir(parsed[0].a1)  # doctest:+ELLIPSIS
[..., 'addr_number', 'addr_regex', 'addr_step', 'addr_type'...]
>>>
>>> dir(parsed[0].x)  # doctest:+ELLIPSIS
[..., 'cmd_subst', 'cmd_txt', 'comment', 'fname', 'int_arg', 'label_name'...]
>>>
>>> dir(parsed[0].x.cmd_subst)  # doctest:+ELLIPSIS
[..., 'outf', 'regx', 'replacement'...]
>>>
```

## Development environment

To create (and update in the future):

    python3 -m venv env
    source env/bin/activate
    pip install -r requirements-dev.txt

To use it while developing:

    source env/bin/activate

To leave it when done developing:

    deactivate

More info at https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/


## Code formatting

In the CI, [black](https://github.com/psf/black) formatting is enforced. To run it locally:

    black sedparse.py tests/test_sedparse.py

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

For a complete reference on how the different sed commands are mapped by the parser, see [tests/reference.sed](tests/reference.sed) and [tests/reference.json](tests/reference.json).


## About the translation

I copied the original code in C and translated everything to Python.

To make it feasible to keep this code updated with future GNU sed code, this is a literal translation, trying to mimic as much as possible of the original code. That includes using the same API, same logic, same variable and method names and same data structures. Pythonic code? Sorry, not here.

Sedparse was translated from this GNU sed version:

http://git.savannah.gnu.org/cgit/sed.git/commit/?id=a9cb52bcf39f0ee307301ac73c11acb24372b9d8

    commit a9cb52bcf39f0ee307301ac73c11acb24372b9d8
    Author: Assaf Gordon <assafgordon@gmail.com>
    Date:   Sun Jun 2 01:14:00 2019 -0600

> Note that this is not a full GNU sed implementation.
> Only the parser for sed scripts was translated.
> Check https://github.com/GillesArcas/PythonSed for a working sed in Python.


## Sedparse extensions to the original parser

- Preserves comments
- Preserves blank lines between commands
- Preserves original flags for the `s` command
- Preserves original flags for regex addresses


## Usage from the command line

You can inform the sed script as a file argument:

```console
$ python sedparse.py script.sed
```

or as text coming from STDIN:

```console
$ echo 's/foo/bar/g' | python sedparse.py
```

The sed script will be parsed and checked for syntax errors. If everything is fine, a JSON representation of the script is sent to STDOUT.

Given the following `script.sed` file:

```sed
11,/foo/ {
  $!N
  s/\n/-/gi
}

# Comments and blank lines are preserved
```

This is the JSON generated by sedparse:

```json
[
    {
        "a1": {
            "addr_number": 11,
            "addr_type": 3
        },
        "a2": {
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

Use `sedparse.compile_string()` to parse a string as a sed script. You must inform a list that will be appended in-place with the parsed commands.

```python
>>> import sedparse
>>> sedscript = """\
... 11,/foo/ {
...     $!N
...     s/\\n/-/gi
... }
... """
>>> parsed = []
>>> sedparse.compile_string(parsed, sedscript)
>>>
```

Each sed command is represented by a `struct_sed_cmd` instance.

```python
>>> import pprint
>>> pprint.pprint(parsed)  # doctest:+ELLIPSIS
[struct_sed_cmd(line=1, cmd='{', ...),
 struct_sed_cmd(line=2, cmd='N', ...),
 struct_sed_cmd(line=3, cmd='s', ...),
 struct_sed_cmd(line=4, cmd='}', ...)]
>>>
```

You can `str()` each command, or any of its inner structs, to get their "human readable" representation.

```python
>>> [str(x) for x in parsed]
['11,/foo/ {', '$ !N', 's/\\n/-/gi', '}']
>>> str(parsed[0])
'11,/foo/ {'
>>> str(parsed[0].a1)
'11'
>>> str(parsed[0].a2)
'/foo/'
>>>
```

Use `.to_dict()` to convert a command into a Python dictionary.

```python
>>> str(parsed[1])
'$ !N'
>>> pprint.pprint(parsed[1].to_dict())
{'a1': {'addr_type': 7}, 'addr_bang': True, 'cmd': 'N', 'line': 2}
>>>
>>> pprint.pprint(parsed[1].to_dict(remove_empty=False))
{'a1': {'addr_number': 0, 'addr_regex': None, 'addr_step': 0, 'addr_type': 7},
 'a2': None,
 'addr_bang': True,
 'cmd': 'N',
 'line': 2,
 'x': {'cmd_subst': {'outf': {'name': ''},
                     'regx': {'flags': '', 'pattern': '', 'slash': ''},
                     'replacement': {'text': ''}},
       'cmd_txt': {'text': []},
       'comment': '',
       'fname': '',
       'int_arg': -1,
       'label_name': ''}}
>>>
```

Use `.to_json()` to convert a command into JSON.

```python
>>> print(parsed[1].to_json())
{
    "a1": {
        "addr_type": 7
    },
    "addr_bang": true,
    "cmd": "N",
    "line": 2
}
>>>
```

Have fun!

```python
>>> [x.cmd for x in parsed]  # list of commands
['{', 'N', 's', '}']
>>> [str(x) for x in parsed if x.a1 is None]  # commands with no address
['s/\\n/-/gi', '}']
>>> [str(x) for x in parsed if x.addr_bang]  # commands with bang !
['$ !N']
>>> [x.x.comment for x in parsed if x.x.comment]  # extract all comments
[]
>>> [x.x.fname for x in parsed if x.cmd in "rRwW"]  # list of read/write filenames
[]
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

    black sedparse.py tests/*.py

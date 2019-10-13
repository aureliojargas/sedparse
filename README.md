# sedparse

This is a work in progress, not yet officially released.

I'm still force pushing and doing wild west cowboy dev.

For now, I do not recommend investing any time on it.

----

A translation from C to Python of GNU sed's parser for sed scripts.

To make it feasable to keep this code updated with future GNU sed code, this is a literal translation, trying to mimic as much as possible of the original code. That includes using the same API, same logic, same variable
and method names and same data structures. Pythonic code? Sorry, not here.

> Note that this is not a full GNU sed implementation.
> Only the parser for sed scripts was translated.
> Check https://github.com/GillesArcas/PythonSed for a working sed in Python.


## Translated from this GNU sed version

    commit a9cb52bcf39f0ee307301ac73c11acb24372b9d8
    Author: Assaf Gordon <assafgordon@gmail.com>
    Date:   Sun Jun 2 01:14:00 2019 -0600

http://git.savannah.gnu.org/cgit/sed.git/commit/?id=a9cb52bcf39f0ee307301ac73c11acb24372b9d8


## Example / Usage

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
>>> parsed[2].x.cmd_subst.slash
'/'
>>> parsed[2].x.cmd_subst.regx.pattern
'\\n'
>>> parsed[2].x.cmd_subst.replacement.text
'-'
>>> parsed[2].x.cmd_subst.flags
['g', 'i']
>>>
```

As you can see, the information is split in lots of different places. Here are some of the most important ones:

```python
>>> dir(parsed[0])  # doctest:+ELLIPSIS
[..., 'a1', 'a2', 'addr_bang', 'cmd', 'line', 'x']
>>>
>>> dir(parsed[0].a1)  # doctest:+ELLIPSIS
[..., 'addr_number', 'addr_regex', 'addr_step', 'addr_type']
>>>
>>> dir(parsed[0].x)  # doctest:+ELLIPSIS
[..., 'cmd_subst', 'cmd_txt', 'comment', 'fname', 'int_arg', 'label_name']
>>>
>>> dir(parsed[0].x.cmd_subst)  # doctest:+ELLIPSIS
[..., 'flags', 'outf', 'regx', 'replacement', 'slash']
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

# sedparse

This is a work in progress, not yet officially released.

I'm still force pushing and doing wild west cowboy dev.

For now, I do not recommend investing any time on it.


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

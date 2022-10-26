# Contributing to sedparse

Please follow the usual GitHub workflow to contribute to this project:

- Use [GitHub issues](https://github.com/aureliojargas/sedparse/issues) for bug reports and feature requests.

- Use GitHub pull requests to submit code.


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


## Code check and formatting

The sedparse code is checked by pylint and formatted by [black](https://github.com/psf/black), so make sure you run both after every change.

Black is used with the default settings (no command line options) and the pylint configuration file is in the root of this repository.

Just run them over the Python files:

    make pylint
    make black

These commands are also automatically executed in the CI for every new push to the repository.

## Testing

Code is tested by the standard `unittest` and `doctest` Python modules, and full command lines are tested by [clitest](https://github.com/aureliojargas/clitest).

    make test

This command is also automatically executed in the CI for every new push to the repository.


## Packaging

To locally install (and uninstall) the package directly from this repository into the virtual env and test the `sedparse` executable:

    pip install -e .
    pip uninstall sedparse

To install the required software for the packaging:

    pip install -r requirements-pkg.txt

To build and upload the packages:

    python3 setup.py sdist bdist_wheel
    twine upload dist/*

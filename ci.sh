#!/bin/bash

set -euo pipefail

is_python36() {
    python --version 2>&1 | grep '^Python 3\.[6-9]' > /dev/null
}

if is_python36
then
    echo pylint
    pylint sedparse.py tests/*.py

    echo black
    black --check --quiet sedparse.py tests/*.py
else
    echo pylint - SKIPPED
    echo black - SKIPPED
fi

echo doc tests
python -m doctest README.md

echo unit tests
python -m unittest discover -s tests/

echo parse reference file
python sedparse.py tests/reference.sed > tests/reference.json
python sedparse.py --verbose --full tests/reference.sed > tests/reference.full.json 2> tests/reference.verbose
git diff --exit-code tests/reference.*

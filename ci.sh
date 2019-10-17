#!/bin/bash

set -euo pipefail

py() {
    if command -v python3 > /dev/null
    then
        python3 "$@"
    else
        python "$@"
    fi
}

is_python36() {
    py --version | grep '^Python 3.[6-9]' > /dev/null
}

if is_python36
then
    echo pylint
    pylint sedparse.py tests/*.py

    echo black
    black --check --quiet sedparse.py tests/*.py
fi

echo doc tests
py -m doctest README.md

echo unit tests
py -m unittest discover --quiet -s tests/

echo parse sample file
py sedparse.py tests/sample.sed > tests/sample.json
py sedparse.py --verbose --full tests/sample.sed > tests/sample.full.json 2> tests/sample.verbose
git diff --exit-code tests/sample.*
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
    pylint sedparse.py tests/test_*.py

    echo black
    black --check --quiet sedparse.py tests/test_*.py
fi

echo doc tests
py -m doctest README.md

echo unit tests
py tests/test_sedparse.py

echo parse sample file
py sedparse.py --verbose tests/sample.sed > tests/sample.out
git diff --exit-code tests/sample.out

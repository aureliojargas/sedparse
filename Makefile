.PHONY: black clean doctest lint pylint requirements sedparse test \
        test-cmdline test-readme test-reference unit-tests

# Main targets

lint: black pylint

test: doctest unit-tests test-cmdline test-readme test-reference

clean:
	rm -f clitest
	pip uninstall --yes sedparse

# Secondary targets

black: requirements
	black --check --diff --quiet ./*.py tests/*.py

pylint: requirements
	pylint ./*.py tests/*.py

doctest:
	python -m doctest README.md

unit-tests:
	python -m unittest discover -s tests/

test-cmdline: clitest
	bash ./clitest --progress none --prefix 4 tests/test_cmdline.md

test-readme: clitest sedparse
	bash ./clitest --progress none README.md

test-reference:
	python sedparse.py -f tests/reference.sed > tests/reference.json
	python sedparse.py --verbose --full -f tests/reference.sed > tests/reference.full.json 2> tests/reference.verbose
	git diff --exit-code tests/reference.*

# Dependencies

clitest:
	curl --location --remote-name --silent \
	https://raw.githubusercontent.com/aureliojargas/clitest/master/clitest

sedparse:
	command -v sedparse || pip install --user --editable .

requirements:
	{ command -v black && command -v pylint; } || \
	pip install --user --requirement requirements-dev.txt

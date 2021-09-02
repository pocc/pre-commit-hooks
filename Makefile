# Simple makefile to do simple tasks
.PHONY: all test test_fresh_installs install upload

clean:
	rm -rf dist *.egg-info

test:
	pip install . && pytest -x -vvv

# Test with fresh installs of downloaded utilities
test_fresh_installs:
	./tests/run_tests.sh

install:
	pip3 install . --user

upload: clean
	python3 setup.py sdist
	twine upload dist/* --verbose

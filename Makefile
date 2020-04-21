# Simple makefile to do simple tasks

clean:
	rm -rf dist *.egg-info

test:
	./tests/run_tests.sh

install:
	pip3 install . --user

upload: clean
	python3 setup.py sdist
	twine upload dist/* --verbose

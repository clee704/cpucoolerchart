.PHONY: clean cleanbuild test dist

all: clean test

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '__pycache__' -depth -exec rm -rf {} \;

cleanbuild:
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

test:
	py.test tests

dist:
	python setup.py sdist

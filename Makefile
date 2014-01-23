.PHONY: clean test

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '__pycache__' -depth -exec rm -rf {} \;

test:
	py.test tests

.PHONY: init updatedata server clean lint

init:
	pip install -r requirements.txt

update:
	python manage.py update

server:
	python manage.py runserver -t 0.0.0.0

clean:
	rm -rf cpucoolerchart/static/compiled
	rm -rf cpucoolerchart/static/.webassets-cache
	find . -type f -name *.pyc -exec rm {} \;
	find . -type d -name __pycache__ -depth -exec rm -rf {} \;

lint:
	jshint cpucoolerchart/static/js/*.js

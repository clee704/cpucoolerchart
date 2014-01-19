.PHONY: init reset update server clean

init:
	pip install -r requirements.txt

reset:
	python manage.py db reset

update:
	python manage.py update

server:
	python manage.py runserver -t 0.0.0.0

clean:
	find . -type f -name *.pyc -exec rm {} \;
	find . -type d -name __pycache__ -depth -exec rm -rf {} \;

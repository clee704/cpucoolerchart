web: gunicorn cpucoolerchart.app:app -w 3 --access-logfile - --access-logformat '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
shell: python manage.py shell
update: python manage.py update

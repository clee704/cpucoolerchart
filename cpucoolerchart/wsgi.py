from .app import create_app
application = create_app()

# Code that only executed when a web server starts, not
# for workers or management scripts.

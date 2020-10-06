web: pipenv run gunicorn 'service.microservice:start_service()'
release: pipenv run alembic upgrade head
worker: celery worker --app=tasks.celery_app
celery_beat: pipenv run celery -A tasks beat --loglevel=info
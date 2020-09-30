"""celery configuration file"""
# pylint: disable=invalid-name

import os

# use local time
enable_utc = False

## Broker settings.
broker_url = os.environ['REDIS_URL']

# List of modules to import when the Celery worker starts.
imports = ('tasks',)

task_serializer = 'pickle'
accept_content = ['pickle', 'application/x-python-serialize', 'json', 'application/json']

beat_schedule = {
    "scheduler": {
        "task": "tasks.scheduler",
        "schedule": 300.0 # run every 5 minutes
    }
}

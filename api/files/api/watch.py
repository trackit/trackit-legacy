#!/usr/bin/env python
from os import environ
from time import sleep
from sys import exit

def wait_forever():
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass

if not environ.get('DEBUG'):
    wait_forever()
    exit(0)

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import PatternMatchingEventHandler
from os import system

class RestartHandler(PatternMatchingEventHandler):
    patterns = ['*.py']

    def on_any_event(self, event):
        self.reload_gunicorn()
        self.restart_celery()

    def reload_gunicorn(self):
        system('supervisorctl status api | grep RUNNING && '
               'kill -HUP $(supervisorctl pid api) && '
               'kill -HUP $(pgrep gunicorn) && '
               'echo SIGHUPed || '
               'supervisorctl start api')

    def restart_celery(self):
        system('supervisorctl restart worker')
        system('supervisorctl restart scheduler')

observer = Observer()
observer.schedule(RestartHandler(), '.', recursive=True)
observer.start()
wait_forever()
observer.stop()
observer.join()

#!/bin/sh

/usr/local/bin/newrelic-admin run-program gunicorn --threads=4 -b 0.0.0.0:5000 app:wsgi

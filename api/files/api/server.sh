#!/bin/sh

(env | grep -q "^NEWRELIC_LICENSE_KEY=") && (env | grep -q "^NEWRELIC_APP_NAME=")
if [ $? -eq "1" ]; then
	gunicorn --threads=4 -b 0.0.0.0:5000 app:wsgi
else
	/usr/local/bin/newrelic-admin generate-config ${NEWRELIC_LICENSE_KEY} /root/newrelic.ini
	sed -i -re "s.app_name = Python Application.app_name = ${NEWRELIC_APP_NAME}.g" /root/newrelic.ini
        kill -9 1
	/usr/local/bin/newrelic-admin run-program gunicorn --threads=4 -b 0.0.0.0:5000 app:wsgi
fi

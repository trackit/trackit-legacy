from app import app
import requests
from time import time
import json

def add_intercom_user(user):
    if 'INTERCOM_APP_ID' not in app.config:
        return
    requests.post('https://api.intercom.io/users',
                  data=json.dumps({'email': user.email, 'signed_up_at': time()}),
                  headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                  auth=(app.config['INTERCOM_APP_ID'], app.config['INTERCOM_APP_SECRET']))

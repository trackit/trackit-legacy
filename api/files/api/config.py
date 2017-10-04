import datetime
import re
from fractions import Fraction

BUILD_VERSION = '1.0.0'
SQLALCHEMY_DATABASE_PASSWORD = ''
SQLALCHEMY_DATABASE_URI = ''
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_POOL_RECYCLE = 540
SMTP_SERVER = ''
SMTP_USERNAME = ''
SMTP_PASSWORD = ''
SMTP_PORT = ''
SMTP_ADDRESS = ''
ES_HOSTS = ['es1']
ES_AUTH = {}
BROKER_URL = 'redis://redis:6379/0'
REDIS_HOST = 'redis'
REDIS_PORT = '6379'
REDIS_DB = '1'
REDIS_ENABLED = 'false'
USER_TOKEN_LIFETIME = datetime.timedelta(days=60)
DB_SECRET_KEY = 'demosecretkey'
GCLOUD_REGISTRATION_TOKEN_LIFETIME = datetime.timedelta(hours=1)
TOKEN_SECRET = 'JWT Token Secret String'
GOOGLE_SECRET = ''
GOOGLE_CLIENT_ID = ''
GOOGLE_RECAPTCHA_SECRET = ''
GOOGLE_RECAPTCHA_SITE_KEY = ''
HOST_DOMAIN = 'api.trackit.io'
WEB_UI_HOST = 'trackit.io'
OAUTH_URIS = {
    'auth_google_initiate': '/auth/google/initiate',
    'auth_google_callback': '/auth/google/callback',
    'key_registration_google_callback': '/gcloud/identity/callback'
}
GOOGLE_OAUTH = {
    'client_id': '',
    'client_secret': ''
}
AZURE_SUBSCRIPTION_ID = ''
AZURE_AD_USERNAME = ''
AZURE_AD_PASSWORD = ''
CONTACT_USER_EMAIL = ''
NEW_USER_EMAIL = ''
BUG_NOTIFICATION_EMAIL = ''
DEVELOPMENT = 'false'
EMAIL_TEMPLATE_DIR = '/usr/trackit/templates'
CLIENT_BILLING_BUCKET = ''
IMPORT_BILLING_AWS_KEY = ''
IMPORT_BILLING_AWS_SECRET = ''
LOCAL_BILLS_DIR = '/root/api/.csv/'
ACCOUNT_DEFAULT_ENABLED = 'true'
ACCOUNT_DEFAULT_CREDENTIALS = {
    'email': u'admin',
    'password': u'admin',
    'firstname': u'Admin',
    'lastname': u'Admin',
    'admin': True,
}

BILLING_FILE_REGEX = re.compile(
    r'(?:^|/)(?P<basename>(?P<account_id>\d+)'
    r'-aws-billing-detailed-line-items-with-resources-and-tags-'
    r'(?P<date>\d{4}-\d{2})\.csv\.zip)$'
)

import imp
import sys
import os
import json

#TODO: Handle the more complex cases.
options = [
    "BUILD_VERSION",
    "SQLALCHEMY_DATABASE_PASSWORD",
    "SQLALCHEMY_DATABASE_URI",
    "SQLALCHEMY_POOL_RECYCLE",
    "TOKEN_SECRET",
    "DB_SECRET_KEY",
    "SMTP_SERVER",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_PORT",
    "SMTP_ADDRESS",
    "AZURE_SUBSCRIPTION_ID",
    "AZURE_AD_USERNAME",
    "AZURE_AD_PASSWORD",
    "CONTACT_USER_EMAIL",
    "NEW_USER_EMAIL",
    "BUG_NOTIFICATION_EMAIL",
    "ACCOUNT_DEFAULT_ENABLED",
    "ES_HOSTS",
    "ES_AUTH",
    "BROKER_URL",
    "TOKEN_SECRET",
    "GOOGLE_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_OAUTH",
    "GOOGLE_RECAPTCHA_SECRET",
    "GOOGLE_RECAPTCHA_SITE_KEY",
    "HOST_DOMAIN",
    "WEB_UI_HOST",
    "OAUTH_URIS",
    "GOOGLE_OAUTH",
    "DEVELOPMENT",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "REDIS_ENABLED",
    "CLIENT_BILLING_BUCKET",
    "IMPORT_BILLING_AWS_KEY",
    "IMPORT_BILLING_AWS_SECRET",
]

config_module = sys.modules[__name__]
for option in options:
    env_option = ('TRACKIT_%s' % option)
    if env_option in os.environ:
        if isinstance(getattr(config_module, option), str):
            setattr(config_module, option, os.environ[env_option])
        else:
            try:
                setattr(sys.modules[__name__], option, json.loads(os.environ[env_option]))
            except ValueError:
                pass

try:
    config_overrides = imp.load_source('config_overrides', '/etc/trackitio.py')
    for config_name in dir(config_overrides):
        if config_name.upper() == config_name:
            setattr(sys.modules[__name__], config_name, getattr(config_overrides, config_name))
except IOError:
    pass

HOST = "%s" % (HOST_DOMAIN, )
if not SQLALCHEMY_DATABASE_URI:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://root:%s@mysql/trackitio?charset=utf8' % SQLALCHEMY_DATABASE_PASSWORD

if DEVELOPMENT.lower() in ['y', 'yes', '1', 't', 'true', 'on', 'o', 'oui']:
    DEVELOPMENT = True
else:
    DEVELOPMENT = False

if REDIS_ENABLED.lower() in ['y', 'yes', '1', 't', 'true', 'on', 'o', 'oui']:
    REDIS_ENABLED = True
else:
    REDIS_ENABLED = False

if ACCOUNT_DEFAULT_ENABLED.lower() in ['y', 'yes', '1', 't', 'true', 'on', 'o', 'oui']:
    ACCOUNT_DEFAULT_ENABLED = True
else:
    ACCOUNT_DEFAULT_ENABLED = False

for option in options:
    print('{}={}'.format(option, getattr(config_module, option)))

if not len(IMPORT_BILLING_AWS_KEY) or not len(IMPORT_BILLING_AWS_SECRET):
    IMPORT_BILLING_AWS_KEY = None
    IMPORT_BILLING_AWS_SECRET = None

if not len(CLIENT_BILLING_BUCKET):
    CLIENT_BILLING_BUCKET = None

if not len(SMTP_ADDRESS):
    SMTP_ADDRESS = None

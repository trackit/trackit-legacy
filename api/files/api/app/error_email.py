from datetime import datetime
from app.send_email import send_email
from app import app
from functools import partial
from hashlib import md5

## AWS

def get_basic_infos(key):
    message = "User id: {}".format(key.user.id) + '\n'
    message += "User email: {}".format(key.user.email) + '\n'
    message += "Account: {}".format(key.get_aws_user_id()) + '\n'
    message += "Key id: {}".format(key.id) + '\n'
    message += "Key: {}".format(key.key) + '\n'
    message += "Key name: {}".format(key.pretty) + '\n'
    message += "Date: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + '\n'
    return message

def aws_error(subject, key, traceback):
    message = get_basic_infos(key)
    message += traceback
    signature = md5()
    signature.update(traceback)
    subject += ' (%s)' % signature.hexdigest()[0:10]
    send_email(app.config['BUG_NOTIFICATION_EMAIL'], subject, message, False)

aws_credentials_error = partial(aws_error, "Error during AWS credentials validation")

aws_bill_parsing_error_email = partial(aws_error, "Error during AWS bill parsing")

aws_bucket_does_not_exist_error_email = partial(aws_error, "Error the specified bucket does not exist")

aws_access_denied_error_email = partial(aws_error, "Insufficient access rights to perform the processing")

aws_key_processing_generic_error_email = partial(aws_error, "Error during AWS key processing")

aws_my_resources_error_email = partial(aws_error, "Error during AWS my resources processing")

## AZURE

def azure_commerce_userpasscredentials_error_email(traceback):
    send_email(app.config['BUG_NOTIFICATION_EMAIL'], "Error during azure UserPassCredentials instantiation", traceback, False)

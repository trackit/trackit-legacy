from app import error_email
from app.models import db
import botocore
import logging
import traceback

def _client_error_exception(exception, key):
    def _accessdenied_ce_exception():
        error_email.aws_access_denied_error_email(key, traceback.format_exc())
        key.error_status = u"access_denied"
        logging.error("[user={}][key={}] Insufficient access rights".format(key.user.email, key.pretty or key.key))

    def _nosuchbucket_ce_exception():
        error_email.aws_bucket_does_not_exist_error_email(key, traceback.format_exc())
        key.error_status = u"no_such_bucket"
        logging.error("[user={}][key={}] The specified billing bucket does not exists".format(key.user.email, key.pretty or key.key))

    def _default_ce_exception():
        error_email.aws_credentials_error(key, traceback.format_exc())
        key.error_status = u"bad_key"
        logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(exception)))
    
    _code_handler = {
        'AccessDenied': _accessdenied_ce_exception,
        'NoSuchBucket': _nosuchbucket_ce_exception,
    }
    _code_handler.get(exception.response['Error']['Code'], _default_ce_exception)()
    db.session.commit()

def _default_exception(exception, key):
    error_email.aws_key_processing_generic_error_email(key, traceback.format_exc())
    key.error_status = u"processing_error"
    db.session.commit()
    #logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))

EXCEPTION_HANDLERS = {
    botocore.exceptions.ClientError: _client_error_exception,
}

def except_handler(exception, key):
    for e, f in EXCEPTION_HANDLERS.iteritems():
        if isinstance(exception, e):
            return f(exception, key)
    return _default_exception(exception, key)

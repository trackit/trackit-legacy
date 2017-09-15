# -*- coding: utf-8 -*-
from app import app
from models import db, User, UserSessionToken, MultikeyKey, MultikeyGroup
import boto3
import botocore
import datetime
import flask
import functools
import models
import re
import sqlalchemy
import werkzeug

# The `with_boto3_session` decorator will ensure the view is provided with a
# boto3 session (using the `boto3_session` kwarg and the calling user ( which
# MUST be authenticated ) via the `user` kwarg.
#
# The boto3 session is not checked in any way and this decorater will catch
# boto3 `ClientError` exceptions.
def with_boto3_session():
    def wrapper(f):
        @functools.wraps(f)
        def s3_session_checker(*args, **kwargs):
            print('Building query.',)
            query = models.User.query.filter_by(token=get_user_token())
            print('Getting user.',)
            user = query.first()
            print('Got', user)
            if user:
                print('Getting key.',)
                key = user.get_aws_key(get_aws_key())
                print('Got', key)
                if key:
                    print('Getting session.',)
                    session = boto3.Session(aws_access_key_id=key.key,
                                            aws_secret_access_key=key.secret)
                    print('Got', session)
                    try:
                        print('Calling function.')
                        return f(*args, boto3_session=session, user=user, **kwargs)
                    except botocore.exceptions.ClientError as error:
                        return flask.jsonify(error=str(error)), 500
                else:
                    return flask.jsonify(error="AWS Key not registered"), 404
            else:
                return flask.jsonify(error="Wrong token"), 401
        return s3_session_checker
    return wrapper

def with_aws_account():
    def wrapper(f):
        @functools.wraps(f)
        def aws_account_checker(user=None, *args, **kwargs):
            if "account_id" in kwargs:
                token = UserSessionToken.query.filter_by(id=get_user_token()).first()
                request_user = User.query.filter_by(id=token.id_user).first()
                query = models.AWSKey.query.filter_by(id=kwargs["account_id"])
                if user:
                    args += (user,)
                    query = query.filter_by(id_user=user.id)
                account = query.first()
                if (account and account.id_user == request_user.id) or (account and request_user.admin):
                    kwargs['account'] = account
                    return f(*args, **kwargs)
                else:
                    return flask.jsonify(error="AWS account not registered"), 404
            else:
                return flask.jsonify(error="Bad request"), 400
        return aws_account_checker
    return wrapper


class AWSMultipleIdsConverter(werkzeug.routing.BaseConverter):
    def to_python(self, value):
        return set(map(int, re.split('[,.]', value)))
    def to_url(self, value):
        return '.'.join(str(id) for id in value)


app.url_map.converters['aws_key_ids'] = AWSMultipleIdsConverter


def with_multiple_aws_accounts():
    def wrapper(f):
        @functools.wraps(f)
        def aws_multiple_account_checker(user=None, *args, **kwargs):
            if 'account_ids' in kwargs:
                if not user:
                    token = UserSessionToken.query.filter_by(id=get_user_token()).one_or_none()
                    user = User.query.filter_by(id=token.id_user).one_or_none()
                try:
                    accounts_query = kwargs['account_ids']
                except ValueError:
                    return flask.jsonify(error='Bad request.'), 400
                query = models.AWSKey.query.filter(models.AWSKey.id_user == user.id, models.AWSKey.id.in_(accounts_query))
                stored_keys = query.all()
                if len(stored_keys) == len(accounts_query) and all(key.id_user == user.id for key in stored_keys):
                    kwargs['accounts'] = stored_keys
                    del kwargs['account_ids']
                    register_key_group(stored_keys)
                    return f(*args, **kwargs)
                else:
                    return flask.jsonify(error='Insufficient rights.'), 403
            return flask.jsonify(error='Bad request.'), 400
        return aws_multiple_account_checker
    return wrapper

def register_key_group(aws_keys):
    aws_keys = set(aws_keys)
    group_id = MultikeyGroup.id_of(aws_keys)
    group = MultikeyGroup.query.get(group_id)
    if not group:
        group = MultikeyGroup(
            id=group_id,
            expires=datetime.datetime.utcnow() + datetime.timedelta(days=30),
            updates=datetime.datetime.utcnow(),
        )
        db.session.add(group)
        for aws_key in aws_keys:
            print(aws_key)
            print(aws_key.key)
            print(aws_key.billing_bucket_name)
            multikey_key = MultikeyKey(
                key=aws_key.key,
                billing_bucket_name=aws_key.billing_bucket_name,
                multikey_group=group,
            )
            db.session.add(multikey_key)
    else:
        group.expires = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    db.session.commit()

def get_aws_key():
    return flask.request.headers.get('User-AWS-Key')

def get_user_token():
    return flask.request.headers.get('Authorization')

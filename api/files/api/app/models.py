from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import EncryptedType
from sqlalchemy.types import TypeDecorator, LargeBinary
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from os import environ
import boto3
import botocore
import uuid
import os
import base64
import datetime
import config
import struct
from StringIO import StringIO
from gzip import GzipFile
import zlib
import json
import hashlib


secret_key = app.config['DB_SECRET_KEY']

db = SQLAlchemy(app)


class CompressedJSON(TypeDecorator):
    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is None:
            return
        return zlib.compress(json.dumps(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return
        return json.loads(zlib.decompress(value))

class Prospect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Unicode(25))
    email = db.Column(db.Unicode(255))
    name = db.Column(db.Unicode(255))
    phone_number = db.Column(db.Unicode(255), nullable=True)
    company_name = db.Column(db.Unicode(255), nullable=True)
    address = db.Column(db.Unicode(255), nullable=True)
    employees = db.Column(db.Unicode(255), nullable=True)
    annual_revenue = db.Column(db.Integer, nullable=True)
    cloud_concerns = db.relationship('CloudConcern', back_populates='prospect')
    which_cloud = db.relationship('WhichCloud', back_populates='prospect')

    def to_dict(self):
        return {
            'type': self.type,
            'email': self.email,
            'name': self.name,
            'phone_number': self.phone_number,
            'company_name': self.company_name,
            'address': self.address,
            'employees': self.employees,
            'annual_revenue': self.annual_revenue,
            'cloud_concerns': [c.concern for c in self.cloud_concerns],
            'which_cloud': [c.cloud for c in self.which_cloud],
        }

class CloudConcern(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_prospect = db.Column(db.Integer, db.ForeignKey('prospect.id'), nullable=False)
    concern = db.Column(db.Unicode(255), nullable=False)
    prospect = db.relationship('Prospect', back_populates='cloud_concerns')

class WhichCloud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_prospect = db.Column(db.Integer, db.ForeignKey('prospect.id'), nullable=False)
    cloud = db.Column(db.Unicode(255), nullable=False)
    prospect = db.relationship('Prospect', back_populates='which_cloud')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(64), unique=True)
    firstname = db.Column(db.Unicode(32))
    lastname = db.Column(db.Unicode(32))
    password_hash = db.Column(db.String(128))
    admin = db.Column(db.Boolean(), default=False)
    aws_keys = db.relationship("AWSKey", backref="user", lazy="dynamic")
    auth_google = db.Column(db.String(120), nullable=True)
    lost_password = db.Column(db.String(32), nullable=True)
    gcloud_identities = db.relationship('GoogleCloudIdentity', back_populates='user')
    report_last_emailed_at = db.Column(db.DateTime(), nullable=True)

    def password_matches(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, 'pbkdf2:sha256:20000')

    def set_lost_password(self, lost):
        self.lost_password = lost

    def get_aws_key(self, key):
        matches = list(filter(lambda k: k.key == key, self.aws_keys))
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            return None

class UserSessionToken(db.Model):
    id = db.Column(db.String(40), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires = db.Column(db.DateTime(), nullable=True)

    def update_token(self):
        b = struct.pack('!16s8sI', uuid.uuid1().bytes, # 16 byte time-and-MAC-based UUID
                                   os.urandom(8), # 8 byte random
                                   self.id_user) # 4 byte user id
        self.id = base64.urlsafe_b64encode(b) # base64 string should be 40 chars wide

    def partial_token(self):
        return self.id[:24] # Only the UUID and part of the random, byte and base64-aligned

    def has_expired(self):
        return self.expires <= datetime.datetime.utcnow()

    @staticmethod
    def for_user(user):
        token = UserSessionToken(id_user=user.id,
                                 expires=datetime.datetime.utcnow() + config.USER_TOKEN_LIFETIME)
        token.update_token()
        return token

class GoogleCloudIdentity(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    credentials = db.Column(db.String(4095), nullable=False)
    last_validated = db.Column(db.DateTime(), nullable=True)
    last_errored = db.Column(db.DateTime(), nullable=True)
    last_fetched = db.Column(db.DateTime(), nullable=True)
    user = db.relationship('User', back_populates='gcloud_identities')

class GoogleCloudIdentityRegistrationToken(db.Model):
    id = db.Column(db.String(24), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires = db.Column(db.DateTime(), nullable=False)

    def update_token(self):
        self.id = base64.urlsafe_b64encode(os.urandom(18))

    def has_expired(self):
        return self.expires <= datetime.datetime.utcnow()

    @staticmethod
    def for_user(user):
        token = GoogleCloudIdentityRegistrationToken(id_user=user.id,
                                                     expires=datetime.datetime.utcnow() + config.GCLOUD_REGISTRATION_TOKEN_LIFETIME)
        token.update_token()
        return token

class AWSKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Unicode(16), nullable=True)
    key = db.Column(db.Unicode(20), nullable=False)
    secret = db.Column(EncryptedType(db.String, secret_key), nullable=False)
    pretty = db.Column(db.Unicode(63), nullable=True)
    billing_bucket_name = db.Column(db.Unicode(63), nullable=True)
    last_fetched = db.Column(db.DateTime())
    error_status = db.Column(db.Unicode(32), nullable=True)
    import_s3 = db.Column(db.Boolean(), default=False)
    is_valid_key = db.Column(db.Boolean(), server_default='1')
    last_duration = db.Column(db.Integer, nullable=True)
    next_s3_bill_import = db.Column(db.DateTime(), nullable=True)

    def get_boto_session(self):
        return boto3.Session(
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
        )

    def get_aws_user_id(self):
        try:
            if not self.account_id:
                sts = self.get_boto_session().client('sts')
                self.account_id = sts.get_caller_identity()['Account']
                self.is_valid_key = True
                db.session.commit()
        except botocore.exceptions.ClientError, e:
            if e.response['Error']['Code'] == 'InvalidClientTokenId':
                self.is_valid_key = False
                db.session.commit()
            else
                raise
        return self.account_id


class AWSPricing(db.Model):
    offer = db.Column(db.Unicode(63), nullable=False, primary_key=True)
    version = db.Column(db.Unicode(63), nullable=False, primary_key=True)
    etag = db.Column(db.String(63))
    value = db.Column(db.BLOB(16 * 1000 * 1000), nullable=False)

    def json(self):
        data = StringIO(self.value)
        try:
            return json.load(GzipFile(fileobj=data))
        except IOError:
            data.seek(0)
            return json.load(data)

    def set_json(self, j):
        data = StringIO()
        with GzipFile(fileobj=data, mode='w') as f:
            json.dump(j, f)
        data.seek(0)
        self.value = data.read()

class MyResourcesAWS(db.Model):
    __tablename__ = 'aws_my_resources'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Unicode(20), nullable=False)
    value = db.Column(db.BLOB(16 * 1000 * 1000), nullable=False)
    date = db.Column(db.DateTime())

    def json(self):
        data = StringIO(self.value)
        try:
            return json.load(GzipFile(fileobj=data))
        except IOError:
            data.seek(0)
            return json.load(data)

    def set_json(self, j):
        data = StringIO()
        with GzipFile(fileobj=data, mode='w') as f:
            json.dump(j, f)
        data.seek(0)
        self.value = data.read()

class ProvidersComparisonGoogle(db.Model):
    __tablename__ = 'providers_comparison_google'
    id = db.Column(db.Integer, primary_key=True)
    id_identity = db.Column(db.Integer, db.ForeignKey('google_cloud_identity.id'), nullable=False)
    identity = db.relationship('GoogleCloudIdentity', backref=db.backref('providers_comparison_googles', cascade='all,delete'))
    value = db.Column(db.BLOB(16 * 1000 * 1000), nullable=False)
    date = db.Column(db.DateTime())

    def json(self):
        data = StringIO(self.value)
        try:
            return json.load(GzipFile(fileobj=data))
        except IOError:
            data.seek(0)
            return json.load(data)

    def set_json(self, j):
        data = StringIO()
        with GzipFile(fileobj=data, mode='w') as f:
            json.dump(j, f)
        data.seek(0)
        self.value = data.read()

class AWSCostByResource(db.Model):
    __tablename__ = 'aws_cost_by_resource'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Unicode(20), nullable=False)
    value = db.Column(db.BLOB(16 * 1000 * 1000), nullable=False)
    date = db.Column(db.DateTime())

    def json(self):
        data = StringIO(self.value)
        try:
            return json.load(GzipFile(fileobj=data))
        except IOError:
            data.seek(0)
            return json.load(data)

    def set_json(self, j):
        data = StringIO()
        with GzipFile(fileobj=data, mode='w') as f:
            json.dump(j, f)
        data.seek(0)
        self.value = data.read()

class MyDBResourcesAWS(db.Model):
    __tablename__ = 'aws_my_db_resources'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Unicode(20), nullable=False)
    value = db.Column(db.BLOB(16 * 1000 * 1000), nullable=False)
    date = db.Column(db.DateTime())

    def json(self):
        data = StringIO(self.value)
        try:
            return json.load(GzipFile(fileobj=data))
        except IOError:
            data.seek(0)
            return json.load(data)

    def set_json(self, j):
        data = StringIO()
        with GzipFile(fileobj=data, mode='w') as f:
            json.dump(j, f)
        data.seek(0)
        self.value = data.read()

class AzurePricing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer = db.Column(db.Unicode(63), nullable=False, primary_key=True)
    date = db.Column(db.DateTime())
    region = db.Column(db.String(32))
    value = db.Column(db.BLOB(16 * 1000 * 1000), nullable=False)

    def json(self):
        data = StringIO(self.value)
        try:
            return json.load(GzipFile(fileobj=data))
        except IOError:
            data.seek(0)
            return json.load(data)

    def set_json(self, j):
        data = StringIO()
        with GzipFile(fileobj=data, mode='w') as f:
            json.dump(j, f)
        data.seek(0)
        self.value = data.read()

class AWSKeyS3Bucket(db.Model):
    id_aws_key = db.Column(db.Integer, db.ForeignKey('aws_key.id'), nullable=False, primary_key=True)
    bucket = db.Column(db.Unicode(63), primary_key=True)

class TaskStatus(db.Model):
    task_name = db.Column(db.Unicode(128), primary_key=True)
    argument_signature = db.Column(db.String(128), primary_key=True)
    error = db.Column(db.Unicode(1024))
    start_time = db.Column(db.DateTime())
    completion_time = db.Column(db.DateTime())

    def set_task_name(self, task_name):
        self.task_name = _get_fn_name(task_name)

    def set_argument_signature(self, args):
        self.argument_signature = _get_arg_signature(args)

    @classmethod
    def find_by_args(cls, task_name, args):
        return cls.query.get((_get_fn_name(task_name),
                              _get_arg_signature(args)))

class MultikeyGroup(db.Model):
    id = db.Column(db.String(40), primary_key=True)
    expires = db.Column(db.DateTime(), nullable=False)
    updates = db.Column(db.DateTime(), nullable=False)
    multikey_keys = db.relationship('MultikeyKey', back_populates='multikey_group')

    @classmethod
    def id_of(cl, keys):
        sha = hashlib.sha1()
        for key in sorted(keys, key=(lambda k: '{}{}'.format(k.key, k.billing_bucket_name or ''))):
            sha.update(key.key)
            sha.update(key.billing_bucket_name or '')
        return sha.hexdigest()

class MultikeyKey(db.Model):
    __tablename__ = "multikey_key"
    id = db.Column(db.Integer, primary_key=True)
    id_multikey_group = db.Column(db.String(40), db.ForeignKey('multikey_group.id'), nullable=False)
    multikey_group = db.relationship('MultikeyGroup', back_populates='multikey_keys')
    key = db.Column(db.String(20), nullable=False)
    billing_bucket_name = db.Column(db.String(64))

    def aws_key(self):
        return AWSKey.query.filter(
            AWSKey.key == self.key,
            AWSKey.billing_bucket_name == self.billing_bucket_name,
        ).first()

def _get_arg_signature(args):
    sha = hashlib.sha512()
    sha.update(str(json.dumps(args)))
    return sha.hexdigest()

def _get_fn_name(task_name):
    if not isinstance(task_name, basestring):
        return task_name.__name__
    return task_name

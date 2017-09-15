from marshmallow import Schema, fields
from flask import url_for
import functools
import json

AWS_KEY_PROCESSING_INTERVAL_HOURS = 6
AWS_RESOURCES_INTERVAL_HOURS = 12


class AWSKeySchema(Schema):
    class Meta:
        load_only = ('secret',)
    id = fields.Integer(required=False)
    links = fields.Method('get_api_links')
    key = fields.Str(required=True)
    secret = fields.Str(required=True)
    pretty = fields.Str(required=False, allow_none=True)
    billing_bucket_name = fields.Str(required=False, allow_none=True)
    is_valid_key = fields.Method('get_is_valid_key', dump_only=True)
    error_status = fields.Str(dump_only=True)

    @staticmethod
    def get_api_links(obj):
        endpoints = {'self': 'get_aws_account'}
        for name in endpoints:
            endpoints[name] = url_for(endpoints[name], _external=True, account_id=obj.id)
        return endpoints

    @staticmethod
    def get_is_valid_key(obj):
        if obj.is_valid_key is None:
            return True
        return obj.is_valid_key


class AWSKeySelectorSchema(Schema):
    key = fields.Str(required=False)
    secret = fields.Str(required=False)


class AWSKeyEditSchema(Schema):
    class Meta:
        load_only = ('secret',)
    key = fields.Str(required=False)
    secret = fields.Str(required=False)
    pretty = fields.Str(required=False)
    billing_bucket_name = fields.Str(required=False)

aws_key_schema = AWSKeySchema()
aws_key_selector_schema = AWSKeySelectorSchema()
aws_key_edit_schema = AWSKeyEditSchema()

json_response = functools.partial(json.dumps, separators=(',', ':'))

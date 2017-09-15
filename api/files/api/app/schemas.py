from marshmallow import Schema, fields
from flask import request, jsonify
from functools import wraps

class GoogleCloudIdentitySchema(Schema):
    id = fields.Integer(required=True)
    id_user = fields.Integer(required=True)
    email = fields.Email(required=True)

class GoogleCloudProjectSchema(Schema):
    id = fields.Integer(required=True)
    id_identity = fields.Integer(required=True)
    code = fields.Str(required=True)
    name = fields.Str(required=True)
    number = fields.Integer(required=True)

class GoogleCloudBillingBucketSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.Str(required=True)

class GoogleCloudBillingBucketSelectorSchema(Schema):
    name = fields.Str(required=True)

class GoogleCloudBillingMeasurementSchema(Schema):
    measurementId = fields.Str(required=True)
    sum = fields.Decimal(required=True)
    unit = fields.Str(required=True)

class GoogleCloudBillingCostSchema(Schema):
    amount = fields.Decimal(required=True)
    currency = fields.Str(required=True)

class GoogleCloudBillingRecordSchema(Schema):
    lineItemId = fields.Str(required=True)
    startTime = fields.DateTime(required=True)
    endTime = fields.DateTime(required=True)
    projectNumber = fields.Integer(required=True)
    measurements = fields.Nested(GoogleCloudBillingMeasurementSchema, many=True, required=True)
    cost = fields.Nested(GoogleCloudBillingCostSchema, many=False, required=True)

google_cloud_billing_record_schema = GoogleCloudBillingRecordSchema()
google_cloud_identity_schema = GoogleCloudIdentitySchema()
google_cloud_project_schema = GoogleCloudProjectSchema()
google_cloud_billing_bucket_schema = GoogleCloudBillingBucketSchema()
google_cloud_billing_bucket_selector_schema = GoogleCloudBillingBucketSelectorSchema()

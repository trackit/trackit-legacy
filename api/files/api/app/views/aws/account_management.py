from datetime import datetime
from app import app
from app.authentication import with_login
from flask import Blueprint, jsonify
from app.request_schema import with_request_schema
from app.models import db, AWSKey, AWSKeyS3Bucket
from app.es.awsdetailedlineitem import AWSDetailedLineitem
from app.aws_keys import with_aws_account, with_multiple_aws_accounts
from app.aws.utils import check_if_valid_key
from . import aws_key_schema, aws_key_edit_schema
from app.generate_csv import get_csv_links
import calendar

aws_account_management_bp = Blueprint('aws_account_management_bp', __name__)


@app.route('/aws/accounts', methods=['POST'])
@with_request_schema(aws_key_schema)
@with_login(True)
def post_aws_account(data, user):
    """---
    post:
        tags:
            - aws
        description: &desc Create AWS account
        summary: *desc
        produces:
            - application/json
        consumes:
            - application/json
        parameters:
            - in: body
              name: body
              schema:
                $ref: "#/definitions/AWSAccount"
        responses:
            200:
                description: Registered account
                schema:
                    $ref: "#/definitions/AWSAccount"
            403:
                description: Not logged in
            409:
                description: AWS account already registered for user
    """
    if user:
        if AWSKey.query.filter_by(id_user=user.id, key=data['key']).count():
            return jsonify(error="Already registered"), 409
        else:
            key = AWSKey()
            key.id_user = user.id
            for data_key, data_value in data.iteritems():
                setattr(key, data_key, data_value)
            key.is_valid_key = check_if_valid_key(key.key, key.secret)
            db.session.add(key)
            db.session.commit()
            return jsonify(aws_key_schema.dump(key)[0]), 200
    else:
        return jsonify(error="Forbidden"), 403


@app.route('/aws/accounts/<int:account_id>', methods=['PUT'])
@with_request_schema(aws_key_edit_schema)
@with_login(True)
def put_aws_account(data, user, account_id):
    """---
    post:
        tags:
            - aws
        description: &desc Modify an AWS account.
        summary: *desc
        produces:
            - application/json
        consumes:
            - application/json
        parameters:
            - in: body
              name: body
              schema:
                  $ref: "#/definitions/AWSAccount"
        responses:
            200:
                description: Registered account
                schema:
                    $ref: "#/definitions/AWSAccount"
            403:
                description: Not logged in
    """
    assert user
    key = AWSKey.query.get(account_id)
    if key and key.id_user == user.id:
        for k, v in data.iteritems():
            setattr(key, k, v)
        key.is_valid_key = check_if_valid_key(key.key, key.secret)
        db.session.commit()
        db.session.refresh(key)
        return jsonify(aws_key_schema.dump(key)[0]), 200
    elif key:
        return jsonify(error='Forbidden.'), 403
    else:
        return jsonify(error='Not found.'), 404


@app.route('/aws/accounts', methods=['GET'])
@with_login(True)
def get_aws_accounts(user):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get AWS accounts
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        accounts:
                            type: array
                            items:
                                $ref: "#/definitions/AWSAccount"
            403:
                description: Not logged in
    """
    if user:
        now = datetime.utcnow()
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = now.replace(day=calendar.monthrange(date_from.year, date_from.month)[1], hour=23, minute=59,
                              second=59, microsecond=999999)
        if user.admin:
            res = []
            keys = AWSKey.query.all()
            for key in keys:
                user_id = key.get_aws_user_id()
                key_infos = aws_key_schema.dump(key)[0]
                full = False if not user_id else AWSDetailedLineitem.keys_has_data(key.get_aws_user_id())
                month = False if not full else AWSDetailedLineitem.keys_has_data(key.get_aws_user_id(), date_from=date_from, date_to=date_to)
                key_infos['has_data_full'] = full
                key_infos['has_data_month'] = month
                if key.id_user != user.id:
                    if not key_infos['pretty']:
                        key_infos['pretty'] = key.user.email
                    else:
                        key_infos['pretty'] = key_infos['pretty'] + ' (' + key.user.email + ')'
                res.append(key_infos)
            return jsonify(accounts=res), 200
        keys = []
        for key in user.aws_keys:
            user_id = key.get_aws_user_id()
            key_infos = aws_key_schema.dump(key)[0]
            full = False if not user_id else AWSDetailedLineitem.keys_has_data(key.get_aws_user_id())
            month = False if not full else AWSDetailedLineitem.keys_has_data(key.get_aws_user_id(), date_from=date_from, date_to=date_to)
            key_infos['has_data_full'] = full
            key_infos['has_data_month'] = month
            keys.append(key_infos)

        return jsonify(accounts=keys), 200
    else:
        return jsonify(error="Forbidden"), 403


@app.route('/aws/accounts/m/<aws_key_ids:account_ids>', methods=['GET'])
@with_login(True)
@with_multiple_aws_accounts()
def aws_test_accounts_test(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description &desc Get multiple AWS accounts.
        summary: *desc
        responses:
            200:
                description: AWS accounts.
                schema:
                    - $ref: "#/definitions/AWSAccount"
            403:
                description: Forbidden.
    """
    return jsonify({
        'accounts': [
            aws_key_schema.dump(a)[0] for a in accounts
        ]
    })


@app.route('/aws/accounts/<int:account_id>', methods=['GET'])
@with_login(True)
@with_aws_account()
def get_aws_account(user, account, account_id):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get AWS account
        summary: *desc
        responses:
            200:
                description: AWS account
                schema:
                    $ref: "#/definitions/AWSAccount"
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    if user:
        return jsonify(aws_key_schema.dump(account)[0]), 200
    else:
        return jsonify(error="Forbidden"), 403


@app.route('/aws/accounts/<int:account_id>', methods=['DELETE'])
@with_login(True)
@with_aws_account()
def delete_aws_account(user, account, account_id):
    """---
    delete:
        tags:
            - aws
        description: &desc Delete AWS account
        summary: *desc
        responses:
            200:
                description: AWS account removed
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    if user and account.id_user == user.id:
        buckets = AWSKeyS3Bucket.query.filter_by(id_aws_key=account_id)
        for bucket in buckets:
            db.session.delete(bucket)
        db.session.delete(account)
        db.session.commit()
        return jsonify({}), 200
    else:
        return jsonify(error="Forbidden"), 403


@app.route('/aws/accounts/<aws_key_ids:account_ids>/csv/export')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_csv_export(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get links where CSV Export is available
        summary: *desc
        responses:
            200:
                description: List links for CSV Export
                schema:
                    properties:
                        csvs:
                            type: array
                            items:
                                properties:
                                    name:
                                        type: string
                                    description:
                                        type: string
                                    link:
                                        type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    return jsonify(csvs=get_csv_links())

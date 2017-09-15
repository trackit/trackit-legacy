from datetime import datetime
from app import app, s3pricing, ec2pricing, tasks
from app.authentication import with_login
from flask import Blueprint, jsonify, request
from app.msol_util import get_next_update_estimation_message_aws
from app.es.awsdetailedlineitem import AWSDetailedLineitem
from app.es.elbpricing import ELBPricing
from app.aws_keys import with_multiple_aws_accounts
from dateutil.relativedelta import relativedelta
from app.s3pricing import estimate_s3_cost
from .. import AWS_KEY_PROCESSING_INTERVAL_HOURS

aws_cost_cost_bp = Blueprint('aws_cost_cost_bp', __name__)


@app.route('/aws/s3pricing')
def aws_s3_pricing():
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get S3 pricing per gibabyte in all regions and storage types
        summary: *desc
        responses:
            200:
                description: List of prices
                schema:
                    properties:
                        prices:
                            type: array
                            items:
                                properties:
                                    cost:
                                        type: number
                                    availability:
                                        type: string
                                    durability:
                                        type: string
                                    location:
                                        type: string
                                    storageClass:
                                        type: string
                                    volumeType:
                                        type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    try:
        stored = float(request.args.get('gigabytes', request.args.get('stored')))
    except:
        return jsonify(error='Required query param `stored` of type float'), 400
    try:
        retrieved = float(request.args.get('retrieved', '0.0'))
    except:
        return jsonify(error='Query param `retrieved` of type float'), 400
    prices = s3pricing.costs(stored, retrieved)
    if not prices:
        tasks.fetch_s3pricing.delay()
    return jsonify(prices=prices)


@app.route('/aws/ec2pricing')
def aws_ec2_pricing():
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get EC2 pricing per gibabyte in all regions and storage types
        summary: *desc
        responses:
            200:
                description: List of instance types
                schema:
                    properties:
                        instances:
                            type: array
                            items:
                                properties:
                                    instanceType:
                                        type: string
                                    location:
                                        type: string
                                    prices:
                                        type: array
                                        items:
                                            properties:
                                                type:
                                                    type: string
                                                costPerHour:
                                                    type: float
                                                upfrontCost:
                                                    type: float
                                                reservationYears:
                                                    type: integer
            403:
                description: Not logged in
    """
    return jsonify(instances=ec2pricing.get_pricing_data())


def x_bandwidth_costs(accounts, f):
    now = datetime.utcnow()
    date_from = now.replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(days=30)
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    raw_data = [
        f(account.get_aws_user_id(), date_to=date_to, date_from=date_from)
        for account in accounts
    ]

    res = dict(total_cost=0, total_gb=0, transfers=[])

    def add_new(new):
        res['total_cost'] += new['cost']
        res['total_gb'] += new['quantity']
        for t in res['transfers']:
            if t['type'] == new['type']:
                t['quantity'] += new['quantity']
                t['cost'] += new['cost']
                return
        res['transfers'].append(new)

    for one in raw_data:
        for r in one:
            if r['type'].endswith('Bytes'):
                add_new(r)

    if not len(res['transfers']):
        return jsonify(message=get_next_update_estimation_message_aws(account, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/ec2_bandwidth_costs')
@with_login()
@with_multiple_aws_accounts()
def ec2_bandwidth_costs(accounts):
    return x_bandwidth_costs(accounts, AWSDetailedLineitem.get_ec2_bandwidth_costs)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/s3_bandwidth_costs')
@with_login()
@with_multiple_aws_accounts()
def s3_bandwidth_costs(accounts):
    return x_bandwidth_costs(accounts, AWSDetailedLineitem.get_s3_bandwidth_costs)


# TODO: swagger
@app.route('/aws/s3/estimate', methods=['GET'])
@with_login()
def s3_estimate():
    args = {}
    for key in request.args:
        try:
            args[key] = int(request.args[key])
        except:
            args[key] = request.args[key]
    res = estimate_s3_cost(**args)
    return jsonify(res)


# API to list all ELB regions and their pricing
@app.route('/aws/elb_region_pricing')
def elb_region_pricing():
    ret_dict = {}
    search = ELBPricing().search()
    results = []
    # Elasticsearch pagination
    for hit in search.scan():
        results.append(hit.to_dict())
    ret_dict["results"] = results
    return jsonify(ret_dict)

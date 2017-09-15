from datetime import timedelta
from app import app
from app.authentication import with_login
from sqlalchemy import desc
from flask import Blueprint, jsonify
from app.models import MyDBResourcesAWS
from app.msol_util import get_next_update_estimation_message_aws
from app.aws_keys import with_multiple_aws_accounts
from app.ec2reservations import get_reservation_forecast
from . import AWS_KEY_PROCESSING_INTERVAL_HOURS, AWS_RESOURCES_INTERVAL_HOURS
import itertools

aws_forecast_bp = Blueprint('aws_forecast_bp', __name__)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/reservationforecast')
@with_login()
@with_multiple_aws_accounts()
def aws_reservation_forecast(accounts):
    forecast = get_reservation_forecast(account.key for account in accounts)
    if not forecast or ('instances' in forecast and not forecast['instances']):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(forecast)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/rds/cost_estimation', methods=['GET'])
@with_login()
@with_multiple_aws_accounts()
def aws_rds_estimation_m(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get RDS cost estimation
        summary: *desc
        responses:
            200:
                description: List of instances
                schema:
                    properties:
                        result:
                            type: array
                            items:
                                properties:
                                    size:
                                        type: string
                                    name:
                                        type: string
                                    engine:
                                        type: string
                                    multi-az:
                                        type: boolean
                                    prices:
                                        type: array
                                        items:
                                            properties:
                                                name:
                                                    type: string
                                                cost:
                                                    type: number
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    my_db_resources = (
            MyDBResourcesAWS
                .query
                .filter(MyDBResourcesAWS.key == a.key)
                .order_by(desc(MyDBResourcesAWS.date))
                .first()
            for a in accounts
    )
    res = list(itertools.chain.from_iterable(
        [] if not r else r.json() for r in my_db_resources
    ))
    last_updated = None # TODO: Handle this in a meaningful way.
    next_update_delta = timedelta(hours=AWS_RESOURCES_INTERVAL_HOURS)
    next_update, remainder = divmod(next_update_delta.seconds, 3600)
    if next_update < 1:
        next_update = 1
    if not res:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_RESOURCES_INTERVAL_HOURS), last_updated=last_updated, next_update=next_update)
    return jsonify(dict(result=res, last_updated=last_updated, next_update=next_update))

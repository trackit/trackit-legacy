import boto3
from sqlalchemy import desc
from datetime import datetime, timedelta
from app import app
from app.authentication import with_login
from flask import Blueprint, jsonify, request
from app.aws_keys import with_aws_account, with_multiple_aws_accounts
from app.compare_providers import get_providers_comparison_aws
from app.msol_util import get_next_update_estimation_message_aws
from app.models import GoogleCloudIdentity, ProvidersComparisonGoogle, MyResourcesAWS
import itertools

compare_providers_bp = Blueprint('compare_providers_bp', __name__)

AWS_RESOURCES_INTERVAL_HOURS = 12

@app.route('/compare_providers/aws/<aws_key_ids:account_ids>')
@with_login()
@with_multiple_aws_accounts()
def compare_providers_aws(accounts):
    my_resources = [
        MyResourcesAWS
            .query
            .filter(MyResourcesAWS.key == a.key)
            .order_by(desc(MyResourcesAWS.date))
            .first()
        for a in accounts
    ]
    res = list(itertools.chain.from_iterable(
        [] if not r else r.json() for r in my_resources
    ))
    last_updated = None # TODO: Handle this in a meaningful way with several keys.
    next_update_delta = timedelta(hours=AWS_RESOURCES_INTERVAL_HOURS)
    next_update, remainder = divmod(next_update_delta.seconds, 3600)
    if next_update < 1:
        next_update = 1
    if not res:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_RESOURCES_INTERVAL_HOURS), last_updated=last_updated, next_update=next_update)
    return jsonify(dict(result=res, last_updated=last_updated, next_update=next_update))

@app.route('/compare_providers/gcloud/<int:identity_id>')
@with_login(True)
def compare_providers_gcloud(user, identity_id):
    identity = GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        res = ProvidersComparisonGoogle.query.filter(ProvidersComparisonGoogle.id_identity == identity.id).order_by(desc(ProvidersComparisonGoogle.date)).first()
        res = [] if not res else res.json()
        return jsonify(dict(result=res))
    else:
        return jsonify(error='No such identity.'), 404

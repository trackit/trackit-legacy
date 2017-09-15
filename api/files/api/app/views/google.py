from app import authentication
from app import google_storage
from app import models
from app import schemas
from app.models import db
from app.es.googledailyresource import GoogleDailyResource
from app.es.googlemetric import GoogleMetric
from app.gcloud.utils import get_credentials_from_identity
from collections import OrderedDict
import apiclient
import app
import config
import datetime
import flask
import httplib2
import oauth2client
import url

google_bp = flask.Blueprint('google_bp', __name__)

# Retrieve Google account userinfo.
def get_google_userinfo(http, google_oauth2_service=None):
    if not google_oauth2_service:
        google_oauth2_service = apiclient.discovery.build('oauth2', 'v2', http=http)
    profile = google_oauth2_service.userinfo().get().execute()
    return profile, google_oauth2_service

google_key_registration_flow = oauth2client.client.OAuth2WebServerFlow(scope='https://www.googleapis.com/auth/monitoring '
                                                                             'https://www.googleapis.com/auth/monitoring.read '
                                                                             'https://www.googleapis.com/auth/monitoring.write '
                                                                             'https://www.googleapis.com/auth/cloud-platform.read-only '
                                                                             'https://www.googleapis.com/auth/compute.readonly '
                                                                             'https://www.googleapis.com/auth/userinfo.email '
                                                                             'https://www.googleapis.com/auth/plus.login',
                                                                       redirect_uri='https://' + config.HOST + config.OAUTH_URIS['key_registration_google_callback'],
                                                                       **(config.GOOGLE_OAUTH))
google_key_registration_flow.params['access_type'] = 'offline'
google_key_registration_flow.params['prompt'] = 'consent'

@app.app.route('/gcloud/identity/initiate', methods=['GET'])
@authentication.with_login(True)
def initiate_auth_google_cloud_user(user):
    """---
    get:
        tags:
            - gcloud
        produces:
            - application/json
        description: |
            Initiate flow to register Google Cloud account: remember the
            attempt and return the corresponding URL which the client shall
            follow.

            This was built so to circumvent cross-site-request policies as the
            API is served on a port different than that of the origin.
        summary: Initiate flow to register Google Cloud account.
        parameters: []
        responses:
            200:
                description: The flow was initiated.
    """
    token = models.GoogleCloudIdentityRegistrationToken.for_user(user)
    db.session.add(token)
    auth_uri = google_key_registration_flow.step1_get_authorize_url(state=token.id)
    db.session.commit()
    return flask.jsonify(uri=auth_uri), 200

@app.app.route('/gcloud/identity/callback', methods=['GET'])
def callback_auth_google_cloud_user():
    """---
    get:
        tags:
            - gcloud
        description: |
            Callback for the Google Cloud account registration flow. Recall an
            attempt and register the Google identity for the initiating user.
        summary: Callback for the Google Cloud account registration flow.
        response:
            400:
                description: The `state` field is missing.
            403:
                description: |
                    The `state` field is either expired or does not exist.
            302:
                description: |
                    The flow successfully concluded. The Google Cloud identity
                    has been added to the user's cloud service accounts.
    """
    try:
        state = flask.request.args.get('state')
        if not state:
            return flask.jsonify(error='No state.'), 400
        token = models.GoogleCloudIdentityRegistrationToken.query.get(state)
        if not token:
            return flask.jsonify(error='Bad state.'), 403
        elif token.has_expired():
            db.session.delete(token)
            db.session.commit()
            return flask.jsonify(error='Expired state.'), 403
        assert token.id_user
        credentials = google_key_registration_flow.step2_exchange(flask.request.args.get('code'))
        http = httplib2.Http()
        http = credentials.authorize(http)
        profile, _ = get_google_userinfo(http)
        email = profile['email']
        identity = models.GoogleCloudIdentity(id_user=token.id_user,
                                       email=email,
                                       credentials=credentials.to_json())
        db.session.add(identity)
        db.session.delete(token)
        db.session.commit()
        return flask.redirect('https://%s/#/app/keyselect' % (config.WEB_UI_HOST,), code=302)
    except oauth2client.client.FlowExchangeError, e:
        return flask.jsonify(error='Failed to negotiate API tokens.')

@app.app.route('/gcloud/identity', methods=['GET'])
@authentication.with_login(True)
def get_gcloud_identity_list(user):
    """---
    get:
        tags:
            - gcloud
        description: |
            Retrieve all configured Google Cloud identities for the currently
            authenticated user.
        summary: Retrieve this user's Google Cloud identities.
        produces:
            - application/json
        response:
            403:
                description: |
                    The user is not authenticated.
            200:
                description: |
                    List of Google Cloud identities.
    """
    return flask.jsonify(identities=map(lambda i: schemas.google_cloud_identity_schema.dump(i).data, user.gcloud_identities))

@app.app.route('/gcloud/identity/<int:identity_id>', methods=['GET'])
@authentication.with_login(True)
def get_gcloud_identity(user, identity_id):
    """---
    get:
        tags:
            - gcloud
        description: |
            Retrieve a configured Google Cloud identity which belongs to
            the currently authenticated user by its ID.
        summary: |
            Retrieve a Google Cloud identity by ID.
        produces:
            - application/json
        response:
            200:
                description: Google Cloud identity.
            403:
                description: The user is not authenticated.
            404:
                description: The user has no identity with this ID.
    """
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        return flask.jsonify(schemas.google_cloud_identity_schema.dump(identity).data)
    else:
        return flask.jsonify(error='No such identity.'), 404

@app.app.route('/gcloud/identity/<int:identity_id>', methods=['DELETE'])
@authentication.with_login(True)
def delete_gcloud_identity(user, identity_id):
    """
    delete:
        tags:
            - gcloud
        description: |
            Deletes one of the user's Google Cloud identities by its ID. Note
            that this will recursively delete all associated projects, buckets,
            records and measurements.
        summary: Delete a Google Cloud identity.
        produces:
            - application/json
        response:
            200:
                description: Success.
            403:
                description: The user is not authenticated.
            404:
                description: The user has no identity with this ID.
    """
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        try:
            credentials = get_credentials_from_identity(identity)
            credentials.revoke(httplib2.Http())
        except:
            pass
        db.session.delete(identity)
        db.session.commit()
    return flask.jsonify({})

@app.app.route('/gcloud/estimate', methods=['GET'])
def gcloud_estimate():
    """---
    get:
        tags:
            - gcloud
        description: |
            Compute an estimate of the user's spendings on Google Cloud Storage
            depending on their needs in terms of services and volumes.
        summary: |
            Compute an estimate of the user's spednings on Google Cloud Storage.
        produces:
            - application/json
        response:
            200:
                description: The estimate was computed.
    """
    args = {}
    for key in filter(lambda k: k in google_storage.fields, flask.request.args):
        try:
            args[key] = int(flask.request.args[key])
        except:
            args[key] = flask.request.args[key]
    return flask.jsonify(google_storage.current_model(**args)), 200

@app.app.route('/gcloud/identity/<int:identity_id>/stats/dailycostbyproduct', methods=['GET'])
@authentication.with_login(True)
def gcloud_identity_daily_cost_by_product(user, identity_id):
    """---
    get:
        tags:
            - gcloud
        description: |
            Get daily costs summed by product
        summary: Get daily costs summed by product
        produces:
            - application/json
        response:
            200:
                description: Success.
            404:
                description: The user has no identity with this ID.
    """
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        res = GoogleDailyResource.daily_cost_by_product(identity.email)
        res['days'] = res['days'][-3:]
        return flask.jsonify(res)
    else:
        return flask.jsonify(error='No such identity.'), 404

@app.app.route('/gcloud/identity/<int:identity_id>/stats/monthcostbyproduct', methods=['GET'])
@authentication.with_login(True)
def gcloud_identity_month_cost_by_product(user, identity_id):
    """---
    get:
        tags:
            - gcloud
        description: |
            Get last month's cost by product
        summary: Get last month's cost by product
        produces:
            - application/json
        response:
            200:
                description: Success.
            404:
                description: The user has no identity with this ID.
    """
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        return flask.jsonify(GoogleDailyResource.month_cost_by_product(identity.email))
    else:
        return flask.jsonify(error='No such identity.'), 404

@app.app.route('/gcloud/identity/<int:identity_id>/stats/costbyresource', methods=['GET'])
@authentication.with_login(True)
def gcloud_identity_cost_by_resource(user, identity_id):
    """---
    get:
        tags:
            - gcloud
        description: |
            Retrieve the monthly cost by resource aggregated by price category
        summary: Get monthly cost by resource
        produces:
            - application/json
        response:
            200:
                description: Success.
            404:
                description: The user has no identity with this ID.
    """
    cost_categories = [1, 10, 100, 1000, 10000, 100000, 1000000]
    def get_max_cost(month):
        max_cost = 0
        for resource in month['resources']:
            if resource['cost'] > max_cost:
                max_cost = resource['cost']
        return max_cost
    def get_max_cost_category(max_cost):
        for category in reversed(cost_categories):
            if max_cost >= category:
                return category
        return 1
    def get_categories_dict(max_cost):
        categories_dict = OrderedDict()
        if max_cost < 1:
            categories_dict['<1'] = dict(resources=[], total=0)
            return categories_dict
        for category in cost_categories:
            categories_dict['<'+str(category)] = dict(resources=[], total=0)
            if category == max_cost_category:
                categories_dict['>'+str(category)] = dict(resources=[], total=0)
                break
        return categories_dict
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        res = []
        monthly_cost_by_resource = GoogleDailyResource.monthly_aggregates_resource(identity.email)
        for month in monthly_cost_by_resource['months']:
            max_cost = get_max_cost(month)
            max_cost_category = get_max_cost_category(max_cost)
            month_aggregate = {
                'month': month['month'],
                'categories': get_categories_dict(max_cost),
                'total': 0
            }
            month_aggregate['category_list'] = month_aggregate['categories'].keys()
            for resource in month['resources']:
                if resource['cost'] < 0:
                    continue
                elif resource['cost'] >= max_cost_category:
                    month_aggregate['categories']['>'+str(max_cost_category)]['resources'].append(resource)
                    month_aggregate['categories']['>'+str(max_cost_category)]['total'] += resource['cost']
                else:
                    for cost_category in cost_categories:
                        if resource['cost'] < cost_category:
                            month_aggregate['categories']['<'+str(cost_category)]['resources'].append(resource)
                            month_aggregate['categories']['<'+str(cost_category)]['total'] += resource['cost']
                            break
                month_aggregate['total'] += resource['cost']
            res.append(month_aggregate)
        return flask.jsonify(months=res)
    else:
        return flask.jsonify(error='No such identity.'), 404

@app.app.route('/gcloud/identity/<int:identity_id>/stats/costbyproject', methods=['GET'])
@authentication.with_login(True)
def gcloud_identity_cost_by_project(user, identity_id):
    """---
    get:
        tags:
            - gcloud
        description: |
            Retrieve the monthly cost by project
        summary: Get monthly cost by project
        produces:
            - application/json
        response:
            200:
                description: Success.
            404:
                description: The user has no identity with this ID.
    """
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        monthly_cost_by_project = GoogleDailyResource.monthly_aggregates_project(identity.email)
        for month in monthly_cost_by_project['months']:
            total = 0
            for project in month['projects']:
                total = total + project['cost']
            month.update(dict(total=total))
        return flask.jsonify(months=monthly_cost_by_project)
    else:
        return flask.jsonify(error='No such identity.'), 404


@app.app.route('/gcloud/identity/<int:identity_id>/stats/usagecost')
@authentication.with_login(True)
def gcloud_usage_cost(user, identity_id):
    """---
    get:
        tags:
            - cloud
        description: |
            Retrieve the Google CPU usage VS cost
        summary: Get the Google CPU usage VS cost
        produces:
            - application/json
        responses:
            200:
                description: List of stats
                schema:
                    properties:
                        days:
                            type: array
                            items:
                                properties:
                                    day:
                                        type: string
                                    cpu:
                                        type: number
                                    cost:
                                        type: number
            404:
                description: The user has no identity with this ID
    """
    identity = models.GoogleCloudIdentity.query.filter_by(id_user=user.id, id=identity_id).first()
    if identity:
        cpu = dict(GoogleMetric.daily_cpu_utilization(identity.email))
        cost = dict(GoogleDailyResource.daily_compute_cost(identity.email))
        days = sorted(set(cpu.keys()) & set(cost.keys()))
        daily = [dict(day=d, cpu=cpu[d] * 100, cost=cost[d]) for d in days]
        return flask.jsonify(dict(days=daily))
    else:
        return flask.jsonify(error='No such identity.'), 404

from datetime import datetime, timedelta
from app import app
from app.authentication import with_login
from flask import Blueprint, jsonify, request
from app.models import AWSKeyS3Bucket
from app.msol_util import get_next_update_estimation_message_aws
from app.es.awsstat import AWSStat
from app.es.s3bucketfile import S3BucketFile
from app.es.awsaccesslog import AWSAccessLog
from app.es.awsdetailedlineitem import AWSDetailedLineitem
from app.es.awselbinfo import AWSELBInfo
from app.es.awsmetric import AWSMetric
from app.aws_keys import with_aws_account, with_multiple_aws_accounts
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from . import AWS_KEY_PROCESSING_INTERVAL_HOURS
import calendar

aws_usage_bp = Blueprint('aws_usage_bp', __name__)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/ondemandswitchsuggestion')
@with_login()
@with_multiple_aws_accounts()
def aws_on_demand_switch_suggestion(accounts):
    return jsonify(AWSStat.latest_on_demand_to_reserved_suggestion(account.key for account in accounts))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/availablevolumes')
@with_login()
@with_multiple_aws_accounts()
def get_aws_available_volumes(accounts):
    return jsonify(AWSStat.latest_available_volumes(account.key for account in accounts))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/stoppedinstances')
@with_login()
@with_multiple_aws_accounts()
def get_aws_stopped_instances(accounts):
    return jsonify(AWSStat.latest_stopped_instances_report(account.key for account in accounts))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/instancestats')
@with_login()
@with_multiple_aws_accounts()
def aws_instance_stats(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get instance statistics
        summary: *desc
        responses:
            200:
                description: List of stats
                schema:
                    properties:
                        stats:
                            type: array
                            items:
                                properties:
                                    reserved:
                                        type: number
                                    unreserved:
                                        type: number
                                    unused:
                                        type: number
                                    stopped:
                                        type: number
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    datasets = []
    reserved_report = []
    for account in accounts:
        instance_stats = AWSStat.latest_instance_stats(account.key)
        if 'stats' in instance_stats and len(instance_stats['stats']):
            datasets.append(instance_stats['stats'][0])
            if 'reserved_instances_report' in instance_stats['stats'][0]:
                reserved_report += instance_stats['stats'][0]['reserved_instances_report']
    if not len(datasets):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify({
        'stats': [
            {
                'reserved_report': reserved_report,
                'reserved': sum(d['reserved'] for d in datasets),
                'stopped': sum(d['stopped'] for d in datasets),
                'unreserved': sum(d['unreserved'] for d in datasets),
                'unused': sum(d['unused'] for d in datasets),
                'time': datasets[0]['time'],
            }
        ]
    })


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/cpuhourlyusage')
@with_login()
@with_multiple_aws_accounts()
def aws_cpu_hourly_usage_m(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc AWS CPU usage by hours of the day
        summary: *desc
        responses:
            200:
                description: List of hours
                schema:
                    properties:
                        hours:
                            type: array
                            items:
                                properties:
                                    hour:
                                        type: string
                                    cpu:
                                        type: number
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    hours = AWSMetric.hourly_cpu_usage(account.key for account in accounts)
    if not hours:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(dict(hours=hours))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/cpuhourlyusagebytag/<path:tag>')
@with_login()
@with_multiple_aws_accounts()
def aws_cpu_hourly_usage_by_tag(accounts, tag):
    res = []
    tpm_cpu_usage_infos = defaultdict(lambda: dict(nb_instances=0, usage={x: [] for x in ["{:02d}".format(x) for x in range(0, 24)]}))
    for account in accounts:
        usage = AWSStat.latest_hourly_cpu_usage_by_tag(account.key)
        if tag in usage['tags']:
            for tag_infos in usage['tags'][tag]:
                tpm_cpu_usage_infos[tag_infos['tag_value']]['nb_instances'] += tag_infos['nb_instances']
                for hour in tag_infos['usage']:
                    tpm_cpu_usage_infos[tag_infos['tag_value']]['usage'][hour['hour']].append(hour['cpu'])
    for tag_value, tag_infos in tpm_cpu_usage_infos.iteritems():
        tag_res = dict(nb_instances=tag_infos['nb_instances'], tag_value=tag_value, usage=[])
        for usage_hour, usage_details in tag_infos['usage'].iteritems():
            cpu_usage = 0 if not len(usage_details) else sum(usage_details) / len(usage_details)
            tag_res['usage'].append(dict(hour=usage_hour, cpu=cpu_usage))
        tag_res['usage'].sort(key=lambda x: x['hour'])
        res.append(tag_res)
    return jsonify(values=res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/cpudaysweekusage')
@with_login()
@with_multiple_aws_accounts()
def aws_cpu_days_of_the_week_usage_m(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc AWS CPU usage by days of the week
        summary: *desc
        responses:
            200:
                description: List of days
                schema:
                    properties:
                        hours:
                            type: array
                            items:
                                properties:
                                    day:
                                        type: string
                                    cpu:
                                        type: number
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    days = AWSMetric.days_of_the_week_cpu_usage(account.key for account in accounts)
    if not days:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(dict(hours=days))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/cpudaysweekusagebytag/<path:tag>')
@with_login()
@with_multiple_aws_accounts()
def aws_cpu_days_of_the_week_usage_by_tag(accounts, tag):
    res = []
    days_of_the_week = dict(Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6)
    tpm_cpu_usage_infos = defaultdict(lambda: dict(nb_instances=0, usage={x: [] for x in range(0, 7)}))
    for account in accounts:
        usage = AWSStat.latest_daily_cpu_usage_by_tag(account.key)
        if tag in usage['tags']:
            for tag_infos in usage['tags'][tag]:
                tpm_cpu_usage_infos[tag_infos['tag_value']]['nb_instances'] += tag_infos['nb_instances']
                for day in tag_infos['usage']:
                    tpm_cpu_usage_infos[tag_infos['tag_value']]['usage'][days_of_the_week[day['day']]].append(day['cpu'])
    for tag_value, tag_infos in tpm_cpu_usage_infos.iteritems():
        tag_res = dict(nb_instances=tag_infos['nb_instances'], tag_value=tag_value, usage=[])
        for usage_day_idx, usage_details in tag_infos['usage'].iteritems():
            cpu_usage = 0 if not len(usage_details) else sum(usage_details) / len(usage_details)
            tag_res['usage'].append(dict(day=usage_day_idx, cpu=cpu_usage))
        tag_res['usage'].sort(key=lambda x: x['day'])
        tag_res['usage'] = [dict(day=calendar.day_name[x['day']], cpu=x['cpu']) for x in tag_res['usage']]
        res.append(tag_res)
    return jsonify(dict(values=res))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/s3/space_usage')
@with_login()
@with_multiple_aws_accounts()
def get_s3_space_usage(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get S3 space usage
        summary: *desc
        responses:
            200:
                description: List of buckets
                schema:
                    properties:
                        buckets:
                            type: array
                            items:
                                properties:
                                    location:
                                        type: string
                                    name:
                                        type: string
                                    type:
                                        type: string
                                    provider:
                                        type: string
                                    used_space:
                                        type: number
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
    res = [
        AWSStat.latest_s3_space_usage(account)
        for account in accounts
    ]
    buckets = sum(
        (
            r['buckets']
            for r in res
            if r and 'buckets' in r
        ),
        []
    )
    last_updated = None #TODO: Decide how to handle this with several accounts.
    next_update_delta = timedelta(hours=AWS_KEY_PROCESSING_INTERVAL_HOURS) #TODO: Same here, I put a value for the demos.
    next_update, remainder = divmod(next_update_delta.seconds, 3600)
    if next_update < 1:
        next_update = 1
    for bucket in buckets:
        bucket['metadata'] = None #TODO: See how to get the account the bucket comes from.
    if not buckets:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS), last_updated=last_updated, next_update=next_update)
    return jsonify({
        'buckets': buckets,
        'last_updated': last_updated,
        'next_update': next_update,
    })


@app.route('/aws/accounts/<int:account_id>/s3/space_usage_directory', methods=['GET'])
@with_login()
@with_aws_account()
def get_s3_space_usage_directory(account, account_id):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get S3 space usage
        summary: *desc
        parameters:
            - in: query
              name: path
              required: false
              description: path prefix for which to retrieve
              type: string
        responses:
            200:
                description: Directory tree
                schema:
                    properties:
                        dirs:
                            type: object
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    path = request.args.get('path', '').split('/')
    if path != ['']:
        if AWSKeyS3Bucket.query.filter_by(id_aws_key=account_id, bucket=path[0]).count():
            dirs = S3BucketFile.get_dir_sizes(path[0], '/'.join(path[1:]))
            return jsonify(dirs=dict(dirs))
        else:
            return jsonify(dirs={})
    else:
        buckets = [b.bucket for b in AWSKeyS3Bucket.query.filter_by(id_aws_key=account_id)]
        return jsonify(dict(dirs=dict(S3BucketFile.get_bucket_sizes(buckets))))


@app.route('/aws/accounts/<int:account_id>/s3/space_usage_tags', methods=['GET'])
@with_login()
@with_aws_account()
def get_s3_space_usage_tags(account, account_id):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get S3 space usage
        summary: *desc
        parameters:
            - in: query
              name: path
              required: false
              description: path prefix for which to retrieve
              type: string
            - in: query
              name: tag
              required: false
              description: tag to filter by
              type: string
            - in: query
              name: tagkey
              required: false
              description: tag key to aggregate by
              type: string
        responses:
            200:
                description: Directory tree
                schema:
                    properties:
                        tags:
                            type: object
                        tagkeys:
                            type: array
                            items:
                                type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    path = request.args.get('path', '').split('/')
    tags = request.args.getlist('tag')
    tagkey = request.args.get('tagkey')
    tagsizes = {}
    tagkeys = []
    if path != ['']:
        if AWSKeyS3Bucket.query.filter_by(id_aws_key=account_id, bucket=path[0]).count():
            tagsizes, tagkeys = S3BucketFile.get_dir_tags(path[0], '/'.join(path[1:]), tags, tagkey)
    else:
        buckets = [b.bucket for b in AWSKeyS3Bucket.query.filter_by(id_aws_key=account_id)]
        tagsizes, tagkeys = S3BucketFile.get_bucket_tags(buckets, tags, tagkey)
    return jsonify(tags=tagsizes, keys=tagkeys)


@app.route('/aws/accounts/<int:account_id>/s3/last_accessed_bucket', methods=['GET'])
@with_login()
@with_aws_account()
def get_s3_last_accessed_bucket(account, account_id):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get S3 most used object list
        summary: *desc
        parameters:
            - in: query
              name: account_id
              required: true
              description: account identifier
              type: string
        responses:
            200:
                description: Directory tree
                schema:
                    properties:
                        objects:
                            type: array
                            items:
                                type: string
            500:
                description: Error
    """
    try:
        buckets = []
        for bucket in AWSKeyS3Bucket.query.filter_by(id_aws_key=account_id):
            buckets.append(dict(bucket_name=bucket.bucket,
                                last_access=AWSAccessLog.last_access_s3_bucket(account.key, bucket.bucket)))
        return jsonify(objects=buckets), 200
    except:
        return jsonify(error='Error.'), 500


@app.route('/aws/accounts/<int:account_id>/s3/most_accessed_objects', methods=['GET'])
@with_login()
@with_aws_account()
def get_s3_most_accessed_objects(account, account_id):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get S3 most used object list
        summary: *desc
        parameters:
            - in: query
              name: account_id
              required: true
              description: account identifier
              type: string
        responses:
            200:
                description: Directory tree
                schema:
                    properties:
                        objects:
                            type: array
                            items:
                                type: string
            500:
                description: Error
    """
    try:
        return jsonify(AWSAccessLog.most_accessed_s3_objects(account.key)), 200
    except:
        return jsonify(error='Error.'), 500


@app.route('/aws/accounts/<aws_key_ids:account_ids>/describe_elb')
@with_login()
@with_multiple_aws_accounts()
def describe_elb(accounts):
    now = datetime.utcnow()
    date_from = now.replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(days=30)
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    ares = []
    for account in accounts:
        res = []
        elb_usage = AWSDetailedLineitem.get_elb_usage_a_day(account.get_aws_user_id(), date_from=date_from, date_to=date_to)
        for elb in AWSELBInfo.get_elb_info(account.get_aws_user_id()):
            for usage in elb_usage:
                if usage['rid'].endswith(elb['name']) or usage['rid'].split('/')[-2] == elb['name']:
                    usage['region'] = elb['region']
                    usage['name'] = elb['name']
                    usage['instances'] = elb['instances']
                    res.append(usage)
        for d in res:
            if d not in ares:
                ares.append(d)
    if not len(ares):
        if AWSDetailedLineitem.keys_has_data([account.get_aws_user_id() for account in accounts]):
            return jsonify(message="You do not have ELB set up in your environment")
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(elbs=ares)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/lambda/usage')
@with_login()
@with_multiple_aws_accounts()
def get_lambda_usage(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get average Lambda usage
        summary: *desc
        responses:
            200:
                description: List of lambda resources
                schema:
                    properties:
                        lambdas:
                            type: array
                            items:
                                properties:
                                    rid:
                                        type: string
                                    name:
                                        type: string
                                    gb_seconds:
                                        type: number
                                    requests:
                                        type: number
                                    cost:
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    res = AWSDetailedLineitem.get_lambda_usage([account.get_aws_user_id() for account in accounts])
    if not len(res):
        return jsonify(message=get_next_update_estimation_message_aws(account, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(lambdas=res)

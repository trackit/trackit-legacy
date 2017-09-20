from app import app
from models import db, MultikeyGroup, MultikeyKey
from celery import Celery
from celery.signals import task_postrun
from celery.decorators import periodic_task
from datetime import datetime, timedelta
from sqlalchemy import or_, desc
import logging
from collections import defaultdict
import traceback
from send_email import send_email as f_send_email, send_email_alternative as f_send_email_alternative
from app.error_email import aws_credentials_error, aws_key_processing_generic_error_email, aws_bucket_does_not_exist_error_email
from functools import wraps
from monthly_report import monthly_html_template

runner = Celery()
runner.config_from_object(app.config)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s: %(levelname)s]%(message)s')

@task_postrun.connect
def close_sqlalchemy_session(*args, **kwargs):
    db.session.close()

def once_per(interval):
    def wrapper(task_fn):
        @wraps(task_fn)
        def wrapped(*args):
            status = TaskStatus.find_by_args(task_fn, args)
            if status:
                if status.completion_time and datetime.utcnow() - status.completion_time < interval:
                    return
            else:
                status = TaskStatus()
                status.set_task_name(task_fn)
                status.set_argument_signature(args)
                db.session.add(status)
            status.error = None
            status.start_time = datetime.utcnow()
            status.completion_time = None
            db.session.commit()
            try:
                return task_fn(*args)
            except Exception as e:
                status.error = str(e)
                raise
            finally:
                db.session.close()
                status.completion_time = datetime.utcnow()
                db.session.merge(status)
                db.session.commit()
        return wrapped
    return wrapper

from app.es.awsmetric import AWSMetric
from app.es.awsstat import AWSStat
from app.es import bulk_save, client as esclient
from app.es.awsaccesslog import AWSAccessLog
from app.es.awselbinfo import AWSELBInfo
from app.models import db, UserSessionToken, AWSKey, MyResourcesAWS, MyDBResourcesAWS, GoogleCloudIdentity, ProvidersComparisonGoogle, AWSKeyS3Bucket, TaskStatus
from app.aws.ec2metrics import get_instance_metrics, get_volume_metrics
from app.aws.s3metrics import get_bucket_metrics
from app.aws.s3accesslogs import get_object_access_logs
from app.aws.instances import get_instance_stats, get_hourly_cpu_usage_by_tag, get_daily_cpu_usage_by_tag, get_all_instances, get_stopped_instances_report
from app.aws.volumes import get_available_volumes
from app.aws.elb import import_elb_infos
from app.ec2reservations import get_reservation_forecast, get_on_demand_to_reserved_suggestion
from app.compare_providers import get_providers_comparison_aws, get_providers_comparison_google
from app.s3_space_usage import get_s3_space_usage
from app.rds import compare_rds_instances
from s3_billing_transfer import prepare_bill_for_es, prepare_bill_for_s3
import s3metadata
import boto3
import botocore

aws_data_fetch_freq = timedelta(hours=6)
aws_data_grace = timedelta(hours=6)
aws_resources_fetch_freq = timedelta(hours=12)

@runner.task
def process_aws_key(key_ids):
    # TODO: remove this
    if not isinstance(key_ids, list):
        key_ids = [key_ids]
    keys = list(AWSKey.query.filter(AWSKey.id.in_(key_ids)))
    if not keys:
        return
    key = min(keys, key=lambda k: k.last_fetched or datetime(1970, 1, 1))
    since = None
    if key.last_fetched:
        since = key.last_fetched - aws_data_grace
        if key.last_fetched > datetime.utcnow() - aws_data_fetch_freq:
            return
    for k in keys:
        k.last_fetched = datetime.utcnow()
    db.session.commit()
    try:
        processing_start = datetime.utcnow()
        session = boto3.Session(aws_access_key_id=key.key,
                                aws_secret_access_key=key.secret)
        AWSStat(key=key.key,
                time=datetime.utcnow(),
                stat='instances',
                data=get_instance_stats(session)).save()

        def get_instance_metric_records():
            for metric in get_instance_metrics(session, since):
                id = checksum(str(metric['time']),
                              metric['metric'],
                              metric['resource'])
                yield AWSMetric(meta={'id': id}, key=key.key, **metric)

        bulk_save(get_instance_metric_records())

        def get_volume_metric_records():
            for metric in get_volume_metrics(session, since):
                id = checksum(str(metric['time']),
                              metric['metric'],
                              metric['resource'])
                yield AWSMetric(meta={'id': id}, key=key.key, **metric)

        bulk_save(get_volume_metric_records())

        def get_bucket_metrics_records():
            for metric in get_bucket_metrics(session, since):
                id = checksum(str(metric['time']),
                                  metric['metric'],
                                  metric['resource'])
                yield AWSMetric(meta={'id': id}, key=key.key, **metric)

        bulk_save(get_bucket_metrics_records())

        def get_bucket_object_access_records():
            for log in get_object_access_logs(session, since):
                id = checksum(str(log['time']),
                                  log['bucket'],
                                  log['object'])
                yield AWSAccessLog(meta={'id': id}, key=key.key, **log)

        bulk_save(get_bucket_object_access_records())

        AWSStat(key=key.key,
                time=datetime.utcnow(),
                stat='ondemandtoreserved',
                data=get_on_demand_to_reserved_suggestion(session, key)).save()

        AWSStat(key=key.key,
                time=datetime.utcnow(),
                stat='s3spaceusage',
                data=get_s3_space_usage(key)).save()

        AWSStat(key=key.key,
                time=datetime.utcnow(),
                stat='detachedvolumes',
                data=get_available_volumes(session)).save()

        AWSStat(key=key.key,
                time=datetime.utcnow(),
                stat='hourlycpubytag',
                data=get_hourly_cpu_usage_by_tag(session, key.key)).save()

        AWSStat(key=key.key,
                time=datetime.utcnow(),
                stat='dailycpubytag',
                data=get_daily_cpu_usage_by_tag(session, key.key)).save()

        my_resources_record = MyResourcesAWS.query.filter(MyResourcesAWS.key == key.key).order_by(desc(MyResourcesAWS.date)).first()
        if not my_resources_record:
            res = get_providers_comparison_aws(key)
            if res is not None:
                my_resources_record = MyResourcesAWS(key=key.key, date=datetime.utcnow())
                my_resources_record.set_json(res)
                db.session.add(my_resources_record)
                db.session.commit()

        my_db_resources_record = MyDBResourcesAWS.query.filter(MyDBResourcesAWS.key == key.key).order_by(desc(MyDBResourcesAWS.date)).first()
        if not my_db_resources_record:
            res = compare_rds_instances(key)
            my_db_resources_record = MyDBResourcesAWS(key=key.key, date=datetime.utcnow())
            my_db_resources_record.set_json(res)
            db.session.add(my_db_resources_record)
            db.session.commit()

        key.error_status = None
        key.last_duration = (datetime.utcnow() - processing_start).total_seconds()
        db.session.commit()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            aws_bucket_does_not_exist_error_email(key, traceback.format_exc())
            key.error_status = u"no_such_bucket"
            logging.error("[user={}][key={}] The specified billing bucket does not exists".format(key.user.email, key.pretty or key.key))
        else:
            aws_credentials_error(key, traceback.format_exc())
            key.error_status = u"bad_key"
            logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))
        key.last_duration = (datetime.utcnow() - processing_start).total_seconds()
        db.session.commit()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            aws_bucket_does_not_exist_error_email(key, traceback.format_exc())
            key.error_status = u"no_such_bucket"
            logging.error("[user={}][key={}] The specified billing bucket does not exists".format(key.user.email, key.pretty or key.key))
        else:
            aws_credentials_error(key, traceback.format_exc())
            key.error_status = u"bad_key"
            logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))
        db.session.commit()
    except Exception, e:
        aws_key_processing_generic_error_email(key, traceback.format_exc())
        key.error_status = u"processing_error"
        key.last_duration = (datetime.utcnow() - processing_start).total_seconds()
        db.session.commit()
        #logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))

@runner.task
def import_aws_client_bills(key_ids, force_import=False):
    u'''
    Transfer bills on S3 then import them on ES

    :param key_ids: list of int or int
    :param force_import: import all bills to ES instead of just the changed bills
    '''
    key_ids = key_ids if isinstance(key_ids, list) else [key_ids]
    keys = list(AWSKey.query.filter(AWSKey.id.in_(key_ids)))
    if not keys:
        return
    for key in keys:
        try:
            bills = prepare_bill_for_s3(key, force_import)
            prepare_bill_for_es(bills)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                aws_bucket_does_not_exist_error_email(key, traceback.format_exc())
                key.error_status = u"no_such_bucket"
                logging.error("[user={}][key={}] The specified billing bucket does not exists".format(key.user.email,
                                                                                                      key.pretty or key.key))
                db.session.commit()
            traceback.print_exc()
        except:
            aws_key_processing_generic_error_email(key, traceback.format_exc())
            traceback.print_exc()


@runner.task
def import_aws_elb_infos(key_ids):
    AWSELBInfo.init()
    key_ids = key_ids if isinstance(key_ids, list) else [key_ids]
    keys = list(AWSKey.query.filter(AWSKey.id.in_(key_ids)))
    if not keys:
        return
    for key in keys:
        try:
            print 'Importing ELB infos for {}...'.format(key.pretty)
            import_elb_infos(key)
            print 'ELB infos imported for {}!'.format(key.pretty)
        except:
            aws_key_processing_generic_error_email(key, traceback.format_exc())
            traceback.print_exc()


@runner.task
@periodic_task(run_every=timedelta(hours=1))
def send_monthly_report():
    monthly_html_template()

@runner.task
@periodic_task(run_every=timedelta(days=1))
def purge_expired_sessions():
    now = datetime.utcnow()
    UserSessionToken.query.filter(UserSessionToken.expires <= now).delete()
    db.session.commit()

@runner.task
@periodic_task(run_every=timedelta(minutes=30))
def get_aws_keys_to_fetch():
    newest_fetch_time = datetime.utcnow() - aws_data_fetch_freq
    keys = AWSKey.query
    unique_keys = defaultdict(list)
    for key in keys:
        unique_keys[key.key, key.secret, key.billing_bucket_name].append(key)
    for grouped_keys in unique_keys.itervalues():
        import_aws_elb_infos.delay([k.id for k in grouped_keys])
        import_aws_client_bills.delay([k.id for k in grouped_keys])
        process_aws_key.delay([
            k.id
            for k in grouped_keys
            if k.last_fetched == None or k.last_fetched < newest_fetch_time
        ])

@runner.task
def process_my_db_resources_aws(key_ids):
    key = AWSKey.query.filter(AWSKey.id.in_(key_ids)).first()
    record = MyDBResourcesAWS.query.filter(MyDBResourcesAWS.key == key.key).order_by(desc(MyDBResourcesAWS.date)).first()
    if not record:
        return
    if record.date < datetime.now() - aws_resources_fetch_freq:
        res = compare_rds_instances(key)
        record.date = datetime.utcnow()
        record.set_json(res)
        db.session.commit()

@runner.task
def process_my_resources_aws(key_ids):
    key = AWSKey.query.filter(AWSKey.id.in_(key_ids)).first()
    record = MyResourcesAWS.query.filter(MyResourcesAWS.key == key.key).order_by(desc(MyResourcesAWS.date)).first()
    if not record:
        return
    if record.date < datetime.now() - aws_resources_fetch_freq:
        res = get_providers_comparison_aws(key)
        if res is None:
            return
        record.date = datetime.utcnow()
        record.set_json(res)
        db.session.commit()

@runner.task
@periodic_task(run_every=timedelta(minutes=30))
def my_resources_aws():
    keys = AWSKey.query.all()
    unique_keys = defaultdict(list)
    for key in keys:
        unique_keys[key.key, key.secret, key.billing_bucket_name].append(key)

    for grouped_keys in unique_keys.itervalues():
        process_my_resources_aws.delay([k.id for k in grouped_keys])
        process_my_db_resources_aws.delay([k.id for k in grouped_keys])

from app import s3pricing

@runner.task
@periodic_task(run_every=timedelta(minutes=30))
def fetch_s3pricing():
    s3pricing.fetch()

from app.aws.instances import get_instances_id_name_mapping
from app.aws.volumes import get_volumes_id_name_mapping
from app.es.awsidnamemapping import AWSIdNameMapping
from app.msol_util import checksum

@runner.task
def process_aws_resources_names(key):
    try:
        key = AWSKey.query.get(key.id)
        session = boto3.Session(aws_access_key_id=key.key,
                                aws_secret_access_key=key.secret)
        id_name_mapping = get_instances_id_name_mapping(session)
        id_name_mapping.update(get_volumes_id_name_mapping(session))
        def get_id_name_mappings():
            now = datetime.utcnow()
            for rid, name in id_name_mapping.iteritems():
                yield AWSIdNameMapping(meta={'id': rid}, key=key.key, date=now, rid=rid, name=name)
        bulk_save(get_id_name_mappings())
    except botocore.exceptions.ClientError as e:
        logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))
        aws_credentials_error(key, traceback.format_exc())
        key.error_status = u"bad_key"
        db.session.commit()
    except Exception, e:
        aws_key_processing_generic_error_email(key, traceback.format_exc())
        key.error_status = u"processing_error"
        db.session.commit()

@runner.task
@periodic_task(run_every=timedelta(days=1))
def aws_resources_names_task():
    keys = AWSKey.query.all()
    unique_keys = defaultdict(list)
    for key in keys:
        unique_keys[key.key, key.secret, key.billing_bucket_name].append(key)

    for grouped_keys in unique_keys.itervalues():
        process_aws_resources_names.delay(grouped_keys[0])

from ms_azure.pricing import fetch_pricings as azure_fetch_pricings

@runner.task
@periodic_task(run_every=timedelta(hours=6))
def fetch_azure_pricing():
    azure_fetch_pricings()

from app.google_billing import get_all_line_items as gcloud_get_all_line_items, ResourceByDayAccumulator as GoogleResourceByDayAccumulator
from app.gcloud.projects import get_identity_projects_from_gcloud_api
from app.gcloud.buckets import get_project_buckets_from_gcloud_api
from app.gcloud.compute_metrics import get_instance_metrics as gcloud_get_instance_metrics
from app.es.googledailyresource import GoogleDailyResource
from app.es.googlemetric import GoogleMetric

google_data_fetch_freq = timedelta(hours=6)
google_data_grace = timedelta(hours=6)

@runner.task
def process_google_identity(identity_ids):
    if not isinstance(identity_ids, list):
        identity_ids = [identity_ids]
    identities = list(GoogleCloudIdentity.query.filter(GoogleCloudIdentity.id.in_(identity_ids)))
    if not identities:
        return
    identity = min(identities, key=lambda i: i.last_fetched or datetime(1970, 1, 1))
    since = None
    if identity.last_fetched:
        since = identity.last_fetched - google_data_grace
        if identity.last_fetched > datetime.utcnow() - google_data_fetch_freq:
            return

    for i in identities:
        i.last_fetched = datetime.utcnow()
    db.session.commit()

    res_by_day = GoogleResourceByDayAccumulator()

    try:
        def get_instance_metric_records(identity, project, since):
            for metric in gcloud_get_instance_metrics(identity, project, since):
                id = checksum(str(metric['time']),
                              metric['metric'],
                              metric['resource'],
                              identity.email)
                yield GoogleMetric(meta={'id': id}, identity=identity.email, **metric)

        for project in get_identity_projects_from_gcloud_api(identity):
            bulk_save(get_instance_metric_records(identity, project, since))
            for bucket in get_project_buckets_from_gcloud_api(identity, project):
                for l in gcloud_get_all_line_items(identity, bucket, since):
                    res_by_day(l)

        def get_daily_resource_usage_records():
            for usage in res_by_day.results():
                yield GoogleDailyResource(meta={'id': checksum(usage.pop('id'), identity.email)}, identity=identity.email, **usage)

        bulk_save(get_daily_resource_usage_records())
    except Exception, e:
        identity.last_errored = datetime.utcnow()
        db.session.commit()
        logging.error("[user={}][identity={}] {}".format(identity.user.email, identity.email, str(e)))


@runner.task
@periodic_task(run_every=timedelta(minutes=30))
def get_google_identities_to_fetch():
    newest_fetch_time = datetime.utcnow() - google_data_fetch_freq
    identities = GoogleCloudIdentity.query.filter(or_(GoogleCloudIdentity.last_fetched < newest_fetch_time,
                                                      GoogleCloudIdentity.last_fetched == None))
    unique_identities = defaultdict(list)
    for identity in identities:
        unique_identities[identity.email].append(identity)

    for grouped_identities in unique_identities.itervalues():
        process_google_identity.delay([i.id for i in grouped_identities])

@runner.task
def process_compare_providers_google(identity):
    res = get_providers_comparison_google(identity)
    record = ProvidersComparisonGoogle.query.filter(ProvidersComparisonGoogle.id_identity == identity.id).order_by(desc(ProvidersComparisonGoogle.date)).first()
    if not record:
        record = ProvidersComparisonGoogle(id_identity=identity.id)
    record.date = datetime.utcnow()
    record.set_json(res)
    if not record.id:
        db.session.add(record)
    db.session.commit()

@runner.task
@periodic_task(run_every=timedelta(hours=12))
def compare_providers_task():
    identities = GoogleCloudIdentity.query.all()
    for identity in identities:
        process_compare_providers_google.delay(identity)

@runner.task
@periodic_task(run_every=timedelta(hours=2))
def get_s3_buckets_to_fetch():
    credential_aws_key_ids = defaultdict(list)
    for key in AWSKey.query.filter_by(import_s3=True):
        credential_aws_key_ids[(key.key, key.secret)].append(key.id)
    for key_ids in credential_aws_key_ids.itervalues():
        fetch_s3_buckets.delay(key_ids)

@runner.task
def fetch_s3_buckets(key_ids):
    keys = list(AWSKey.query.filter(AWSKey.id.in_(key_ids)))
    if not keys:
        return
    session = boto3.Session(aws_access_key_id=keys[0].key,
                            aws_secret_access_key=keys[0].secret)
    s3 = session.resource('s3')
    for bucket in s3.buckets.all():
        for key in keys:
            db.session.merge(AWSKeyS3Bucket(id_aws_key=key.id, bucket=bucket.name))
        db.session.commit()
        fetch_s3_bucket.delay(bucket.name, key.key, key.secret)

@runner.task
@periodic_task(run_every=timedelta(minutes=30))
def get_multikey_groups_to_update():
    now = datetime.utcnow()
    query = MultikeyGroup.query.filter(
        MultikeyGroup.expires > now,
        MultikeyGroup.updates <= now + timedelta(hours=1),
    )
    for group in query.all():
        update_multikey_group.delay(group.id)

@runner.task
def update_multikey_group(group_id):
    group = MultikeyGroup.query.get(group_id)
    if group:
        aws_keys = set(multikey_key.aws_key() for multikey_key in group.multikey_keys)
        if all(k is not None for k in aws_keys):
            get_reservation_forecast(aws_keys) # Populate the cache.
        group.updates = datetime.utcnow() + timedelta(hours=6)
        db.session.commit()

@runner.task
@once_per(timedelta(days=7))
def fetch_s3_bucket(bucket_name, key, secret):
    session = boto3.Session(aws_access_key_id=key,
                            aws_secret_access_key=secret)
    s3metadata.fetch(session, bucket_name, esclient, 's3bucketfile', 's3_bucket_file')

@runner.task
@periodic_task(run_every=timedelta(days=1))
def get_keys_instances_state():
    keys = AWSKey.query.all()
    unique_keys = defaultdict(list)
    for key in keys:
        unique_keys[key.key, key.secret, key.billing_bucket_name].append(key)

    for grouped_keys in unique_keys.itervalues():
        fetch_aws_instances_state.delay(grouped_keys[0])
        generate_stopped_instances_report.delay(grouped_keys[0])

@runner.task
def fetch_aws_instances_state(key):
    try:
        session = boto3.Session(aws_access_key_id=key.key,
                                aws_secret_access_key=key.secret)
    except Exception, e:
        logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))
        aws_credentials_error(key, traceback.format_exc())
        key.error_status = u"bad_key"
        db.session.commit()
        return
    now = datetime.utcnow()
    def get_instances_state():
        for region, instance in get_all_instances(session):
            yield AWSStat(key=key.key, time=now, stat='instancestate/'+instance.id, data=dict(state=instance.state['Name']))
    bulk_save(get_instances_state())

@runner.task
def generate_stopped_instances_report(key):
    try:
        session = boto3.Session(aws_access_key_id=key.key,
                                aws_secret_access_key=key.secret)
    except Exception, e:
        logging.error("[user={}][key={}] {}".format(key.user.email, key.pretty or key.key, str(e)))
        aws_credentials_error(key, traceback.format_exc())
        key.error_status = u"bad_key"
        db.session.commit()
        return

    AWSStat(key=key.key,
            time=datetime.utcnow(),
            stat='stoppedinstancesreport',
            data=get_stopped_instances_report(session, key.key)).save()

@runner.task
def send_email_alternative(email, subject, content_plain, content_html, bypass_debug=False):
    f_send_email_alternative(email, subject, content_plain, content_html, bypass_debug)

@runner.task
def send_email(email, subject, text, html, bypass_debug=False):
    f_send_email(email, subject, text, html, bypass_debug)

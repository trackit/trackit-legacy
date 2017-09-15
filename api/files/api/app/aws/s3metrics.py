from .buckets import get_s3_buckets
from ..aws import region_names
from datetime import datetime, timedelta

MAX_QUERIED_DATA_POINTS = 50850
MAX_RETURNED_DATA_POINTS = 1440
METRICS_DATA_POINT_PERIOD = 60
AGGREGATION_PERIOD = 3600
MAX_QUERIED_SECONDS = MAX_QUERIED_DATA_POINTS * METRICS_DATA_POINT_PERIOD
MAX_RETURNED_SECONDS = AGGREGATION_PERIOD * MAX_RETURNED_DATA_POINTS
CHUNK_TIMESPAN = timedelta(seconds=min(MAX_QUERIED_SECONDS,
                                       MAX_RETURNED_SECONDS))

METRICS = (('BucketSizeBytes', ('Average',)),)

STORAGE_TYPES = [
    'StandardStorage',
    'StandardIAStorage'
]

def get_bucket_metrics(session, since=None):
    region_clients = {}
    for region_name in region_names:
        for bucket in get_s3_buckets(session):
            client = region_clients.get(region_name)
            if not client:
                client = session.client('cloudwatch', region_name=region_name)
                region_clients[region_name] = client
            bucket_since = bucket['CreationDate'].replace(tzinfo=None)
            if since and since > bucket_since:
                bucket_since = since
            while bucket_since < datetime.utcnow():
                start = bucket_since
                stop = bucket_since + CHUNK_TIMESPAN
                for metric_name, stats in METRICS:
                    for storage_type in STORAGE_TYPES:
                        metrics = get_bucket_metric_type(client, metric_name, stats,
                                                           region_name, bucket, storage_type,
                                                           start, stop)
                        for metric in metrics:
                            yield metric
                bucket_since = bucket_since + CHUNK_TIMESPAN

def get_bucket_metric_type(client, name, stats, region_name, bucket, storage_type, start, stop):
    metrics = client.get_metric_statistics(
        Namespace='AWS/S3',
        MetricName=name,
        Period=AGGREGATION_PERIOD,
        StartTime=start,
        EndTime=stop,
        Statistics=stats,
        Dimensions=[{'Name': 'BucketName', 'Value': bucket['Name']},
                    {'Name': 'StorageType', 'Value': storage_type}]
    )
    for metric in metrics['Datapoints']:
        base = dict(period=AGGREGATION_PERIOD,
                    time=metric['Timestamp'],
                    resource=region_name + '/' + bucket['Name'] + '/' + storage_type)
        for stat in stats:
            base.update(metric='AWS/S3:%s:%s' % (name, stat),
                        value=metric[stat])
            yield base

from .instances import get_all_instances
from datetime import datetime, timedelta

MAX_QUERIED_DATA_POINTS = 50850
MAX_RETURNED_DATA_POINTS = 1440
METRICS_DATA_POINT_PERIOD = 60
AGGREGATION_PERIOD = 3600
MAX_QUERIED_SECONDS = MAX_QUERIED_DATA_POINTS * METRICS_DATA_POINT_PERIOD
MAX_RETURNED_SECONDS = AGGREGATION_PERIOD * MAX_RETURNED_DATA_POINTS
CHUNK_TIMESPAN = timedelta(seconds=min(MAX_QUERIED_SECONDS,
                                       MAX_RETURNED_SECONDS))
METRICS = (('CPUUtilization', ('Maximum',)),('DiskReadOps', ('Average',)),('DiskWriteOps', ('Average',)),('DiskReadBytes', ('Average',)),('DiskWriteBytes', ('Average',)),('NetworkIn', ('Average',)),('NetworkOut', ('Average',)),)
METRICS_VOLUMES = (('VolumeReadOps', ('Average',)),('VolumeWriteOps', ('Average',)),('VolumeReadBytes', ('Average',)),('VolumeWriteBytes', ('Average',)),)

def get_volume_metrics(session, since=None):
    region_clients = {}
    for region_name, instance in get_all_instances(session):
        client = region_clients.get(region_name)
        if not client:
            client = session.client('cloudwatch', region_name=region_name)
            region_clients[region_name] = client
        instance_since = instance.launch_time.replace(tzinfo=None)
        if since and since > instance_since:
            instance_since = since
        while instance_since < datetime.utcnow():
            start = instance_since
            stop = instance_since + CHUNK_TIMESPAN
            for volume in instance.volumes.all():
                for metric_name, stats in METRICS_VOLUMES:
                    metrics = get_volume_metric_type(client, metric_name, stats,
                                                     region_name, volume,
                                                     start, stop)
                    for metric in metrics:
                        yield metric
            instance_since = instance_since + CHUNK_TIMESPAN

def get_volume_metric_type(client, name, stats, region_name, volume, start, stop):
    metrics = client.get_metric_statistics(
        Namespace='AWS/EBS',
        MetricName=name,
        Period=AGGREGATION_PERIOD,
        StartTime=start,
        EndTime=stop,
        Statistics=stats,
        Dimensions=[{'Name': 'VolumeId', 'Value': volume.id}]
    )
    for metric in metrics['Datapoints']:
        base = dict(period=AGGREGATION_PERIOD,
                    time=metric['Timestamp'],
                    resource=region_name + '/' + volume.id)
        for stat in stats:
            base.update(metric='AWS/EBS:%s:%s' % (name, stat),
                        value=metric[stat])
            yield base

def get_instance_metrics(session, since=None):
    region_clients = {}
    for region_name, instance in get_all_instances(session):
        client = region_clients.get(region_name)
        if not client:
            client = session.client('cloudwatch', region_name=region_name)
            region_clients[region_name] = client
        instance_since = instance.launch_time.replace(tzinfo=None)
        if since and since > instance_since:
            instance_since = since
        while instance_since < datetime.utcnow():
            start = instance_since
            stop = instance_since + CHUNK_TIMESPAN
            for metric_name, stats in METRICS:
                metrics = get_instance_metric_type(client, metric_name, stats,
                                                   region_name, instance,
                                                   start, stop)
                for metric in metrics:
                    yield metric
            instance_since = instance_since + CHUNK_TIMESPAN

def get_instance_metric_type(client, name, stats, region_name, instance, start, stop):
    metrics = client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName=name,
        Period=AGGREGATION_PERIOD,
        StartTime=start,
        EndTime=stop,
        Statistics=stats,
        Dimensions=[{'Name': 'InstanceId', 'Value': instance.id}]
    )
    for metric in metrics['Datapoints']:
        base = dict(period=AGGREGATION_PERIOD,
                    time=metric['Timestamp'],
                    resource=region_name + '/' + instance.id)
        for stat in stats:
            base.update(metric='AWS/EC2:%s:%s' % (name, stat),
                        value=metric[stat])
            yield base

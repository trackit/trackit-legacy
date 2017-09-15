from app.gcloud.utils import refresh_credentials, get_gapi_authorized_http
from datetime import datetime, timedelta
import oauth2client
import apiclient

INSTANCE_METRICS = [
    'compute.googleapis.com/instance/cpu/utilization'
]

INSTANCE_DISK_METRICS = [
    'compute.googleapis.com/instance/disk/read_bytes_count',
    'compute.googleapis.com/instance/disk/write_bytes_count',
    'compute.googleapis.com/instance/disk/read_ops_count',
    'compute.googleapis.com/instance/disk/write_ops_count'
]

INSTANCE_NETWORK_METRICS = [
    'compute.googleapis.com/instance/network/received_bytes_count',
    'compute.googleapis.com/instance/network/sent_bytes_count'
]

def get_instance_metrics(identity, project, since=None):
    http = get_gapi_authorized_http(identity)
    google_monitoring_service = apiclient.discovery.build('cloudmonitoring', 'v2beta2', http=http)
    if not since:
        since = datetime(1970, 1, 1)
    since_string = since.isoformat("T") + '+00:00'
    for metric in INSTANCE_METRICS:
        now_string = datetime.utcnow().isoformat("T") + '+00:00'
        for metric in get_instance_metric_type(identity, project, metric, since_string, now_string):
            yield metric
    for metric in INSTANCE_DISK_METRICS:
        now_string = datetime.utcnow().isoformat("T") + '+00:00'
        for metric in get_instance_disk_metric_type(identity, project, metric, since_string, now_string):
            yield metric
    for metric in INSTANCE_NETWORK_METRICS:
        now_string = datetime.utcnow().isoformat("T") + '+00:00'
        for metric in get_instance_network_metric_type(identity, project, metric, since_string, now_string):
            yield metric

def get_instance_metric_type(identity, project, metric_name, start, stop):
    next_page_token = None
    while True:
        res = retrieve_timeseries(identity, project, metric_name, start, stop, next_page_token)

        if 'timeseries' in res:
            for t in res['timeseries']:
                resource = t['timeseriesDesc']['labels']['compute.googleapis.com/instance_name'] if 'compute.googleapis.com/instance_name' in t['timeseriesDesc']['labels'] else t['timeseriesDesc']['labels']['compute.googleapis.com/resource_id']
                base = dict(resource=resource,
                            metric='GCLOUD/COMPUTE:{}'.format(metric_name))
                for point in t['points']:
                    if 'doubleValue' in point:
                        base.update(value=point['doubleValue'],
                                    time=point['start'])
                        yield base
        if not 'nextPageToken' in res:
            break
        else:
            next_page_token = res['nextPageToken']

def get_instance_disk_metric_type(identity, project, metric_name, start, stop):
    next_page_token = None
    while True:
     res = retrieve_timeseries(identity, project, metric_name, start, stop, next_page_token)
     if 'timeseries' in res:
         for t in res['timeseries']:
             resource = t['timeseriesDesc']['labels']['compute.googleapis.com/device_name'] if 'compute.googleapis.com/device_name' in t['timeseriesDesc']['labels'] else t['timeseriesDesc']['labels']['compute.googleapis.com/resource_id']
             base = dict(resource=resource,
                         metric='GCLOUD/COMPUTE:{}'.format(metric_name))
             for point in t['points']:
                 if 'int64Value' in point:
                     base.update(value=point['int64Value'],
                                 time=point['start'])
                     yield base
     if not 'nextPageToken' in res:
         break
     else:
         next_page_token = res['nextPageToken']

def get_instance_network_metric_type(identity, project, metric_name, start, stop):
    next_page_token = None
    while True:
     res = retrieve_timeseries(identity, project, metric_name, start, stop, next_page_token)
     if 'timeseries' in res:
         for t in res['timeseries']:
             resource = t['timeseriesDesc']['labels']['compute.googleapis.com/instance_name'] if 'compute.googleapis.com/instance_name' in t['timeseriesDesc']['labels'] else t['timeseriesDesc']['labels']['compute.googleapis.com/resource_id']
             base = dict(resource=resource,
                         metric='GCLOUD/COMPUTE:{}'.format(metric_name))
             for point in t['points']:
                 if 'int64Value' in point:
                     base.update(value=point['int64Value'],
                                 time=point['start'])
                     yield base
     if not 'nextPageToken' in res:
         break
     else:
         next_page_token = res['nextPageToken']

def retrieve_timeseries(identity, project, metric_name, start, stop, next_page_token=None):
    def get_timeseries():
        http = get_gapi_authorized_http(identity)
        google_monitoring_service = apiclient.discovery.build('cloudmonitoring', 'v2beta2', http=http)
        res = google_monitoring_service.timeseries().list(project=project['code'], metric=metric_name, oldest=start, youngest=stop, pageToken=next_page_token).execute()
        return res
    try:
        timeseries = get_timeseries()
    except oauth2client.client.HttpAccessTokenRefreshError:
        refresh_credentials(identity)
        timeseries = get_timeseries()
    return timeseries

import elasticsearch_dsl as dsl
from datetime import datetime, timedelta
from . import client


class GoogleMetric(dsl.DocType):
    class Meta:
        index = 'googlemetric'
    identity = dsl.String(index='not_analyzed')
    resource = dsl.String(index='not_analyzed')
    metric = dsl.String(index='not_analyzed')
    time = dsl.Date(format='date_optional_time||epoch_millis')
    value = dsl.Double()

    @classmethod
    def daily_cpu_utilization(cls, identity_email):
        s = cls.search()
        s = s.filter('term', identity=identity_email)
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/cpu/utilization')

        agg = s.aggs.bucket('intervals', 'date_histogram', field='time', interval='day', min_doc_count=1)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for interval in res['aggregations']['intervals']['buckets']:
            yield interval['key_as_string'].split('T')[0], interval['utilization']['value']

    @classmethod
    def get_cpu_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/cpu/utilization')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_disk_read_iops_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/disk/read_ops_count')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_disk_write_iops_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/disk/write_ops_count')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_disk_read_bytes_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/disk/read_bytes_count')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_disk_write_bytes_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/disk/write_bytes_count')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_network_in_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/network/received_bytes_count')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_network_out_usage(cls, identity_email, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='GCLOUD/COMPUTE:compute.googleapis.com/instance/network/sent_bytes_count')
        s = s.filter('term', identity=identity_email)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='googlemetric', body=s.to_dict(), size=0)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

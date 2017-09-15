import elasticsearch_dsl as dsl
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from . import client, any_key_to_string_array
import calendar
import itertools


class AWSMetric(dsl.DocType):
    class Meta:
        index = 'awsmetric'
    key = dsl.String(index='not_analyzed')
    resource = dsl.String(index='not_analyzed')
    metric = dsl.String(index='not_analyzed')
    time = dsl.Date(format='date_optional_time||epoch_millis')
    period = dsl.Integer()
    value = dsl.Double()

    @classmethod
    def underutilized_resources(cls, keys, timespan=timedelta(days=30)):
        keys = any_key_to_string_array(keys)
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EC2:CPUUtilization:Maximum')
        s = s.filter('terms', key=keys)
        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('percentiles', 'percentile_ranks', field='value', values=[20, 50])
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        resources = []
        for resource in res['aggregations']['resources']['buckets']:
            if resource['percentiles']['values']['20.0'] == 100:
                res_region, res_id = resource['key'].split('/')
                resources.append(dict(
                    type='EC2 Instance',
                    id=res_id,
                    region=res_region,
                    underutilized=['CPU usage under 20%']
                ))

        return dict(resources=resources)

    @classmethod
    def hourly_cpu_usage(cls, keys, resources=None):
        s = cls.search()
        if isinstance(keys, basestring):
            keys = [keys]
        elif not isinstance(keys, list):
            keys = list(keys)
        assert all(isinstance(key, basestring) for key in keys)
        s = s.filter('terms', key=keys)
        if resources:
            s = s.filter('terms', resource=resources)
        s = s.filter('term', metric='AWS/EC2:CPUUtilization:Maximum')

        agg = s.aggs.bucket('intervals', 'date_histogram', field='time', interval='hour', min_doc_count=1)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        tmp_hours = defaultdict(list)
        for interval in res['aggregations']['intervals']['buckets']:
            interval_hour = interval['key_as_string'].split('T')[1].split(':')[0]
            tmp_hours[interval_hour].append(interval['utilization']['value'])
        hours = OrderedDict(zip(["{:02d}".format(x) for x in range(0, 24)], itertools.repeat(0)))
        for hour, values in tmp_hours.iteritems():
            hours[hour] = sum(values) / len(values)
        if not tmp_hours:
            return None
        return [dict(hour=hour, cpu=float(cpu)) for hour, cpu in hours.iteritems()]

    @classmethod
    def days_of_the_week_cpu_usage(cls, keys, resources=None):
        s = cls.search()
        if isinstance(keys, basestring):
            keys = [keys]
        elif not isinstance(keys, list):
            keys = list(keys)
        assert all(isinstance(key, basestring) for key in keys)
        s = s.filter('terms', key=keys)
        if resources:
            s = s.filter('terms', resource=resources)
        s = s.filter('term', metric='AWS/EC2:CPUUtilization:Maximum')

        agg = s.aggs.bucket('intervals', 'date_histogram', field='time', interval='day', min_doc_count=1)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        tmp_days_of_the_week = defaultdict(list)
        for interval in res['aggregations']['intervals']['buckets']:
            weekday = datetime.strptime(interval['key_as_string'].split('T')[0], '%Y-%m-%d').date().weekday()
            tmp_days_of_the_week[weekday].append(interval['utilization']['value'])
        days = OrderedDict(zip(range(0, 7), itertools.repeat(0)))
        for weekday, values in tmp_days_of_the_week.iteritems():
            days[weekday] = sum(values) / len(values)
        if not tmp_days_of_the_week:
            return None
        return [dict(day=calendar.day_name[weekday], cpu=float(cpu)) for weekday, cpu in days.iteritems()]

    @classmethod
    def daily_cpu_utilization(cls, key):
        s = cls.search()
        s = s.filter('term', key=key)
        s = s.filter('term', metric='AWS/EC2:CPUUtilization:Maximum')

        agg = s.aggs.bucket('intervals', 'date_histogram', field='time', interval='day', min_doc_count=1)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for interval in res['aggregations']['intervals']['buckets']:
            yield interval['key_as_string'].split('T')[0], interval['utilization']['value']

    @classmethod
    def get_cpu_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EC2:CPUUtilization:Maximum')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_instance_read_iops_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EC2:DiskReadOps:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_instance_write_iops_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EC2:DiskWriteOps:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_instance_read_bytes_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EBS:DiskReadBytes:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_instance_write_bytes_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EBS:DiskWriteBytes:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_volume_read_iops_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EBS:VolumeReadOps:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_volume_write_iops_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EBS:VolumeWriteOps:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_volume_read_bytes_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EBS:VolumeReadBytes:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_volume_write_bytes_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EBS:VolumeWriteBytes:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_network_in_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EC2:NetworkIn:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_network_out_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/EC2:NetworkOut:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

    @classmethod
    def get_s3_space_usage(cls, key, timespan=timedelta(days=30)):
        s = cls.search()
        s = s.filter('range', time={'gt': (datetime.utcnow() - timespan).isoformat()})
        s = s.filter('term', metric='AWS/S3:BucketSizeBytes:Average')
        s = s.filter('term', key=key)

        agg = s.aggs.bucket('resources', 'terms', field='resource', size=300)
        agg.metric('utilization', 'avg', field='value')
        res = client.search(index='awsmetric', body=s.to_dict(), size=0, request_timeout=60)

        for resource in res['aggregations']['resources']['buckets']:
            yield resource['key'], resource['utilization']['value']

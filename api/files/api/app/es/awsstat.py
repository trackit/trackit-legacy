import elasticsearch_dsl as dsl
from . import client, any_key_to_string_array


class AWSStat(dsl.DocType):
    class Meta:
        index = 'awsstat'
    key = dsl.String(index='not_analyzed')
    time = dsl.Date(format='date_optional_time||epoch_millis')
    stat = dsl.String(index='not_analyzed')
    data = dsl.Object(enabled=False)

    @classmethod
    def latest_instance_stats(cls, key):
        s = cls.search()
        s = s.filter('term', key=key)
        s = s.filter('term', stat='instances').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=10, request_timeout=60)
        stats = []
        for r in res['hits']['hits']:
            stat = r['_source']['data']
            stat.update(time=r['_source']['time'])
            stats.append(stat)
        stats.sort(key=lambda s: s['time'], reverse=True)
        return dict(stats=stats)

    @classmethod
    def get_latest_instance_states(cls, key, instance_id, days=5):
        s = cls.search()
        s = s.filter('term', key=key)
        s = s.filter('term', stat='instancestate/'+instance_id).sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=days, request_timeout=60)

        states = []
        for r in res['hits']['hits']:
            states.append(dict(time=r['_source']['time'], state=r['_source']['data']['state']))
        return states

    @classmethod
    def latest_on_demand_to_reserved_suggestion(cls, keys):
        keys = any_key_to_string_array(keys)
        s = cls.search()
        s = s.filter('terms', key=keys)
        s = s.filter('term', stat='ondemandtoreserved').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=1, request_timeout=60)

        if res['hits']['total'] > 0:
            return res['hits']['hits'][0]['_source']['data']
        return dict(total=0)

    @classmethod
    def latest_s3_space_usage(cls, keys):
        keys = any_key_to_string_array(keys)
        s = cls.search()
        s = s.filter('terms', key=keys)
        s = s.filter('term', stat='s3spaceusage').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=1, request_timeout=60)

        if res['hits']['total'] > 0:
            return res['hits']['hits'][0]['_source']['data']
        return None

    @classmethod
    def latest_available_volumes(cls, keys):
        keys = any_key_to_string_array(keys)
        s = cls.search()
        s = s.filter('terms', key=keys)
        s = s.filter('term', stat='detachedvolumes').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=1, request_timeout=60)

        if res['hits']['total'] > 0:
            return res['hits']['hits'][0]['_source']['data']
        return dict(total=0)

    @classmethod
    def latest_hourly_cpu_usage_by_tag(cls, key):
        s = cls.search()
        s = s.filter('term', key=key)
        s = s.filter('term', stat='hourlycpubytag').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=1, request_timeout=60)

        if res['hits']['total'] > 0 and 'data' in res['hits']['hits'][0]['_source']:
            return res['hits']['hits'][0]['_source']['data']
        return dict(tags=[])

    @classmethod
    def latest_daily_cpu_usage_by_tag(cls, key):
        s = cls.search()
        s = s.filter('term', key=key)
        s = s.filter('term', stat='dailycpubytag').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=1, request_timeout=60)

        if res['hits']['total'] > 0 and 'data' in res['hits']['hits'][0]['_source']:
            return res['hits']['hits'][0]['_source']['data']
        return dict(tags=[])

    @classmethod
    def latest_stopped_instances_report(cls, keys):
        keys = any_key_to_string_array(keys)
        s = cls.search()
        s = s.filter('terms', key=keys)
        s = s.filter('term', stat='stoppedinstancesreport').sort('-time')
        res = client.search(index='awsstat', body=s.to_dict(), size=1, request_timeout=60)

        if res['hits']['total'] > 0:
            return res['hits']['hits'][0]['_source']['data']
        return dict(total=0)

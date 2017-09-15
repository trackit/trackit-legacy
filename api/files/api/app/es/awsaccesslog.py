import elasticsearch_dsl as dsl
from . import client


class AWSAccessLog(dsl.DocType):
    class Meta:
        index = 'awsaccesslog'
    key = dsl.String(index='not_analyzed')
    resource = dsl.String(index='not_analyzed')
    time = dsl.Date(format='date_optional_time||epoch_millis')
    period = dsl.Integer()
    bucket = dsl.String(index='not_analyzed')
    object = dsl.String(index='not_analyzed')

    @classmethod
    def most_accessed_s3_objects(cls, key):
        s = cls.search()
        s = s.filter('term', key=key)
        agg = s.aggs.bucket('objects', 'terms', field='object')
        agg.bucket('buckets', 'terms', field='bucket')
        res = client.search(index='awsaccesslog', body=s.to_dict(), request_timeout=60)

        objects = []
        for object in res['aggregations']['objects']['buckets']:
             objects.append(dict(
                 bucket=object['buckets']['buckets'][0]['key'],
                 object=object['key'],
                 access_count=object['doc_count']
             ))
        return dict(objects=objects)

    @classmethod
    def last_accessed_s3_objects(cls, key):
        s = cls.search()
        s = s.filter('term', key=key)
        agg = s.aggs.bucket('objects', 'terms', field='object')
        res = client.search(index='awsaccesslog', body=s.to_dict(), request_timeout=60)
        objects = []
        for object in res['aggregations']['objects']['buckets']:
            s2 = cls.search()
            s2 = s2.query("match", object=object['key'])
            s2 = s2.sort('-time')
            res2 = client.search(index='awsaccesslog', body=s2.to_dict(), request_timeout=60)
            objects.append(dict(
                object=object['key'],
                bucket=res2['hits']['hits'][0]['_source']['bucket'],
                last_access=res2['hits']['hits'][0]['_source']['time']
            ))
        return dict(objects=objects)

    @classmethod
    def last_access_s3_bucket(cls, key, bucket):
        s = cls.search()
        s = s.filter('term', key=key).filter('term', bucket=bucket)
        s.sort('-time')
        res = client.search(index='awsaccesslog', body=s.to_dict(), request_timeout=60)
        if res['hits']['total'] > 0:
            return res['hits']['hits'][0]['_source']['time']
        else:
            return 'never_accessed'

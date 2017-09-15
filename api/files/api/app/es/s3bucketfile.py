import elasticsearch_dsl as dsl
import re
from . import client, directory_analyzer, tag_key_analyzer


class S3BucketFile(dsl.DocType):
    class Meta:
        index = 's3bucketfile'
    bucket = dsl.String(index='not_analyzed')
    key = dsl.String(index='not_analyzed',
                     fields={'path': dsl.String(analyzer=directory_analyzer)})
    tags = dsl.String(index='not_analyzed',
                      fields={'key': dsl.String(analyzer=tag_key_analyzer)})
    size = dsl.Integer()
    modified = dsl.Date(format='date_optional_time||epoch_millis')

    @classmethod
    def get_bucket_sizes(cls, buckets):
        s = cls.search()
        s = s.filter('terms', bucket=buckets)
        agg = s.aggs.bucket('buckets', 'terms', field='bucket', size=len(buckets))
        agg.metric('size', 'sum', field='size')
        res = client.search(index='s3bucketfile', body=s.to_dict(), size=0)
        for bucket in res['aggregations']['buckets']['buckets']:
            yield bucket['key'], bucket['size']['value']

    @classmethod
    def get_dir_sizes(cls, bucket, path=None):
        s = cls.search()
        s = s.filter('term', bucket=bucket)
        if path:
            s = s.filter({'term': {'key.path': path}})
        path_regex = '[^/]+'
        if path:
            path_regex = path + '/' + path_regex
        agg = s.aggs.bucket('dirs', 'terms', field='key.path', size=1000, include=path_regex)
        agg.metric('size', 'sum', field='size')
        res = client.search(index='s3bucketfile', body=s.to_dict(), size=0)
        for directory in res['aggregations']['dirs']['buckets']:
            key = directory['key']
            if path:
                key = key.replace(path, '')
                if key.startswith('/'):
                    key = key[1:]
            yield key, directory['size']['value']

    @classmethod
    def get_bucket_tags(cls, buckets, tags=[], tagkey=None):
        return cls.get_dir_tags(buckets, tags=tags, tagkey=tagkey)

    @classmethod
    def get_dir_tags(cls, buckets, path=None, tags=[], tagkey=None):
        s = cls.search()
        if isinstance(buckets, list):
            s = s.filter('terms', bucket=buckets)
        else:
            s = s.filter('term', bucket=buckets)
        if path:
            s = s.filter({'term': {'key.path': path}})
        if tags:
            s = s.filter('terms', tags=tags)
        if tagkey:
            agg = s.aggs.bucket('tags', 'terms', field='tags', include=re.escape(tagkey) + '=.*', size=500)
        else:
            agg = s.aggs.bucket('tags', 'terms', field='tags', size=500)
        agg.metric('size', 'sum', field='size')
        s.aggs.bucket('tagkeys', 'terms', field='tags.key', size=100)

        res = client.search(index='s3bucketfile', body=s.to_dict(), size=0)
        tags_agg = res['aggregations']['tags']['buckets']
        tags = dict((b['key'], b['size']['value']) for b in tags_agg)
        tagkeys = [b['key'] for b in res['aggregations']['tagkeys']['buckets']]
        return tags, tagkeys

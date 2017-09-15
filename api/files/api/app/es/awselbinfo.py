import elasticsearch_dsl as dsl
from . import client


class AWSELBInfo(dsl.DocType):
    class Meta:
        index = 'awselbinfo'
    linked_account_id = dsl.String(index='not_analyzed')
    name = dsl.String(index='not_analyzed')
    region = dsl.String(index='not_analyzed')
    instances = dsl.String()

    @classmethod
    def init(cls, index=None, using=None):
        client.indices.create('awselbinfo', ignore=400)
        client.indices.put_mapping(index='awselbinfo', doc_type='a_ws_el_binfo', body={'_ttl': {'enabled': True}})
        cls._doc_type.init(index, using)

    @classmethod
    def get_elb_info(cls, key):
        s = cls.search()
        s = s.filter('term', linked_account_id=key)
        s = s.sort('-_ttl')
        res = client.search(index='awselbinfo', body=s.to_dict(), size=10000, request_timeout=60)
        if res['hits']['total'] == 0:
            return []
        return [
            {
                'instances': elb['_source']['instances'].split(' '),
                'name': elb['_source']['name'],
                'region': elb['_source']['region'],
            }
            for elb in res['hits']['hits']
        ]

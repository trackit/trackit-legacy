import elasticsearch_dsl as dsl
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from fractions import Fraction
from app.cache import with_cache
from awsstat import AWSStat
from app.aws import lambdapricing
from . import client, SHORT_NAMES
import calendar


class AWSDetailedLineitem(dsl.DocType):
    class Meta:
        index = 'awsdetailedlineitem'
    availability_zone = dsl.String(index='not_analyzed')
    cost = dsl.Double()
    un_blended_cost = dsl.Double()
    item_description = dsl.String(index='not_analyzed')
    linked_account_id = dsl.String(index='not_analyzed')
    operation = dsl.String()
    payer_account_id = dsl.String(index='not_analyzed')
    pricing_plan_id = dsl.Long()
    product_name = dsl.String(index='not_analyzed')
    rate = dsl.Double()
    un_blended_rate = dsl.Double()
    rate_id = dsl.Long()
    record_id = dsl.String(index='not_analyzed')
    reserved_instance = dsl.Boolean()
    resource_id = dsl.String(index='not_analyzed')
    subscription_id = dsl.Long()
    tag = dsl.Object(
        properties={
            'key': dsl.String(index='not_analyzed'),
            'value': dsl.String(index='not_analyzed')
        }
    )
    usage_end_date = dsl.Date(format='strict_date_optional_time||epoch_millis')
    usage_quantity = dsl.Double()
    usage_start_date = dsl.Date(format='strict_date_optional_time||epoch_millis')
    usage_type = dsl.String(index='not_analyzed')

    @classmethod
    @with_cache(ttl=3600 * 3, worker_refresh=True)
    def keys_has_data(cls, keys, date_from=None, date_to=None):
        date_to = date_to or datetime.utcnow()
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        if date_from:
            s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)
        return res['hits']['total'] > 0

    @classmethod
    @with_cache(is_json=False, ret=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    def get_first_date(cls, keys):
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.sort('usage_start_date')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=1, request_timeout=60)
        if res['hits']['total'] == 0:
            return
        return res['hits']['hits'][0]['_source']['usage_start_date'].split('T')[0]

    @classmethod
    @with_cache(is_json=False, ret=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    def get_last_date(cls, keys, limit=None):
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        if limit:
            s = s.filter('range', usage_start_date={'to': limit.isoformat()})
        s = s.sort('-usage_start_date')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=1, request_timeout=60)
        if res['hits']['total'] == 0:
            return
        return res['hits']['hits'][0]['_source']['usage_start_date'].split('T')[0]

    @classmethod
    def get_first_to_now_date(cls, keys):
        def from_date_to_today(d):
            now = datetime.utcnow()
            while d < now:
                yield d
                d += relativedelta(months=1)
        return list(from_date_to_today(cls.get_first_date(keys)))

    @classmethod
    def get_first_to_last_date(cls, keys):
        def from_date_to_last(d):
            last = cls.get_last_date(keys)
            while d < last:
                yield d
                d += relativedelta(months=1)
        return list(from_date_to_last(cls.get_first_date(keys)))

    @classmethod
    @with_cache(6 * 3600)
    def get_available_tags(cls, keys, only_with_data=None):
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s.aggs.bucket('tag_key', 'terms', field='tag.key')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        tags = []
        for tag in res['aggregations']['tag_key']['buckets']:
            if tag['key'].startswith('user:'):
                name = tag['key'].split(':')[1]
                if not only_with_data or name in AWSStat.latest_hourly_cpu_usage_by_tag(only_with_data)['tags'] or name in AWSStat.latest_daily_cpu_usage_by_tag(only_with_data)['tags']:
                    tags.append(name)
        tags.sort()
        return dict(tags=tags)

    @classmethod
    @with_cache(ttl=6 * 3600)
    def get_cost_by_tag(cls, keys, tag, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('term', **{'tag.key': 'user:{}'.format(tag)})
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        s.aggs.bucket('total_cost', 'sum', field='cost')
        agg = s.aggs.bucket('tag_value', 'terms', field='tag.value', size=0x7FFFFFFF)
        agg.bucket('cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        tags = [
            {
                'tag_value': tag['key'],
                'cost': tag['cost']['value'],
            } for tag in res['aggregations']['tag_value']['buckets']
        ]
        return dict(tags=tags, total_cost=res['aggregations']['total_cost']['value'])

    @classmethod
    @with_cache(ttl=6 * 3600)
    def get_cost(cls, keys, date_from, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        s.aggs.bucket('total_cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        return dict(total_cost=res['aggregations']['total_cost']['value'])

    @classmethod
    @with_cache()
    def get_monthly_cost_by_tag(cls, keys, tag, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('term', **{'tag.key': 'user:{}'.format(tag)})
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('intervals', 'date_histogram', field='usage_start_date', interval='month', min_doc_count=1)
        agg.bucket('total_cost', 'sum', field='cost')
        agg = agg.bucket('tag_value', 'terms', field='tag.value', size=0x7FFFFFFF)
        agg.bucket('cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        months = [
            {
                'month': interval['key_as_string'].split('T')[0][:-3],
                'tags': [
                     {
                         'tag_value': tag['key'],
                         'cost': tag['cost']['value'],
                     } for tag in interval['tag_value']['buckets']],
                'total_cost': interval['total_cost']['value'],
            } for interval in res['aggregations']['intervals']['buckets']
        ]
        return dict(months=months)

    @classmethod
    @with_cache()
    def get_cost_by_product(cls, key, date_from=None, date_to=None, without_discount=False, only_discount=False, size=0x7FFFFFFF):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('term', linked_account_id=key)
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        if without_discount:
            s = s.query('bool', filter=[~dsl.Q('term', item_description='PAR_APN_ProgramFee_2500')])
        if only_discount:
            s = s.filter('term', item_description='PAR_APN_ProgramFee_2500')
        agg = s.aggs.bucket('products', 'terms', field='product_name', order={'cost': 'desc'}, size=size)
        agg.bucket('cost', 'sum', field='cost')
        s = s.query('bool', filter=[~dsl.Q('term', cost=0)])
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        products = [
            {
                'product': SHORT_NAMES.get(product['key'], product['key']),
                'cost': product['cost']['value'],
            } for product in res['aggregations']['products']['buckets']
        ]
        return dict(products=products)

    @classmethod
    @with_cache()
    def get_cost_by_region(cls, keys, tagged=False, byaccount=False, date_from=None, date_to=None, size=0x7FFFFFFF):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})

        agg = s.aggs
        if byaccount:
            agg = agg.bucket('accounts', 'terms', field='linked_account_id')
        agg = agg.bucket('intervals', 'date_histogram', field='usage_start_date', interval='month', min_doc_count=1)
        agg = agg.bucket('regions', 'terms', field='availability_zone', size=size)
        agg.bucket('cost', 'sum', field='cost')
        if tagged:
            agg = agg.bucket('tags', 'terms', field='tag.value')
            agg.bucket('cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0)

        return res['aggregations']

    @classmethod
    @with_cache()
    def get_monthly_cost(cls, keys, date_from=None, date_to=None, size=0x7FFFFFFF):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(day=calendar.monthrange(date_from.year, date_from.month)[1], hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('intervals', 'date_histogram', field='usage_start_date', interval='month', min_doc_count=1)
        agg.bucket('cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        res = [
            {
                'month': interval['key_as_string'].split('T')[0],
                'total_cost': interval['cost']['value'],
            } for interval in res['aggregations']['intervals']['buckets']
        ]
        return dict(months=res)

    @classmethod
    @with_cache()
    def get_monthly_cost_by_product(cls, keys, tagged=False, date_from=None, date_to=None, size=0x7FFFFFFF):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(day=calendar.monthrange(date_from.year, date_from.month)[1], hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('intervals', 'date_histogram', field='usage_start_date', interval='month', min_doc_count=1)
        agg = agg.bucket('products', 'terms', field='product_name', size=size)
        agg.bucket('cost', 'sum', field='cost')
        if tagged:
            agg = agg.bucket('tags', 'terms', field='tag.value')
            agg.bucket('cost', 'sum', field='cost')
        s = s.query('bool', filter=[~dsl.Q('term', cost=0)])
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        def tagged_cost(bucket, total):
            total_tag = 0.0
            for tag in bucket:
                total_tag += tag['cost']['value']
                yield (tag['key'], tag['cost']['value'])
            if total != total_tag:
                yield ('untagged', total - total_tag)

        res = [
            {
                'month': interval['key_as_string'].split('T')[0],
                'products': [
                     {
                         'product': SHORT_NAMES.get(product['key'], product['key']),
                         'cost': product['cost']['value'],
                         'tags': [
                             {
                                 'name': tag[0],
                                 'cost': tag[1],
                             }
                             for tag in tagged_cost(product['tags']['buckets'], product['cost']['value'])
                         ],
                     } for product in interval['products']['buckets']] if tagged else
                [
                    {
                        'product': SHORT_NAMES.get(product['key'], product['key']),
                        'cost': product['cost']['value'],
                    } for product in interval['products']['buckets']]
            } for interval in res['aggregations']['intervals']['buckets']
        ]
        return dict(months=res)

    @classmethod
    @with_cache(ttl=4 * 3600)
    def get_daily_cost_by_product(cls, keys, date_from=None, date_to=None, size=0x7FFFFFFF):
        date_from = date_from or datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('intervals', 'date_histogram', field='usage_start_date', interval='day', min_doc_count=1)
        agg = agg.bucket('products', 'terms', field='product_name', size=size)
        agg.metric('cost', 'sum', field='cost')
        s = s.query('bool', filter=[~dsl.Q('term', cost=0)])
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        res = [
            {
                'day': interval['key_as_string'].split('T')[0],
                'products': [
                     {
                         'product': SHORT_NAMES.get(product['key'], product['key']),
                         'cost': product['cost']['value'],
                     } for product in interval['products']['buckets']]
            } for interval in res['aggregations']['intervals']['buckets']
        ]
        return dict(days=res)

    @classmethod
    @with_cache(ttl=24 * 3600)
    def get_yearly_cost_by_product(cls, keys, date_from=None, date_to=None, size=0x7FFFFFFF):
        date_from = date_from or datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('intervals', 'date_histogram', field='usage_start_date', interval='year', min_doc_count=1)
        agg = agg.bucket('products', 'terms', field='product_name', size=size)
        agg.metric('cost', 'sum', field='cost')
        s = s.query('bool', filter=[~dsl.Q('term', cost=0)])
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        res = [
            {
                'year': interval['key_as_string'][:4],
                'products': [
                     {
                         'product': SHORT_NAMES.get(product['key'], product['key']),
                         'cost': product['cost']['value'],
                     } for product in interval['products']['buckets']]
            } for interval in res['aggregations']['intervals']['buckets']
        ]
        return dict(years=res)

    @classmethod
    @with_cache()
    def get_cost_by_resource(cls, keys, date_from=None, date_to=None, search=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        if search:
            s = s.query('wildcard', resource_id='*{}*'.format(search))
        agg = s.aggs.bucket('resources', 'terms', field='resource_id', order={'cost': 'desc'}, size=0x7FFFFFFF)
        agg.bucket('cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        resources = [
            {
                'resource': resource['key'],
                'cost': resource['cost']['value'],
            } for resource in res['aggregations']['resources']['buckets']
        ]
        return resources

    @classmethod
    def get_monthly_cost_by_resource(cls, resource_ids, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        if resource_ids:
            s = cls.search()
            s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
            s = s.filter('terms', resource_id=list(resource_ids))
            agg = s.aggs.bucket('months', 'date_histogram', field='usage_start_date', interval='month', min_doc_count=1)
            agg.metric('cost', 'sum', field='cost')
            r = client.search('awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)
            return {
                e['key_as_string']: e['cost']['value']
                for e in r['aggregations']['months']['buckets']
            }
        else:
            return {}

    @classmethod
    @with_cache()
    def get_lambda_usage(cls, keys, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('term', product_name='AWS Lambda')
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('resources', 'terms', field='resource_id', size=0x7FFFFFFF)
        agg.metric('cost', 'avg', field='cost')
        agg = agg.bucket('types', 'terms', field='usage_type', size=0x7FFFFFFF)
        agg.metric('quantity', 'sum', field='usage_quantity')
        agg = agg.bucket('descriptions', 'terms', field='item_description', size=0x7FFFFFFF)
        agg.metric('quantity', 'sum', field='usage_quantity')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)
        #return res

        def _lambda_usage_regb(buckets, endswith):
            for b in buckets:
                if b['key'].endswith(endswith):
                    return b['quantity']['value']

        usages = [
            {
                'rid': usage['key'],
                'name': usage['key'].split(':')[-1],
                'requests': _lambda_usage_regb(usage['types']['buckets'], '-Request'),
                'gb_seconds': _lambda_usage_regb(usage['types']['buckets'], '-Lambda-GB-Second'),
                'cost': usage['cost']['value'],
                'raw_cost': lambdapricing.get_raw_cost([x['descriptions']['buckets'] for x in usage['types']['buckets']]),
            } for usage in res['aggregations']['resources']['buckets']
        ]
        return usages

    @classmethod
    @with_cache()
    def get_s3_bandwidth_costs(cls, key, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('term', linked_account_id=key)
        s = s.filter('term', product_name='Amazon Simple Storage Service')
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('types', 'terms', field='usage_type', size=0x7FFFFFFF)
        agg.metric('cost', 'sum', field='cost')
        agg.metric('gb', 'sum', field='usage_quantity')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        transfers = [
            {
                'type': transfer['key'],
                'quantity': transfer['gb']['value'],
                'cost': transfer['cost']['value'],
            } for transfer in res['aggregations']['types']['buckets']
        ]
        return transfers

    @classmethod
    @with_cache()
    def get_ec2_bandwidth_costs(cls, key, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('term', linked_account_id=key)
        s = s.filter('term', product_name='Amazon Elastic Compute Cloud')
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        agg = s.aggs.bucket('types', 'terms', field='usage_type', size=0x7FFFFFFF)
        agg.metric('cost', 'sum', field='cost')
        agg.metric('gb', 'sum', field='usage_quantity')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        transfers = [
            {
                'type': transfer['key'],
                'quantity': transfer['gb']['value'],
                'cost': transfer['cost']['value'],
            } for transfer in res['aggregations']['types']['buckets']
        ]
        return transfers

    @classmethod
    def get_ec2_daily_cost(cls, key):
        s = cls.search()
        s = s.filter('term', linked_account_id=key)
        s = s.filter('term', product_name='Amazon Elastic Compute Cloud')

        agg = s.aggs.bucket('intervals', 'date_histogram', field='usage_start_date', interval='day', min_doc_count=1)
        agg.metric('cost', 'sum', field='cost')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        for interval in res['aggregations']['intervals']['buckets']:
            yield interval['key_as_string'].split('T')[0], interval['cost']['value']

    @classmethod
    @with_cache()
    def get_elb_usage_a_day(cls, keys, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        gib = Fraction(2 ** 30)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        s = s.filter("prefix", resource_id="arn:aws:elasticloadbalancing")
        s = s.sort({"usage_start_date": {"order": "desc"}})
        agg = s.aggs.bucket('rid', 'terms', field='resource_id', size=0x7FFFFFFF)
        agg.metric('cost', 'sum', field='cost')
        agg = agg.bucket('types', 'terms', field='usage_type', size=0x7FFFFFFF)
        agg.metric('quantity', 'sum', field='usage_quantity')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)
        elbs = [
            {
                'rid': elb['key'],
                'cost': elb['cost']['value'] / (date_to - date_from).days,
                'hours': float(sum([
                    x['quantity']['value']
                    for x in elb['types']['buckets']
                    if x['key'].endswith('LoadBalancerUsage')
                ]) / (date_to - date_from).days),
                'bytes': float((sum([
                    x['quantity']['value']
                    for x in elb['types']['buckets']
                    if x['key'].endswith('Bytes')
                ]) * gib) / (date_to - date_from).days),
            }
            for elb in res['aggregations']['rid']['buckets']
        ]
        return elbs

    @classmethod
    @with_cache()
    def get_instance_type(cls, keys, date_from=None, date_to=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.extra(_source=['usage_start_date', 'usage_type', 'availability_zone', 'resource_id'])
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        s = s.filter("term", product_name='Amazon Elastic Compute Cloud')
        s = s.query('wildcard', usage_type='*BoxUsage:*')
        s = s.filter('exists', field='resource_id')
        s = s.sort({"usage_start_date": {"order": "desc"}})
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=10000, request_timeout=60)

        def cut_region_name(s):
            return s[:-1] if s[-1].isalpha() else s
        types = []
        refs = {}
        def add_in_types(type, rid):
            ref_tuple = (type['hour'], type['instance'], type['region'])
            if ref_tuple in refs:
                refs[ref_tuple]['rids'].append(rid)
                refs[ref_tuple]['ridCount'] += 1
                return
            type['rids'] = [rid]
            types.append(type)
            refs[ref_tuple] = types[-1]

        for r in res['hits']['hits']:
            elem = {
                'hour': r['_source']['usage_start_date'],
                'instance': r['_source']['usage_type'].split(':')[1],
                'region': cut_region_name(r['_source']['availability_zone']) if 'availability_zone' in r['_source'] else 'unknown',
                'ridCount': 1,
            }
            add_in_types(elem, r['_source']['resource_id'])
        return types

    @classmethod
    @with_cache()
    def get_instance_hour(cls, keys, date_from=None, date_to=None, min_hour=None):
        date_from = date_from or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        s = s.filter("term", product_name='Amazon Elastic Compute Cloud')
        s = s.filter('prefix', resource_id='i-')
        s = s.query('wildcard', usage_type='*BoxUsage*')
        agg = s.aggs.bucket('resource_id', 'terms', field='resource_id', size=0x7FFFFFFF)
        agg.bucket('days', 'date_histogram', field='usage_start_date', interval='day', min_doc_count=1)
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        instance_list = []
        for instance in res['aggregations']['resource_id']['buckets']:
            tmp_hours = []
            for day in instance['days']['buckets']:
                tmp_hours.append(day['doc_count'])
            avg_hours = sum(tmp_hours) / float(len(tmp_hours))
            if not min_hour or avg_hours >= min_hour:
                instance_list.append(dict(id=instance['key'], hours=avg_hours))
        return sorted(instance_list, key=lambda x: x['hours'], reverse=True)

    @classmethod
    @with_cache()
    def get_s3_buckets_per_tag(cls, keys):
        def _check_if_in_list(dict_list, value, key):
            return next((item for item in dict_list if item[key] == value), None)

        def _parse_tag_keys_results(res):
            bucket_tagged = []
            for bucket_tag_key in res['aggregations']['tag_key']['buckets']:
                buff_tag_key = _check_if_in_list(bucket_tagged, bucket_tag_key['key'], 'tag_key')
                if buff_tag_key is None:
                    buff_tag_key = {
                        "tag_key": bucket_tag_key['key'],
                        "tag_value": []
                    }
                buff_tag_key = _parse_tag_values_results(bucket_tag_key, buff_tag_key)
                bucket_tagged.append(buff_tag_key)
            return bucket_tagged

        def _parse_tag_values_results(bucket_tag_key, buff_tag_key):
            for bucket_tag_value in bucket_tag_key['tag_value']['buckets']:
                buff_tag_value = _check_if_in_list(buff_tag_key['tag_value'], bucket_tag_value['key'], 'tag_value')
                if buff_tag_value is None:
                    buff_tag_value = {
                        "tag_value": bucket_tag_value['key'],
                        "s3_buckets": []
                    }
                buff_tag_value = _parse_buckets_results(buff_tag_value, bucket_tag_value)
                buff_tag_key['tag_value'].append(buff_tag_value)
            return buff_tag_key

        def _parse_buckets_results(buff_tag_value, bucket_tag_value):
            for bucket_resource_id in bucket_tag_value['ressource_id']['buckets']:
                buff_bucket_resource_id = _check_if_in_list(buff_tag_value['s3_buckets'], bucket_resource_id['key'], 'bucket_name')
                if buff_bucket_resource_id is None:
                    buff_bucket_resource_id = {
                        "bucket_name": bucket_resource_id['key'],
                        "account_id": bucket_resource_id['account_id']['buckets'][0]['key']
                    }
                buff_tag_value['s3_buckets'].append(buff_bucket_resource_id)
            return buff_tag_value

        s = cls.search()
        s = s.filter('terms', linked_account_id=keys if isinstance(keys, list) else [keys])
        s = s.filter('term', product_name='Amazon Simple Storage Service')
        s = s.query('exists', field="tag")
        s = s.query('wildcard', item_description="*storage*")
        agg = s.aggs.bucket('tag_key', 'terms', field="tag.key")
        agg = agg.bucket('tag_value', 'terms', field='tag.value')
        agg.bucket('ressource_id', 'terms', field='resource_id').bucket('account_id', 'terms', field='linked_account_id')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)

        '''
        bucket_tagged structure
        [{
            "tag_key" : "KEY", # Unique in list
            "tag_value": [{
                "tag_value": "VALUE", # Unique in list
                "s3_buckets": [{
                    "bucket_name": "BUCKET_NAME",
                    "account_id": "ACCOUND_ID"
                }, {...}]
            }, {...}]
        }, {...}]
        '''

        bucket_tagged = _parse_tag_keys_results(res)
        return bucket_tagged

    @classmethod
    @with_cache()
    def get_s3_bandwith_info_and_cost_per_name(cls, key, bucket_resource_ids, date_from=None, date_to=None):
        date_from = date_from or (datetime.utcnow() - relativedelta(month=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to or date_from.replace(
            day=calendar.monthrange(date_from.year, date_from.month)[1],
            hour=23, minute=59, second=59, microsecond=999999)
        s = cls.search()
        s = s.filter('term', linked_account_id=key)
        s = s.filter('term', product_name='Amazon Simple Storage Service')
        s = s.filter('terms', resource_id=bucket_resource_ids if isinstance(bucket_resource_ids, list) else [bucket_resource_ids])
        s = s.filter('range', usage_start_date={'from': date_from.isoformat(), 'to': date_to.isoformat()})
        s = s.filter('wildcard', usage_type="*Bytes")
        agg = s.aggs.bucket('bucket_name', 'terms', field='resource_id', size=0x7FFFFFFF)
        agg.metric('cost', 'sum', field='cost')
        agg = agg.bucket('transfer_type', 'terms', field='usage_type')
        agg.metric('data', 'sum', field='usage_quantity')
        res = client.search(index='awsdetailedlineitem', body=s.to_dict(), size=0, request_timeout=60)
        data = [{
            "bucket_name": bucket['key'],
            "cost": bucket['cost']['value'],
            "transfer_stats": [{
                "type": transfer_stat['key'],
                "data": transfer_stat['data']['value']
                }
                for transfer_stat in bucket['transfer_type']['buckets']
            ]
            }
            for bucket in res['aggregations']['bucket_name']['buckets']
        ]
        return data

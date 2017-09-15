import elasticsearch_dsl as dsl
from datetime import datetime, timedelta
from collections import defaultdict
from . import client, get_google_uri_name


class GoogleDailyResource(dsl.DocType):
    class Meta:
        index = 'googledailyresource'
    identity = dsl.String(index='not_analyzed')
    rid = dsl.String(index='not_analyzed')
    product = dsl.String(index='not_analyzed')
    project_name = dsl.String(index='not_analyzed')
    date = dsl.Date(format='date_optional_time||epoch_millis')
    cost = dsl.Double()

    @classmethod
    def daily_compute_cost(cls, identity_email):
        s = cls.search()
        s = s.filter('term', identity=identity_email)
        s = s.filter('term', product='com.google.cloud/services/compute-engine')

        agg = s.aggs.bucket('intervals', 'date_histogram', field='date', interval='day', min_doc_count=1)
        agg.metric('cost', 'sum', field='cost')
        res = client.search(index='googledailyresource', body=s.to_dict(), size=0)

        for interval in res['aggregations']['intervals']['buckets']:
            yield interval['key_as_string'].split('T')[0], interval['cost']['value']

    @classmethod
    def daily_cost_by_product(cls, identity_email, timespan=timedelta(days=7), top=4):
        now = datetime.utcnow()
        rollup = cls.rollup_by_product(identity_email, now - timespan, now, 'day', top)

        days = defaultdict(list)
        for interval, product, cost in rollup:
            days[interval.split('T')[0]].append(dict(cost=cost, product=get_google_uri_name(product)))

        res = dict(days=[dict(day=d, products=ps) for d, ps in days.items()])
        res['days'] = sorted(res['days'], key=lambda x: x['day'])
        return res

    @classmethod
    def month_cost_by_product(cls, identity_email, top=4):
        now = datetime.utcnow()
        rollup = cls.rollup_by_product(identity_email, datetime(now.year, now.month, 1), datetime.utcnow(), 'month', top)
        month = {'products': []}
        for interval, product, cost in rollup:
            month['month'] = '-'.join(interval.split('-')[:2])
            month['products'].append(dict(cost=cost, product=get_google_uri_name(product)))

        return month

    @classmethod
    def range_query(cls, identity_email, start, stop):
        s = cls.search()
        s = s.filter('term', identity=identity_email)
        s = s.filter('range', date={'gt': start.isoformat(), 'lte': stop.isoformat()})
        return s

    @classmethod
    def rollup_by_product(cls, identity_email, start, stop, interval, top):
        s = cls.range_query(identity_email, start, stop)
        agg = s.aggs.bucket('intervals', 'date_histogram', field='date', interval=interval, min_doc_count=1)
        agg.bucket('product', 'terms', field='product').metric('cost', 'sum', field='cost')
        res = client.search(index='googledailyresource', body=s.to_dict(), size=0)

        product_costs = defaultdict(float)
        for interval in res['aggregations']['intervals']['buckets']:
         for product in interval['product']['buckets']:
             product_costs[product['key']] += product['cost']['value']

        top_prods = set(sorted(product_costs, key=lambda p: product_costs[p], reverse=True)[:top])
        interval_prods = defaultdict(set)

        for interval in res['aggregations']['intervals']['buckets']:
         for product in interval['product']['buckets']:
             if product['key'] in top_prods:
                 yield interval['key_as_string'], product['key'], product['cost']['value']
                 interval_prods[interval['key_as_string']].add(product['key'])

        for interval, prods in interval_prods.items():
         missing = top_prods - prods
         for prod in missing:
             yield interval, prod, 0.0

    @classmethod
    def monthly_aggregates_resource(cls, identity_email):
        s = cls.search()
        s = s.filter('term', identity=identity_email)
        agg = s.aggs.bucket('months', 'date_histogram', field='date', interval='month', min_doc_count=1)
        agg.bucket('rid', 'terms', field='rid', size=0x7FFFFFFF).metric('cost', 'sum', field='cost')
        res = client.search(index='googledailyresource', body=s.to_dict(), size=0)

        months = []
        for month in res['aggregations']['months']['buckets']:
            resources = []
            for resource in month['rid']['buckets']:
                resources.append(dict(cost=resource['cost']['value'],
                                     resource=resource['key']))
            if resources == []:
                continue
            months.append(dict(month=month['key_as_string'].split('T')[0],
                               resources=resources))

        return dict(months=months)

    @classmethod
    def monthly_aggregates_project(cls, identity_email):
        s = cls.search()
        s = s.filter('term', identity=identity_email)
        agg = s.aggs.bucket('months', 'date_histogram', field='date', interval='month', min_doc_count=1)
        agg.bucket('project_name', 'terms', field='project_name', size=0x7FFFFFFF).metric('cost', 'sum', field='cost')
        res = client.search(index='googledailyresource', body=s.to_dict(), size=0)

        months = []
        for month in res['aggregations']['months']['buckets']:
            projects = []
            for project in month['project_name']['buckets']:
                projects.append(dict(cost=project['cost']['value'],
                                     project=project['key']))
            if projects == []:
                continue
            months.append(dict(month=month['key_as_string'].split('T')[0],
                               projects=projects))

        return dict(months=months)

from datetime import datetime
from app import app
from app.authentication import with_login
from flask import Blueprint, jsonify, request, Response
from app.generate_csv import generate_csv_clean
from app.msol_util import get_next_update_estimation_message_aws
from app.es.awsmetric import AWSMetric
from app.es.awsstat import AWSStat
from app.es.awsdetailedlineitem import AWSDetailedLineitem
from app.aws_keys import with_multiple_aws_accounts
from dateutil.relativedelta import relativedelta
from app.generate_csv import generate_csv
from app.cache import compressed_json, decompressed_json, cache, with_cache
from hashlib import sha256
from .. import AWS_KEY_PROCESSING_INTERVAL_HOURS
import itertools
import calendar
import config

aws_cost_stats_bp = Blueprint('aws_cost_stats_bp', __name__)


def cut_cost_by_product(products, cut):
    res = []
    other = {'product': 'Other Services', 'cost': 0}
    i = 0
    for p in products:
        if i < cut and p['cost'] >= 0.01:
            res.append(p)
        else:
            other['cost'] += p['cost']
        i += 1
    if other['cost'] >= 0.01:
        res.append(other)
    return res


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycost', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycost/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycost(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    total_cost:
                                        type: number
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=nb_months - 1)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1],
                          hour=23, minute=59, second=59, microsecond=999999)
    data = AWSDetailedLineitem.get_monthly_cost(keys=[account.get_aws_user_id() for account in accounts],
                                                    date_from=date_from,
                                                    date_to=date_to)
    return jsonify(data)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyregion', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyregion/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycostbyregion(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs summed by region
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                region:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=nb_months - 1)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1],
                                hour=23, minute=59, second=59, microsecond=999999)
    raw_data = AWSDetailedLineitem.get_cost_by_region(keys=[account.get_aws_user_id() for account in accounts],
                                                      date_from=date_from,
                                                      date_to=date_to)['intervals']['buckets']
    res = [
        {
            'month': data['key_as_string'].split('T')[0],
            'regions': [
                {
                    'region': region['key'],
                    'cost': region['cost']['value'],
                }
                for region in data['regions']['buckets']
            ],
        }
        for data in raw_data
    ]

    if 'csv' in request.args:
        return Response(generate_csv(res, 'regions', 'region'), mimetype='text/csv')
    return jsonify(months=res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyregionbyaccount', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyregionbyaccount/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycostbyregionbyaccount(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs summed by region for each account
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                region:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=nb_months - 1)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1],
                          hour=23, minute=59, second=59, microsecond=999999)
    raw_data = AWSDetailedLineitem.get_cost_by_region(keys=[account.get_aws_user_id() for account in accounts],
                                                      byaccount=True,
                                                      date_from=date_from,
                                                      date_to=date_to)['accounts']['buckets']
    res = [
        {
            'account_id': account['key'],
            'account_name': [a.pretty for a in accounts if account['key'] == a.get_aws_user_id()][0],
            'months': [
                {
                    'month': data['key_as_string'].split('T')[0],
                    'regions': [
                        {
                            'region': region['key'],
                            'cost': region['cost']['value'],
                        }
                        for region in data['regions']['buckets']
                    ],
                }
                for data in account['intervals']['buckets']
            ]
        }
        for account in raw_data
    ]

    if 'csv' in request.args:
        return Response(generate_csv(res, 'regions', 'region', account=True), mimetype='text/csv')
    return jsonify(accounts=res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyregionbytagbyaccount', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyregionbytagbyaccount/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycostbyregionbytagbyaccount(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs summed by region for each account
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                region:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=nb_months - 1)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1],
                          hour=23, minute=59, second=59, microsecond=999999)
    raw_data = AWSDetailedLineitem.get_cost_by_region(keys=[account.get_aws_user_id() for account in accounts],
                                                      tagged=True,
                                                      byaccount=True,
                                                      date_from=date_from,
                                                      date_to=date_to)['accounts']['buckets']

    def tagged_cost(bucket, total):
        total_tag = 0.0
        for tag in bucket:
            total_tag += tag['cost']['value']
            yield (tag['key'], tag['cost']['value'])
        if total != total_tag:
            yield ('untagged', total - total_tag)

    res = [
        {
            'account_id': account['key'],
            'account_name': [a.pretty for a in accounts if a.get_aws_user_id() == account['key']][0],
            'months': [
                {
                    'month': data['key_as_string'].split('T')[0],
                    'regions': [
                        {
                            'region': region['key'],
                            'tags': [
                                {
                                    'name': tag[0],
                                    'cost': tag[1],
                                }
                                for tag in tagged_cost(region['tags']['buckets'], region['cost']['value'])
                            ],
                        }
                        for region in data['regions']['buckets']
                    ],
                }
                for data in account['intervals']['buckets']
            ]
        }
        for account in raw_data
    ]

    if 'csv' in request.args:
        return Response(generate_csv(res, 'regions', 'region', account=True, tagged=True), mimetype='text/csv')
    return jsonify(accounts=res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/dailycostbyproduct', defaults={'nb_days': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/dailycostbyproduct/<int:nb_days>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_dailycostbyproduct(accounts, nb_days):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get daily costs summed by product
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        days:
                            type: array
                            items:
                                properties:
                                    day:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                product:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0
    now = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    now = AWSDetailedLineitem.get_last_date([account.get_aws_user_id() for account in accounts], limit=now)
    date_from = now.replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(days=nb_days)
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=999999) - relativedelta(days=1)
    data = AWSDetailedLineitem.get_daily_cost_by_product(keys=[account.get_aws_user_id() for account in accounts],
                                                         date_from=date_from,
                                                         date_to=date_to)['days']
    for d in data:
        d['products'] = cut_cost_by_product(sorted(d['products'], key=lambda x: x['cost'], reverse=True), int(request.args['show']) - 1 if 'show' in request.args else 9)

    if not len(data):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(days=data)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyproduct', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyproduct/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycostbyproduct(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs summed by product
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                product:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    now = AWSDetailedLineitem.get_last_date([account.get_aws_user_id() for account in accounts], limit=now)
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=nb_months - 1)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1], hour=23, minute=59, second=59, microsecond=999999)
    data = AWSDetailedLineitem.get_monthly_cost_by_product(keys=[account.get_aws_user_id() for account in accounts],
                                                           date_from=date_from,
                                                           date_to=date_to)['months']
    for d in data:
        if 'csv' not in request.args:
            d['products'] = cut_cost_by_product(sorted(d['products'], key=lambda x: x['cost'], reverse=True), int(request.args['show']) - 1 if 'show' in request.args else 9)

    if not len(data):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    if 'csv' in request.args:
        return Response(generate_csv(data, 'products', 'product'), mimetype='text/csv')
    return jsonify(months=data)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyproductbyaccount', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyproductbyaccount/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycostbyproductbyaccount(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs summed by product for each account
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                product:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    month = nb_months - 1
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=month)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1],
                          hour=23, minute=59, second=59, microsecond=999999)
    res = [
        {
            'account_id': account.get_aws_user_id(),
            'account_name': account.pretty,
            'months': AWSDetailedLineitem.get_monthly_cost_by_product(keys=account.get_aws_user_id(),
                                                                      date_from=date_from,
                                                                      date_to=date_to)['months'],
        }
        for account in accounts
    ]

    if 'csv' in request.args:
        return Response(generate_csv(res, 'products', 'product', account=True), mimetype='text/csv')
    return jsonify(accounts=res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyproductbytagbyaccount', defaults={'nb_months': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/monthlycostbyproductbytagbyaccount/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_monthlycostbyproductbytagbyaccount(accounts, nb_months):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get monthly costs summed by product for each account
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        months:
                            type: array
                            items:
                                properties:
                                    month:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                product:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    month = nb_months - 1
    date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=month)
    date_to = now.replace(day=calendar.monthrange(now.year, now.month)[1],
                          hour=23, minute=59, second=59, microsecond=999999)
    res = [
        {
            'account_id': account.get_aws_user_id(),
            'account_name': account.pretty,
            'months': AWSDetailedLineitem.get_monthly_cost_by_product(keys=account.get_aws_user_id(),
                                                                      tagged=True,
                                                                      date_from=date_from,
                                                                      date_to=date_to)['months'],
        }
        for account in accounts
    ]
    if 'csv' in request.args:
        return Response(generate_csv(res, 'products', 'product', account=True, tagged=True), mimetype='text/csv')

    return jsonify(accounts=res)



@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/yearlycostbyproduct', defaults={'nb_years': 3})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/yearlycostbyproduct/<int:nb_years>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_yearlycostbyproduct(accounts, nb_years):
    """---
    get:
        tags:
            - aws
        produces:
            - application/json
        description: &desc Get yearly costs summed by product
        summary: *desc
        responses:
            200:
                description: List of AWS accounts
                schema:
                    properties:
                        years:
                            type: array
                            items:
                                properties:
                                    year:
                                        type: string
                                    products:
                                        type: array
                                        items:
                                            properties:
                                                cost:
                                                    type: number
                                                product:
                                                    type: string
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    now = datetime.utcnow()
    date_from = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(years=nb_years - 1)
    date_to = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    data = AWSDetailedLineitem.get_yearly_cost_by_product(keys=[account.get_aws_user_id() for account in accounts],
                                                              date_from=date_from,
                                                              date_to=date_to)['years']
    for d in data:
        d['products'] = cut_cost_by_product(sorted(d['products'], key=lambda x: x['cost'], reverse=True), int(request.args['show']) - 1 if 'show' in request.args else 9)

    if not len(data):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(years=data)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbyresource/months')
@with_login()
@with_multiple_aws_accounts()
def aws_cost_by_resource_months(accounts):
    raw_data = AWSDetailedLineitem.get_first_to_last_date([account.get_aws_user_id() for account in accounts])
    if not raw_data:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(months=[data.strftime("%Y-%m-01") for data in raw_data])


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbyresource/<month>/categories')
@with_login()
@with_multiple_aws_accounts()
def aws_cost_by_resource_month_categories_m(accounts, month):
    try:
        date_from = datetime.strptime(month, "%Y-%m-%d")
    except:
        return jsonify(error='Not found.'), 404
    raw_data = AWSDetailedLineitem.get_cost_by_resource([account.get_aws_user_id() for account in accounts], date_from=date_from)
    cat = []
    max_cat = 0
    for new in raw_data:
        x = 1
        while new['cost'] > x:
            x *= 10
        if x >= max_cat:
            max_cat = x
        elif '<{}'.format(x) not in cat:
            cat.append('<{}'.format(x))
    cat.append('>{}'.format(max_cat / 10))
    return jsonify(categories=cat)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbyresource/<month>/chart')
@with_login()
@with_multiple_aws_accounts()
def aws_cost_by_resource_month_chart_m(accounts, month):
    # TODO: Use ES agg to categorize
    try:
        date_from = datetime.strptime(month, "%Y-%m-%d")
    except:
        return jsonify(error='Not found.'), 404
    raw_data = [
        AWSDetailedLineitem.get_cost_by_resource(account.get_aws_user_id(), date_from=date_from)
        for account in accounts
    ]
    data = []

    def get_cat_with_cost(cost):
        x = 1
        while cost > x:
            x *= 10
        return x

    def add_resource_in_data(new):
        new_cat = get_cat_with_cost(new['cost'])
        for cat in data:
            if cat['category'] == '<{}'.format(new_cat):
                cat['total'] += new['cost']
                return
        data.append(dict(category='<{}'.format(new_cat), total=new['cost']))

    for one in raw_data:
        for new in one:
            add_resource_in_data(new)
    if not len(data):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    max_cat = 0
    for i in range(len(data)):
        if len(data[i]['category']) > len(data[max_cat]['category']):
            max_cat = i
    data[max_cat]['category'] = data[max_cat]['category'][:-1]
    data[max_cat]['category'] = data[max_cat]['category'].replace('<', '>', 1)
    return jsonify(categories=data)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbyresource/<month>/<category>')
@with_login()
@with_multiple_aws_accounts()
def aws_cost_by_resource_m(accounts, month, category):
    try:
        date_from = datetime.strptime(month, "%Y-%m-%d")
        assert category[0] in ['<', '>']
        cat = int(category[1:])
    except:
        return jsonify(error='Not found.'), 404
    raw_data = AWSDetailedLineitem.get_cost_by_resource([account.get_aws_user_id() for account in accounts], date_from=date_from)

    def transform(r):
        r['resource_name'] = r['resource']
        return r

    minus = category[0] == '<'
    data = [
        transform(r)
        for r in raw_data
        if (minus and cat > r['cost'] >= cat / 10) or (not minus and r['cost'] > cat)
    ]
    if len(data) <= 0:
        return jsonify(error='Not found.'), 404
    return jsonify(category=dict(resources=data, total=sum([x['cost'] for x in data])))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbyresource/<month>/search/<search>')
@with_login()
@with_multiple_aws_accounts()
def aws_cost_by_resource_search_m(accounts, month, search):
    try:
        date_from = datetime.strptime(month, "%Y-%m-%d")
    except:
        return jsonify(error='Not found.'), 404
    raw_data = [
        AWSDetailedLineitem.get_cost_by_resource(account.get_aws_user_id(), date_from=date_from, search=search)
        for account in accounts
    ]

    def transform(r):
        r['resource_name'] = r['resource']
        return r

    data = [
        transform(r)
        for raw in raw_data
        for r in raw
    ]
    if not len(data):
        return jsonify(error='Not found.'), 404
    return jsonify(search_result=data)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/tags')
@with_login()
@with_multiple_aws_accounts()
def aws_get_resource_tags(accounts):
    tags =  AWSDetailedLineitem.get_available_tags([account.get_aws_user_id() for account in accounts])['tags']
    if not len(tags):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(tags=sorted(tags, key=unicode.lower))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/tags_only_with_data')
@with_login()
@with_multiple_aws_accounts()
def aws_get_resource_tags_with_data(accounts):
    tags = list(set(itertools.chain.from_iterable(
        AWSDetailedLineitem.get_available_tags(account.get_aws_user_id(), only_with_data=account.key)['tags']
        for account in accounts
    )))
    if not len(tags):
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(tags=sorted(tags, key=unicode.lower))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbytag/<path:tag>', defaults={'nb_months': 5})
@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/costbytag/<path:tag>/<int:nb_months>')
@with_login()
@with_multiple_aws_accounts()
def aws_cost_by_tags_months(accounts, nb_months, tag):
    date_to = datetime.now()
    date_from = date_to.replace(day=1, minute=0, second=0, microsecond=0) - relativedelta(months=nb_months - 1)
    return jsonify(AWSDetailedLineitem.get_monthly_cost_by_tag([account.get_aws_user_id() for account in accounts], tag, date_from=date_from, date_to=date_to))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/underutilized')
@with_login()
@with_multiple_aws_accounts()
def aws_underutilized_resources(accounts):
    return jsonify(AWSMetric.underutilized_resources(account.key for account in accounts))


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/underutilizedreducedcost')
@with_login()
@with_multiple_aws_accounts()
def aws_underutilized_resources_reduced_cost(accounts):
    now = datetime.utcnow()
    date_from = now.replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=6)
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    resources = AWSMetric.underutilized_resources(account.key for account in accounts)
    resource_ids = set(r['id'] for r in resources['resources'])
    months = AWSDetailedLineitem.get_monthly_cost_by_resource(resource_ids, date_from=date_from, date_to=date_to)
    res = {  # Simply multiply every cost by 20% as all instances usage is
        k: v * 0.2  # less than 20%. TODO: intelligently find the best type
        for k, v in months.iteritems()
    }
    return jsonify(res)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/usagecost')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_usagecost(accounts):

    def get_account_data(account):
        for date, cpu_usage in dict(AWSMetric.daily_cpu_utilization(account.key)).iteritems():
            yield (date, cpu_usage, None)
        for date, cost in dict(AWSDetailedLineitem.get_ec2_daily_cost(account.get_aws_user_id())).iteritems():
            yield (date, None, cost)

    @with_cache()
    def get_all_account_data():
        return list(
            itertools.chain.from_iterable(
                get_account_data(account)
                for account in accounts
            )
        )

    data = get_all_account_data()
    days = {}
    for day, cpu_usage, cost in data:
        day_data = days.setdefault(day, {'day': day, 'cpu': None, 'cost': None})
        if cpu_usage is not None:
            day_data['cpu'] = (day_data['cpu'] or 0.0) + cpu_usage
        if cost is not None:
            day_data['cost'] = (day_data['cost'] or 0.0) + cost
    res = sorted([
        value
        for value in days.itervalues()
        if value['cpu'] is not None and value['cost'] is not None # Comment/remove if None values are OK
    ], key=lambda e: e['day'])
    if not res:
        return jsonify(message=get_next_update_estimation_message_aws(accounts, AWS_KEY_PROCESSING_INTERVAL_HOURS))
    return jsonify(days=res)

def _build_list_used_transfer_types(stat_list):
    return frozenset(
        elem['type']
        for bucket in stat_list
        for elem in bucket['transfer_stats']
    )


def _check_if_in_list(dict_list, value, key):
    return next((item for item in dict_list if item[key] == value), None)


def _append_to_header_list(header_list, new_data):
    for elem in new_data:
        if elem not in header_list:
            header_list.append(elem)
    return header_list



@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/s3bucketsizepername')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_s3bucketsizepername(accounts):
    """---
    get:
        tags:
            - aws
        produces:
            - application/csv
        description: &desc Stats about cost and usage of bandwith and storag on s3 buckets, organised by name
        summary: *desc
        responses:
            200:
                description: Stats about cost and usage of bandwith and storag on s3 buckets, organised by name
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """


    def _create_bandwith_breakdown(transfer_types_list, csv_row, bucket_bandwith_stat):
        for elem in transfer_types_list:
            _current_transfer_type = _check_if_in_list(bucket_bandwith_stat['transfer_stats'], elem, 'type')
            if _current_transfer_type is not None:
                csv_row[elem] = _current_transfer_type['data'] * 1024 * 1024 * 1024 # The is by default given in GB
        return csv_row

    def _create_csv_rows(bucket_list, account, bandwith_cost, csv_row_all):
        for bucket in bucket_list['buckets']:
            csv_row = {
                'account_id': account.get_aws_user_id(),
                'used_space': bucket['used_space'],
                'name': bucket['name'],
                'storage_cost': _check_if_in_list(bucket['prices'], bucket['provider'], 'provider')['cost']
            }
            bucket_bandwith_stat = _check_if_in_list(bandwith_cost, bucket['name'], 'bucket_name')
            if bucket_bandwith_stat is not None:
                csv_row = _create_bandwith_breakdown(transfer_types_list, csv_row, bucket_bandwith_stat)
            csv_row['bandwith_cost'] = bucket_bandwith_stat['cost'] if bucket_bandwith_stat is not None else 0
            csv_row['total_cost'] = csv_row['storage_cost'] + csv_row['bandwith_cost']
            csv_row_all.append(csv_row)
        return csv_row_all

    assert len(accounts) > 0
    csv_header = ['account_id', 'name', 'used_space', 'storage_cost', 'bandwith_cost', 'total_cost']
    csv_row_all = []
    for account in accounts:
        bucket_list = AWSStat.latest_s3_space_usage(account)
        bucket_ids = [
            bucket['name']
            for bucket in (bucket_list['buckets'] if bucket_list is not None else [])
        ]
        bandwith_cost = AWSDetailedLineitem.get_s3_bandwith_info_and_cost_per_name(account.get_aws_user_id(), bucket_ids)
        transfer_types_list = _build_list_used_transfer_types(bandwith_cost)
        csv_header = _append_to_header_list(csv_header, transfer_types_list)
        csv_row_all = _create_csv_rows(bucket_list, account, bandwith_cost, csv_row_all)

    if len(csv_row_all) > 0 and csv_row_all[0] is None:
        csv_row_all = []
    if 'csv' in request.args:
        return Response(generate_csv_clean(csv_row_all, csv_header))
    return jsonify(accounts=csv_row_all)


@app.route('/aws/accounts/<aws_key_ids:account_ids>/stats/s3bucketsizepertag/<path:tag>')
@with_login()
@with_multiple_aws_accounts()
def aws_accounts_m_stats_s3bucketsizepertag(accounts, tag):
    """---
    get:
        tags:
            - aws
        produces:
            - application/csv
        description: &desc Stats about cost and usage of bandwith and storag on s3 buckets, organised by tag
        summary: *desc
        responses:
            200:
                description: Stats about cost and usage of bandwith and storag on s3 buckets, organised by tag
            403:
                description: Not logged in
            404:
                description: AWS account not registered
    """
    assert len(accounts) > 0

    def _get_total_sizes_cost_and_names(bucket_names_list, bucket_list):
        total_size = 0
        total_cost = 0
        names = ""
        for bucket in bucket_list['buckets']:
            if _check_if_in_list(bucket_names_list, bucket['name'], 'bucket_name') is not None:
                total_size += float(bucket['used_space'])
                total_cost += _check_if_in_list(bucket['prices'], bucket['provider'], 'provider')['cost']
                names += bucket['name'] + ", "
        return total_size, names[:-2], total_cost

    def _get_bandwith_info(account, bucket_names):
        bucket_ids = [
            bucket
            for bucket in (bucket_names if isinstance(bucket_names, list) else [bucket_names])
        ]
        bandwith_cost = AWSDetailedLineitem.get_s3_bandwith_info_and_cost_per_name(account.get_aws_user_id(), bucket_ids)
        return bandwith_cost


    def _iterate_over_buckets_in_tag_for_total(bucket_bandwith_stat):
        total_cost = 0
        for bucket in (bucket_bandwith_stat if bucket_bandwith_stat is not None else []):
            total_cost += bucket['cost']
        return total_cost

    def _iterate_over_buckets_and_make_breakdown_bandwith_stat(bucket_bandwith_stat, buff_row_csv, tag_value):
        bandwith_cost = 0
        for bucket in bucket_bandwith_stat:
            bandwith_cost += bucket['cost']
            for elem in bucket['transfer_stats']:
                if elem['type'] in buff_row_csv:
                    buff_row_csv[elem['type']] += (elem['data'] * 1024 * 1024 * 1024)
                else:
                    buff_row_csv[elem['type']] = (elem['data'] * 1024 * 1024 * 1024)
        buff_row_csv['bandwith_cost'] = bandwith_cost
        return buff_row_csv

    def _build_csv_row_and_add_header(bucket_list_tagged, bucket_list, account, csv_header, csv_row_all):
        for tag_value in bucket_list_tagged['tag_value']:
            bucket_info = _get_total_sizes_cost_and_names(tag_value['s3_buckets'], bucket_list)
            bucket_bandwith_stat = _get_bandwith_info(account, bucket_info[1])
            csv_header = _append_to_header_list(csv_header, _build_list_used_transfer_types(bucket_bandwith_stat))
            csv_row = {
                "tag_key": bucket_list_tagged['tag_key'].split(':')[1],
                "tag_value": tag_value['tag_value'],
                "account_id": tag_value['s3_buckets'][0]["account_id"],
                "total_size": bucket_info[0],
                "bucket_names": bucket_info[1],
                "storage_cost": bucket_info[2],
            }
            csv_row = _iterate_over_buckets_and_make_breakdown_bandwith_stat(bucket_bandwith_stat, csv_row, tag_value)
            csv_row['total_cost'] = csv_row['storage_cost'] + csv_row['bandwith_cost']
            csv_row_all.append(csv_row)
        return csv_header, csv_row_all

    def _select_bucket_list_tag(bucket_list_per_tag, tag):
        for bucket_list_tagged in bucket_list_per_tag:
            if tag in bucket_list_tagged['tag_key'].split(':')[1]:
                return bucket_list_tagged

    csv_header = ["account_id", "tag_key", "tag_value", "total_size", "bucket_names", "bandwith_cost", "storage_cost", "total_cost"]
    csv_data = []
    for account in accounts:
        bucket_list_per_tag = AWSDetailedLineitem.get_s3_buckets_per_tag(account.get_aws_user_id())
        bucket_list_tagged = _select_bucket_list_tag(bucket_list_per_tag, tag)
        bucket_list = AWSStat.latest_s3_space_usage(account)
        csv_header, csv_data = _build_csv_row_and_add_header(bucket_list_tagged, bucket_list, account, csv_header, csv_data)

    if 'csv' in request.args:
        return Response(generate_csv_clean(csv_data, csv_header))
    return jsonify(res=csv_data)

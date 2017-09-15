import pricing
from collections import defaultdict
from app.cache import with_cache


REPLACE_FREE_TIER = {
    'Compute Free Tier - 400,000 GB-Seconds': 'Total Compute',
    'Requests Free Tier - 1,000,000 Requests': 'Total Requests',
}


@with_cache(ttl=24 * 3600)
def _get_price():
    raw = pricing.get('AWSLambda')
    return raw.json()['terms']['OnDemand'] if raw else pricing.fetch('AWSLambda')['terms']['OnDemand']


@with_cache(ttl=24 * 3600)
def _search_cost(desc):
    prices = _get_price()
    for sku in prices.itervalues():
        for term in sku.itervalues():
            for price_dimension in term['priceDimensions'].itervalues():
                if price_dimension['description'] == desc:
                    return float(price_dimension['pricePerUnit']['USD'])
    return 0.0


def _flat_data(data):
    flattened = defaultdict(int)

    for d in data:
        for one in d:
            flattened[one['key']] += one['quantity']['value']
    return flattened


def get_raw_cost(data):
    data = _flat_data(data)
    raw_cost = 0
    for desc, quantity in data.iteritems():
        for old, new in REPLACE_FREE_TIER.iteritems():
            desc = desc.replace(old, new)
        raw_cost += _search_cost(desc) * quantity
    return raw_cost
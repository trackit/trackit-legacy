from werkzeug.contrib.cache import SimpleCache
from app.aws import pricing as aws_pricing

cache = SimpleCache()

def get_pricing_data():
    pricing_data = cache.get('rdspricingdata')
    if not pricing_data:
        pricing_data = list(process(aws_pricing.fetch('AmazonRDS')))
        cache.set('rdspricingdata', pricing_data)
    return pricing_data

def process(data):
    reserved_terms = data['terms']['Reserved']
    ondemand_terms = data['terms']['OnDemand']
    for product in data['products'].values():
        if product.get('productFamily') != 'Database Instance':
            continue
        if 'InstanceUsage' not in product['attributes']['usagetype']:
            continue

        prices = []
        for term in reserved_terms.get(product['sku'], {}).values():
            upfront_cost = 0
            hourly_cost = 0
            for dim in term['priceDimensions'].itervalues():
                if dim['unit'].lower() == 'quantity':
                    upfront_cost = float(dim['pricePerUnit']['USD'])
                elif dim['unit'].lower() == 'hrs':
                    hourly_cost = float(dim['pricePerUnit']['USD'])
            prices.append({
                'type': 'reserved',
                'reservationYears': int(term['termAttributes']['LeaseContractLength'].replace('yr', '')),
                'upfrontCost': upfront_cost,
                'costPerHour': hourly_cost
            })

        prices.sort(key=lambda p: (p['reservationYears'], p['upfrontCost']), reverse=True)

        product_ondemand_terms = ondemand_terms.get(product['sku'], {}).values()
        # assert len(product_ondemand_terms) == 1
        if len(product_ondemand_terms) != 1:
            continue
        product_ondemand_price_dims = product_ondemand_terms[0]['priceDimensions'].values()
        # assert len(product_ondemand_price_dims) == 1
        if len(product_ondemand_price_dims) != 1:
            continue
        prices.append({
            'type': 'ondemand',
            'reservationYears': 0,
            'upfrontCost': 0,
            'costPerHour': float(product_ondemand_price_dims[0]['pricePerUnit']['USD'])
        })

        res = dict(product['attributes'])
        res['prices'] = prices

        yield res

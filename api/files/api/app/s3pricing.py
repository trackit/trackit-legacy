from werkzeug.contrib.cache import SimpleCache
from app.aws import pricing as aws_pricing
from app.aws import region_fullnames
from fractions import Fraction

cache = SimpleCache()

gib = Fraction(2 ** 30)

def get_latest_pricing():
    return aws_pricing.get('AmazonS3')

def get_pricing_data():
    pricing_data = cache.get('s3pricingdata')
    if not pricing_data:
        latest = get_latest_pricing()
        if latest:
            pricing_data = latest.json()
            cache.set('s3pricingdata', pricing_data)
        else:
            pricing_data = fetch()
    return pricing_data

def fetch():
    return aws_pricing.fetch('AmazonS3')

def costs(stored, retrieved):
    pricing_data = get_pricing_data()
    if not pricing_data:
        return
    return calculate_all_storage_costs(pricing_data, stored, retrieved)

def get_external_transfer_products(data):
    for product in data['products'].itervalues():
        if 'productFamily' in product and product['productFamily'] == 'Data Transfer' and product['attributes']['toLocation'] == 'External':
            yield product

def get_internal_transfer_products(data):
    for product in data['products'].itervalues():
        if 'productFamily' in product and product['productFamily'] == 'Data Transfer' and product['attributes']['toLocation'] != 'External' and product['attributes']['fromLocation'] != 'External':
            yield product

def get_storage_products(data):
    for product in data['products'].itervalues():
        if 'productFamily' in product and product['productFamily'] == 'Storage':
            yield product

def get_glacier_retrieval_products(data):
    for product in data['products'].itervalues():
        if 'productFamily' in product and product['productFamily'] == 'Fee' and product['attributes']['feeCode'] == 'Glacier:PeakRestore':
            yield product

def calculate_cost(data, sku, gigabytes):
    price_root = data['terms']['OnDemand'].get(sku)
    if price_root is None:
        raise ValueError, "no product with sku %s found" % sku

    total_usd = 0.0
    price_dimensions = ((int(d['beginRange']), d) for d in price_root.values()[0]['priceDimensions'].itervalues())
    for begin_range, dim in sorted(price_dimensions, reverse=True):
        if gigabytes <= begin_range:
            continue
        gigs_in_range = gigabytes - begin_range
        total_usd += gigs_in_range * float(dim['pricePerUnit']['USD'])
        gigabytes -= gigs_in_range

    return total_usd

def storage_product_sort_key(storage_product):
    attrs = storage_product['attributes']
    return attrs['location'] + ':' + attrs['storageClass']

def calculate_all_storage_costs(data, gigs_stored, gigs_retrieved):
    glacier_retrieval_product_skus = dict((p['attributes']['location'], p['sku']) for p in get_glacier_retrieval_products(data))
    external_transfer_product_skus = dict((p['attributes']['fromLocation'], p['sku']) for p in get_external_transfer_products(data))
    costs = []
    for product in sorted(get_storage_products(data), key=storage_product_sort_key):
        cost = calculate_cost(data, product['sku'], gigs_stored)
        transfer_sku = external_transfer_product_skus.get(product['attributes']['location'])
        if not transfer_sku:
            continue
        cost += calculate_cost(data, transfer_sku, gigs_retrieved)
        if product['attributes']['volumeType'] == 'Amazon Glacier' and gigs_retrieved > gigs_stored * 0.05:
            cost += calculate_cost(data, glacier_retrieval_product_skus[product['attributes']['location']], gigs_retrieved)
        costs.append(dict(
            location=product['attributes']['location'],
            availability=product['attributes']['availability'],
            durability=product['attributes']['durability'],
            storageClass=product['attributes']['storageClass'],
            volumeType=product['attributes']['volumeType'],
            cost=cost
        ))
    return costs

class S3CostEstimator(object):
    def __init__(self, pricing_data=None):
        if pricing_data is None:
            pricing_data = get_pricing_data()
        self.pricing_data = pricing_data
        self.storage_products_skus = dict(((p['attributes']['volumeType'], p['attributes']['location']), p['sku']) for p in get_storage_products(pricing_data))
        self.glacier_retrieval_product_skus = dict((p['attributes']['location'], p['sku']) for p in get_glacier_retrieval_products(pricing_data))
        self.external_transfer_product_skus = dict((p['attributes']['fromLocation'], p['sku']) for p in get_external_transfer_products(pricing_data))
        self.internal_transfer_product_skus = dict(((p['attributes']['fromLocation'], p['attributes']['transferType']), p['sku']) for p in get_internal_transfer_products(pricing_data))

    def estimate(self,
                 storage_standard = 0,                        # Standard storage in B
                 storage_dra = 0,                             # Standard - Infrequent Access storage in B
                 storage_nearline = 0,                        # Amazon Glacier storage in B
                 class_a_operations = 0,                      # Class A IO operations
                 class_b_operations = 0,                      # Class B IO operations
                 restore_nearline = 0,                        # Nearline restore volume in B
                 egress_americas_emea = 0,                    # Egress from Americas/EMEA in B
                 egress_asia_pacific = 0,                     # Egress from Asia/Pacific in B
                 egress_china = 0,                            # Egress from China in B
                 egress_australia = 0,                        # Egress from Australia in B
                 transfer_same_region = 0,                    # Same region transfer in B
                 transfer_same_multiregion = 0,               # Same-multiregion transfer in B
                 transfer_region_multiregion = 0,             # Region-multiregion transfer in B
                 transfer_multiregion_multiregion = 0,        # Multiregion-multiregion transfer in B
                 period=30,
                 region='us-east-1'):
        pricing_data = self.pricing_data
        storage_products_skus = self.storage_products_skus
        glacier_retrieval_product_skus = self.glacier_retrieval_product_skus
        external_transfer_product_skus = self.external_transfer_product_skus
        internal_transfer_product_skus = self.internal_transfer_product_skus
        detail = {
            'storage_standard': calculate_cost(pricing_data, storage_products_skus[('Standard', region_fullnames[region])], storage_standard / gib) * 1000,
            'storage_dra': calculate_cost(pricing_data, storage_products_skus[('Standard - Infrequent Access', region_fullnames[region])], storage_dra / gib) * 1000,
            'storage_nearline': calculate_cost(pricing_data, storage_products_skus[('Amazon Glacier', region_fullnames[region])], storage_nearline / gib) * 1000,
            'restore_nearline': calculate_cost(pricing_data, glacier_retrieval_product_skus[region_fullnames[region]], restore_nearline / gib) * 1000,
            'class_a_operations': 0,
            'class_b_operations': 0,
            'egress_americas_emea': calculate_cost(pricing_data, external_transfer_product_skus[region_fullnames[region]], egress_americas_emea / gib) * 1000,
            'egress_asia_pacific': calculate_cost(pricing_data, external_transfer_product_skus[region_fullnames[region]], egress_asia_pacific / gib) * 1000,
            'egress_china': calculate_cost(pricing_data, external_transfer_product_skus[region_fullnames[region]], egress_china / gib) * 1000,
            'egress_australia': calculate_cost(pricing_data, external_transfer_product_skus[region_fullnames[region]], egress_australia / gib) * 1000,
            'transfer_same_region': 0,
            'transfer_same_multiregion': calculate_cost(pricing_data, internal_transfer_product_skus[(region_fullnames[region], 'InterRegion Outbound')], transfer_same_multiregion / gib) * 1000,
            'transfer_region_multiregion': calculate_cost(pricing_data, internal_transfer_product_skus[(region_fullnames[region], 'InterRegion Outbound')], transfer_region_multiregion / gib) * 1000,
            'transfer_multiregion_multiregion': calculate_cost(pricing_data, internal_transfer_product_skus[(region_fullnames[region], 'InterRegion Outbound')], transfer_multiregion_multiregion / gib) * 1000
        }
        bill = {
            'detail': detail,
            'total': int(sum(detail.values())),
            'period': period,
            'region': region
        }
        for k, v in detail.iteritems():
            if type(v) == Fraction:
                detail[k] = int(v)
        return bill

def estimate_s3_cost(**kwargs):
    estimator = S3CostEstimator()
    return estimator.estimate(**kwargs)

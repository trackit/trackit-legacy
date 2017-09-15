from app import app
from app.models import db, AzurePricing
from sqlalchemy import and_, desc
from werkzeug.contrib.cache import SimpleCache
from app.ms_azure import azure_offers, azure_region_currency, azure_region_names
from app.ms_azure.pricing import fetch_region_pricing
from fractions import Fraction

cache = SimpleCache()

gib = Fraction(2 ** 30)

storage_mapping = {
    'storage_standard': 'Standard IO - Page Blob/Disk (GB)',
    'storage_dra': 'Standard IO - Hot Block Blob (GB)',
    'storage_nearline': 'Standard IO - Cool Block Blob (GB)'
}

pretty_storage_classes = {
    'storage_standard': 'Standard storage disk',
    'storage_dra': 'Hot Block Blob',
    'storage_nearline': 'Cool Block Blob',
}

def get_pricing_data(region):
    offer = azure_offers['Pay-As-You-Go']
    rate = cache.get('azurestoragerate') or {}
    if not region in rate:
        record = AzurePricing.query.filter(and_(AzurePricing.offer == offer, AzurePricing.region == region)).order_by(desc(AzurePricing.date)).first()
        if not record:
            fetch_region_pricing(offer, region)
            record = AzurePricing.query.filter(and_(AzurePricing.offer == offer, AzurePricing.region == region)).order_by(desc(AzurePricing.date)).first()
        rate[region] = record.json()['pricing'] if record else None
        cache.set('azurestoragerate', rate)
    return rate[region]

def calculate_cost(pricing, quantity):
    if pricing['included_quantity'] != 0:
        quantity = quantity - pricing['included_quantity']
        if quantity <= 0:
            return 0
    if len(pricing['meter_rates']) == 1:
        return pricing['meter_rates']['0'] * quantity

    tiers = []
    for key, value in pricing['meter_rates'].iteritems():
        tiers.append(dict(limit=int(key), cost=value))
    tiers.sort(key=lambda x: x['limit'], reverse=True)

    cost = 0
    for tier in tiers:
        if tier['limit'] < quantity:
            diff = quantity - tier['limit']
            cost = cost + (diff * tier['cost'])
            quantity = tier['limit']
    return cost

def estimate_cost(compute_nb_servers = 0,                              # Number of servers
                          compute_os = 'linux',                        # Operating system type
                          compute_instance_type = 'A0 VM',             # compute_instance_type
                          storage_standard = 0,                        # Standard storage in B
                          storage_dra = 0,                             # Standard - Infrequent Access storage in B
                          storage_nearline = 0,                        # Archive storage in B
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
                          region='US'):
    pricing_data = get_pricing_data(region)
    if not pricing_data:
        return {'detail': None, 'total': 0, 'period': period}

    azure_products = dict(((p['meter_category'], p['meter_name'], p['meter_sub_category']), p) for p in pricing_data)

    detail = {
        'compute_servers': compute_nb_servers * calculate_cost(azure_products[('Virtual Machines', "Compute Hours", compute_instance_type)], period * 24) * 1000,
        'storage_standard': calculate_cost(azure_products[('Storage', storage_mapping['storage_standard'], 'Locally Redundant')], storage_standard / gib) * 1000,
        'storage_dra': calculate_cost(azure_products[('Storage', storage_mapping['storage_dra'], 'Locally Redundant')], storage_dra / gib) * 1000,
        'storage_nearline': calculate_cost(azure_products[('Storage', storage_mapping['storage_nearline'], 'Locally Redundant')], storage_nearline / gib) * 1000,
        'restore_nearline': calculate_cost(azure_products[('Data Management', 'Standard IO - Cool Block Blob Data Retrieval (GB)', '')], restore_nearline / gib) * 1000,
        'class_a_operations': 0,
        'class_b_operations': 0,
        'egress_americas_emea': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], egress_americas_emea / gib) * 1000,
        'egress_asia_pacific': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], egress_asia_pacific / gib) * 1000,
        'egress_china': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], egress_china / gib) * 1000,
        'egress_australia': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], egress_australia / gib) * 1000,
        'transfer_same_region': 0,
        'transfer_same_multiregion': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], transfer_same_multiregion / gib) * 1000,
        'transfer_region_multiregion': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], transfer_region_multiregion / gib) * 1000,
        'transfer_multiregion_multiregion': calculate_cost(azure_products[('Networking', 'Data Transfer Out (GB)', '')], transfer_multiregion_multiregion / gib) * 1000
    }
    bill = {
        'detail': detail,
        'total': int(sum(detail.values())),
        'period': period
    }
    for k, v in detail.iteritems():
        if type(v) == Fraction:
            detail[k] = int(v)
    return bill

def get_storage_map(storage_bytes):
    pricing_list = []
    pricings = AzurePricing.query.filter(AzurePricing.offer == azure_offers['Pay-As-You-Go'])
    us_pricing = AzurePricing.query.filter(and_(AzurePricing.offer == azure_offers['Pay-As-You-Go'], AzurePricing.region == 'US')).first()
    us_products = dict(((p['meter_category'], p['meter_name'], p['meter_sub_category']), p) for p in us_pricing.json()['pricing'])
    for pricing in pricings:
        pricing_data = pricing.json()['pricing']
        azure_products = dict(((p['meter_category'], p['meter_name'], p['meter_sub_category']), p) for p in pricing_data)
        for storage_type, azure_storage_type in storage_mapping.iteritems():
            region_infos = {
                'region': azure_region_names[pricing.region],
                'availability': 'N/A',
                'durability': 'N/A',
                'storageClass': pretty_storage_classes[storage_type],
                'volumeType': pretty_storage_classes[storage_type],
                'cost': round(calculate_cost(us_products[('Storage', azure_storage_type, 'Locally Redundant')], storage_bytes / gib), 2)
            }
            pricing_list.append(region_infos)
    return dict(prices=pricing_list)

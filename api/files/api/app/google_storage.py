#!/usr/bin/env python2.7
from fractions import Fraction
import config
import json
import celery
import requests
import math
from celery.decorators import periodic_task
from app.runner import runner
from datetime import timedelta

compute_local_ssd_size = 375

pib = Fraction(2 ** 50)
tib = Fraction(2 ** 40)
gib = Fraction(2 ** 30)
mib = Fraction(2 ** 20)
kib = Fraction(2 ** 10)
pb = Fraction(10 ** 15)
tb = Fraction(10 ** 12)
gb = Fraction(10 ** 9)
mb = Fraction(10 ** 6)
kb = Fraction(10 ** 3)

unit_alias = {
    'pib': ['pebibyte', 'pebibytes'],
    'tib': ['tebibyte', 'tebibytes'],
    'gib': ['gibibyte', 'gibibytes'],
    'mib': ['mebibyte', 'mebibytes'],
    'kib': ['kibibyte', 'kibibytes'],
    'pb': ['petabyte', 'petabytes'],
    'tb': ['terabyte', 'terabytes'],
    'gb': ['gigabyte', 'gigabytes'],
    'mb': ['megabyte', 'megabytes'],
    'kb': ['kilobyte', 'kilobytes'],
}

units = {
    'pib': pib,
    'tib': tib,
    'gib': gib,
    'mib': mib,
    'kib': kib,
    'pb': pb,
    'tb': tb,
    'gb': gb,
    'mb': mb,
    'kb': kb,
}

for u, a in unit_alias.iteritems():
    for i in a:
        units[i] = units[u]

fields = [
    'compute_nb_servers',
    'compute_os',
    'compute_vm_class',
    'compute_instance_type',
    'compute_local_ssd',
    'compute_location',
    'compute_avg_minutes_per_day',
    'compute_avg_days_per_week',
    'compute_custom_cores',
    'compute_custom_ram',
    'compute_storage_ssd',
    'compute_storage_standard',
    'compute_storage_snapshot',
    'forwarding_rules',
    'forwarding_network_traffic',
    'storage_standard',
    'storage_dra',
    'storage_nearline',
    'restore_nearline',
    'class_a_operations',
    'class_b_operations',
    'egress_americas_emea',
    'egress_asia_pacific',
    'egress_china',
    'egress_australia',
    'transfer_same_region',
    'transfer_same_multiregion',
    'transfer_region_multiregion',
    'transfer_multiregion_multiregion',
    'unused_static_ip',
]

types_compute_instance = [
    "F1-MICRO",
    "G1-SMALL",
    "N1-STANDARD-1",
    "N1-STANDARD-2",
    "N1-STANDARD-4",
    "N1-STANDARD-8",
    "N1-STANDARD-16",
    "N1-STANDARD-32",
    "N1-HIGHMEM-2",
    "N1-HIGHMEM-4",
    "N1-HIGHMEM-8",
    "N1-HIGHMEM-16",
    "N1-HIGHMEM-32",
    "N1-HIGHCPU-2",
    "N1-HIGHCPU-4",
    "N1-HIGHCPU-8",
    "N1-HIGHCPU-16",
    "N1-HIGHCPU-32"
]

low_rates_premium_images = [
    "f1-micro",
    "g1-small"
]

def total_hours_per_month(minutes_per_day, days_per_week):
    return ((4.35 * days_per_week * minutes_per_day) / 60) * (days_per_week / 7)

def _egress(volume, tiers, rates):
    total = 0
    for tier, rate in reversed(zip(tiers, rates)):
        if volume > tier:
            part = volume - tier
            volume = tier
            total += (part / gib) * rate
    return total

_transfer = _egress

def configuration_from_json(obj):
    def exact(f): # We want our fractions to be exactly the written number, not its unexact float representation
        return Fraction(str(f)) # A bit crude, but it works wonderfully
    def prepare_region_pricing(instance):
        instance["us"] = instance["us"] * 1000
        instance["europe"] = instance["europe"] * 1000
        instance["asia"] = instance["asia"] * 1000
        return instance
    def prepare_compute_os_pricing(os_pricing):
        for key, os in os_pricing.iteritems():
            os["high"] = os["high"] * 1000
            os["low"] = os["low"] * 1000
        return os_pricing
    if type(obj) == str:
        obj = json.load(open(obj))
    pricings = obj['gcp_price_list']
    rate_compute_instance = {}
    for type_instance in types_compute_instance:
        rate_compute_instance[type_instance] = {
            "regular": prepare_region_pricing(pricings['CP-COMPUTEENGINE-VMIMAGE-'+type_instance]),
            "preemptible": prepare_region_pricing(pricings['CP-COMPUTEENGINE-VMIMAGE-'+type_instance+'-PREEMPTIBLE'])
        }
    rate_compute_instance["CUSTOM"] = {
        "regular": {
            "core": prepare_region_pricing(pricings['CP-COMPUTEENGINE-CUSTOM-VM-CORE']),
            "ram": prepare_region_pricing(pricings['CP-COMPUTEENGINE-CUSTOM-VM-RAM'])
        },
        "preemptible": {
            "core": prepare_region_pricing(pricings['CP-COMPUTEENGINE-CUSTOM-VM-CORE-PREEMPTIBLE']),
            "ram": prepare_region_pricing(pricings['CP-COMPUTEENGINE-CUSTOM-VM-RAM-PREEMPTIBLE'])
        }
    }
    return {
        'rate_sustained_use_tiers': sorted([(float(k), v) for k, v in pricings['sustained_use_tiers'].iteritems()], key=lambda tup: tup[0]),
        'rate_compute_os': prepare_compute_os_pricing(pricings['CP-COMPUTEENGINE-OS']),
        'rate_compute_instance': rate_compute_instance,
        'rate_compute_local_ssd': exact(pricings['CP-COMPUTEENGINE-LOCAL-SSD']['us']) * 1000,
        'rate_compute_storage_ssd': exact(pricings['CP-COMPUTEENGINE-STORAGE-PD-SSD']['us']) * 1000 / 30,
        'rate_compute_storage_standard': exact(pricings['CP-COMPUTEENGINE-STORAGE-PD-CAPACITY']['us']) * 1000 / 30,
        'rate_compute_storage_snapshot': exact(pricings['CP-COMPUTEENGINE-STORAGE-PD-SNAPSHOT']['us']) * 1000 / 30,
        'rate_forwarding_rule_base': exact(pricings['FORWARDING_RULE_CHARGE_BASE']['us']) * 1000,
        'rate_forwarding_rule_extra': exact(pricings['FORWARDING_RULE_CHARGE_EXTRA']['us']) * 1000,
        'rate_forwarding_network_traffic': exact(pricings['NETWORK_LOAD_BALANCED_INGRESS']['us']) * 1000,
        'rate_storage_standard': exact(pricings['CP-BIGSTORE-STORAGE']['us']) * 1000 / 30,
        'rate_storage_dra': exact(pricings['CP-BIGSTORE-STORAGE-DRA']['us']) * 1000 / 30,
        'rate_storage_nearline': exact(pricings['CP-NEARLINE-STORAGE']['us']) * 1000 / 30,
        'rate_class_a_operations': exact(pricings['CP-BIGSTORE-CLASS-A-REQUEST']['us']),
        'rate_class_b_operations': exact(pricings['CP-BIGSTORE-CLASS-B-REQUEST']['us']) / 10,
        'rate_restore_nearline': exact(pricings['CP-NEARLINE-RESTORE-SIZE']['us']) * 1000 / 30,
        'rate_egress_tiers': [0, 1*tib, 10*tib], # TODO Change tiers to be per egress type
        'rate_egress_americas_emea': list(map(lambda p: exact(p) * 1000 ,pricings['CP-COMPUTEENGINE-INTERNET-EGRESS-NA-NA']['tiers'].values())),
        'rate_egress_asia_pacific': list(map(lambda p: exact(p) * 1000 ,pricings['CP-COMPUTEENGINE-INTERNET-EGRESS-APAC-APAC']['tiers'].values())),
        'rate_egress_china': list(map(lambda p: exact(p) * 1000 ,pricings['CP-COMPUTEENGINE-INTERNET-EGRESS-CN-CN']['tiers'].values())),
        'rate_egress_australia': list(map(lambda p: exact(p) * 1000 ,pricings['CP-COMPUTEENGINE-INTERNET-EGRESS-AU-AU']['tiers'].values())),
        'rate_transfer_tiers': [0, 1*tib, 10*tib],
        'rate_transfer_same_region': [0, 0, 0], # Does not appear in dynamic data
        'rate_transfer_same_multiregion': [0, 0, 0], # Does not appear in dynamic data
        'rate_transfer_region_multiregion': [exact(pricings['CP-COMPUTEENGINE-INTERNET-EGRESS-REGION']['us']) * 1000] * 3,
        'rate_transfer_multiregion_multiregion': list(map(lambda p: exact(p) * 1000 ,pricings['CP-COMPUTEENGINE-INTERNET-EGRESS-NA-NA']['tiers'].values())), # Same as transfer to Americas and EMEA
        'rate_unused_static_ip': exact(pricings['CP-COMPUTEENGINE-STATIC-IP-CHARGE']['us']) * 1000,
    }

def configuration_from_jsons(obj):
    return configuration_from_json(json.loads(obj))

# Generate a Google Cloud Storage pricing model.
def gen_google_cloud_storage_model(rate_sustained_use_tiers,
                                   rate_compute_os,
                                   rate_compute_instance,
                                   rate_compute_local_ssd,
                                   rate_compute_storage_ssd,
                                   rate_compute_storage_standard,
                                   rate_compute_storage_snapshot,
                                   rate_forwarding_rule_base,
                                   rate_forwarding_rule_extra,
                                   rate_forwarding_network_traffic,
                                   rate_storage_standard,
                                   rate_storage_dra,
                                   rate_storage_nearline,
                                   rate_class_a_operations,
                                   rate_class_b_operations,
                                   rate_restore_nearline,
                                   rate_egress_tiers,
                                   rate_egress_americas_emea,
                                   rate_egress_asia_pacific,
                                   rate_egress_china,
                                   rate_egress_australia,
                                   rate_transfer_tiers,
                                   rate_transfer_same_region,
                                   rate_transfer_same_multiregion,
                                   rate_transfer_region_multiregion,
                                   rate_transfer_multiregion_multiregion, #
                                   rate_unused_static_ip,
                                   ):
    # Compute Google Cloud Storage pricings all returned money values are in thousandths of dollar
    def google_cloud_storage_model(compute_nb_servers = 0,                      # Number of servers
                                   compute_os = 'free',                         # Operating system type: free|win|rhel|suse
                                   compute_vm_class = 'regular',                # VM class: regular|preemptible
                                   compute_instance_type = 'f1-micro',          # compute_instance_type: f1-micro|g1-small|...|custom
                                   compute_local_ssd = 0,                       # Number of local ssd
                                   compute_location = 'us',                     # Server location: us|europe|asia
                                   compute_avg_minutes_per_day = 1440,          # Average minutes per day each server is running
                                   compute_avg_days_per_week = 7,               # Average days per week each server is running
                                   compute_custom_cores = 0,                    # Number of cores for custom compute engine
                                   compute_custom_ram = 0,                      # Memory size for custom compute engine in B
                                   compute_storage_ssd = 0,                     # SSD storage in B (compute engine)
                                   compute_storage_standard = 0,                # Standard storage in B (compute engine)
                                   compute_storage_snapshot = 0,                # Snapshot storage in B (compute engine)
                                   forwarding_rules = 0,                        # Number of forwarding rules
                                   forwarding_network_traffic = 0,              # Forwarding network traffinc in B
                                   storage_standard = 0,                        # Standard storage in B per day
                                   storage_dra = 0,                             # DRA storage in B per day
                                   storage_nearline = 0,                        # Nearline storage in B per day
                                   class_a_operations = 0,                      # Class A IO operations
                                   class_b_operations = 0,                      # Class B IO operations
                                   restore_nearline = 0,                        # Nearline restore volume in B per day
                                   egress_americas_emea = 0,                    # Egress from Americas/EMEA in B
                                   egress_asia_pacific = 0,                     # Egress from Asia/Pacific in B
                                   egress_china = 0,                            # Egress from China in B
                                   egress_australia = 0,                        # Egress from Australia in B
                                   transfer_same_region = 0,                    # Same region transfer in B
                                   transfer_same_multiregion = 0,               # Same-multiregion transfer in B
                                   transfer_region_multiregion = 0,             # Region-multiregion transfer in B
                                   transfer_multiregion_multiregion = 0,        # Multiregion-multiregion transfer in B
                                   unused_static_ip = 0,                        # Number of unused static IPs
                                   period=30,                                   # Evaluated period in days
                                   ):

        def get_compute_price_with_sustained_discount():
            price = 0
            compute_minutes_per_day = 10 if compute_avg_minutes_per_day < 10 else compute_avg_minutes_per_day
            total_hours_running = total_hours_per_month(compute_minutes_per_day, compute_avg_days_per_week)
            full_month = (1440 * 7 * 4.35) / 60
            prev_tier_limit = 0.0
            for (tier, rate) in rate_sustained_use_tiers:
                tier_limit = tier * full_month
                hours_current_tier = tier_limit - prev_tier_limit if total_hours_running > full_month * tier else total_hours_running - prev_tier_limit
                if hours_current_tier > 0:
                    if compute_instance_type == 'custom':
                        price = price + (hours_current_tier * rate_compute_instance[compute_instance_type.upper()][compute_vm_class]["core"][compute_location] * compute_custom_cores * rate)
                        price = price + (hours_current_tier * rate_compute_instance[compute_instance_type.upper()][compute_vm_class]["ram"][compute_location] * (compute_custom_ram / gib) * rate)
                    else:
                        price = price + (hours_current_tier * rate_compute_instance[compute_instance_type.upper()][compute_vm_class][compute_location] * rate)
                prev_tier_limit = tier_limit
            return price

        def get_compute_os_price():
            price = 0
            rate = 0
            core_multiplier = 1
            if compute_os == "free":
                return price
            os_minutes_per_day = 10 if compute_avg_minutes_per_day < 10 else compute_avg_minutes_per_day
            # rhel is charged by 1 hour increments
            if compute_os == "rhel":
                os_minutes_per_day = int(math.ceil(compute_avg_minutes_per_day / 60.0)) * 60
            total_hours_running = total_hours_per_month(os_minutes_per_day, compute_avg_days_per_week)
            if compute_instance_type == "custom":
                nb_cores = compute_custom_cores
            else:
                if rate_compute_instance[compute_instance_type.upper()][compute_vm_class]["cores"]:
                    nb_cores = 1
                else:
                    nb_cores = int(rate_compute_instance[compute_instance_type.upper()][compute_vm_class]["cores"])
            if rate_compute_os[compute_os]["percore"]:
                core_multiplier = nb_cores
            if rate_compute_os[compute_os]["cores"] == "shared":
                if compute_instance_type in low_rates_premium_images:
                    rate = rate_compute_os[compute_os]["low"]
                else:
                    rate = rate_compute_os[compute_os]["high"]
            else:
                if nb_cores < int(rate_compute_os[compute_os]["cores"]):
                    rate = rate_compute_os[compute_os]["low"]
                else:
                    rate = rate_compute_os[compute_os]["high"]
            price = total_hours_running * rate * core_multiplier
            return price

        def get_forwarding_rules_price():
            if forwarding_rules == 0:
                return 0
            forwarding_rules_base_limit = 5
            total_hours = total_hours_per_month(compute_avg_minutes_per_day, compute_avg_days_per_week)
            forwarding_data_price = (rate_forwarding_network_traffic / gib) * forwarding_network_traffic
            if forwarding_rules <= forwarding_rules_base_limit:
                return rate_forwarding_rule_base * total_hours + forwarding_data_price
            else:
                return rate_forwarding_rule_base * total_hours + ((forwarding_rules - forwarding_rules_base_limit) * rate_forwarding_rule_extra * total_hours) + forwarding_data_price

        detail = {
            'compute_servers': compute_nb_servers * get_compute_price_with_sustained_discount(),
            'compute_os': compute_nb_servers * get_compute_os_price(),
            'compute_local_ssd': rate_compute_local_ssd * compute_local_ssd_size * compute_local_ssd * total_hours_per_month(compute_avg_minutes_per_day, compute_avg_days_per_week),
            'compute_storage_ssd': (rate_compute_storage_ssd / gib) * compute_storage_ssd * period,
            'compute_storage_standard': (rate_compute_storage_standard / gib) * compute_storage_standard * period,
            'compute_storage_snapshot': (rate_compute_storage_snapshot / gib) * compute_storage_snapshot * period,
            'forwarding_rules': get_forwarding_rules_price(),
            'storage_standard': (rate_storage_standard / gib) * storage_standard * period,
            'storage_dra': (rate_storage_dra / gib) * storage_dra * period,
            'storage_nearline': (rate_storage_nearline / gib) * storage_nearline * period,
            'restore_nearline': (rate_restore_nearline / gib) * restore_nearline * period,
            'class_a_operations': rate_class_a_operations * class_a_operations,
            'class_b_operations': rate_class_b_operations * class_b_operations,
            'egress_americas_emea': _egress(egress_americas_emea, rate_egress_tiers, rate_egress_americas_emea), # TODO Investigate egress billing
            'egress_asia_pacific': _egress(egress_asia_pacific, rate_egress_tiers, rate_egress_asia_pacific),    # for periods inferior to 30 days
            'egress_china': _egress(egress_china, rate_egress_tiers, rate_egress_china),
            'egress_australia': _egress(egress_australia, rate_egress_tiers, rate_egress_australia),
            'transfer_same_region': _transfer(transfer_same_region, rate_transfer_tiers, rate_transfer_same_region),
            'transfer_same_multiregion': _transfer(transfer_same_multiregion, rate_transfer_tiers, rate_transfer_same_multiregion),
            'transfer_region_multiregion': _transfer(transfer_region_multiregion, rate_transfer_tiers, rate_transfer_region_multiregion),
            'transfer_multiregion_multiregion': _transfer(transfer_multiregion_multiregion, rate_transfer_tiers, rate_transfer_multiregion_multiregion),
            'unused_static_ip' : total_hours_per_month(compute_avg_minutes_per_day, compute_avg_days_per_week) * rate_unused_static_ip * unused_static_ip
        }
        bill = {
            'detail': detail,
            'total': int(sum(detail.values())),
            'period': period,
        }
        for k, v in detail.iteritems():
            if type(v) == Fraction:
                detail[k] = int(v)
        return bill
    return google_cloud_storage_model

# Initialize with a stored model
current_model = gen_google_cloud_storage_model(**(configuration_from_json('pricings/1-6.json')))

@runner.task
@periodic_task(run_every=timedelta(hours=6))
def update_model():
    r = requests.get('https://cloudpricingcalculator.appspot.com/static/data/pricelist.json')
    new_model = gen_google_cloud_storage_model(**(configuration_from_json(r.json())))
    current_model = new_model

def apply_unit(magnitude, unit):
    return magnitude * units[unit]

if __name__ == '__main__':
    price = model_1_6(
        storage_standard=2 * tib,
        storage_dra=15 * tib,
        storage_nearline=15 * tib,
        class_a_operations=1000000,
        class_b_operations=4000000,
        egress_americas_emea=489*gib,
        egress_asia_pacific=22*tib,
        egress_australia=3*tib,
        transfer_same_region=10*tib,
        transfer_same_multiregion=20*tib,
        transfer_region_multiregion=30*tib,
        transfer_multiregion_multiregion=40*tib,
    )
    print(round(price['total'] / 1000.0, 2))
    print(price)

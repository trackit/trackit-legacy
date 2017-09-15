from app import ec2pricing
from app.es.awsidnamemapping import AWSIdNameMapping
from app.es.awsstat import AWSStat
from app.es.awsdetailedlineitem import AWSDetailedLineitem
from app.es.awsmetric import AWSMetric
from app.aws.instances import get_all_instances
import app.models as models
from collections import defaultdict
from scipy.stats import linregress
from datetime import date, timedelta, datetime
from app.aws import region_fullnames_inverse
from dateutil.relativedelta import relativedelta
import itertools

REGIONS = region_fullnames_inverse

YEAR_HOURS = (3 * 365 + 366) / 4 * 24
MONTH_HOURS = YEAR_HOURS / 12


def hours_since_epoch(hour):
    return int((hour - datetime(1970, 1, 1)).total_seconds() / 3600)


def parse_datetime(hour_str):
    return datetime.strptime('%', hour_str)


def count_forecast(hourly_counts, range_start, now, hours_ahead):
    hourly_counts = sorted(hourly_counts)
    for datum in hourly_counts:
        yield datum
    xys = ((hours_since_epoch(h), c) for h, c in hourly_counts)
    now = hours_since_epoch(now)
    range_start = hours_since_epoch(range_start)

    def filled_in_xys():
        last_h, last_v = next(xys)
        for h, v in xys:
            if h == last_h:
                last_v += v
            else:
                yield (last_h, last_v)
                for mid_h in xrange(last_h, h):
                    yield (mid_h, 0)
                last_h = h
                last_v = v
        yield (last_h, last_v)

    slope, intercept, _, _, _ = linregress(list(filled_in_xys()))
    if slope != slope:
        return
    last_hour = hourly_counts[-1][0]
    last_hour_since_epoch = hours_since_epoch(hourly_counts[-1][0])
    for hour_i in xrange(1, hours_ahead + 1):
        estimated_use = max(0, int(round(slope * (last_hour_since_epoch + hour_i) + intercept)))
        yield (last_hour + timedelta(hours=hour_i), estimated_use)


def group_by(keys, records):
    keys_and_results = [(k, defaultdict(list)) for k in xrange(len(keys))]
    for record in records:
        for key, results in keys:
            results[key(record)].append(record)
    return [res for _, res in keys_and_results]


def get_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_monthly_prices(total_hours, hourly_counts, prices, ondemand_price):
    count_hours_by_month = defaultdict(lambda: defaultdict(int))
    count_hours = defaultdict(int)

    for hour, count in hourly_counts:
        count_hours_by_month[get_month(hour)][count] += 1
        count_hours[count] += 1

    prices_and_counts = []
    for price in prices:
        res_count = get_best_reserved_count(count_hours, ondemand_price, price, total_hours)
        months = []
        for month, month_count_hours in count_hours_by_month.iteritems():
            cost = get_ondemand_cost(month_count_hours, price, res_count)
            cost += MONTH_HOURS * price * res_count
            months.append((month, cost))
        months.sort()
        prices_and_counts.append((price, res_count, months))
    months = []
    for month, month_count_hours in count_hours_by_month.iteritems():
        cost = get_ondemand_cost(month_count_hours, ondemand_price, 0)
        months.append((month, cost))
    months.sort()
    prices_and_counts.append((ondemand_price, None, months))

    return prices_and_counts

from cache import cache, compressed_json, decompressed_json

def get_reservation_forecast(keys):
    if not isinstance(keys, list):
        keys = list(keys)
    keys = set(models.AWSKey.query.filter_by(key=k).first() if isinstance(k, basestring) else k for k in keys)
    if not all(isinstance(k, models.AWSKey) for k in keys):
        raise TypeError('All keys must be strings or AWSKeys.')
    cache_key = 'get_reservation_forecast#' + models.MultikeyGroup.id_of(keys)
    cached = cache.get(cache_key)
    if cached:
        unpacked = decompressed_json(cached)
    else:
        unpacked = compute_reservation_forecast(keys)
        cache.setex(cache_key, 12 * 60 * 60, compressed_json(unpacked))
    return unpacked


def compute_reservation_forecast(keys):
    if isinstance(keys, models.AWSKey):
        keys = [keys]
    elif not isinstance(keys, list):
        keys = list(keys)
    if not all(isinstance(k, models.AWSKey) for k in keys):
        raise TypeError('All keys must be AWSKey.')
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    range_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    range_end -= timedelta(days=1)
    range_start = range_end - timedelta(days=120)
    range_start = range_start.replace(day=1)
    s = AWSDetailedLineitem.get_instance_type([k.get_aws_user_id() for k in keys], date_from=range_start, date_to=range_end)
    instance_type_hours = defaultdict(list)
    first_hour = datetime(2099, 1, 1)
    for r in s:
        rhour = datetime.strptime(r['hour'], "%Y-%m-%dT%H:%M:%S")
        if r['region'] != 'unknown':  # Some EC2 instances have no region, sometimes...
            instance_type_hours[(r['region'], r['instance'])].append((rhour, r['ridCount']))
            first_hour = min(first_hour, rhour)
    hours_ahead = 120 * 24
    total_hours = (range_end - first_hour).total_seconds() / 3600 - 1 + hours_ahead

    instance_types = []
    lookup = get_instance_lookup()
    for (region, instance_type), hours in instance_type_hours.iteritems():
        hours = count_forecast(hours, range_start, now, hours_ahead)
        prices = lookup[region, instance_type]
        price_results = get_monthly_prices(total_hours, hours, [p['amortized'] for p in prices['reserved']], prices['ondemand']['amortized'])
        ps = []
        for pricing, (_, count, months) in zip(prices['reserved'] + [prices['ondemand']], price_results):
            pricing = dict(pricing)
            if count is not None:
                pricing['count'] = count
            pricing['months'] = [dict(month=m.strftime('%Y-%m'), cost=c) for m, c in months[:-1]]
            ps.append(pricing)
        instance_types.append(dict(region=region, type=instance_type, pricing_options=ps))
    available_volumes = AWSStat.latest_available_volumes([k.key for k in keys])
    now = datetime.utcnow()
    date_from = now.replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=6)
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    volume_monthly_costs = AWSDetailedLineitem.get_monthly_cost_by_resource(available_volumes['volumes'] if 'volumes' in available_volumes else (), date_from=date_from, date_to=date_to)
    resources = AWSMetric.underutilized_resources([k.key for k in keys])
    rids = set(r['id'] for r in resources['resources'])
    months = AWSDetailedLineitem.get_monthly_cost_by_resource(rids, date_from=date_from, date_to=date_to)
    reduced_instance_costs = {
        k: v * 0.2
        for k, v in months.iteritems()
    }

    return dict(
        instances=instance_types,
        volume_monthly_costs=volume_monthly_costs,
        reduced_instance_costs=reduced_instance_costs,
    )


def get_best_reserved_count(count_hours, ondemand_hour, reserved_hour, hours_total):
    best = (float('inf'), 0)
    for reserved_count in count_hours:
        cost = hours_total * reserved_hour * reserved_count + get_ondemand_cost(count_hours, ondemand_hour, reserved_count)
        best = min(best, (cost, reserved_count))
    return best[1]


def get_ondemand_cost(count_hours, ondemand_hour, reserved_count):
    cost = 0
    for count, hours in count_hours.iteritems():
        cost += max(0, count - reserved_count) * hours * ondemand_hour
    return cost


def get_instance_lookup():
    pricing_data = ec2pricing.get_pricing_data()
    lookup = {}
    for instance_type in pricing_data:
        # TODO: deal with OS licensing
        if instance_type['operatingSystem'] != 'Linux':
            continue
        if 'govcloud' in instance_type['location'].lower():
            continue
        if 'BoxUsage' not in instance_type['usagetype'] or 'HostBoxUsage' in instance_type['usagetype']:
            continue
        try:
            key = (REGIONS[instance_type['location']], instance_type['instanceType'])
        except KeyError:
            continue
        assert key not in lookup
        ondemand = None
        pricings = []
        for p in instance_type['prices']:
            p = dict(p)
            p['amortized'] = p['costPerHour']
            if p['reservationYears']:
                p['amortized'] += p['upfrontCost'] / (YEAR_HOURS * p['reservationYears'])
                pricings.append(p)
            else:
                ondemand = p
        lookup[key] = dict(reserved=pricings, ondemand=ondemand)
    return lookup


def get_on_demand_to_reserved_suggestion(session, key):
    existing_instances = []
    for region, instance in get_all_instances(session):
        if instance.state != 'terminated':
            existing_instances.append(instance.id)
    now = datetime.utcnow()
    id_name_mapping = AWSIdNameMapping.get_id_name_mapping(key.key)
    instances_to_switch = AWSDetailedLineitem.get_instance_hour(key.get_aws_user_id(), now - timedelta(days=30), now, 15)
    res = []
    for instance in instances_to_switch:
        if instance['id'] in existing_instances:
            instance['name'] = id_name_mapping[instance['id']] if instance['id'] in id_name_mapping else instance['id']
            res.append(instance)
    return dict(total=len(res), on_demand_instances=res)

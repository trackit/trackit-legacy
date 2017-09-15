import json
from app import app
from app.msol_util import checksum, day_allocations
from app.gcloud.buckets import get_billing_files, download_billing_file
from models import db, User, GoogleCloudIdentity
from datetime import datetime, time
from time import strptime, mktime
import oauth2client
import httplib2
import msol_util
import apiclient
import flask
import json
import re

class GoogleCloudException(Exception):
    pass

class GoogleCloudBillingException(GoogleCloudException):
    pass

class GoogleCloudBillingValueException(GoogleCloudBillingException):
    pass

class GoogleCloudBillingFormatException(GoogleCloudBillingException):
    pass

def parse_billing_json(json_billing_data):
    try:
        if type(json_billing_data) == str:
            return json.loads(json_billing_data)
        elif type(json_billing_data) == file:
            return json.load(json_billing_data)
    except ValueError:
        raise GoogleCloudBillingFormatException('Failed to parse JSON data.')

def get_billing_record_raw(billing_file, billing_data):
    if type(billing_data) == list:
        for record in billing_data:
            yield record
    else:
        raise GoogleCloudBillingFormatException('Billing data is not a list.')

def get_all_line_items(identity, billing_bucket, since=None):
    first_month_string = since.strftime('%Y-%m') if since else ''
    for raw_file in get_billing_files(identity, billing_bucket):
        match = re.search(r'\d{4}-\d{2}-\d{2}', raw_file['name'])
        file_month_string = datetime.strptime(match.group(), '%Y-%m-%d').strftime('%Y-%m')
        if file_month_string < first_month_string:
            continue
        print raw_file['name']
        response, billing_data = download_billing_file(identity, raw_file)
        billing_json = parse_billing_json(billing_data)
        for record in get_billing_record_raw(raw_file, billing_json):
            yield record

class ResourceByDayAccumulator(object):
    def __init__(self):
        self._resource_by_day = {}
        self._time_cache = CachedTimeParse()

    def __call__(self, line_item):
        rid = line_item['lineItemId']
        description = line_item['description']
        account = line_item['accountId']
        project_number = line_item['projectNumber']
        project_name = project_number if not 'projectName' in line_item else line_item['projectName']
        usage_start = self._time_cache[line_item['startTime']]
        usage_end = self._time_cache[line_item['endTime']]
        cost = parse_float(line_item['cost']['amount'])

        credits = 0
        if 'credits' in line_item:
            for credit in line_item['credits']:
                credits += parse_float(credit['amount'])

        day = usage_end.date()
        key = (day, rid, project_number)
        if key not in self._resource_by_day:
            self._resource_by_day[key] = dict(description=description,
                                              project_name=project_name,
                                              product=rid.rsplit('/', 1)[0],
                                              date=day,
                                              cost=cost + credits,
                                              account=account,
                                              rid=rid,
                                              id=checksum(account, *map(str, key)))
        else:
            self._resource_by_day[key]['cost'] += cost
            self._resource_by_day[key]['cost'] += credits

    def results(self):
        for by_day in self._resource_by_day.itervalues():
            by_day = dict(by_day)
            yield by_day

def nonempty_parse(parser):
    def parse(val):
        if val:
            return parser(val)
    return parse

parse_json = nonempty_parse(lambda v: json.loads(v))

parse_time = nonempty_parse(lambda v: datetime.fromtimestamp(mktime(strptime(v.rsplit('-', 1)[0], '%Y-%m-%dT%H:%M:%S'))))

parse_float = nonempty_parse(float)

parse_str = nonempty_parse(lambda v: v)

class CachedTimeParse(dict):
    def __missing__(self, time_str):
        parsed = parse_time(time_str)
        self[time_str] = parsed
        return parsed

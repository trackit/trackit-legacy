from object_storage import S3BucketObjectStore
from config import BILLING_FILE_REGEX, CLIENT_BILLING_BUCKET, IMPORT_BILLING_AWS_KEY, IMPORT_BILLING_AWS_SECRET, LOCAL_BILLS_DIR
from es import client
from es.awsdetailedlineitem import AWSDetailedLineitem
from contextlib import contextmanager
from zipfile import ZipFile
from tempfile import mkdtemp, TemporaryFile
from shutil import rmtree
from datetime import date, datetime
import os
import io
import csv
import calendar
import elasticsearch.helpers
import itertools
import traceback
import boto3


def _is_line_item(line):
    return line['RecordType'] == 'LineItem'


def _str_to_date(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


@contextmanager
def extract_zipped_csvs(zip_stream, conversion=csv.reader):
    with TemporaryFile() as zip_file_stream:
        while True:
            chunk = zip_stream.read(2 ** 15)
            if not chunk:
                break
            zip_file_stream.write(chunk)
        zip_file = ZipFile(zip_file_stream)

        def files():
            for name in zip_file.namelist():
                if not name.lower().endswith('.csv'):
                    continue
                file = zip_file.open(name)
                yield name, conversion(file)
        try:
            yield files()
        except:
            pass


_index_es = 'awsdetailedlineitem'
_type_es = 'a_ws_detailed_lineitem'

session = boto3.Session(aws_access_key_id=IMPORT_BILLING_AWS_KEY,
                        aws_secret_access_key=IMPORT_BILLING_AWS_SECRET)

_converted_fields = {
    'PayerAccountId': str,
    'LinkedAccountId': str,
    # 'RecordId': int,
    'RateId': int,
    'SubscriptionId': int,
    'PricingPlanId': int,
    'UsageQuantity': float,
    'Rate': float,
    'BlendedRate': float,
    'UnBlendedRate': float,
    'Cost': float,
    'BlendedCost': float,
    'UnBlendedCost': float,
    'ReservedInstance': (lambda s: s == 'Y'),
    'UsageStartDate': _str_to_date,
    'UsageEndDate': _str_to_date,
    'UsageType': str,
}


_converted_name = {
    'PayerAccountId': 'payer_account_id',
    'LinkedAccountId': 'linked_account_id',
    'RecordId': 'record_id',
    'ProductName': 'product_name',
    'RateId': 'rate_id',
    'SubscriptionId': 'subscription_id',
    'PricingPlanId': 'pricing_plan_id',
    'UsageType': 'usage_type',
    'Operation': 'operation',
    'AvailabilityZone': 'availability_zone',
    'ReservedInstance': 'reserved_instance',
    'ItemDescription': 'item_description',
    'UsageStartDate': 'usage_start_date',
    'UsageEndDate': 'usage_end_date',
    'UsageQuantity': 'usage_quantity',
    'UsageType': 'usage_type',
    'Rate': 'rate',
    'BlendedRate': 'rate',
    'UnBlendedRate': 'un_blended_rate',
    'Cost': 'cost',
    'BlendedCost': 'cost',
    'UnBlendedCost': 'un_blended_cost',
    'ResourceId': 'resource_id',
    'Tags': 'tag',
}


_csv_path = lambda x: '{}{}'.format(LOCAL_BILLS_DIR, x)


def _line_to_document(line):
    try:
        line['Tags'] = []
        deleted_fields = set(('InvoiceID', 'RecordType'))
        for k, v in line.iteritems():
            if k.startswith('aws:') or k.startswith('user:'):
                if v:
                    line['Tags'].append({
                        'key': k,
                        'value': v,
                    })
                deleted_fields.add(k)
            elif not v and k != 'Tags':
                deleted_fields.add(k)
        if not line['Tags']:
            deleted_fields.add('Tags')
        for k in deleted_fields:
            del line[k]
        for k, v in line.iteritems():
            if k in _converted_fields:
                line[k] = _converted_fields[k](v)
        res = {}
        for k, v in line.iteritems():
            if k in _converted_name:
                res[_converted_name[k]] = v
        return res
    except:
        print("------")
        print(line)
        traceback.print_exc()
        return None


def _document_to_index(index):
    def do_document_to_index(document):
        try:
            return {
                '_index': index,
                '_id': document['record_id'],
                '_type': _type_es,
                '_source': document,
            } if 'record_id' in document else None
        except:
            print("------")
            print(document)
            traceback.print_exc()
            return None
    return do_document_to_index


def _clean_aws_discounts_in_es(month, es, account_id):
    month = datetime.combine(month, datetime.min.time())
    date_from = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date_to = month.replace(day=calendar.monthrange(month.year, month.month)[1], hour=0, minute=59, second=59, microsecond=999999)
    response = es.search(
        index=_index_es,
        filter_path=["hits.hits._id"],
        body={"size": 10000, "query": {"bool": {"filter": [
            {"term": {"item_description": "PAR_APN_ProgramFee_2500"}},
            {"term": {"linked_account_id": account_id}},
            {"range": {"usage_start_date": {"from": date_from, "to": date_to}}}
             ]}}})
    if 'hits' not in response or 'hits' not in response['hits']:
        return
    ids = [
        line['_id']
        for line in response['hits']['hits']
    ]
    if len(ids) < 0:
        return
    bulk_body = [
        '{{"delete": {{"_index": "{}", "_type": "{}", "_id": "{}"}}}}'.format(_index_es, _type_es, id)
        for id in ids
    ]
    es.bulk('\n'.join(bulk_body), timeout='120s', request_timeout=120)


def _import_bill_to_es(bill, es, name):
    tmp_file = bill.get_file() if CLIENT_BILLING_BUCKET else bill
    account_id = BILLING_FILE_REGEX.search(name).group('account_id')
    print name
    print '  Cleaning'
    _clean_aws_discounts_in_es(date(int(name[:-11][-4:]), int(name[:-8][-2:]), 1), es, account_id)
    print '  Extracting'
    with extract_zipped_csvs(tmp_file, lambda x: x) as files:
        for fi, csvfile in files:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            line_items = itertools.ifilter(_is_line_item, reader)
            documents = itertools.ifilter(bool, itertools.imap(_line_to_document, line_items))
            actions = itertools.ifilter(bool, itertools.imap(_document_to_index(_index_es), documents))
            print '  Importing'
            elasticsearch.helpers.bulk(es, actions, timeout='120s', request_timeout=120, chunk_size=200)
    tmp_file.close()
    print '  Ok'


def _upload_bill_to_s3(bill, session, force_yield=False):
    if not CLIENT_BILLING_BUCKET:
        if not os.path.exists(_csv_path(bill.key())):
            print bill.key()
            print '  Downloading'
            if not os.path.exists(_csv_path('')):
                os.mkdir(_csv_path(''))
            bill.get_file(f=io.open(_csv_path(bill.key()), 'w+b'))
            print '  Ok'
            return bill.key()
        return
    s3 = session.resource('s3')
    up_bill = S3BucketObjectStore(s3.Bucket(CLIENT_BILLING_BUCKET)).object(bill.key())
    if not up_bill.exists() or up_bill.size() != bill.size():
        print bill.key()
        print '  Downloading'
        f = bill.get_file()
        print '  Uploading'
        up_bill.put_file(f)
        print '  Ok'
        return bill.key()
    elif force_yield:
        return bill.key()


def prepare_bill_for_s3(key, force_yield=False):
    '''
    - Download bills (cf. BILLING_FILE_REGEX) from S3 with keys in key_ids if they differs from our S3.
    - Upload downloaded bills on our S3.
    - Yield name of uploaded bills.

    :param key: models.AWSKey
    :param force_yield: yield name of all bills instead of uploaded bills only
    :return: generator (list of string)
    '''
    if key.billing_bucket_name is None:
        return
    client_session = key.get_boto_session()
    client_s3 = client_session.resource('s3')
    bucket = sorted(S3BucketObjectStore(client_s3.Bucket(key.billing_bucket_name)), key=lambda x: x.key(), reverse=True)
    for bill in bucket:
        m = BILLING_FILE_REGEX.match(bill.key())
        if m is not None:
            yield _upload_bill_to_s3(bill, session, force_yield)


def prepare_bill_for_es(tr_bills):
    '''
    - Download bills in tr_bills from our S3
    - Process zip and csv
    - Import data in ES

    :param tr_bills: list of string
    :return:
    '''
    if not tr_bills:
        return
    s3 = session.resource('s3')
    AWSDetailedLineitem.init()
    for bill in tr_bills:
        if bill:
            s3_bill = S3BucketObjectStore(s3.Bucket(CLIENT_BILLING_BUCKET)).object(bill) if CLIENT_BILLING_BUCKET else io.open(_csv_path(bill), 'r+b')
            if not CLIENT_BILLING_BUCKET or s3_bill.exists():
                _import_bill_to_es(s3_bill, client, bill)

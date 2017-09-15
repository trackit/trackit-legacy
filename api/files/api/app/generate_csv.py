import csv
import StringIO

def _get_cost(rgg, name, tag_name, sub_header_name, tagged):
    for rg in rgg:
        if rg[sub_header_name].lower() == name:
            if not tagged:
                return rg['cost']
            else:
                for tagl in rg['tags']:
                    if tagl['name'] == tag_name:
                        return tagl['cost']
    return 0

def _process(splitted_res, header_column, header_name, sub_header_name, tagged, available_tag, account):
    fsplitted_res = splitted_res['months'] if account else splitted_res
    for r in fsplitted_res:
        if tagged:
            for atag in available_tag:
                gen = [_get_cost(r[header_name], p, atag, sub_header_name, tagged) for p in header_column]
                if sum(gen):
                    yield '{}{},{}{},{}\n'.format(
                        '{},{},'.format(splitted_res['account_name'], splitted_res['account_id']) if account else '',
                        r['month'],
                        str(sum(gen)),
                        ',{}'.format(atag) if tagged else '',
                        ','.join(str(g) for g in gen))
        else:
            gen = [_get_cost(r[header_name], p, None, sub_header_name, tagged) for p in header_column]
            yield '{}{},{},{}\n'.format(
                '{},{},'.format(splitted_res['account_name'], splitted_res['account_id']) if account else '',
                r['month'],
                str(sum(gen)),
                ','.join(str(g) for g in gen))

def generate_csv_clean(data, header_name):
    si = StringIO.StringIO()
    writer = csv.DictWriter(si, header_name)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return si.getvalue()


def generate_csv(data, header_name, sub_header_name, account=False, tagged=False):
    header_column = set(
        hc[sub_header_name].lower()
        for r in data
        for hc in r[header_name]
    ) if not account else set(
        hc[sub_header_name].lower()
        for p in data
        for r in p['months']
        for hc in r[header_name]
    )
    available_tag = set(
        t['name']
        for p in data
        for r in p['months']
        for hc in r[header_name]
        for t in hc['tags']
    ) if tagged else None
    yield '{}month,total{},{}\n'.format('account_name,account_id,' if account else '',
                                        ',tag' if tagged else '',
                                        ','.join(header_column))

    if account:
        for splitted_res in data:
            for p in _process(splitted_res, header_column, header_name, sub_header_name, tagged, available_tag, account):
                yield p
    else:
        for p in _process(data, header_column, header_name, sub_header_name, tagged, available_tag, account):
            yield p


def get_csv_links():
    res = [
        {
            'name': 'Monthly Cost By Region',
            'link': 'monthlycostbyregion',
        },
        {
            'name': 'Monthly Cost By Region By Account',
            'link': 'monthlycostbyregionbyaccount',
        },
        {
            'name': 'Monthly Cost By Region By Tag By Account',
            'link': 'monthlycostbyregionbytagbyaccount',
        },
        {
            'name': 'Monthly Cost By Product',
            'link': 'monthlycostbyproduct',
        },
        {
            'name': 'Monthly Cost By Product By Account',
            'link': 'monthlycostbyproductbyaccount',
        },
        {
            'name': 'Monthly Cost By Product By Tag By Account',
            'link': 'monthlycostbyproductbytagbyaccount',
        },
        {
            'name': 'Sizes of S3 buckets per name',
            'link': 's3bucketsizepername',
        },
        {
            'name': 'Sizes of S3 buckets per tag',
            'link': 's3bucketsizepertag'
        }
    ]
    return sorted(res, key=lambda x: x['name'])

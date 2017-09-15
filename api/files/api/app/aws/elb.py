from ..aws import region_names
from app.es import client

ELB_NAME = {
    'elb': 'LoadBalancerDescriptions',
    'elbv2': 'LoadBalancers',
}

def get_load_balancers(session):
    for elb_version in ('elb', 'elbv2'):
        for region_name in region_names:
            client = session.client(elb_version, region_name=region_name)
            paginator = client.get_paginator('describe_load_balancers')
            for page in paginator.paginate():
                for load_balancer in page[ELB_NAME[elb_version]]:
                    yield (elb_version, region_name, load_balancer)


def import_elb_infos(key):
    session = key.get_boto_session()
    for version, region, lb in get_load_balancers(session):
        doc = {
            'linked_account_id': key.get_aws_user_id(),
            'name': lb['LoadBalancerName'],
            'region': region,
        }
        if version == 'elb':
            doc['instances'] = ' '.join([instance['InstanceId'] for instance in lb['Instances']])
        elif version == 'elbv2':
            doc['instances'] = ''
        client.index(index='awselbinfo', doc_type='a_ws_el_binfo', body=doc, ttl='18h', timeout='120s', request_timeout=120)

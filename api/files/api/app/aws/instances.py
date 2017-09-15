from ..aws import region_names
from app.es.awsmetric import AWSMetric
from app.es.awsstat import AWSStat
from collections import defaultdict
import time

def get_rds_instances(session):
    for region_name in region_names:
        client = session.client('rds', region_name=region_name)
        paginator = client.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                yield (region_name, instance)

def get_running_instances(session):
    for region_name in region_names:
        client = session.resource('ec2', region_name=region_name)
        instances = client.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        for instance in instances:
            yield (region_name, instance)

def get_all_instances(session):
    for region_name in region_names:
        ec2 = session.resource('ec2', region_name=region_name)
        for i in ec2.instances.iterator():
            yield (region_name, i)

def get_instance_stats(session):
    reserved_instances_report = []
    az_class_reservations = defaultdict(int)
    az_class_running_instances = defaultdict(int)
    stopped_instances = 0

    for region_name in region_names:
        client = session.client('ec2', region_name=region_name)
        reserved = client.describe_reserved_instances()
        instances = client.describe_instances()

        for r in reserved['ReservedInstances']:
            if r['State'] != "retired":
                if r['Scope'] == 'Region':
                    placement = region_name
                elif 'AvailabilityZone' in r:
                    placement = r['AvailabilityZone']
                else:
                    continue
                az_class_reservations[(placement, r['InstanceType'])] += r['InstanceCount']
                reserved_instances_report.append({
                    'location': placement,
                    'offer': r['OfferingType'],
                    'instance_type': r['InstanceType'],
                    'state': r['State'],
                    'count': r['InstanceCount'],
                    'start': time.mktime(r['Start'].timetuple()),
                    'end': time.mktime(r['End'].timetuple())
                })

        for r in instances['Reservations']:
            for i in r['Instances']:
                if i['State']['Name'] == 'running':
                    az_class_running_instances[(i['Placement']['AvailabilityZone'], i['InstanceType'])] += 1
                else:
                    stopped_instances += 1

    reserved_instances = 0
    unreserved_instances = 0
    unused_reserved_instances = 0

    az_classes = set(az_class_reservations.keys() + az_class_running_instances.keys())
    for az_class in az_classes:
        reserved = az_class_reservations[az_class]
        running = az_class_running_instances[az_class]
        if az_class[0] in region_names:
            reserved_instances += reserved
        elif reserved > running:
            unused_reserved_instances += reserved - running
        else:
            unreserved_instances += running - reserved
        reserved_instances += min(reserved, running)

    reserved_instances_report.sort(key=lambda x: x['end'])

    return dict(reserved_instances_report=reserved_instances_report,
                reserved=reserved_instances,
                unreserved=unreserved_instances,
                unused=unused_reserved_instances,
                stopped=stopped_instances)

def get_instances_id_name_mapping(session):
    res = {}
    for region, instance in get_all_instances(session):
        try:
            instance_name = next(d['Value'] for (index, d) in enumerate(instance.tags) if d["Key"] == "Name")
        except:
            instance_name = instance.id
        res[instance.id] = instance_name
    for region, instance in get_rds_instances(session):
        if 'DBName' in instance:
            res[instance['DBInstanceIdentifier']] = instance['DBName']
        else:
            res[instance['DBInstanceIdentifier']] = instance['DBInstanceIdentifier']
    return res

def get_hourly_cpu_usage_by_tag(session, key):
    tags = defaultdict(lambda : defaultdict(list))
    res = defaultdict(list)
    for region, instance in get_all_instances(session):
        if instance.tags:
            for tag in instance.tags:
                if tag['Key'] != 'Name' and not tag['Key'].startswith('aws:'):
                    tags[tag['Key']][tag['Value']].append(region+'/'+instance.id)
    for tag_key, tag_values_dict in tags.iteritems():
        for tag_value, instance_ids in tag_values_dict.iteritems():
            usage = AWSMetric.hourly_cpu_usage(key, resources=instance_ids)
            if usage:
                res[tag_key].append(dict(tag_value=tag_value, usage=usage, nb_instances=len(instance_ids)))
    for tag_key, values in res.iteritems():
        res[tag_key] = sorted(res[tag_key], key=lambda x: x['nb_instances'], reverse=True)[:10]
    return dict(tags=res)

def get_daily_cpu_usage_by_tag(session, key):
    tags = defaultdict(lambda : defaultdict(list))
    res = defaultdict(list)
    for region, instance in get_all_instances(session):
        if instance.tags:
            for tag in instance.tags:
                if tag['Key'] != 'Name' and not tag['Key'].startswith('aws:'):
                    tags[tag['Key']][tag['Value']].append(region+'/'+instance.id)
    for tag_key, tag_values_dict in tags.iteritems():
        for tag_value, instance_ids in tag_values_dict.iteritems():
            usage = AWSMetric.days_of_the_week_cpu_usage(key, resources=instance_ids)
            if usage:
                res[tag_key].append(dict(tag_value=tag_value, usage=usage, nb_instances=len(instance_ids)))
    for tag_key, values in res.iteritems():
        res[tag_key] = sorted(res[tag_key], key=lambda x: x['nb_instances'], reverse=True)[:10]
    return dict(tags=res)

def get_stopped_instances_report(session, key, days=5):
    stopped_instances = []
    for region, instance in get_all_instances(session):
        latest_states = AWSStat.get_latest_instance_states(key, instance.id, days)
        if len(latest_states) != days:
            continue
        not_stopped_states = [state for state in latest_states if state['state'] != 'stopped']
        if not len(not_stopped_states):
            stopped_instances.append(instance.id)
    return dict(stopped_instances=stopped_instances, total=len(stopped_instances))

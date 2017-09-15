import boto3
import traceback
from fractions import Fraction
from app.aws import region_fullnames, region_names_aws_google, region_names_aws_azure
from app.aws.instances import get_running_instances as get_running_instances_aws
from app.gcloud import number_cpu_instances as gcloud_number_cpu_instances
from app.gcloud.instances import get_running_instances as get_running_instances_gcloud
from app.ec2pricing import get_pricing_data
from app.azure import estimate_cost as estimate_cost_azure
from app import google_storage, app
from app.es.awsmetric import AWSMetric
from app.es.googlemetric import GoogleMetric
from app.models import db, AWSKey
from app.error_email import aws_credentials_error, aws_my_resources_error_email
import logging
import traceback

gb = Fraction(10 ** 9)
mb = Fraction(10 ** 6)

regions_mapping = [
    {'aws': 'us-east-1', 'gcloud': 'us', 'azure': 'US'},
    {'aws': 'us-east-2', 'gcloud': 'us', 'azure': 'US'},
    {'aws': 'us-west-1', 'gcloud': 'us', 'azure': 'US'},
    {'aws': 'us-west-2', 'gcloud': 'us', 'azure': 'US'},
    {'aws': 'ap-northeast-1', 'gcloud': 'asia', 'azure': 'JP'},
    {'aws': 'ap-northeast-2', 'gcloud': 'asia', 'azure': 'JP'},
    {'aws': 'ap-southeast-1', 'gcloud': 'asia', 'azure': 'SG'},
    {'aws': 'ap-southeast-2', 'gcloud': 'asia', 'azure': 'AU'},
    {'aws': 'sa-east-1', 'gcloud': 'us', 'azure': 'BR'},
    {'aws': 'eu-central-1', 'gcloud': 'europe', 'azure': 'NL'},
    {'aws': 'eu-west-1', 'gcloud': 'europe', 'azure': 'IE'}
]

def get_regions_mapping(provider, region_name):
    for region in regions_mapping:
        if provider in region and region[provider] == region_name:
            return region
    return None

instances_mapping = [
    {'aws': 't2.nano', 'gcloud': {'compute_instance_type' : 'g1-small'}, 'azure': {'compute_instance_type' : 'A0 VM'}},
    {'aws': 't2.nano', 'gcloud': {'compute_instance_type' : 'f1-micro'}, 'azure': {'compute_instance_type' : 'A0 VM'}},
    {'aws': 't2.micro', 'gcloud': {'compute_instance_type' : 'g1-small'}, 'azure': {'compute_instance_type' : 'A0 VM'}},
    {'aws': 't2.small', 'gcloud': {'compute_instance_type' : 'n1-standard-1'}, 'azure': {'compute_instance_type' : 'A1 VM'}},
    {'aws': 't2.medium', 'gcloud': {'compute_instance_type' : 'n1-standard-1'}, 'azure': {'compute_instance_type' : 'A2 VM'}},
    {'aws': 't2.large', 'gcloud': {'compute_instance_type' : 'n1-standard-2'}, 'azure': {'compute_instance_type' : 'Standard_D2 VM'}},
    {'aws': 'm4.large', 'gcloud': {'compute_instance_type' : 'n1-standard-2'}, 'azure': {'compute_instance_type' : 'Standard_D2_v2 VM'}},
    {'aws': 'm4.xlarge', 'gcloud': {'compute_instance_type' : 'n1-standard-4'}, 'azure': {'compute_instance_type' : 'Standard_D3 VM'}},
    {'aws': 'm4.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-standard-8'}, 'azure': {'compute_instance_type' : 'Standard_D4 VM'}},
    {'aws': 'm4.4xlarge', 'gcloud': {'compute_instance_type' : 'n1-standard-16'}, 'azure': {'compute_instance_type' : 'Standard_D5_v2 VM'}},
    {'aws': 'm4.10xlarge', 'gcloud': {'compute_instance_type' : 'n1-standard-32'}, 'azure': {'compute_instance_type' : 'Standard_D5_v2 VM'}},
    {'aws': 'm3.medium', 'gcloud': {'compute_instance_type' : 'n1-standard-1'}, 'azure': {'compute_instance_type' : 'Standard_D1 VM'}},
    {'aws': 'm3.large', 'gcloud': {'compute_instance_type' : 'n1-standard-2'}, 'azure': {'compute_instance_type' : 'Standard_D2 VM'}},
    {'aws': 'm3.xlarge', 'gcloud': {'compute_instance_type' : 'n1-standard-4'}, 'azure': {'compute_instance_type' : 'Standard_D3 VM'}},
    {'aws': 'm3.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-standard-8'}, 'azure': {'compute_instance_type' : 'Standard_D4 VM'}},
    {'aws': 'c4.large', 'gcloud': {'compute_instance_type' : 'n1-highcpu-2'}, 'azure': {'compute_instance_type' : 'Standard_F2 VM'}},
    {'aws': 'c4.xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-4'}, 'azure': {'compute_instance_type' : 'Standard_F4 VM'}},
    {'aws': 'c4.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-8'}, 'azure': {'compute_instance_type' : 'Standard_F8 VM'}},
    {'aws': 'c4.4xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-16'}, 'azure': {'compute_instance_type' : 'Standard_F16 VM'}},
    {'aws': 'c4.8xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-32'}, 'azure': {'compute_instance_type' : 'Standard_F16 VM'}},
    {'aws': 'c3.large', 'gcloud': {'compute_instance_type' : 'n1-highcpu-2'}, 'azure': {'compute_instance_type' : 'Standard_F2 VM'}},
    {'aws': 'c3.xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-4'}, 'azure': {'compute_instance_type' : 'Standard_F4 VM'}},
    {'aws': 'c3.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-8'}, 'azure': {'compute_instance_type' : 'Standard_F8 VM'}},
    {'aws': 'c3.4xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-16'}, 'azure': {'compute_instance_type' : 'Standard_F16 VM'}},
    {'aws': 'c3.8xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-32'}, 'azure': {'compute_instance_type' : 'Standard_F16 VM', 'compute_nb_servers': 2}},
    {'aws': 'x1.32xlarge', 'gcloud': {'compute_instance_type' : 'n1-highcpu-32'}, 'azure': {'compute_instance_type' : 'Standard_F16 VM', 'compute_nb_servers': 2}},
    {'aws': 'r3.large', 'gcloud': {'compute_instance_type' : 'n1-highmem-2'}, 'azure': {'compute_instance_type' : 'Standard_D11 VM'}},
    {'aws': 'r3.xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-4'}, 'azure': {'compute_instance_type' : 'Standard_D12 VM'}},
    {'aws': 'r3.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-8'}, 'azure': {'compute_instance_type' : 'Standard_D13 VM'}},
    {'aws': 'r3.4xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-16'}, 'azure': {'compute_instance_type' : 'Standard_D14 VM'}},
    {'aws': 'r3.8xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-32'}, 'azure': {'compute_instance_type' : 'Standard_D14 VM', 'compute_nb_servers': 2}},
    {'aws': 'i2.xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-4'}, 'azure': {'compute_instance_type' : 'Standard_D12_v2 VM'}},
    {'aws': 'i2.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-8'}, 'azure': {'compute_instance_type' : 'Standard_D13_v2 VM'}},
    {'aws': 'i2.4xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-16'}, 'azure': {'compute_instance_type' : 'Standard_D14_v2 VM'}},
    {'aws': 'i2.8xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-32'}, 'azure': {'compute_instance_type' : 'Standard_D15_v2 VM'}},
    {'aws': 'd2.xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-4'}, 'azure': {'compute_instance_type' : 'A6 VM'}},
    {'aws': 'd2.2xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-8'}, 'azure': {'compute_instance_type' : 'A7 VM'}},
    {'aws': 'd2.4xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-16'}, 'azure': {'compute_instance_type' : 'A9 VM'}},
    {'aws': 'd2.8xlarge', 'gcloud': {'compute_instance_type' : 'n1-highmem-32'}, 'azure': {'compute_instance_type' : 'A9 VM'}}
]

def get_instances_mapping(provider, instance_size):
    for instances in instances_mapping:
        if provider not in instances:
            continue
        if type(instances[provider]) is str and instances[provider] == instance_size:
            return instances
        elif type(instances[provider]) is dict and instances[provider]['compute_instance_type'] == instance_size:
            return instances
    return None

aws_default_costs = {
    'm3.large': 0.133,
    'c3.4xlarge': 0.84
}

aws_disk_throughput = {
    'io1': 320 * mb,
    'gp2': 160 * mb,
    'st1': 500 * mb,
    'sc1': 250 * mb,
    'standard': 90 * mb,
    'default': 160 * mb
}

aws_bandwidth = {
    'Low': 6.25 * mb,
    'Low to Moderate': 37.5 * mb,
    'Moderate': 37.5 * mb,
    'High': 125 * mb,
    'Very high': 1250 * mb,
    '10 Gigabit': 1250 * mb,
    'default': 37.5 * mb
}

gcloud_disk_throughput = {
    'standard': {'read': 180 * mb, 'write': 120 * mb},
    'SSD': {'read': 240 * mb, 'write': 240 * mb},
    'SCSI': {'read': 1560 * mb, 'write': 1090 * mb},
    'NVMe': {'read': 2650 * mb, 'write': 1400 * mb},
    'default': {'read': 180 * mb, 'write': 120 * mb}
}

def calculate_aws_cost(aws_pricing_data, instance, regions):
    try:
        if instance['provider'] == 'aws':
            instance_size = instance['size']
        else:
            instances = get_instances_mapping(instance['provider'], instance['size'])
            instance_size = instances['aws']
        aws_instance_pricing = aws_pricing_data[(instance_size, region_fullnames[regions['aws']], 'Linux')]
        aws_cost_per_hour = next(x for x in aws_instance_pricing['prices'] if x['type'] == 'ondemand')['costPerHour']
        if aws_cost_per_hour == 0 and instance_size in aws_default_costs:
            aws_cost_per_hour = aws_default_costs[instance_size]
    except Exception, e:
        traceback.print_exc()
        print(instance)
        print(regions)
        return 0
    return aws_cost_per_hour

def calculate_google_cost(instance, regions):
    try:
        if instance['provider'] == 'gcloud':
            instance_size = {'compute_instance_type': instance['size']}
        else:
            instances = get_instances_mapping(instance['provider'], instance['size'])
            instance_size = instances['gcloud']
        args = dict(compute_nb_servers = 1, compute_location = regions['gcloud'])
        args.update(instance_size)
        res = google_storage.current_model(**args)
    except Exception, e:
        traceback.print_exc()
        print(instance)
        print(regions)
        return 0
    return res['total'] / 1000.0 / (res['period'] * 24)

def calculate_azure_cost(instance, regions):
    try:
        if instance['provider'] == 'azure':
            instance_size = {'compute_instance_type': instance['size']}
        else:
            instances = get_instances_mapping(instance['provider'], instance['size'])
            instance_size = instances['azure']
        args = dict(compute_nb_servers = 1)
        args.update(instance_size)
        res = estimate_cost_azure(**args)
    except:
        return 0
    return res['total'] / 1000.0 / (res['period'] * 24)

def calculate_providers_cost(aws_pricing_data, instance, region):
    regions = get_regions_mapping(instance['provider'], region)
    prices = []
    prices.append(dict(name='aws', cost=calculate_aws_cost(aws_pricing_data, instance, regions)))
    prices.append(dict(name='gcloud', cost=calculate_google_cost(instance, regions)))
    prices.append(dict(name='azure', cost=calculate_azure_cost(instance, regions)))
    instance['prices'] = prices
    return instance

def get_io_throughput_aws(metrics_name, iops_usage, bytes_usage):
    read_iops = 0 if metrics_name not in iops_usage['read'] else iops_usage['read'][metrics_name]
    write_iops = 0 if metrics_name not in iops_usage['write'] else iops_usage['write'][metrics_name]
    read_bytes = 0 if metrics_name not in bytes_usage['read'] else bytes_usage['read'][metrics_name]
    write_bytes = 0 if metrics_name not in bytes_usage['write'] else bytes_usage['write'][metrics_name]
    read_throughput = read_iops * read_bytes
    write_throughput = write_iops * write_bytes
    return read_throughput + write_throughput

def get_io_usage_aws(region, instance, instance_iops_usage, instance_bytes_usage, volume_iops_usage, volume_bytes_usage):
    volumes_usage = []
    metrics_instance_name = region+'/'+instance.id
    instance_read_iops = 0 if metrics_instance_name not in instance_iops_usage['read'] else instance_iops_usage['read'][metrics_instance_name]
    instance_write_iops = 0 if metrics_instance_name not in instance_iops_usage['write'] else instance_iops_usage['write'][metrics_instance_name]
    if instance_read_iops or instance_write_iops:
        max_throughput = aws_disk_throughput['default']
        throughput = get_io_throughput_aws(metrics_instance_name, instance_iops_usage, instance_bytes_usage)
        percent = throughput * 100 / max_throughput
        volumes_usage.append(percent)

    for volume in instance.volumes.all():
        max_throughput = aws_disk_throughput['default'] if volume.volume_type not in aws_disk_throughput else aws_disk_throughput[volume.volume_type]
        throughput = get_io_throughput_aws(region+'/'+volume.id, volume_iops_usage, volume_bytes_usage)
        percent = float(throughput * 100 / max_throughput)
        if percent > 100.0:
            percent = 100
        volumes_usage.append(percent)

    return 0 if not len(volumes_usage) else sum(volumes_usage) / len(volumes_usage)

def get_io_throughput_gcloud(disk_infos, disk_iops_usage, disk_bytes_usage):
    device_name = disk_infos['deviceName']
    read_iops = 0 if device_name not in disk_iops_usage['read'] else disk_iops_usage['read'][device_name]
    write_iops = 0 if device_name not in disk_iops_usage['write'] else disk_iops_usage['write'][device_name]
    read_bytes = 0 if device_name not in disk_bytes_usage['read'] else disk_bytes_usage['read'][device_name]
    write_bytes = 0 if device_name not in disk_bytes_usage['write'] else disk_bytes_usage['write'][device_name]
    read_throughput = read_iops * read_bytes
    write_throughput = write_iops * write_bytes
    return read_throughput, write_throughput

def get_io_usage_gcloud(instance, disk_iops_usage, disk_bytes_usage):
    disks_usage = []
    for disk_infos in instance['disks']:
        max_throughput = gcloud_disk_throughput['default'] if disk_infos['interface'] not in gcloud_disk_throughput else gcloud_disk_throughput[disk_infos['interface']]
        read_throughput, write_throughput = get_io_throughput_gcloud(disk_infos, disk_iops_usage, disk_bytes_usage)
        percent_read = float(read_throughput * 100 / max_throughput['read'])
        percent_write = float(write_throughput * 100 / max_throughput['write'])
        percent = (percent_read + percent_write) / 2
        if percent > 100:
            percent = 100
        disks_usage.append(percent)
    return 0 if not len(disks_usage) else sum(disks_usage) / len(disks_usage)

def get_bandwidth_usage_aws(region, instance, aws_pricing_data, network_usage):
    metrics_resource_name = region + '/' + instance.id
    networkPerformance = aws_pricing_data[(instance.instance_type, region_fullnames[region], 'Linux')]['networkPerformance']
    bandwidth = aws_bandwidth['default'] if networkPerformance not in aws_bandwidth else aws_bandwidth[networkPerformance]

    network_in = 0 if metrics_resource_name not in network_usage['in'] else network_usage['in'][metrics_resource_name]
    network_out = 0 if metrics_resource_name not in network_usage['out'] else network_usage['out'][metrics_resource_name]
    total = network_in + network_out
    percent = float(total * 100 / bandwidth)
    # Avoid usage > 100%, it could happen because we do not know the real bandwidth
    if percent > 100.0:
        percent = 100
    return percent

def get_bandwidth_usage_gcloud(instance, network_usage):
    nb_cores = 1 if instance['size'] not in gcloud_number_cpu_instances else gcloud_number_cpu_instances[instance['size']]
    max_throughput = 2 * gb * nb_cores
    # througput limit for a virtual machine
    if max_throughput > 16 * gb:
        max_throughput = 16 * gb
    network_in = 0 if instance['name'] not in network_usage['in'] else network_usage['in'][instance['name']]
    network_out = 0 if instance['name'] not in network_usage['out'] else network_usage['out'][instance['name']]
    total = network_in + network_out
    percent = float(total * 100 / max_throughput)
    if percent > 100.0:
        percent = 100
    return percent

def get_providers_comparison_aws(aws_account):
    aws_account = AWSKey.query.get(aws_account.id)
    res = []
    try:
        session = boto3.Session(aws_access_key_id=aws_account.key,
                                aws_secret_access_key=aws_account.secret)
    except Exception, e:
        logging.error("[user={}][key={}] {}".format(aws_account.user.email, aws_account.pretty or aws_account.key, str(e)))
        aws_credentials_error(aws_account, traceback.format_exc())
        aws_account.error_status = u"bad_key"
        db.session.commit()
        return

    try:
        aws_pricing_data = {(f['instanceType'], f['location'], f['operatingSystem']): f for f in get_pricing_data() if 'HostBoxUsage' not in f.get('usagetype', '')}

        cpu_usage = {key: value for key, value in AWSMetric.get_cpu_usage(aws_account.key)}
        instance_iops_usage = {
            'read': {key: value for key, value in AWSMetric.get_instance_read_iops_usage(aws_account.key)},
            'write': {key: value for key, value in AWSMetric.get_instance_write_iops_usage(aws_account.key)}
        }
        instance_bytes_usage = {
            'read': {key: value for key, value in AWSMetric.get_instance_read_bytes_usage(aws_account.key)},
            'write': {key: value for key, value in AWSMetric.get_instance_write_bytes_usage(aws_account.key)}
        }
        volume_iops_usage = {
            'read': {key: value for key, value in AWSMetric.get_volume_read_iops_usage(aws_account.key)},
            'write': {key: value for key, value in AWSMetric.get_volume_write_iops_usage(aws_account.key)}
        }
        volume_bytes_usage = {
            'read': {key: value for key, value in AWSMetric.get_volume_read_bytes_usage(aws_account.key)},
            'write': {key: value for key, value in AWSMetric.get_volume_write_bytes_usage(aws_account.key)}
        }
        network_usage = {
            'in': {key: value for key, value in AWSMetric.get_network_in_usage(aws_account.key)},
            'out': {key: value for key, value in AWSMetric.get_network_out_usage(aws_account.key)}
        }

        for region, instance in get_running_instances_aws(session):
            metrics_resource_name = region + '/' + instance.id
            try:
                instance_name = next(d['Value'] for (index, d) in enumerate(instance.tags) if d["Key"] == "Name")
            except:
                instance_name = instance.id
            instance_infos = calculate_providers_cost(aws_pricing_data, dict(name=instance_name, size=instance.instance_type, provider='aws'), region)
            instance_infos.update({'region': region, 'id': instance.id})
            instance_infos.update({'cpu_usage' : 0 if metrics_resource_name not in cpu_usage else cpu_usage[metrics_resource_name]})
            instance_infos.update({'io_usage' : get_io_usage_aws(region, instance, instance_iops_usage, instance_bytes_usage, volume_iops_usage, volume_bytes_usage)})
            instance_infos.update({'bandwidth_usage': get_bandwidth_usage_aws(region, instance, aws_pricing_data, network_usage)})
            res.append(instance_infos)
        return res
    except Exception, e:
        logging.error("[user={}][key={}] my resources: {}".format(aws_account.user.email, aws_account.pretty or aws_account.key, str(e)))
        aws_my_resources_error_email(aws_account, traceback.format_exc())
        return None

def get_providers_comparison_google(identity):
    aws_pricing_data = {(f['instanceType'], f['location'], f['operatingSystem']): f for f in get_pricing_data() if 'HostBoxUsage' not in f.get('usagetype', '')}

    cpu_usage = {key: value for key, value in GoogleMetric.get_cpu_usage(identity.email)}

    disk_iops_usage = {
        'read': {key: value for key, value in GoogleMetric.get_disk_read_iops_usage(identity.email)},
        'write': {key: value for key, value in GoogleMetric.get_disk_write_iops_usage(identity.email)}
    }
    disk_bytes_usage = {
        'read': {key: value for key, value in GoogleMetric.get_disk_read_bytes_usage(identity.email)},
        'write': {key: value for key, value in GoogleMetric.get_disk_write_bytes_usage(identity.email)}
    }
    network_usage = {
        'in': {key: value for key, value in GoogleMetric.get_network_in_usage(identity.email)},
        'out': {key: value for key, value in GoogleMetric.get_network_out_usage(identity.email)}
    }

    res = []
    for instance in get_running_instances_gcloud(identity):
        instance_name = instance['name'] or instance['id']
        instance_size = instance['machineType'].rsplit('/', 1)[1]
        region = instance['zone'].rsplit('/', 1)[1].split('-', 1)[0]
        instance_infos = calculate_providers_cost(aws_pricing_data, dict(name=instance_name, size=instance_size, provider='gcloud'), region)
        instance_infos.update({'cpu_usage' : 0 if instance_name not in cpu_usage else cpu_usage[instance_name] * 100})
        instance_infos.update({'io_usage' : get_io_usage_gcloud(instance, disk_iops_usage, disk_bytes_usage)})
        instance_infos.update({'bandwidth_usage': get_bandwidth_usage_gcloud(instance_infos, network_usage)})
        res.append(instance_infos)
    return res

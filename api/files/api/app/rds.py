import boto3
from app.aws import region_fullnames
from app.aws.instances import get_rds_instances
from app.rdspricing import get_pricing_data

rds_engine_pricing_name = {
    'aurora': 'Aurora MySQL',
    'mysql': 'MySQL',
    'mariadb': 'MySQL',
    'postgres': 'PostgreSQL',
    'oracle': 'Oracle',
    'sqlserver': 'SQL Server'
}

supported_db_engines = [
    'mariadb',
    'mysql',
    'aurora',
    'postgres',
    'oracle',
    'sqlserver'
]

def calculate_engine_cost(rds_pricing_data, instance, region, engine):
    if engine == 'aurora':
        return calculate_aurora_cost(rds_pricing_data, instance, region)
    if engine == 'mysql' and instance['engine'] == 'mariadb':
        engine = 'mariadb'
    try:
        rds_instance_pricing = rds_pricing_data[(instance['size'], region_fullnames[region], rds_engine_pricing_name[engine])]
        cost_per_hour = next(x for x in rds_instance_pricing['prices'] if x['type'] == 'ondemand')['costPerHour']
        if instance['multi-az'] == True or instance['engine'] == 'aurora':
            cost_per_hour = cost_per_hour * 2
    except:
        cost_per_hour = 0
    return dict(name=engine, cost=cost_per_hour)

def calculate_aurora_cost(rds_pricing_data, instance, region):
    engine = 'aurora'
    try:
        rds_aurora_instance_pricing = rds_pricing_data[(instance['size'], region_fullnames[region], rds_engine_pricing_name[engine])]
    except:
        rds_aurora_instance_pricing = rds_pricing_data[('db.r3.large', region_fullnames[region], rds_engine_pricing_name[engine])]
    aurora_cost_per_hour = next(x for x in rds_aurora_instance_pricing['prices'] if x['type'] == 'ondemand')['costPerHour']
    return dict(name=engine, cost=aurora_cost_per_hour)

def calculate_rds_instance_cost(rds_pricing_data, instance, region):
    engines = ['aurora', 'mysql', 'postgres', 'oracle', 'sqlserver']
    prices = []
    for engine in engines:
        try:
            prices.append(calculate_engine_cost(rds_pricing_data, instance, region, engine))
        except Exception as exc:
            pass
    if not prices:
        raise exc
    instance['prices'] = prices
    return instance

def compare_rds_instances(aws_account):
    session = boto3.Session(aws_access_key_id=aws_account.key,
                            aws_secret_access_key=aws_account.secret)

    rds_pricing_data = {(f['instanceType'], f['location'], f['databaseEngine']): f for f in get_pricing_data()}

    instances = []
    for region, instance in get_rds_instances(session):
        if instance['Engine'] in supported_db_engines:
            infos = {
                'size': instance['DBInstanceClass'],
                'name': instance['DBInstanceIdentifier'],
                'engine': instance['Engine'],
                'multi-az': instance['MultiAZ']
            }
            instance_infos = calculate_rds_instance_cost(rds_pricing_data, infos, region)
            instance_infos.update({'region': region, 'id': instance['DbiResourceId']})
            instances.append(instance_infos)
    return instances

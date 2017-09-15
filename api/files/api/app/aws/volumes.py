from ..aws import region_names

def get_volumes(session):
    for region_name in region_names:
        client = session.client('ec2', region_name=region_name)
        paginator = client.get_paginator('describe_volumes')
        for page in paginator.paginate():
            for volume in page['Volumes']:
                yield (region_name, volume)

def get_volumes_id_name_mapping(session):
    res = {}
    for region, volume in get_volumes(session):
        try:
            volume_name = next(d['Value'] for (index, d) in enumerate(volume['Tags']) if d["Key"] == "Name")
        except:
            volume_name = volume['VolumeId']
        res[volume['VolumeId']] = volume_name
    return res

def get_available_volumes(session):
    res = []
    for region, volume in get_volumes(session):
        if volume['State'] == 'available':
            res.append(volume['VolumeId'])
    return dict(volumes=res, total=len(res))

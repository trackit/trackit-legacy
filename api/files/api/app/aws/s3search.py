import boto3
from .buckets import get_s3_buckets


def search_buckets(key, search_key="", search_bucket=""):
    session = boto3.Session(aws_access_key_id=key.key,
                            aws_secret_access_key=key.secret)
    list_files = []
    for bucket in get_s3_buckets(session):
        if not search_bucket or search_bucket == bucket['Name']:
            client = session.client('s3')
            for object in client.list_objects(Bucket=bucket['Name'])['Contents']:
                if object['Key'].split("/")[-1].find(search_key) != -1:
                    object['Bucket'] = bucket['Name']
                    list_files.append(object)
    return { "result": list_files }

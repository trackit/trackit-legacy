def get_s3_buckets(session):
    client = session.client('s3')
    for bucket in client.list_buckets()['Buckets']:
        yield bucket

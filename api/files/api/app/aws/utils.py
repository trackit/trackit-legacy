import boto3

def check_if_valid_key(key, secret):
    try:
        session = boto3.Session(aws_access_key_id=key,
                                aws_secret_access_key=secret)
        client = session.client('sts')
        response = client.get_caller_identity()
        return True
    except:
        return False

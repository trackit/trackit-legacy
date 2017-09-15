from datetime import datetime
from app import google_storage
from app.s3pricing import S3CostEstimator
from app.es.awsmetric import AWSMetric
from app.azure import estimate_cost as azure_estimate_cost

def get_s3_space_usage(account):
    res = []
    s3_estimator = S3CostEstimator()
    s3_space_usage = list(AWSMetric.get_s3_space_usage(account.key))
    for name, value in s3_space_usage:
        tmp = name.split('/', 2)
        if len(tmp) == 3:
            storage_type = 'infrequent_access' if tmp[2] == 'StandardIAStorage' else 'standard'
            storage_standard = 0 if tmp[2] == 'StandardIAStorage' else value
            storage_dra = 0 if tmp[2] == 'StandardStorage' else value
            args = dict(
                storage_standard=storage_standard,
                storage_dra=storage_dra
            )
            prices = []
            args.update(region=tmp[0])
            prices.append(dict(provider='aws', cost=s3_estimator.estimate(**args)['total'] / 1000.0))
            del args['region']
            prices.append(dict(provider='gcloud', cost=google_storage.current_model(**args)['total'] / 1000.0))
            prices.append(dict(provider='azure', cost=azure_estimate_cost(**args)['total'] / 1000.0))
            res.append(dict(location=tmp[0], name=tmp[1], type=storage_type, provider='aws', used_space=value, prices=prices))
    return dict(buckets=res)

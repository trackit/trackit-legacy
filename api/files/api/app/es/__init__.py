from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.helpers import bulk
from requests_aws4auth import AWS4Auth
from app.models import AWSKey
from elasticsearch_dsl.connections import connections
from app import app
import elasticsearch_dsl as dsl

try:
    es_aws_auth = app.config['ES_AUTH']
    es_auth = AWS4Auth(es_aws_auth['key'], es_aws_auth['secret'], es_aws_auth['region'], 'es')
except:
    es_auth = None
client = Elasticsearch(hosts=app.config['ES_HOSTS'], http_auth=es_auth, connection_class=RequestsHttpConnection, sniff_timeout=60)
connections.add_connection('default', client)

SHORT_NAMES = {
    "Amazon Elastic Compute Cloud": "EC2",
    "Amazon EC2 Container Registry (ECR)": "ECR",
    "Amazon Simple Storage Service": "S3",
    "Amazon RDS Service": "RDS",
    "Amazon ElastiCache": "ElastiCache",
    "Amazon Elastic File System": "EFS",
    "Amazon Elastic MapReduce": "EMR",
    "Amazon Route 53": "Route 53",
    "AWS Key Management Service": "KMS",
    "Amazon DynamoDB": "DynamoDB",
    "Amazon Simple Email Service": "SES",
    "Amazon Simple Notification Service": "SNS",
    "Amazon Simple Queue Service": "SQS",
    "Amazon SimpleDB": "Simple",
    "AWS Support (Developer)": "Support",
    "AWS CloudTrail": "CloudTrail",
    "AWS Lambda": "Lambda",
    "AmazonCloudWatch": "CloudWatch",
    "Amazon Elasticsearch Service": "Elasticsearch",
    "AWS Directory Service": "Directory Service",
    "Amazon Virtual Private Cloud": "VPC",
    "Amazon Kinesis Firehose": "Kinesis Firehose",
    "Amazon Kinesis": "Kinesis",
    "Amazon Redshift": "Redshift",
    "Amazon CloudFront": "CloudFront",
    "Amazon CloudSearch": "CloudSearch",
    "AWS Database Migration Service": "DMS",
    "AWS WAF": "WAF",
    "Amazon Athena": "Athena",
    "AWS Support (Business)": "Business Support",
}

GOOGLE_URI_NAMES = {
    'com.google.cloud/services/compute-engine': 'Compute engine',
    'com.google.cloud/services/cloud-storage': 'Storage',
}


def get_google_uri_name(uri):
    if uri in GOOGLE_URI_NAMES:
        return GOOGLE_URI_NAMES[uri]
    return uri.rsplit('/', 1)[1]


def bulk_save(docs):
    def ops():
        for doc in docs:
            doc.full_clean()
            yield doc.to_dict(include_meta=True)
    bulk(client, ops(), raise_on_error=True, timeout='120s', request_timeout=120, chunk_size=200)


def any_key_to_string_array(keys):
    """Convert single keys to list of keys, and individual keys to strings."""
    if isinstance(keys, basestring) or isinstance(keys, AWSKey):
        keys = [keys]
    keys = list(k.key if isinstance(k, AWSKey) else k for k in keys)
    if not all(isinstance(k, basestring) for k in keys):
        raise TypeError('All supplied keys must be either strings or AWSKeys.')
    return keys

tag_key_tokenizer = dsl.tokenizer('tagkey', 'pattern', pattern='^[^=]+', group=0)
tag_key_analyzer = dsl.analyzer('tagkey', tokenizer=tag_key_tokenizer)
directory_analyzer = dsl.analyzer('directory', tokenizer='path_hierarchy')

import awsaccesslog
import awsdetailedlineitem
import awselbinfo
import awsidnamemapping
import awsmetric
import awsstat
import elbpricing
import googledailyresource
import googlemetric
import s3bucketfile
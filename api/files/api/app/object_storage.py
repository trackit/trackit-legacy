"""
Abstraction for an object storage service and an implementation for S3 storage.
"""

import boto3
import botocore
import os

class ObjectStore:
    pass


class ObjectStoreObject:
    def __init__(self, object_store):
        self.object_store = object_store

    def store(self):
        return self.object_store


class S3BucketObjectStore(ObjectStore):
    def __init__(self, bucket):
        """
        `bucket' is the Boto3 resource for the S3 bucket that shall be used for
        object storage.
        """
        self.bucket = bucket

    def __str__(self):
        return 's3://{}'.format(self.bucket.name)

    def object(self, key):
        return S3BucketObjectStoreObject(
            self,
            self.bucket.Object(key),
        )

    def exists(self, key):
        return self.object(key).exists()

    def __iter__(self):
        return (
            S3BucketObjectStoreObject(self, o)
            for o in self.bucket.objects.iterator()
        )


class S3BucketObjectStoreObject(ObjectStoreObject):
    def __init__(self, object_store, object_):
        ObjectStoreObject.__init__(self, object_store)
        self.object = object_

    def __str__(self):
        return 's3://{}/{}'.format(self.object.bucket_name, self.object.key)

    def key(self):
        return self.object.key

    def last_changed(self):
        return self.object.last_modified

    def size(self):
        try:
            return self.object.content_length
        except AttributeError:
            return self.object.size

    def etag(self):
        return self.object.e_tag

    def get_file(self, f=None):
        f = f or os.tmpfile()
        a = self.object.get()
        while True:
            b = a['Body'].read()
            if b:
                f.write(b)
            else:
                break
        f.seek(0)
        return f

    def put_file(self, f, **kwargs):
        return self.object.put(Body=f, **kwargs)

    def put_bytes(self, b, **kwargs):
        return self.object.put(Body=b, **kwargs)

    def exists(self):
        try:
            self.object.load()
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise

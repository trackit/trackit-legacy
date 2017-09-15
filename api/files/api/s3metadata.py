from threading import local
from multiprocessing.pool import ThreadPool
from itertools import imap, chain
from functools import partial
from elasticsearch.helpers import scan, bulk
from Peekable import Peekable


def fetch(session, bucket, client, index, mapping):
    pool = ThreadPool(16)
    try:
        object_chunks = each_chunk(list_directory(session, bucket), 1000)
        def fetch_docs_between(**range_clause):
            return scan(client=client, query={
                'query': {
                    'filtered': {
                        'filter': {
                            'and': [
                                {'range': {'key': range_clause}},
                                {'term': {'bucket': bucket}}
                            ]
                        }
                    }
                },
                'sort': {
                    'key': 'asc'
                }
            }, index=index, preserve_order=True)
        fetch_heads = partial(keys_with_head, session, bucket, pool.imap_unordered)
        ops = reconcile_ops(object_chunks, fetch_docs_between, fetch_heads, bucket)
        bulk(client, ops, index=index, doc_type=mapping)
    finally:
        pool.close()

def reconcile_ops(object_chunks, fetch_docs_between, fetch_heads, bucket_name):
    ops = []
    low = None
    high = None
    for chunk in object_chunks:
        if low is None:
            low = chunk[0]['Key']
        high = chunk[-1]['Key']
        objects = Peekable(chunk)
        docs_between = Peekable(fetch_docs_between(gte=chunk[0]['Key'], lte=chunk[-1]['Key']))
        key_ids = {}

        while objects.has_next() or docs_between.has_next():
            obj = objects.peek(None)
            doc = docs_between.peek(None)

            if doc and obj:
                if doc['_source']['key'] > obj['Key']:
                    key_ids[obj['Key']] = None
                    objects.next()
                elif obj['Key'] > doc['_source']['key']:
                    yield {'_op_type': 'delete', '_id': doc['_id']}
                    docs_between.next()
                else:
                    if doc['_source'].get('modified') != obj['LastModified'].isoformat():
                        key_ids[doc['_source']['key']] = doc['_id']
                    docs_between.next()
                    objects.next()
            elif doc:
                yield {'_op_type': 'delete', '_id': doc['_id']}
                docs_between.next()
            else:
                key_ids[obj['Key']] = None
                objects.next()

        for key, meta in fetch_heads(key_ids):
            tags = ['%s=%s' % p for p in meta['Metadata'].iteritems()]
            if meta['ContentType']:
                tags.append('content-type=%s' % meta['ContentType'])
            op = {
                '_op_type': 'index',
                'key': key,
                'bucket': bucket_name,
                'size': meta['ContentLength'],
                'tags': tags,
                'modified': meta['LastModified'].isoformat()
            }
            if key_ids[key]:
                op['_id'] = key_ids[key]
            yield op
    ranges = []
    if low is not None:
        ranges.append(fetch_docs_between(lt=low))
    if high is not None:
        ranges.append(fetch_docs_between(gt=high))
    for doc in chain(*ranges):
        yield {'_op_type': 'delete', '_id': doc['_id']}

def list_directory(session, bucket_name):
    client = session.client('s3')
    is_truncated = True
    continuation = None
    while is_truncated:
        if continuation:
            response = client.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation)
        else:
            response = client.list_objects_v2(Bucket=bucket_name)
        is_truncated = response['IsTruncated']
        continuation = response.get('NextContinuationToken')
        for obj in response['Contents']:
            yield obj

def keys_with_head(session, bucket_name, mapper, keys):
    clients = local()
    def head_object(key):
        if not hasattr(clients, 'client'):
            clients.client = session.client('s3')
        head = clients.client.head_object(Key=key, Bucket=bucket_name)
        return (key, head)
    return mapper(head_object, keys)

def each_chunk(iterable, size):
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

from .buckets import get_s3_buckets
from datetime import datetime
from re import compile as re
import traceback
import botocore

def get_object_access_logs(session, since=None):
    client = session.client('s3')
    for bucket in get_s3_buckets(session):
        try:
            for o in get_gets(client, bucket['Name'], since):
                yield o
        except botocore.exceptions.ClientError:
            pass # Most likely we don't have sufficient permissions to read that bucket.
        except:
            traceback.print_exc()

log_line_re = re(r'\w+ *([A-Za-z-]+) *\[(\d+/\w+/\d+:\d+:\d+:\d+).{4,10}\].*GET\.OBJECT *([^ ]+) *.*')
key_name_re = re(r'(.*/)?\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\w+')

def parse(lines):
    for line in lines:
        if 'GET.OBJECT' not in line:
            continue
        match = log_line_re.match(line)
        if match:
            t = datetime.strptime(match.group(2), '%d/%b/%Y:%H:%M:%S')
            yield dict(bucket=match.group(1), time=t, object=match.group(3))

def get_gets(client, bucket_name, since=None):
    def ls(**kw):
        return client.list_objects_v2(Bucket=bucket_name, **kw)
    if since:
        prefixes = ls(Delimiter='/')['CommonPrefixes']
        for prefix in prefixes:
            prefix = prefix['Prefix'] + since.strftime('%Y-%m-%d-%H-%M-%S-')
            res = ls(StartAfter=prefix)
            if not 'Contents' in res:
                return
            if any(key_name_re.match(o['Key']) for o in res['Contents']):
                break
            else:
                return
    else:
        res = ls()
        if not 'Contents' in res:
            return
        if not any(key_name_re.match(o['Key']) for o in res['Contents']):
            return
    while True:
        for o in res['Contents']:
            if not key_name_re.match(o['Key']):
                continue
            body = client.get_object(Bucket=bucket_name, Key=o['Key'])['Body']
            lines = get_lines(body)
            for r in parse(lines):
                yield r
        if res['IsTruncated']:
            res = ls(ContinuationToken=res['NextContinuationToken'])
        else:
            break

def get_lines(s, size=2048):
    ch = s.read(size)
    buff = []
    while ch:
        segs = ch.split('\n')
        if len(segs) == 1:
            buff.append(segs[0])
        else:
            if buff:
                buff.append(segs[0])
                buff.append('\n')
                yield ''.join(buff)
                buff = []
            else:
                yield segs[0] + '\n'
            for i in xrange(1, len(segs)-1):
                yield segs[i] + '\n'
            buff.append(segs[-1])
        ch = s.read(size)
    if buff:
        yield ''.join(buff)

from redis import StrictRedis
from app import app
from zlib import compress, decompress
from hashlib import sha256
import json
import config

cache = StrictRedis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DB'])
cached_function = []

def compressed_json(j):
    return compress(json.dumps(j))


def decompressed_json(j):
    return json.loads(decompress(j))


class CacheObject:
    def __init__(self, f, is_json, ttl, ret):
        self.f = f
        self.is_json = is_json
        self.ttl = ttl
        self.ret = ret
        global cached_function
        cached_function.append(self)

    def __call__(self, *args, **kwargs):
        if not config.REDIS_ENABLED:
            return self.ret(self.f(*args, **kwargs)) if self.ret else self.f(*args, **kwargs)
        if 'cache_ttl' in kwargs:
            self.ttl = kwargs['cache_ttl']
            del kwargs['cache_ttl']
        cache_var_name = '{}#{}'.format(self.f.__name__,
                                        sha256('{}_{}'.format(
                                            '_'.join(sorted(['_'.join([k, str(v)]) for k, v in kwargs.iteritems()])),
                                            '_'.join(str(args[1:])))
                                        ).hexdigest())
        c = cache.get(cache_var_name)
        if not c:
            c = self.f(*args, **kwargs)
            cache.setex(cache_var_name, self.ttl, compressed_json(c) if self.is_json else c)
            return self.ret(c) if self.ret else c
        c = decompressed_json(c) if self.is_json else c
        return self.ret(c) if self.ret else c

    def flush(self):
        for cache_var_name in cache.scan_iter('{}#*'.format(self.f.__name__)):
            cache.delete(cache_var_name)


def with_cache(is_json=True, ttl=3600 * 12, ret=None):
    def wrapper(f):
        return CacheObject(f, is_json, ttl, ret)
    return wrapper

import json
import requests
from werkzeug.contrib.cache import SimpleCache
from app.models import AWSPricing, db
from StringIO import StringIO

cache = SimpleCache()

PRICING_URL_TPL = 'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/%s/current/index.json'

def get(offer):
    return AWSPricing.query.order_by(-AWSPricing.version).filter(AWSPricing.offer == offer).first()

def fetch(offer):
    latest = get(offer)

    headers = {}
    if latest and latest.etag:
        headers['If-None-Match'] = latest.etag

    res = requests.get(PRICING_URL_TPL % offer, headers=headers)

    if res.status_code == 304:
        return latest.json()

    data = res.json()
    if not latest:
        new = AWSPricing(offer=offer,
                        version=data['version'].decode('utf-8'),
                        etag=res.headers.get('ETag'))
        new.set_json(data)
        db.session.add(new)
    else:
        latest.offer = offer
        latest.version = data['version'].decode('utf-8')
        latest.etag = res.headers.get('ETag')
        latest.set_json(data)
    db.session.commit()

    return data

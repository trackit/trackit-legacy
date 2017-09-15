from app import app
from app.models import db, AzurePricing
from app.ms_azure import azure_offers, azure_region_currency
from app.ms_azure.utils import meter_info_to_dict
from app.error_email import azure_commerce_userpasscredentials_error_email
from sqlalchemy import and_, desc
from azure.common.credentials import UserPassCredentials
from azure.mgmt.commerce import UsageManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient
from datetime import datetime, timedelta
import traceback
import logging

azure_fetch_freq = timedelta(hours=6)

COMMERCE_CREDENTIALS_ERROR_EMAIL_SENT = False

def fetch_region_pricing(offer, region):
    now = datetime.utcnow()
    record = AzurePricing.query.filter(and_(AzurePricing.offer == offer, AzurePricing.region == region)).order_by(desc(AzurePricing.date)).first()
    if record and record.date > now - azure_fetch_freq:
        return
    if not record:
        record = AzurePricing(offer=offer, region=region)
    try:
        azure_subscription_id = app.config['AZURE_SUBSCRIPTION_ID']
        azure_ad_username = app.config['AZURE_AD_USERNAME']
        azure_ad_password = app.config['AZURE_AD_PASSWORD']

        azure_credentials = UserPassCredentials(azure_ad_username, azure_ad_password)
        azure_commerce_client = UsageManagementClient(azure_credentials, azure_subscription_id)

        azure_resource_client = ResourceManagementClient(azure_credentials, azure_subscription_id)
        azure_resource_client.providers.register('Microsoft.Commerce')
    except Exception, e:
        logging.error("Error during azure UserPassCredentials instantiation in app.ms_azure.pricing.fetch_region_pricing")
        global COMMERCE_CREDENTIALS_ERROR_EMAIL_SENT
        if not COMMERCE_CREDENTIALS_ERROR_EMAIL_SENT:
            azure_commerce_userpasscredentials_error_email(traceback.format_exc())
            COMMERCE_CREDENTIALS_ERROR_EMAIL_SENT = True
        return
    # OfferDurableID: https://azure.microsoft.com/en-us/support/legal/offer-details/
    rate = azure_commerce_client.rate_card.get(
        "OfferDurableId eq '{}' and Currency eq '{}' and Locale eq 'en-US' and RegionInfo eq '{}'".format(offer, azure_region_currency[region], region)
    )

    rate.meters.sort(key=lambda x: x.effective_date.replace(tzinfo=None))
    pricing_data = map(meter_info_to_dict, rate.meters)

    record.date = datetime.utcnow()
    record.set_json(dict(pricing=pricing_data))
    if not record.id:
        db.session.add(record)
    db.session.commit()

def fetch_pricings():
    for offer in azure_offers.values():
        for region in azure_region_currency.keys():
            fetch_region_pricing(offer, region)

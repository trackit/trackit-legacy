from datetime import datetime
from app.msol_util import content_diff, index_of
from app.gcloud.utils import refresh_credentials, get_gapi_authorized_http
import oauth2client
import apiclient

# In case this is a versionned bucket, we have to ignore older revisions
def _purge_outdated_files(acc, el):
    i = index_of(el['name'] == a['name'] for a in acc)
    if i is not None:
        a = acc[i]
        acc[i] = max(el, a, key=(lambda f: int(f['generation'])))
        return acc
    else:
        return acc + [el]

# Get from the Google API a list of buckets for a project by identity ID and
# project ID.
def get_project_buckets_from_gcloud_api(identity, project):
    def get_buckets():
        http = get_gapi_authorized_http(identity)
        google_storage_service = apiclient.discovery.build('storage', 'v1', http=http)
        buckets = google_storage_service.buckets().list(project=project['number']).execute()
        return buckets
    try:
        buckets = get_buckets()
    except oauth2client.client.HttpAccessTokenRefreshError:
        refresh_credentials(identity)
        buckets = get_buckets()
    if not 'items' in buckets:
        return []
    buckets = [
        dict(
            id=None,
            name=b['name'],
        ) for b in buckets['items']
    ]
    return buckets

def get_billing_files(identity, billing_bucket):
    def get_files():
        http = get_gapi_authorized_http(identity)
        google_storage_service = apiclient.discovery.build('storage', 'v1', http=http)
        files = google_storage_service.objects().list(bucket=billing_bucket['name']).execute()
        return files
    try:
        files = get_files()
    except oauth2client.client.HttpAccessTokenRefreshError:
        refresh_credentials(identity)
        files = get_files()
    if 'items' in files:
        raw_files = [ f for f in files['items'] if f['name'].endswith('.json')]
        raw_files = reduce(_purge_outdated_files, raw_files, [])
        for raw_file in raw_files:
            yield raw_file

def download_billing_file(identity, billing_file):
    def download_file():
        http = get_gapi_authorized_http(identity)
        google_storage_service = apiclient.discovery.build('storage', 'v1', http=http)
        response, billing_data = http.request(billing_file['mediaLink'])
        return response, billing_data
    try:
        response, billing_data = download_file()
    except oauth2client.client.HttpAccessTokenRefreshError:
        refresh_credentials(identity)
        response, billing_data = download_file()
    return response, billing_data

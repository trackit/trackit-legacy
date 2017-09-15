from app.gcloud.utils import refresh_credentials, get_gapi_authorized_http
from app.gcloud.projects import get_identity_projects_from_gcloud_api
import oauth2client
import apiclient

def get_running_instances(identity):
    def get_instances():
        http = get_gapi_authorized_http(identity)
        google_compute_service = apiclient.discovery.build('compute', 'v1', http=http)
        instances = []
        for project in get_identity_projects_from_gcloud_api(identity):
            zones = google_compute_service.zones().list(project=project['code']).execute()
            for zone in zones['items']:
                try:
                    compute_instances_infos = google_compute_service.instances().list(project=project['code'], zone=zone['name']).execute()
                except apiclient.errors.HttpError as err:
                    continue
                if 'items' in compute_instances_infos:
                    for instance in compute_instances_infos['items']:
                        if instance['status'] == 'RUNNING':
                            instances.append(instance)
        return instances
    try:
        instances = get_instances()
    except oauth2client.client.HttpAccessTokenRefreshError:
        refresh_credentials(identity)
        instances = get_instances()
    return instances

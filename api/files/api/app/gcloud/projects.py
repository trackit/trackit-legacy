from datetime import datetime
from app.msol_util import content_diff
from app.gcloud.utils import refresh_credentials, get_gapi_authorized_http
import oauth2client
import apiclient

# Returns a list of projects for a Google Cloud identity.
def get_identity_projects_from_gcloud_api(identity):
    def get_projects():
        http = get_gapi_authorized_http(identity)
        google_projects_service = apiclient.discovery.build('cloudresourcemanager', 'v1', http=http)
        # May raise oauth2client.client.HttpAccessTokenRefreshError
        projects = google_projects_service.projects().list().execute()
        return projects
    try:
        projects = get_projects()
    except oauth2client.client.HttpAccessTokenRefreshError:
        refresh_credentials(identity)
        projects = get_projects()
    return [
        dict(
            id_identity=identity.id,
            code=project['projectId'],
            name=project['name'],
            number=int(project['projectNumber'])
        ) for project in filter(lambda p: p['lifecycleState'] == 'ACTIVE', projects['projects'])
    ]

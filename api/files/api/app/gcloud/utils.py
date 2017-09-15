from app.models import db, GoogleCloudIdentity
import oauth2client
import httplib2

def get_credentials_from_identity(identity):
    return oauth2client.client.OAuth2Credentials.from_json(identity.credentials)

def refresh_credentials(identity):
    credentials = get_credentials_from_identity(identity)
    http = httplib2.Http()
    http = credentials.refresh(http)
    identity.credentials = credentials.to_json()
    db.session.commit()

# Returns an Http object authenticated with the identity's credentials.
def get_gapi_authorized_http(identity):
    credentials = get_credentials_from_identity(identity)
    http = httplib2.Http()
    http = credentials.authorize(http)
    return http

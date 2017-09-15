import apiclient;
import httplib2;
import oauth2client;

CLIENT_SECRET_PATH = 'google-app-secret.json'

credentials = oauth2client.client.credentials_from_clientsecret_and_code(
    CLIENT_SECRET_PATH,
    ['profile', 'email'],
    auth_code)

http_auth = credentials.authorize(httplib2.Http())
user_id = credentials.id_token['sub']
email = credentials.id_token['email']


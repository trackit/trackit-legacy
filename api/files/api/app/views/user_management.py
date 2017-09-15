from app import app
from app.authentication import with_login
from flask import Blueprint, jsonify, request, redirect
from marshmallow import Schema, fields
from app.request_schema import with_request_schema
from app.models import db, User, UserSessionToken, AWSKey
import app.models as models
from app.intercom import add_intercom_user
from app.tasks import send_email, send_email_alternative
from app.onboarding_email import onboarding_email
from app.g_recaptcha import with_g_recaptcha
import uuid
import json
import oauth2client
import jinja2
import apiclient
import httplib2
import config
import traceback


user_management_bp = Blueprint('user_management_bp', __name__)

class UserLoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)

class BaseUserSchema(Schema):
    # TODO: remove IDs from API?
    email = fields.Email(required=True)
    firstname = fields.Str(required=True)
    lastname = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class UserSchema(BaseUserSchema):
    id = fields.Integer(dump_only=True)

class UserSignupSchema(BaseUserSchema):
    pass

class UserEditSchema(Schema):
    email = fields.Email(required=False)
    firstname = fields.Str(required=False)
    lastname = fields.Str(required=False)
    password = fields.Str(required=False, load_only=True)

class PostProspectSchema(Schema):
    #g_recaptcha_response = fields.Str(required=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone_number = fields.Str(required=False)
    company_name = fields.Str(required=False)
    address = fields.Str(required=False)
    which_cloud = fields.List(
        fields.Str(),
        required=False,
    )
    employees = fields.Str(required=False)
    annual_revenue = fields.Str(required=False)
    cloud_concerns = fields.List(
        fields.Str(),
        required=False,
    )

class ProspectSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone_number = fields.Str(required=False)
    company_name = fields.Str(required=False)
    address = fields.Str(required=False)
    which_cloud = fields.List(
        fields.Str(),
        required=False,
    )
    employees = fields.Str(required=False)
    annual_revenue = fields.Integer(required=False)
    cloud_concerns = fields.List(
        fields.Str(),
        required=False,
    )

user_login_schema = UserLoginSchema()
user_schema = UserSchema()
user_signup_schema = UserSignupSchema()
user_edit_schema = UserEditSchema()
prospect_schema = ProspectSchema()
post_prospect_schema = PostProspectSchema()

@app.route('/prospect/<string:type>', methods=['POST'])
@with_request_schema(post_prospect_schema)
#@with_g_recaptcha()
def prospect(data, type):
    """---
    post:
        tags:
            - user
        produces:
            - application/json
        consumes:
            - application/json
        description: &desc Create a new prospect
        summary: *desc
        parameters:
            - in: body
              name: name body
              schema:
                $ref: "#/definitions/PostProspectSchema"
        responses:
            200:
                description: Successfully creation
                schema:
                    $ref: "#/definitions/ProspectSchema"
            422:
                description: Invalid body
            404:
                description: Prospect type not found
            403:
                description: Captcha validation failed
                schema:
                    properties:
                        error:
                            type: string
    """
    data, error = prospect_schema.load(data)
    if error:
        return jsonify(
            error="Validation error",
            fields=error,
        ), 422
    if type != 'trial' and type != 'demo':
        return jsonify(error="Prospect type not found"), 404
    if 'cloud_concerns' in data:
        concerns = [
            models.CloudConcern(concern=c)
            for c in data['cloud_concerns']
        ]
        del data['cloud_concerns']
    else:
        concerns = []
    if 'which_cloud' in data:
        clouds = [
            models.WhichCloud(cloud=c)
            for c in data['which_cloud']
        ]
        del data['which_cloud']
    else:
        clouds = []
    data['type'] = type
    try:
        prospect = models.Prospect(**data)
        db.session.add(prospect)
        for c in concerns:
            c.prospect = prospect
            db.session.add(c)
        for c in clouds:
            c.prospect = prospect
            db.session.add(c)
        db.session.commit()
    except:
        traceback.print_exc()
        return jsonify(error="Internal database access error"), 500
    try:
        email_txt, email_html = render_prospect_email(prospect)
        send_email_alternative.delay(
            app.config['NEW_USER_EMAIL'],
            "New {} prospect".format(type),
            email_txt,
            email_html,
            bypass_debug=True,
        )
    except:
        traceback.print_exc()
    return jsonify(prospect.to_dict()), 200


@app.route('/send', methods=['POST'])
def contact():
    """---
    post:
        tags:
            - user
        produces:
            - application/json
        consumes:
            - application/json
        description: &desc Send message
        summary: *desc
        responses:
            200:
                description: Successfully sent
            422:
                description: Invalid body
            404:
                description: Prospect type not found
    """
    data = request.values
    email_txt = 'Name: {}\nEmail: {}\nPhone : {}\nMessage :\n{}\n'.format(data['name'], data['email'], data['phone'], data['message'])
    email_html = email_txt.replace('\n', '<br>')
    try:
        send_email_alternative.delay(
            app.config['CONTACT_USER_EMAIL'],
            "New message from contact form",
            email_txt,
            email_html,
            bypass_debug=True,
        )
    except:
        return "error", 502

    return "sent", 200

_template_dir = app.config['EMAIL_TEMPLATE_DIR']
_template_loader = jinja2.FileSystemLoader(_template_dir)
_template_env = jinja2.Environment(loader=_template_loader)
_template_prospect_html = _template_env.get_template('emailNewProspect.html')
_template_prospect_txt = _template_env.get_template('emailNewProspect.txt')
def render_prospect_email(prospect):
    content_data = prospect.to_dict()
    content_data_pruned = {}
    for k, v in content_data.iteritems():
        if v is not None: # Jinja2 does not consider None as un undefined value.
            content_data_pruned[k] = v
    assert 'name' in content_data_pruned
    assert 'email' in content_data_pruned
    content_html = _template_prospect_html.render(**content_data_pruned)
    content_txt = _template_prospect_txt.render(**content_data_pruned)
    return content_txt, content_html

@app.route('/login', methods=['POST'])
@with_request_schema(user_login_schema)
def login(data):
    """---
    post:
        tags:
            - user
        produces:
            - application/json
        consumes:
            - application/json
        description: &desc Log user in
        summary: *desc
        parameters:
            - in: body
              name: body
              schema:
                $ref: "#/definitions/UserLogin"
        responses:
            200:
                description: Successful login
                schema:
                    properties:
                        token:
                            type: string
            401:
                description: Invalid credentials
                schema:
                    properties:
                        error:
                            type: string
    """
    user = User.query.filter_by(email=data['email']).first()
    if user and user.password_matches(data['password']):
        token = UserSessionToken.for_user(user)
        db.session.add(token)
        db.session.commit()
        return jsonify(token=token.id)
    return jsonify(error="Wrong user or password"), 401

google_auth_flow = oauth2client.client.OAuth2WebServerFlow(scope='https://www.googleapis.com/auth/plus.me '
                                                                 'https://www.googleapis.com/auth/plus.login '
                                                                 'https://www.googleapis.com/auth/userinfo.email '
                                                                 'https://www.googleapis.com/auth/userinfo.profile',
                                                           redirect_uri='https://' + config.HOST_DOMAIN + config.OAUTH_URIS['auth_google_callback'],
                                                           **(config.GOOGLE_OAUTH))

@app.route('/lostpassword', methods=['POST'])
def lostpassword():
    email = request.json.get("email")
    user = User.query.filter_by(email=email).first()
    if user:
        token = uuid.uuid4().hex
        user.set_lost_password(token)
        db.session.add(user)
        db.session.commit()
        message = "Hello,\n\nYou requested to reset your password, please follow this link: https://trackit.io/#/lostpassword/" + token
        send_email.delay(email, "Forgotten password", message, False, bypass_debug=True)
        return jsonify(message="A request was sent")
    return jsonify(error="Wrong email"), 400

@app.route('/changelostpassword', methods=['POST'])
def changelostpassword():
    lost_password = request.json.get("lost_password")
    password = request.json.get("password")
    if lost_password and password:
        user = User.query.filter_by(lost_password=request.json.get("lost_password")).first()
        if user:
            token = ""
            user.set_lost_password(token)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        return jsonify(message="Password was changed")
    return jsonify(error="Wrong token or password"), 400

@app.route('/auth/google/initiate', methods=['GET'])
def initiate_auth_google():
    auth_uri = google_auth_flow.step1_get_authorize_url()
    return redirect(auth_uri, code=302)

@app.route('/auth/google/callback', methods=['GET'])
def auth_google():
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    people_api_url = 'https://www.googleapis.com/plus/v1/people/me/openIdConnect'

    credentials = google_auth_flow.step2_exchange(request.args.get('code'))
    http = httplib2.Http()
    http = credentials.authorize(http)
    google_oauth2_service = apiclient.discovery.build('oauth2', 'v2', http=http)
    profile = google_oauth2_service.userinfo().get().execute()

    user_google_id = profile['id']
    user_email = profile['email']
    criteria = ((User.auth_google == user_google_id) |
                ((User.auth_google == None) & (User.email == user_email)))
    user = User.query.filter(criteria).first()

    if user:
        token = UserSessionToken.for_user(user)
        db.session.add(token)
        db.session.commit()
    else:
        user_given_name = profile['given_name']
        user_family_name = profile['family_name']
        user = User(auth_google=user_google_id,
                    firstname=user_given_name,
                    lastname=user_family_name,
                    email=user_email)
        db.session.add(user)
        db.session.flush()
        db.session.refresh(user)
        token = UserSessionToken.for_user(user)
        db.session.add(token)

        key = AWSKey()
        key.id_user = user.id
        for data_key, data_value in config.ACCOUNT_CREATION_DEFAULT_AWS_KEY.iteritems():
            setattr(key, data_key, data_value)
        key.import_s3 = True
        key.is_valid_key = True
        db.session.add(key)

        db.session.commit()
    return redirect(('https://%s/#/authenticated?token=%s&token_expires=%s' % (config.WEB_UI_HOST, token.id, token.expires.isoformat())), code=302)

@app.route('/logout', methods=['GET'])
@with_login(load_user=True, load_token=True)
def logout(user, token):
    """---
    get:
        tags:
            - user
        produces:
            - application/json
        consumes:
            - application/json
        description: &desc Log user out
        summary: *desc
        responses:
            200:
                description: Successful user logout
                schema:
                    properties:
                        message:
                            type: string
    """
    db.session.delete(token)
    db.session.commit()
    return jsonify(message="Logout")

@app.route('/tokens', methods=['GET'])
@with_login(load_user=True)
def get_tokens(user):
    query = UserSessionToken.query.filter_by(id_user=user.id)
    tokens = filter(lambda t: not t.has_expired(), query.all())
    stripped_tokens = [{ 'id': t.partial_token(), 'expires': t.expires.isoformat() + 'Z' } for t in tokens]
    return jsonify(tokens=stripped_tokens), 200

@app.route('/signup', methods=['POST'])
@with_request_schema(user_signup_schema)
def signup(data):
    """---
    post:
        tags:
            - user
        produces:
            - application/json
        consumes:
            - application/json
        description: &desc Create user account
        summary: *desc
        parameters:
            - in: body
              name: body
              schema:
                $ref: "#/definitions/UserSignup"
        responses:
            201:
                description: Successful signup
                schema:
                    $ref: "#/definitions/User"
            409:
                description: Email already taken
            422:
                description: Invalid parameters
    """
    if User.query.filter_by(email=data['email']).count():
        return jsonify(error="Email already taken", fields={'email': ["Email already taken"]}), 409
    user = User()
    for key, value in data.iteritems():
        if key == 'password':
            user.set_password(value)
        elif key in ['email', 'firstname', 'lastname']:
            setattr(user, key, value)
    db.session.add(user)
    db.session.flush()
    db.session.refresh(user)

    key = AWSKey()
    key.id_user = user.id
    for data_key, data_value in config.ACCOUNT_CREATION_DEFAULT_AWS_KEY.iteritems():
        setattr(key, data_key, data_value)
    key.import_s3 = True
    key.is_valid_key = True
    db.session.add(key)

    db.session.commit()
    add_intercom_user(user)
    onboarding_email(user.email, user.firstname)
    return jsonify(user_schema.dump(user)[0]), 201

@app.route('/user', methods=['GET'])
@with_login(True)
def user(user):
    return jsonify(user_schema.dump(user)[0])

@app.route('/user', methods=['PUT'])
@with_login(True)
@with_request_schema(user_edit_schema)
def edit_user(user, data):
    for key, value in data.iteritems():
        if key == 'password':
            user.set_password(value)
        elif key in ['email', 'firstname', 'lastname']:
            setattr(user, key, value)
    db.session.commit()
    return jsonify(user_schema.dump(user)[0]), 200

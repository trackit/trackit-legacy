from flask import jsonify, request
from models import db, User, UserSessionToken
from functools import wraps

def with_login(load_user=False, load_token=False):
    def wrapper(f):
        @wraps(f)
        def token_checker(*args, **kwargs):
            token = UserSessionToken.query.filter_by(id=get_user_token()).first()
            if token and not token.has_expired():
                if load_user:
                    user = User.query.filter_by(id=token.id_user).first()
                    assert user != None # The database should enforce the relationship
                    args += (user,)
                if load_token:
                    kwargs['token'] = token
                return f(*args, **kwargs)
            else:
                return jsonify(error="Wrong token"), 401
        return token_checker
    return wrapper

def get_user_token():
    return request.headers.get('Authorization')

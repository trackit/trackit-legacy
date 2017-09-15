from app import app, swagger
from flask import Blueprint, jsonify
from config import BUILD_VERSION


swagger_bp = Blueprint('swagger_bp', __name__)

@app.route('/')
def show_swagger():
    res = swagger.spec.to_dict()
    for hidden_views in ('/signup',):
        if hidden_views in res['paths']:
            del res['paths'][hidden_views]
    return jsonify(res)


@app.route('/version')
def show_version():
    return BUILD_VERSION, 200

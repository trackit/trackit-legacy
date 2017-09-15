from app import app
from app.authentication import with_login
from app.azure import estimate_cost, get_storage_map
from flask import Blueprint, jsonify, request
from fractions import Fraction
import json

ms_azure_bp = Blueprint('ms_azure_bp', __name__)

gib = Fraction(2 ** 30)

# TODO: swagger
@app.route('/azure/storage/estimate', methods=['GET'])
@with_login()
def get_estimate_storage_cost():
    args = {}
    for key in request.args:
        try:
            args[key] = int(request.args[key])
        except:
            args[key] = request.args[key]
    res = estimate_cost(**args)
    return jsonify(res)

@app.route('/azure/storage/map', methods=['GET'])
@with_login()
def get_azure_storage_map():
    if request.args.get('gigabytes'):
        gigabytes = int(request.args.get('gigabytes'))
        res = get_storage_map(gigabytes * gib)
        return jsonify(res)
    return jsonify(error='Required param `gigabytes`'), 400

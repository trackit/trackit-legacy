from app import app
from app.models import db, AWSKey
from flask import jsonify

@app.route('/healthcheck')
def healthcheck():
    try:
        aws_account_count = AWSKey.query.count()
        return jsonify(status='ok', awsaccounts=aws_account_count)
    except:
        return jsonify(status='unhealthy', awsaccounts=None), 500

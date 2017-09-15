from os import environ

from flask import Flask

app = Flask(__name__)
app.debug = bool(environ.get('DEBUG'))
app.config.from_object('config')

from flask.ext.cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=['X-Requested-With', 'Content-Type', 'Authorization', 'user-aws-key', 'Accept', 'Access-Control-Allow-Origin'])

from views.swagger import swagger_bp
from views.user_management import user_management_bp
from app.views.aws.account_management import aws_account_management_bp
from app.views.aws.cost.cost import aws_cost_cost_bp
from app.views.aws.cost.stats import aws_cost_stats_bp
from app.views.aws.forecast import aws_forecast_bp
from app.views.aws.usage import aws_usage_bp
from views.google import google_bp
from views.ms_azure import ms_azure_bp
from views.compare_providers import compare_providers_bp
import views.health

app.register_blueprint(swagger_bp)
app.register_blueprint(user_management_bp)
app.register_blueprint(aws_account_management_bp)
app.register_blueprint(aws_cost_cost_bp)
app.register_blueprint(aws_cost_stats_bp)
app.register_blueprint(aws_forecast_bp)
app.register_blueprint(aws_usage_bp)
app.register_blueprint(google_bp)
app.register_blueprint(ms_azure_bp)
app.register_blueprint(compare_providers_bp)

if app.debug:
    from paste.exceptions.errormiddleware import ErrorMiddleware
    wsgi = ErrorMiddleware(app, debug=True)
else:
    wsgi = app

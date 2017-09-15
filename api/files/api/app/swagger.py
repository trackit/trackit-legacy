import apispec

from app import app
from config import BUILD_VERSION


def add_routes_from(module, spec):
    for _, f in vars(module).items():
        if callable(f) and hasattr(f, 'func_doc') and getattr(f, 'func_doc'):
            try:
                spec.add_path(view=f)
            except apispec.exceptions.APISpecError:
                print("Failed to add documented callable {} to swagger.".format(f))

spec = apispec.APISpec(
    title='trackit.io',
    version=BUILD_VERSION,
    plugins=[
        'apispec.ext.flask',
        'apispec.ext.marshmallow',
    ],
)

ctx = app.test_request_context()
ctx.push()

from app.views.aws import account_management, forecast, usage, aws_key_schema
from app.views.aws.cost import cost, stats

add_routes_from(account_management, spec)
add_routes_from(cost, spec)
add_routes_from(stats, spec)
add_routes_from(forecast, spec)
add_routes_from(usage, spec)

from views import google
add_routes_from(google, spec)

from views import user_management
add_routes_from(user_management, spec)

spec.definition('UserLogin', schema=user_management.user_login_schema)
#spec.definition('UserSignup', schema=user_management.user_signup_schema)
spec.definition('User', schema=user_management.user_schema)
spec.definition('AWSAccount', schema=aws_key_schema)

ctx.pop()

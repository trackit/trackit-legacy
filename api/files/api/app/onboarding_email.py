from app.send_email import send_email
from app import app
from jinja2 import Template

ONBOARD_TPL = Template('''
<html>
    <head></head>
    <body>
        <p>Hi {{ firstname }} !<br><br>Welcome to Trackit.IO</p>
    </body>
</html>
''', autoescape=True)


def onboarding_email(email, firstname):
    message = ONBOARD_TPL.render(firstname=firstname)
    send_email(email, "Welcome to Trackit.IO", message, True)
    send_email(app.config['NEW_USER_EMAIL'], "New user sign up", "%s: %s" % (firstname, email), False)

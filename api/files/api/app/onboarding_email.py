from app.send_email import send_email, send_raw_email
from app import app
import jinja2

_template_dir = app.config['EMAIL_TEMPLATE_DIR']
_template_loader = jinja2.FileSystemLoader(_template_dir)
_template_env = jinja2.Environment(loader=_template_loader)
_template_onboarding = _template_env.get_template('onboarding.mime')

def _render_onboarding_email(recipient, firstname):
    return _template_onboarding.render(recipient=recipient)


def onboarding_email(email, firstname):
    content_mime = _render_onboarding_email(email, firstname)
    send_raw_email("team@trackit.io" , email, content_mime)
    send_email(app.config['NEW_USER_EMAIL'], "New user sign up", "%s: %s" % (firstname, email), False)

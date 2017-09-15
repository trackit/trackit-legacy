import jinja2
import json
from send_email import send_email
from app.models import User, MyResourcesAWS, db
from app.es.awsdetailedlineitem import AWSDetailedLineitem
from sqlalchemy import desc
import subprocess
import datetime
from flask import render_template

def monthly_html_template():
    template_dir = '/usr/trackit/templates'
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader)
    template = env.get_template('emailPDFreport.html')
    now = datetime.datetime.now()
    try:
        users = User.query.all()
        for user in users:
            if user.report_last_emailed_at == None:
                user.report_last_emailed_at = datetime.datetime.utcnow()
                db.session.add(user)
                db.session.commit()
            last_emailed_days = (now - user.report_last_emailed_at).days
            if last_emailed_days >= 30:
                for key in user.aws_keys:
                    date = "{} {}".format(now.strftime("%B"), now.year)
                    pretty_key = user.get_aws_key(key.key).pretty + ' ' + key.key
                    monthly_cost = AWSDetailedLineitem.get_monthly_cost_by_product(key.get_aws_user_id())
                    estimation_hour, estimation_month = get_estimation(user, key)
                    total = sum(float(i.get("cost")) for i in monthly_cost['products'])
                    email_template = template.render(email=user.email, date=date, key=pretty_key, products=monthly_cost['products'], total=total, hourly_cost=estimation_hour, monthly_cost=estimation_month)
                    if user.email.endswith("msolution.io"):
                        send_email(user.email, 'Trackit monthly report', email_template.encode('utf-8').strip(), True)
                    user.report_last_emailed_at = datetime.datetime.utcnow()
                    db.session.add(user)
                    db.session.commit()
    except Exception, e:
        print("ERROR " + str(e))


def get_estimation(user, key):
    estimation = MyResourcesAWS.query.filter(MyResourcesAWS.key == key.key).order_by(desc(MyResourcesAWS.date)).first()
    estimation = [] if not estimation else estimation.json()
    cost = sum(estimation_cost(e) for e in estimation)
    return cost, cost*720

def estimation_cost(estimation):
    return sum(item['cost'] for item in estimation['prices'] if item['name'] == 'aws')

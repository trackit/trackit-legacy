import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from app import app
import config

def send_email(email, subject, text, html, bypass_debug=False):
    if not config.SMTP_ADDRESS:
        return
    if app.debug:
        print 'EMAIL', email, subject.encode('utf8'), text.encode('utf8')
        if not bypass_debug:
            return
    fromaddr = config.SMTP_ADDRESS
    toaddrs  = email


    smtp_server = config.SMTP_SERVER
    smtp_username = config.SMTP_USERNAME
    smtp_password = config.SMTP_PASSWORD
    smtp_port = config.SMTP_PORT
    smtp_do_tls = True

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = email
    msg['Subject'] = subject
    message = text.encode('utf8')
    if html:
        msg.attach(MIMEText(message, 'html', 'UTF-8'))
    else:
        msg.attach(MIMEText(message, 'plain', 'UTF-8'))
    server = smtplib.SMTP(
        host = smtp_server,
        port = smtp_port,
        timeout = 10
    )
    server.set_debuglevel(10)
    server.starttls()
    server.ehlo()
    server.login(smtp_username, smtp_password)
    server.sendmail(fromaddr, toaddrs, msg.as_string())

def send_email_alternative(email, subject, content_plain, content_html, bypass_debug=False):
    if app.debug:
        print('EMAIL')
        print(email)
        print(subject.encode('utf8'))
        print((content_plain or u'').encode('utf8'))
        print((content_html or u'').encode('utf8'))
        if not bypass_debug:
            return

    fromaddr = config.SMTP_ADDRESS
    toaddrs  = email

    smtp_server = config.SMTP_SERVER
    smtp_username = config.SMTP_USERNAME
    smtp_password = config.SMTP_PASSWORD
    smtp_port = config.SMTP_PORT
    smtp_do_tls = True

    msg = MIMEMultipart('alternative')
    msg['From'] = fromaddr
    msg['To'] = email
    msg['Subject'] = subject
    content_plain = content_plain.encode('utf8')
    content_html = content_html.encode('utf8')
    msg.attach(MIMEText(content_plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(content_html, 'html', 'utf-8'))
    server = smtplib.SMTP(
        host = smtp_server,
        port = smtp_port,
        timeout = 10
    )
    server.set_debuglevel(10)
    server.starttls()
    server.ehlo()
    server.login(smtp_username, smtp_password)
    server.sendmail(fromaddr, toaddrs, msg.as_string())

def send_raw_email(sender, recipient, content_mime):
    if app.debug:
        print('RAW EMAIL')
    else:
        smtp_server = config.SMTP_SERVER
        smtp_username = config.SMTP_USERNAME
        smtp_password = config.SMTP_PASSWORD
        smtp_port = config.SMTP_PORT
        smtp_do_tls = True
        server = smtplib.SMTP(
            host = smtp_server,
            port = smtp_port,
            timeout = 10
        )
        server.set_debuglevel(10)
        server.starttls()
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender, recipient, content)

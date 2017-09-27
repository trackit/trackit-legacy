from celery import Celery
from app import app

runner = Celery()
runner.config_from_object(app.config)
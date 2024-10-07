from celery import Celery
import os
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoAPI.settings")

app = Celery("djangoAPI")

app.config_from_object('django.conf:settings', namespace="CELERY")

app.autodiscover_tasks()

@app.task
def ola_mundo():
    return "ola mundo"
    
#AutodockGPU. 

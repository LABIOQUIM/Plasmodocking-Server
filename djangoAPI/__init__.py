from __future__ import absolute_import,unicode_literals
from .tasks import app as celery_app

_all_ = ('celery_app',)
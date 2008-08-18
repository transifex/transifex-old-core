"""
>>> from django.test import Client
>>> from models import Project
>>> import datetime

>>> client = Client()

>>> response = client.get('/projects/')
>>> response.status_code
200
"""
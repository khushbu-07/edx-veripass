"""
URLs for the Veripass API

"""
from django.conf import settings
from django.conf.urls import url

from .views import (
    VeriPassView
)
app_name = 'edx_veripass'

urlpatterns = [
    url(r'^veripass/$', VeriPassView.as_view(), name='veripass'),
]

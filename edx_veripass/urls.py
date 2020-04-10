"""
URLs for the Veripass API

"""
from django.conf.urls import url

from .views import (
    VeriPassView,
    VeripassResultsCallback
)
app_name = 'edx_veripass'

urlpatterns = [
    url(r'^veripass/$', VeriPassView.as_view(), name='veripass'),
    url(r'^verified_results_callback$', VeripassResultsCallback.as_view(), name='veripass_results_callback'),
]

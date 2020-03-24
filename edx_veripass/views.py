# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import requests
from django.conf import settings
from django.http import Http404
from edxmako.paths import add_lookup
from edxmako.shortcuts import render_to_response
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .decorators import is_student


# Create your views here.
class VeriPassView(TemplateView):
    """
    Dashboard view that show veripass dashboard of student in iframe.
    Added decorator that will check user role. Only students can access this page. Raise 404 page if staff, superuser or course instructor tries to access this page directly.
    """
    template_name = 'edx_veripass/veripass_dashboard.html'

    @method_decorator(login_required)
    @is_student()
    def dispatch(self, request, *args, **kwargs):
        return super(VeriPassView, self).dispatch(request, *args, **kwargs)


    def get(self, request):
        user = request.user
        add_lookup('main', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'edx_veripass/templates'))
        # check if proctortrack is enabled or not.
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and settings.PROCTORING_BACKENDS['DEFAULT'] == 'proctortrack':

            #get configuration details of proctortrack client
            backend_name = settings.PROCTORING_BACKENDS['DEFAULT']
            proctoring_config = settings.PROCTORING_BACKENDS[backend_name]

            # get base url
            base_url = "{base_url}/{account_id}".format(
                base_url=proctoring_config['base_url'],
                account_id=proctoring_config['account_id']
            )

            # generate url that will get access token
            token_url = "{base_url}/jwt/access_token/".format(base_url=base_url)
            # data that need to send with url to get token
            token_payload = {
                "client_id": proctoring_config['client_id'],
                "client_secret": proctoring_config['client_secret']
            }
            # post request call to get access token
            token_response = requests.post(token_url, data=token_payload)

            # raise 404 page if will not get success response.
            if token_response.status_code == 200:
                access_token = token_response.json().get('access_token', None)
            else:
                raise Http404

            # generating url to get sso url for veripass dashboard of student
            signon_url = "{base_url}/sign-on/user/".format(base_url=base_url)
            signon_header = {'Authorization': "jwt {jwt_token}".format(jwt_token=access_token)}

            # data that need to be send with request
            full_name = user.profile.name.split(' ')
            signon_payload = {
                "first_name": full_name[0],
                "last_name": full_name[1] if len(full_name) > 1 else user.last_name,
                "user_id": user.id,
                "email": user.email,
                "role": "student",
            }
            signon_response = requests.post(signon_url, data=signon_payload, headers=signon_header)

            # get the sso url from response to launch student veripass dashboard. and return to the template.
            if signon_response.status_code == 200:
                pt_dashboard_url = signon_response.json().get('url', None)
            else:
                pt_dashboard_url = None
        else:
            pt_dashboard_url = None

        context = {
            'pt_dashboard_url': pt_dashboard_url,
        }
        return render_to_response(self.template_name, context)

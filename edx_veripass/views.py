# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import urllib
import requests
import logging
import datetime
from django.urls import reverse
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from common.djangoapps.edxmako.paths import add_lookup
from django.core.mail import send_mail
from common.djangoapps.edxmako.shortcuts import render_to_response
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from rest_framework.views import APIView
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication

from opaque_keys.edx.keys import CourseKey
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.verify_student.models import ManualVerification
from lms.djangoapps.verify_student.tasks import send_verification_status_email

from .decorators import is_student

log = logging.getLogger(__name__)

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
            # get course id from request and if exist then enroll student to verified track
            course_id = urllib.parse.unquote(urllib.parse.quote_plus(request.GET.get('course_id', '')))
            if course_id:
                self.set_verified_enrollment_track(user, course_id)

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


    def set_verified_enrollment_track(self, user, course_id):
        """This will get existing enrollment track of requested user and course and set it to verified mode"""
        course_key = CourseKey.from_string(course_id)
        try:
            enrollment = CourseEnrollment.objects.filter(user=user, mode__in=['audit', 'honor']).last()
        except CourseEnrollment.DoesNotExist:
            raise Http404

        if enrollment.mode.lower() != 'verified':
            enrollment.enroll(user, course_key, mode='verified')


class VeripassResultsCallback(APIView):

    authentication_classes = (SessionAuthentication, JwtAuthentication)

    def post(self, request):
        """
        Veripass will call this callback to tell us whether a user is
        verified to be who they said they are.
        """
        body = request.body

        try:
            body_dict = json.loads(body)
        except ValueError:
            log.exception("Invalid JSON received from Proctortrack:\n\n{}\n".format(body))
            return HttpResponseBadRequest("Invalid JSON. Received:\n\n{}".format(body))

        user_email = body_dict.get('user_email')
        result = body_dict.get('result')
        reason = body_dict.get('reason')
        error_code = body_dict.get("system_msg", "")

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            log.error("User does not exist with email %s", user_email)
            return HttpResponseBadRequest("User {} not found".format(user_email))

        try:
            attempt = ManualVerification.objects.get(user=user)
        except ManualVerification.DoesNotExist:
            attempt = ManualVerification.objects.create(user=user, status='created')
            attempt.save()
            log.info("Manual Verification created for user {username} with status {status}".format(username=user.username, status='created'))

        verification_status_email_vars = {
            'platform_name': settings.PLATFORM_NAME,
        }
        if result.lower() == 'submitted':
            attempt.status = 'submitted'
            attempt.save()
            log.info("Manual Verification status submitted to user: {username}".format(username=user.username))
        elif result.lower() == "pass":
            log.debug("Approving verification for %s", user.username)
            attempt.status = "approved"
            attempt.save()
            status = "approved"
            # email context - pass
            # expiry_date = datetime.date.today() + datetime.timedelta(
            #     days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
            # )
            # verification_status_email_vars['expiry_date'] = expiry_date.strftime("%m/%d/%Y")
            # verification_status_email_vars['full_name'] = user.profile.name
            # subject = _("Your {platform_name} ID Verification Approved").format(
            #     platform_name=settings.PLATFORM_NAME
            # )
            # context = {
            #     'subject': subject,
            #     'template': 'emails/passed_verification_email.txt',
            #     'email': user.email,
            #     'email_vars': verification_status_email_vars
            # }
            # send_verification_status_email(context)
            log.info("*****"*20)

        elif result.lower() == "fail":
            log.debug("Denying verification for %s", user.username)
            attempt.status = "denied"
            attempt.reason = reason
            attempt.save()
            status = "denied"
            # email context - fail
            # reverify_url = '{}{}'.format(settings.LMS_ROOT_URL, reverse("edx_veripass:veripass"))
            # verification_status_email_vars['reasons'] = json.loads(reason)
            # verification_status_email_vars['reverify_url'] = reverify_url
            # verification_status_email_vars['faq_url'] = settings.ID_VERIFICATION_SUPPORT_LINK
            # subject = _("Your {platform_name} Verification Has Been Denied").format(
            #     platform_name=settings.PLATFORM_NAME
            # )
            # context = {
            #     'subject': subject,
            #     'template': 'emails/failed_verification_email.txt',
            #     'email': user.email,
            #     'email_vars': verification_status_email_vars
            # }
            # send_verification_status_email(context)
            log.info("111111"*20)

        elif result.lower() == "system_fail":
            log.debug("System failure for %s -- resetting to must_retry", user.username)
            attempt.status = "must_retry"
            attempt.reason = reason
            attempt.save()
            status = "error"
            log.error("Veripass callback attempt for %s failed: %s", user.username, reason)
        else:
            log.error("Veripass returned unknown result %s", result)
            return HttpResponseBadRequest(
                "Result {} not understood. Known results: submitted, pass, fail, system_fail".format(result)
            )

        return HttpResponse("OK!")

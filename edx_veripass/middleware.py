from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from lms.djangoapps.verify_student.models import ManualVerification


class VeripassMiddleware(MiddlewareMixin):
    """
    Middleware to show veripass to students.

    Show veripass link in header if student has submitted
    face scan and id scan through veripass dashboard during
    enrollment or from student dashboard.
    """

    def process_request(self, request):
        show_veripass = False

        if request.user.is_authenticated:
            user = request.user
            verification = ManualVerification.objects.filter(user=user)

            if settings.FEATURES.get('ENABLE_VERIPASS', False) and \
                not (user.is_staff or user.is_superuser or user.courseaccessrole_set.count()) and \
                verification:
                show_veripass = True

        request.show_veripass = show_veripass

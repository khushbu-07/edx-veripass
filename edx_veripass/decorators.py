"""
This file defines any decorators used by the edx_veripaas app
"""
import functools
from django.http import Http404


def is_student():

    def _decorator(func):
        """Outer method decorator."""

        @functools.wraps(func)
        def _wrapper(self, request, *args, **kwargs):
            if request.user.courseaccessrole_set.count():
                raise Http404
            return func(self, request, *args, **kwargs)

        return _wrapper

    return _decorator

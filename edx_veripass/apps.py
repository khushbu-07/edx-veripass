# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class EdxVeripassConfig(AppConfig):
	"""
    Application Configuration for Veripass.
    """
    name = 'edx_veripass'

    def ready(self):
    	"""
        Connect handlers to signals.
        """
        from . import signals
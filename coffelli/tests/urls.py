# coding: utf-8

# DJANGO IMPORTS
from django.conf.urls import patterns, include

# GRAPPELLI IMPORTS
from coffelli.tests import admin


urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    (r'^coffelli/', include('coffelli.urls')),
)

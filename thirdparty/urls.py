

import os
from django.conf.urls.defaults import *


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import settings

urlpatterns = patterns('',
    # Example:
    # (r'^thirdparty/', include('thirdparty.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Development stuff, media served by django itself. Remove for a real
    # Emocracy installation (and have Apache handle media).
    (r'^media/(.*)', 'django.views.static.serve', {
        'document_root' : os.path.join(settings.PROJECT_PATH, 'media')
    }),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
    (r'^issues/', include('thirdparty.web.urls')),
)
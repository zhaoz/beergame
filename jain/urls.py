from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^jain/', include('jain.foo.urls')),


    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
              {'document_root': '%s/static/' % (settings.APP_DIR), 'show_indexes': True}),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'', include('jain.beergame.urls')),
)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.http import JsonResponse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import views

AdminSite.login_template = 'rest_framework/login.html'
views.LogoutView.template_name = 'rest_framework/login.html'


def get_version_for_api(_):
    from . import VERSION
    return JsonResponse(
        {
            'version': ".".join(str(i) for i in VERSION[:4]),
            'status': VERSION[-1],
            'metaData': "+%s" % VERSION[4]
        }
    )

def get_organization_specific_employee_directory(_):
    organization_specific_employee_directory = False
    if hasattr(settings, 'ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY'):
        organization_specific_employee_directory = settings.ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY
    return JsonResponse({'organization_specific_employee_directory': organization_specific_employee_directory})


urlpatterns = [
    # change this url after making sure /version/ api is allowed from nginx
    # probably /backend/ should be made as namespace , and all api inside it
    # so that we can put all api which are not depended on api version inside
    # /backend/ directly
    path('api/v1/version/', get_version_for_api, name='get_application_version'),
    path('api/v1/organization-specific/',get_organization_specific_employee_directory,name ='get_organization_specifiec_directory'),
    path('dj-admin/leave/actions/', include('irhrs.leave.admin_urls')),
    path('dj-admin/payroll/actions/', include('irhrs.payroll.admin_urls')),
    path('dj-admin/attendance/actions/', include('irhrs.attendance.admin_urls')),
    path('dj-admin/', admin.site.urls),
    path('ws/', include('irhrs.websocket.urls')),

    # TODO: Ravi remove this permission URL redirection
    path('permission/',
         RedirectView.as_view(url='/a/portal/', permanent=True)),
    path('a/', RedirectView.as_view(url='/a/portal/', permanent=False)),
    path('a/portal/', include('irhrs.portal.urls',
                              namespace='portal')),
    path('api-auth/', include('rest_framework.urls',
                              namespace='rest_framework')),

    # api urls
    path('api/v1/', include('irhrs.api.v1.urls')),
    path('o/', include('irhrs.openid.urls', namespace='oauth2_provider')),

]

if settings.DEBUG:

    # media render during
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

    # websocket echo test
    from irhrs.core.utils import echo

    urlpatterns += [
        path('echo/<status>/', echo)
    ]

    # swagger
    if 'rest_framework_swagger' in settings.INSTALLED_APPS:
        from irhrs.common.api.views.swagger_views import SwaggerSchemaView

        urlpatterns += [
            path('api/root/', SwaggerSchemaView.as_view(), name='swagger_view'),
            path('', RedirectView.as_view(url='/api/root/', permanent=False))
        ]

    # django-debug-toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            re_path(r'^__debug__/', include(debug_toolbar.urls))
        ]

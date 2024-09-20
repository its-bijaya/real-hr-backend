from django.urls import path, include
from rest_framework.routers import DefaultRouter

from irhrs.export.api.v1.views.export import ExportViewSet

router = DefaultRouter()

router.register('', ExportViewSet, 'export')

urlpatterns = [
    path(
        '<slug:organization_slug>/reports/', include(router.urls)
    ),
]

from .views import ExtractForPortal
from django.urls import path

app_name = 'portal'

urlpatterns = [
    path('extract/', ExtractForPortal.as_view(), name='extract-for-portal'),
]

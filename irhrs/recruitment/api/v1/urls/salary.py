from django.urls import path
from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import salary

app_name = 'salary'

router = DefaultRouter()


router.register(
    r'(?P<job_slug>[\w-]+)',
    salary.SalaryDeclarationViewSet,
    basename='declaration'
)


urlpatterns = [
    path(
        '<uuid:user_id>/<int:declaration_id>/',
        salary.SalaryDeclarationApproveView.as_view(
            {'patch': 'partial_update', 'get': 'retrieve'}
        ),
        name='declaration-approval'
    )
]

urlpatterns += router.urls

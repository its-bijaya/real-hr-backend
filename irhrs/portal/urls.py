from django.urls import path

from irhrs.portal.views import PermissionHomeView, GroupEditView, \
    GroupCreateView, UserGroupEditView, GroupDeleteView, \
    UserOrganizationEditView, OrganizationCreateView, OrganizationGroupUpdateView, OrganizationGroupListView

app_name = 'portal'

urlpatterns = [
    path('', PermissionHomeView.as_view(), name="permission-home"),
    path('groups/', GroupCreateView.as_view(), name="group-create"),
    path('groups/<int:pk>/permission/', GroupEditView.as_view(),
         name='group-edit'),
    path('groups/<int:pk>/users/', UserGroupEditView.as_view(),
         name='user-group-edit'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(),
         name='group-delete'),
    path('organization', OrganizationCreateView.as_view(),
         name='organization-create'),
    path('organization/<int:pk>/users/', UserOrganizationEditView.as_view(),
         name='user-organization-edit'),
    path(
        'organization-permissions/<int:pk>/',
        OrganizationGroupUpdateView.as_view(),
        name='organization-permissions-edit'
    ),
    path(
        'organization-permissions/', OrganizationGroupListView.as_view(),
        name='organization-permissions-list'
    ),
]

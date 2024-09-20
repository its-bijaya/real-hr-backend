from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, \
    PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, CreateView, \
    DeleteView, ListView
from rest_framework.generics import get_object_or_404

from irhrs.organization.models import Organization
from irhrs.permission.constants.groups import ADMIN, HR_ADMIN, ORG_HEAD, \
    DIVISION_HEAD, BRANCH_MANAGER
from irhrs.permission.constants.permissions import AUTH_PERMISSION
from irhrs.permission.models import HRSPermission
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.users.models import User
from .forms import GroupForm, GroupPermissionUpdateForm, \
    UserGroupForm, UserOrganizationForm, OrganizationCreateForm, \
    OrganizationGroupForm

initial_groups = [ADMIN, HR_ADMIN, ORG_HEAD, DIVISION_HEAD, BRANCH_MANAGER]


class AuthGroupViewMixin(LoginRequiredMixin, PermissionRequiredMixin):
    do_not_raise_exception = False

    def handle_no_permission(self):
        if self.do_not_raise_exception:
            return redirect_to_login(self.request.get_full_path(),
                                     self.get_login_url())

        raise PermissionDenied(self.get_permission_denied_message())

    def has_permission(self):
        return AUTH_PERMISSION.get(
            "code"
        ) in self.request.user.get_hrs_permissions()


class PermissionHomeView(AuthGroupViewMixin, TemplateView):
    do_not_raise_exception = True

    template_name = 'portal/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['groups'] = Group.objects.all().annotate(
            user_count=Count('user')
        ).order_by("name")
        context['groups_count'] = Group.objects.count()
        context['permissions'] = HRSPermission.objects.all().order_by("id")
        context['users'] = User.objects.all()
        context['organizations'] = Organization.objects.all().annotate(
            admin_count=Count(
                'users',
                filter=Q(users__can_switch=True),
                distinct=True
            ),
            permission_count=Count(
                'organization_permission_groups', distinct=True
            )
        )
        context['organization_count'] = Organization.objects.all().count()
        context['allowed_organization_count'] = settings.MAX_ORGANIZATION_COUNT
        context[
            'can_create_organization'] = context['organization_count'] < context['allowed_organization_count']
        context['common_permissions_count'] = OrganizationGroup.objects.filter(
            organization=None
        ).count()
        return context


class GroupEditView(AuthGroupViewMixin, UpdateView):
    queryset = Group.objects.all().exclude(name=ADMIN)
    form_class = GroupPermissionUpdateForm
    template_name = 'portal/ajax_form.html'
    success_url = '/a/portal/'

    def _get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"].update({
            'hrs_permissions':
                self.get_object().hrs_permissions.all()
        })
        return kwargs


class GroupCreateView(AuthGroupViewMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'portal/ajax_form.html'
    success_url = '/a/portal/'


class GroupDeleteView(AuthGroupViewMixin, DeleteView):
    queryset = Group.objects.all().exclude(name__in=initial_groups)
    success_url = '/a/portal/'
    template_name = 'portal/confirm_delete.html'


class UserGroupEditView(AuthGroupViewMixin, UpdateView):
    model = Group
    form_class = UserGroupForm
    template_name = 'portal/ajax_form.html'
    success_url = '/a/portal/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"].update({
            'users':
                self.get_object().user_set.all(),
        })
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs['multi_select_ids'] = ['id_users']
        return super().get_context_data(**kwargs)


class UserOrganizationEditView(AuthGroupViewMixin, UpdateView):
    model = Organization
    form_class = UserOrganizationForm
    success_url = '/a/portal'
    template_name = 'portal/ajax_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"].update({
            'users':
                User.objects.filter(
                    organization__organization=self.get_object(),
                    organization__can_switch=True),
        })
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs['multi_select_ids'] = ['id_users']
        return super().get_context_data(**kwargs)


class OrganizationCreateView(AuthGroupViewMixin, CreateView):
    model = Organization
    form_class = OrganizationCreateForm
    success_url = '/a/portal/'
    template_name = 'portal/ajax_form.html'

    def dispatch(self, request, *args, **kwargs):
        if Organization.objects.count() >= settings.MAX_ORGANIZATION_COUNT:
            return HttpResponseForbidden(
                f"Creating organizations more than {settings.MAX_ORGANIZATION_COUNT}"
                " is forbidden.")
        return super().dispatch(request, *args, **kwargs)


class OrganizationGroupUpdateView(AuthGroupViewMixin, UpdateView):
    form_class = OrganizationGroupForm
    queryset = OrganizationGroup.objects.exclude(
        group__name=ADMIN
    )
    template_name = 'portal/ajax_form.html'
    success_url = reverse_lazy('portal:organization-permissions-list')

    def get_context_data(self, **kwargs):
        kwargs['multi_select_ids'] = ['id_permissions']
        return super().get_context_data(**kwargs)


class OrganizationGroupListView(AuthGroupViewMixin, ListView):
    form_class = OrganizationGroupForm
    queryset = OrganizationGroup.objects.exclude(
        group__name=ADMIN
    )
    template_name = 'portal/organization_permission_list.html'
    success_url = 'a/portal/'

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=object_list, **kwargs)
        ctx['common_permissions_count'] = OrganizationGroup.objects.filter(
            organization=None
        ).count()
        ctx.update({
            'organizations': Organization.objects.all().annotate(
                admin_count=Count('users', filter=Q(users__can_switch=True)),
                permission_count=Count(
                    'organization_permission_groups', distinct=True
                )
            ),
            'groups': Group.objects.all(),
            'organization_groups': OrganizationGroup.objects.exclude(
                group__name=ADMIN
            ).annotate(
                permission_count=Count(
                    'permissions', distinct=True
                )
            ).order_by(
                'organization',
                '-permission_count'
            ),
            'common_permissions': HRSPermission.objects.filter(
              organization_specific=False
            ).count(),
            'org_permissions': HRSPermission.objects.filter(
              organization_specific=True
            ).count(),
        })
        return ctx

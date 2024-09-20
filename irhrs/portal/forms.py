from django.contrib.auth.models import Group
from django import forms
from django.db.models import Q, FloatField
from django.db.models.functions import Cast

from irhrs.organization.models import Organization, UserOrganization
from irhrs.permission.constants.groups import ADMIN, HR_ADMIN, ORG_HEAD, \
    DIVISION_HEAD, BRANCH_MANAGER
from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission
from irhrs.users.models import User
from irhrs.users.utils import set_user_organization_permission_cache

initial_groups = [ADMIN, HR_ADMIN, ORG_HEAD, DIVISION_HEAD, BRANCH_MANAGER]


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ("id", "name")


class GroupPermissionUpdateForm(GroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.name in initial_groups:
            self.fields.pop('name', None)


class UserGroupForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        to_field_name='id',
        required=False,
    )

    class Meta:
        model = Group
        fields = ("id",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {'class': 'form-control'})

    def save(self, commit=True):
        group = self.instance
        users = self.cleaned_data.get('users')

        group.user_set.clear()
        group.user_set.add(*users)
        group.save()

        for user in users:
            set_user_organization_permission_cache(user)

        return group


class UserOrganizationForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        to_field_name='id',
        required=False,
    )

    class Meta:
        model = Organization
        fields = ("id",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {'class': 'form-control'})

    def save(self, commit=True):
        organization = self.instance
        users = self.cleaned_data.get('users')

        users_set = set(users.all().values_list('id', flat=True))

        user_of_the_organization = UserOrganization.objects.filter(organization=organization)
        existing_from_list = user_of_the_organization.filter(user__in=users)

        new_user_ids = users_set - set(existing_from_list.values_list('user_id', flat=True))

        existing_from_list.update(can_switch=True)
        user_of_the_organization.filter(~Q(user__in=users)).update(can_switch=False)

        new_user_organization = list()

        for user_id in new_user_ids:
            new_user_organization.append(UserOrganization(user_id=user_id, organization=organization, can_switch=True))

        if new_user_organization:
            UserOrganization.objects.bulk_create(new_user_organization)

        return organization


class OrganizationCreateForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "abbreviation", "about", "ownership"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {'class': 'form-control'})

    def save(self, commit=True):
        self.instance.contacts = {}
        return super().save(commit=commit)


class OrganizationGroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=HRSPermission.objects.annotate(
            numeric_code=Cast('code', FloatField())
        ).order_by(
            'numeric_code'
        ),
        to_field_name='id',
        required=False,
    )

    class Meta:
        model = OrganizationGroup
        fields = 'permissions',

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if self.instance and self.instance.organization:
                field.queryset = field.queryset.filter(
                    organization_specific=True
                )
            else:
                field.queryset = field.queryset.exclude(
                    organization_specific=True
                )
            field.widget.attrs.update(
                {'class': 'form-control'}
            )

    def save(self, commit=True):
        from django.core.cache import cache
        cache.clear()
        return super().save(commit)

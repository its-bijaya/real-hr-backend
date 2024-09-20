from django import forms
from django.core.validators import FileExtensionValidator

from irhrs.leave.models import MasterSetting
from irhrs.organization.models import Organization


class MasterSettingExportForm(forms.Form):
    master_setting = forms.ModelChoiceField(
        queryset=MasterSetting.objects.all())


class MasterSettingImportForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=Organization.objects.all())
    name = forms.CharField(max_length=150)
    import_file = forms.FileField(
        validators=[FileExtensionValidator(
            allowed_extensions=['pickle', 'pkl'])]
    )

    def clean_organization(self):
        organization = self.cleaned_data['organization']
        if MasterSetting.objects.filter(
            organization=organization
        ).idle().exists():
            self.add_error(
                "organization",
                'This organization already has an idle master setting. '
                'Please delete that and try again.',
            )
        return organization

    def clean_name(self):
        organization = self.cleaned_data['organization']
        name = self.cleaned_data['name']

        if organization.leave_master_settings.filter(name=name).exists():
            self.add_error(
                "name",
                "Master setting with this name already exists for the organization."
            )
        return name


class LeaveBalanceImportForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=Organization.objects.all())
    import_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['xls', 'xlsx'])]
    )

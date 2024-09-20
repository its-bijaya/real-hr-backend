from django import forms
from django.core.validators import FileExtensionValidator

from irhrs.organization.models import Organization


class HeadingExportForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=Organization.objects.all())

    def clean_organization(self):
        organization = self.cleaned_data.get('organization')
        if not organization.headings.exists():
            self.add_error('organization', 'Organization has no headings.')
        return organization


class HeadingImportForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=Organization.objects.all())
    import_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['pickle', 'pkl'])]
    )

    def clean_organization(self):
        organization = self.cleaned_data.get('organization')
        if organization.headings.exists():
            self.add_error('organization', 'Organization already has payroll headings.'
                                           ' Please delete them before importing.')
        return organization

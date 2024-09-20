from django import forms
from django.contrib.auth import get_user_model
from django.http import Http404

from irhrs.attendance.models import WorkShift
from irhrs.organization.models import Organization

USER = get_user_model()


class AssignShiftToUserFromDateForm(forms.Form):
    from_date = forms.DateField(help_text="Select date to assign shift to user.")

    def __init__(self, *args, **kwargs):
        self.slug = kwargs.pop('slug')
        super(AssignShiftToUserFromDateForm, self).__init__(*args, **kwargs)
        slug_exists = Organization.objects.filter(slug=self.slug).exists()
        if not slug_exists:
            raise Http404
        self.fields['users'] = forms.ModelMultipleChoiceField(
            queryset=USER.objects.filter(detail__organization__slug=self.slug).current(),
            help_text="Select users to assign work shift."
        )
        self.fields['work_shift'] = forms.ModelChoiceField(
            queryset=WorkShift.objects.filter(organization__slug=self.slug),
            help_text="Select work shift to assign to user."
        )

from oauth2_provider.forms import AllowForm
from django import forms


class OCIDAllowForm(AllowForm):
    nonce = forms.CharField(required=False, widget=forms.HiddenInput())
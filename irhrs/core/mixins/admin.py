"""@irhrs_docs"""
from django import forms
from django.contrib import admin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import FormView


class ModelResourceMetaMixin:
    """
    Meta class for ImportExport Resource
    """
    exclude = ("created_by", "modified_by", "created_at", "modified_at",)


class AdminNotRequiredFormMixin(forms.ModelForm):
    not_required_fields = []

    def get_not_required_fields(self):
        return self.not_required_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for label, field in self.fields.items():
            if label in self.get_not_required_fields():
                field.required = False


class AdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user and self.request.user.is_authenticated and\
            self.request.user.is_staff


class AdminFormMixin(AdminMixin, FormView):
    template_name = 'admin_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(admin.site.each_context(self.request))
        return ctx

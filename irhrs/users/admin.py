from django import forms
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from irhrs.core.mixins.admin import ModelResourceMetaMixin

from irhrs.core.utils.admin.filter import AdminFilterByStatus, SearchByName, SearchByTitle


from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models.change_request import *
from .models.contact_and_address import *
from .models.education_and_training import *
from .models.experience import *
from .models.insurance import *
from .models.key_skill_ability import *
from .models.medical_and_legal import *
from .models.other import *
from .models.supervisor_authority import *
from .models.user import *

admin.site.register(ChangeRequest, AdminFilterByStatus)

admin.site.register(UserContactDetail, SearchByName)

admin.site.register(UserTraining, SearchByName)

admin.site.register(UserPastExperience, SearchByTitle)

admin.site.register(UserVolunteerExperience, SearchByTitle)

admin.site.register(ChronicDisease, SearchByTitle)

admin.site.register(RestrictedMedicine, SearchByTitle)

admin.site.register(AllergicHistory, SearchByTitle)

admin.site.register(UserLanguage, SearchByName)

admin.site.register(UserPublishedContent, SearchByTitle)

admin.site.register(UserSocialActivity, SearchByTitle)

admin.site.register(UserDocument, SearchByTitle)

admin.site.register([
    ChangeRequestDetails, UserAddress, UserEducation,
    UserExperienceStepHistory, UserInsurance,
    UserKSAO, UserMedicalInfo, UserLegalInfo, UserBank,
    UserSupervisor, UserPhone, ExternalUser
])

class UserExperienceResource(resources.ModelResource):

    class Meta(ModelResourceMetaMixin):
        model = UserExperience


class UserExperienceAdmin(ImportExportModelAdmin):
    resource_class = UserExperienceResource


admin.site.register(UserExperience, UserExperienceAdmin)



class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Password Confirmation',
                                       widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords didn't match.")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'email',
            'password',
            'is_active',
            'is_superuser',
        )

    def clean_password(self):
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    search_fields = ('first_name', 'middle_name', 'last_name')
    list_display = ('email', 'first_name', 'middle_name', 'last_name', 'email', 'is_active')
    list_filter = ('is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'middle_name',
                                      'last_name')}),
        ('Permissions', {'fields': ('is_superuser', 'is_active', 'groups',
                                    'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'confirm_password')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)


class UserDetailResource(resources.ModelResource):

    class Meta(ModelResourceMetaMixin):
        model = UserDetail


class UserDetailAdmin(ImportExportModelAdmin):
    resource_class = UserDetailResource


admin.site.register(UserDetail, UserDetailAdmin)

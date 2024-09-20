
# Monkey Patch ModelAdmin to create readonly_fields
# for 'created_by', 'modified_by', 'created_at', 'modified_at' as default field
# Register the app to make those fields as readonly
# if registering app is not possible for every models ,
# register the model in _ALLOWED_APPS and _ALLOWED_MODELS respectively
# Note :
# declaring readonly_fields in custom ModelAdmin will override this behaviour .
# if both of the behaviour is required , then merge_read_only_fields has to be
# set to True
# Example :
# class CustomModelAdmin(ModelAdmin):
#     readonly_fields = ('id',)
#     merge_read_only_fields = True # handler for merging

import types
from django.contrib.admin import ModelAdmin as DJModelAdmin

actual_init_from_model_admin = DJModelAdmin.__init__

_ALLOWED_MODELS = []
_ALLOWED_APPS = ['task', 'organization', 'attendance', 'event', 'leave']
_read_only_fields = 'created_by', 'modified_by', 'created_at', 'modified_at',


def patched_init(self, model, admin_site):
    def get_readonly_fields(self, _, obj=None):
        if obj :
            if (obj._meta.model.__name__.lower() in _ALLOWED_MODELS or
                    obj._meta.app_label.lower() in _ALLOWED_APPS):
                if self.readonly_fields is None:
                    return _read_only_fields
                elif self.readonly_fields and self.merge_read_only_fields:
                    return self.readonly_fields + _read_only_fields
            # hack for DJango_q since it has implemented this method0
            # need to refactor this Patch to work with such condition also
            # verified with : django-q==1.0.1
            statuses = ['success', 'failure']
            if (obj._meta.model.__name__.lower() in statuses and
                    obj._meta.app_label.lower() == 'django_q'):
                return [field.name for field in obj._meta.fields]
        return self.readonly_fields
    self.get_readonly_fields = types.MethodType(get_readonly_fields, self)
    actual_init_from_model_admin(self, model, admin_site)


DJModelAdmin.merge_read_only_fields = False
DJModelAdmin.__init__ = patched_init

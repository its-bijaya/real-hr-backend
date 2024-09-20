"""@irhrs_docs"""
from rest_framework.fields import JSONField


class JSONTextField(JSONField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if not isinstance(data, dict):
            self.fail('invalid')
        return data
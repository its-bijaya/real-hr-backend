from oauth2_provider.scopes import BaseScopes
from irhrs.openid.constants import (
    OPENID,
    PROFILE,
    APPLICATION_GROUPS
)


class SettingsScopes(BaseScopes):
    def get_all_scopes(self):

        scope_description = dict()

        scope_description[OPENID] = 'Has openid scope'
        scope_description[PROFILE] = 'Has basic profile info'
        scope_description[APPLICATION_GROUPS] = 'Has application group'

        return scope_description

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):

        scopes = self.get_default_scopes(
            application,
            request,
            *args,
            **kwargs
        )
        scopes.append(APPLICATION_GROUPS)
        return scopes

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        return [OPENID, PROFILE]

from urllib.parse import parse_qsl, urlparse
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from oauth2_provider.models import (
    AbstractApplication,
    AbstractAccessToken,
    AbstractGrant,
    AbstractRefreshToken
)

from irhrs.openid.utils.fields import ChoiceArrayField


class ApplicationManager(models.Manager):
    def get_by_natural_key(self, client_id):
        return self.get(client_id=client_id)


class Application(AbstractApplication):

    GRANT_AUTHORIZATION_CODE = "authorization-code"
    GRANT_IMPLICIT = "implicit"
    GRANT_HYBRID = "hybrid"
    GRANT_PASSWORD = "password"
    GRANT_CLIENT_CREDENTIALS = "client-credentials"
    GRANT_TYPES = (
        (GRANT_AUTHORIZATION_CODE, "Authorization code"),
        (GRANT_IMPLICIT, "Implicit"),
        (GRANT_PASSWORD, "Resource owner password-based"),
        (GRANT_CLIENT_CREDENTIALS, "Client credentials"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="applications",
        null=True, blank=True, on_delete=models.CASCADE
    )

    authorization_grant_type = None

    authorization_grant_types = ChoiceArrayField(
        models.CharField(
            max_length=32,
            choices=GRANT_TYPES,
        )
    )

    objects = ApplicationManager()

    def natural_key(self):
        return (self.client_id,)

    def redirect_uri_allowed(self, uri):
        """
        Checks if given url is one of the items in :attr:`redirect_uris` string

        :param uri: Url to check
        """
        parsed_uri = urlparse(uri)
        uqs_set = set(parse_qsl(parsed_uri.query))
        for allowed_uri in self.redirect_uris.split():
            parsed_allowed_uri = urlparse(allowed_uri)

            if (parsed_allowed_uri.scheme == parsed_uri.scheme and
                    parsed_allowed_uri.netloc == parsed_uri.netloc):

                aqs_set = set(parse_qsl(parsed_allowed_uri.query))

                if aqs_set.issubset(uqs_set):
                    return True

        return False

    def allows_grant_type(self, *grant_types):
        return set(
            self.authorization_grant_types
        ) & set(grant_types) == set(grant_types)


class Grant(AbstractGrant):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="grants"
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='grants'
    )


class RefreshToken(AbstractRefreshToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="refresh_tokens"
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    access_token = models.OneToOneField(
        'openid.AccessToken', on_delete=models.SET_NULL, blank=True, null=True,
        related_name="refresh_token"
    )


class AccessToken(AbstractAccessToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True,
        related_name="access_tokens"
    )
    source_refresh_token = models.OneToOneField(
        RefreshToken, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="refresh_token"
    )

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, blank=True, null=True,
        related_name='access_tokens'
    )
    token = models.TextField(unique=True, )


class ApplicationGroup(models.Model):
    name = models.CharField(max_length=120)
    application = models.ForeignKey(
        Application,
        related_name='application_groups',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class ApplicationUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='application_users',
        on_delete=models.CASCADE
    )

    application = models.ForeignKey(
        Application,
        related_name='application_users',
        on_delete=models.CASCADE
    )

    groups = models.ManyToManyField(ApplicationGroup)

    def __str__(self):
        return '%s - %s' % (
            self.user,
            self.application
        )

    class Meta:
        unique_together = (('user', 'application'),)

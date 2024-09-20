from django.core.cache import cache


def build_application_settings_cache(organization):
    for_user = list(
            organization.application_settings.all().values_list(
                'application', flat=True)
            )
    for_hr = list(
        organization.application_settings.filter(
            enabled=False
        ).values_list('application', flat=True)
    )
    disabled_apps = {"for_user":for_user, "for_hr":for_hr}
    cache.set(f'disabled_applications_{organization.id}', disabled_apps)

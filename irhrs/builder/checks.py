from django.core.checks import Tags, register, Critical

IS_REPORT_BUILDER_STABLE = False


@register(Tags.compatibility, deploy=True)
def report_builder_stability(app_configs, **kwargs):
    errors = []
    # some specific System config required for Report Builder
    if not IS_REPORT_BUILDER_STABLE:
        errors.append(
            Critical(
                "Report Builder is not Production Ready",
                hint="This app is currently in Development phase",
                id="report_builder.C001"
            )
        )
    return errors

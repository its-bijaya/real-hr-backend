import re
import subprocess

from django.core.checks import register, Tags, Error


@register(Tags.compatibility, deploy=True)
def check_redis_compatibility(app_configs, **kwargs):
    errors = []
    required_major_version = 5
    try:
        p = subprocess.Popen(["redis-server", "-v"], stdout=subprocess.PIPE)
    except FileNotFoundError:
        errors.append(
            Error(
                'Redis server not installed.',
                hint='apt install redis-server',
            )
        )

    out, err = p.communicate()
    decoded_output = out.decode("utf-8")
    matched_pattern = re.compile(r'v=\d+\.\d+\.\d+').findall(decoded_output)
    if matched_pattern:
        full_version = matched_pattern[0].split("=")[1]
        if full_version and int(full_version[0]) < required_major_version:
            errors.append(
                Error(
                    f'Redis server version must be greater or equal to {required_major_version}.',
                    hint='apt install redis-server',
                )
            )

    return errors

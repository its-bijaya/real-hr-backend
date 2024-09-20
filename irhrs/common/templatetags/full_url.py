from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def get_full_url(context, url):
    request = context.get('request')
    if request:
        return request.build_absolute_uri(url)
    else:
        # HACK : sometime i dont have request to generate absolute url
        # eg : sending email remainders to users >> TASK, reminder_email.py
        from django.conf import settings
        import urllib.parse
        BACKEND_URL = getattr(settings, 'BACKEND_URL')
        return urllib.parse.urljoin(BACKEND_URL, url)


@register.simple_tag()
def root_fe_url():
    from django.conf import settings
    return getattr(settings, 'FRONTEND_URL', 'localhost')

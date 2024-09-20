from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from irhrs.event.models import Event


def validate_event(post, request):
    """
    This is used to check whether the event associated
     with the post is enabled or not.
    It also checks for interactive event.
    It also verifies whether requested user is member/creator of event or none.

    :param post: instance of post method
    :param request:
    :return:
    """
    ct_event = ContentType.objects.get_for_model(Event)
    if post.content_type == ct_event:
        event = post.content_object
        if not event.enabled_event:
            raise ValidationError({'post': _('Event has been disabled')})
        if not event.interactive_event:
            raise ValidationError({'post': _('This event is not interactive')})
        if request and not event.event_members.filter(
                user=request.user).exists() and \
                not event.created_by == request.user:
            raise ValidationError({'post': _("You don't have permission"
                                             " to perform this action")})

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

VALID_MSG_TYPES = ['echo', 'notification', 'org_notification', 'logged_out', 'user_update']


def send_for_group(group_name, data, msg_type):
    if msg_type not in VALID_MSG_TYPES:
        return False
    if msg_type != 'echo':
        _ = data.update({'type': 'send.all'})
    _ = data.update({'event_type': msg_type.lower()})
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(group_name, data)
    return True

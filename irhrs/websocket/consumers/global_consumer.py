import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.functional import classproperty

from irhrs.organization.models import Organization
from ..utils import get_user_or_none, update_user
from asgiref.sync import sync_to_async

USER = get_user_model()

logger = logging.getLogger(__name__)


class UserOnline:
    CACHE_KEY = 'user_sockets_count'

    @classproperty
    def user_sockets_count(cls):
        return cache.get(cls.CACHE_KEY, {})

    @classmethod
    def reset_user_sockets_count(cls):
        cls.set_user_socket_count({})

    @classmethod
    def set_user_socket_count(cls, value):
        cache.set(cls.CACHE_KEY, value)

    @classmethod
    def register_user(cls, user_id):
        user_sockets_count = cls.user_sockets_count
        active_sessions = user_sockets_count.get(user_id, 0)
        active_sessions += 1
        user_sockets_count[user_id] = active_sessions

        cls.set_user_socket_count(user_sockets_count)

    @classmethod
    def remove_user(cls, user_id):
        user_sockets_count = cls.user_sockets_count
        active_sessions = user_sockets_count.get(str(user_id), 0)
        active_sessions -= 1

        if active_sessions <= 0 and cls.is_user_online(user_id):
            del user_sockets_count[user_id]
        else:
            user_sockets_count[user_id] = active_sessions

        cls.set_user_socket_count(user_sockets_count)

    @classmethod
    def is_user_online(cls, user_id):
        return str(user_id) in cls.user_sockets_count

    @classmethod
    def all_active_user_ids(cls):
        return list(map(int, cls.user_sockets_count.keys()))


class GlobalConsumer(AsyncJsonWebsocketConsumer):
    """
    Global Consumer

    Register a command by defining a method name `handle_command_(command_name)`

    eg.


    """
    _connected_organizations = []
    user_id = None

    async def connect(self):
        await self.accept()
        await self.send_json({
            'event_type': 'websocket',
            'message': 'WS connection successful ,  send user parameters now'
        })

    async def receive_json(self, content, **kwargs):
        try:
            handler_name = f"handle_command_{content.get('command', None)}"
            await getattr(self, handler_name, self._handle_command_not_found)(content, **kwargs)
        except Exception as e:
            logger.error(e, exc_info=True)

    async def disconnect(self, code):
        if self.user_id is not None:
            UserOnline.remove_user(self.user_id)

            await update_user(self.user_id, {'last_online': timezone.now()})
            # TODO @Ravi: Find why group_discard is raising CancelledError.
            await self.channel_layer.group_discard(self.user_id, self.channel_name)
            await self.__disconnect_organizations()
            self.user_id = None
        await self.send_json({
            'event_type': 'websocket',
            'message': 'Successfully disconnected from socket'
        })

    async def send_all(self, data):
        event_type = data.pop('event_type', None)
        await self.send_json({
                'event_type': event_type,
                'data': data
            })

    async def send_welcome(self, _):
        await self.send_json({
                'event_type': 'websocket',
                'message': 'Welcome Message'
            })

    async def send_echo(self, data):
        await self.send_json({
                'event_type': 'websocket',
                'message': 'Echo Test',
                'extra': data
            })

    @sync_to_async
    def __get_user(self):
        if self.user_id:
            return USER.objects.get(id=self.user_id)
        return None

    async def __disconnect_organizations(self):
        for channel_name in self._connected_organizations:
            await self.channel_layer.group_discard(channel_name, self.channel_name)

    @staticmethod
    def __get_organization(org_slug):
        return Organization.objects.filter(slug=org_slug).first()

    async def _handle_command_not_found(self, content, **kwargs):
        await self.send_json({
            'event_type': 'websocket',
            'message': 'Invalid Data Command'
        })

    # command handlers
    async def handle_command_join(self, content, **kwargs):
        if not content.get('token', None):
            await self.send_json({
                'event_type': 'websocket',
                'message': 'Valid User token is required to join'
            })
        else:
            user_id = await get_user_or_none(content.get('token'))
            if user_id is not None:
                if user_id == self.user_id:
                    await self.send_json({
                        'event_type': 'websocket',
                        'message': 'Already Joined'
                    })
                else:
                    # Add to group
                    self.user_id = user_id

                    UserOnline.register_user(user_id)

                    await self.channel_layer.group_add(self.user_id, self.channel_name)
                    await self.channel_layer.group_send(self.user_id, {'type': 'send.welcome'})
                    await self.send_json({
                        'event_type': 'websocket',
                        'message': 'joined'
                    })
            else:
                await self.send_json({
                    'event_type': 'websocket',
                    'message': 'Invalid User Token'
                })

    async def handle_command_subscribe_organization(self, content, **kwargs):
        if not self.user_id:
            await self.send_json({
                'event_type': 'websocket',
                'message': 'Not authenticated. Call join command to authenticate'
            })
            return

        organization_slug = content.get('organization_slug', None)
        user = await self.__get_user()
        organization = await self.__get_organization(organization_slug)

        await self.__disconnect_organizations()

        if user and organization:
            if organization.id in user.switchable_organizations_pks:
                self._connected_organizations.append(f'org_{organization.slug}')
                await self.channel_layer.group_add(f'org_{organization.slug}', self.channel_name)
                await self.channel_layer.group_send(self.user_id, {'type': 'send.welcome'})
            else:
                await self.send_json({
                    'event_type': 'websocket',
                    'message': 'Permission Denied.'
                })
        else:
            await self.send_json({
                'event_type': 'websocket',
                'message': 'Bad request.'
            })

    async def handle_command_unsubscribe_organizations(self, content, **kwargs):
        if not self.user_id:
            await self.send_json({
                'event_type': 'websocket',
                'message': 'Not authenticated. Call join command to authenticate'
            })
            return
        await self.__disconnect_organizations()
        await self.send_json({
            'event_type': 'websocket',
            'message': 'Successfully Unsubscribed to all organizations.'
        })

    async def handle_command_logout(self, content, **kwargs):
        if self.user_id is not None:
            UserOnline.remove_user(self.user_id)

            await self.channel_layer.group_discard(self.user_id, self.channel_name)
            await self.__disconnect_organizations()
            await update_user(self.user_id, {'last_online': timezone.now()})

            self.user_id = None
            await self.send_json({
                'event_type': 'websocket',
                'message': 'Successfully logged out from socket'
            })
        else:
            await self.send_json({
                'event_type': 'websocket',
                'message': 'Already logged out'
            })

    def __del__(self):
        # logger.debug(f"DELETED INSTANCE {self.user_id}")
        if self.user_id:
            UserOnline.remove_user(self.user_id)

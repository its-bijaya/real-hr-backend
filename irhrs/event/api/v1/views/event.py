import types

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count, Prefetch
from django.http import Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.constants.organization import EVENT_CANCELED_DELETED_EMAIL
from irhrs.core.mixins.viewset_mixins import DateRangeParserMixin
from irhrs.core.parser import MultiPartJSONParser
from irhrs.core.utils import email
from irhrs.core.utils.common import get_today, validate_permissions
from irhrs.event.api.v1.serializers.event import EventSerializer, \
    EventMembersSerializer, TopLikeSerializer, TopCommentSerializer
from irhrs.event.api.v1.serializers.meeting import MeetingSerializer
from irhrs.event.constants import PUBLIC, PENDING, ACCEPTED, REJECTED, MAYBE, \
    PRIVATE, MEMBERS_INVITATION_STATUS, \
    EVENT_TYPE_CHOICES, MEETING
from irhrs.event.models import Event, EventMembers, MeetingAcknowledgeRecord, \
    EventDetail, MeetingAttendance
from irhrs.event.utils import get_event_frontend_url
from irhrs.noticeboard.api.v1.serializers.post import PostSerializer
from irhrs.noticeboard.models import User, Post, CommentLike
from irhrs.notification.utils import add_notification
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import EVENT_PERMISSION


class EventViewSet(DateRangeParserMixin, ModelViewSet):
    serializer_class = EventSerializer
    parser_classes = (MultiPartParser, MultiPartJSONParser, FormParser)

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = (
        "title",
        "description",
    )

    ordering_fields = (
        'id',
        'created_at',
    )

    filter_fields = ('created_by', 'event_category', 'interactive_event')

    def get_organization(self):
        organization_slug = self.request.query_params.get('org_slug')
        as_hr = self.request.query_params.get('as')
        if as_hr == 'hr':
            organization = get_object_or_404(Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ), slug=organization_slug)
        else:
            organization = None
        return organization

    def get_serializer(self, *args, **kwargs):
        # if self.request.method.lower() != 'get':
        #     if 'members' not in self.request.data.keys():
        #         kwargs.update({'exclude_fields': ('members',)})
        if self.request.method.lower() == "post":
            if 'members' not in self.request.data.keys():
                kwargs.update({'exclude_fields': ('enabled_event', 'members')})
            else:
                kwargs.update({'exclude_fields': ('enabled_event',)})
        if self.request.method.lower() in ['put', 'patch']:
            if self.request.query_params.get('as', None) != 'hr' \
                or validate_permissions(
                        self.request.user.get_hrs_permissions(
                            self.get_organization()
                        ), EVENT_PERMISSION
                    ):
                if 'members' not in self.request.data.keys():
                    kwargs.update(
                        {'exclude_fields': ('enabled_event', 'members')})
                else:
                    kwargs.update({'exclude_fields': ('enabled_event',)})
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['org'] = self.get_organization()
        return ctx

    def get_queryset(self):
        if self.request.query_params.get('as', None) == 'hr' \
            and validate_permissions(
                        self.request.user.get_hrs_permissions(
                            self.get_organization()
                        ), EVENT_PERMISSION
                    ):
            queryset = Event.objects.filter(created_by__detail__organization=self.get_organization())
        else:
            queryset = Event.objects.filter(
                Q(created_by=self.request.user) |
                Q(members__in=[self.request.user]) |
                Q(event_type=PUBLIC)).distinct()
        return queryset.select_related('created_by',
                                       'created_by__detail',
                                       'created_by__detail__job_title',
                                       'room', 'room__meeting_room',
                                       'room__meeting_room__branch',
                                       'room__meeting_room__organization',
                                       ).prefetch_related(
            Prefetch('event_members',
                     queryset=EventMembers.objects.select_related('user',
                                                                  'user__detail',
                                                                  'user__detail__job_title'),
                     to_attr='_prefetched_members'))

    def filter_queryset(self, queryset, stats=False):
        invitation_status = self.request.query_params.get("invitation_status")
        event_type = self.request.query_params.get(
            "event_type") if not stats else None

        start_date, end_date = self.get_parsed_dates()
        queryset = super().filter_queryset(queryset).filter(
            start_at__date__lte=end_date,
            end_at__date__gte=start_date
        )

        _valid_event_types = [x for x in dict(EVENT_TYPE_CHOICES).keys()] + [
            'all']
        if event_type and event_type in _valid_event_types:
            if event_type != 'all':
                queryset = queryset.filter(event_type=event_type)

        _valid_invitation_status = [x for x in
                                    dict(MEMBERS_INVITATION_STATUS).keys()] + [
                                       'all']
        if invitation_status and invitation_status in _valid_invitation_status:
            if invitation_status == 'all':
                queryset = queryset.filter(
                    event_members__user=self.request.user)
            else:
                queryset = queryset.filter(
                    event_members__user=self.request.user,
                    event_members__invitation_status=invitation_status)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        agg_events_types = self.filter_queryset(
            self.get_queryset(), stats=True
        ).aggregate(
            all=Count('id', distinct=True),
            public=Count('id', filter=Q(event_type=PUBLIC), distinct=True),
            private=Count('id', filter=Q(event_type=PRIVATE), distinct=True)
        )
        start_date, end_date = self.get_parsed_dates()
        agg_invitation_data = EventMembers.objects.filter(
            event__start_at__date__lte=end_date,
            event__end_at__date__gte=start_date
        ).aggregate(
            all=Count('id', filter=Q(user=self.request.user)),
            pending=Count('id', filter=(Q(invitation_status=PENDING) & Q(
                user=self.request.user))),
            accepted=Count('id', filter=Q(invitation_status=ACCEPTED) & Q(
                user=self.request.user)),
            rejected=Count('id', filter=Q(invitation_status=REJECTED) & Q(
                user=self.request.user)),
            maybe=Count('id', filter=Q(invitation_status=MAYBE) & Q(
                user=self.request.user))
        )

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        resp = self.get_paginated_response(serializer.data)
        resp.data.update({'event_summary': agg_events_types})
        resp.data.update({'invitation_summary': agg_invitation_data})
        return resp

    def update(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.start_at <= get_today(with_time=True) <= obj.end_at:
            raise ValidationError({'detail': 'In progress event can\'t be updated.'})

        if self.request.query_params.get('as', None) == 'hr' \
            and validate_permissions(
                        self.request.user.get_hrs_permissions(
                            self.get_organization()
                        ), EVENT_PERMISSION
                    ):
            serializer = self.get_serializer_class()(obj, data=request.data,
                                                     fields=['enabled_event'],
                                                     context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)

        if obj.created_by == self.request.user:
            return super().update(request, *args, **kwargs)
        if obj.event_members.filter(user=self.request.user).exists():
            _fields = []
            if obj.members_can_modify:
                _fields += ['title', 'description', 'start_at', 'end_at',
                            'location',
                            'featured_image']
            if obj.members_can_invite:
                _fields += ['members']
            if _fields:
                serializer = EventSerializer(instance=obj,
                                             fields=_fields,
                                             data=request.data,
                                             context={'request': self.request},
                                             partial=kwargs.get(
                                                 'partial', False)
                                             )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            return Response(
                {'detail': 'You are a Member but not authorized '
                           'to perform this action'},
                status=status.HTTP_403_FORBIDDEN)

        return Response(
            {'detail': 'You are not authorized to perform this action'},
            status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """
        Delete event created by me only
        """
        obj = self.get_object()
        if obj.created_by == self.request.user:
            if not obj.repeat_rule:
                return super().destroy(request, *args, **kwargs)
            else:
                # add Accept-confirm : confirm-delete in HTTP Header to force delete
                if self.request.META.get(
                    'HTTP_ACCEPT_CONFIRM') == 'confirm-delete':
                    return super().destroy(request, *args, **kwargs)
                else:
                    return Response({
                        'detail': '{} is a recurring event and has its\
                                    recurring child. Deleting this event will \
                                    automatically delete the child events'.format(
                            obj.title)},
                        status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response(
            {'detail': 'You are not authorized to perform this action'},
            status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], parser_classes=[JSONParser])
    def accept(self, request, pk=None):
        obj = self.get_object()
        user = self.request.user
        if obj.created_by == user:
            return Response({'detail': 'Cannot join Events created by self'},
                            status=status.HTTP_400_BAD_REQUEST)
        if obj.end_at <= timezone.now():
            return Response({'detail': 'Cannot Join expired events'},
                            status=status.HTTP_400_BAD_REQUEST)
        if obj.event_members.filter(user=user).exists():
            ser = EventMembersSerializer(fields=('invitation_status',),
                                         data=request.data)
            if ser.is_valid(raise_exception=True):
                invitation_status = ser.data.get('invitation_status')
                initial_state = obj.event_members.filter(
                    user=user).first().invitation_status
                _ = obj.event_members.filter(user=user).update(
                    invitation_status=invitation_status)
                if initial_state != invitation_status:
                    self.send_response_notification(event=obj,
                                                    invitation_status=invitation_status)
                return Response(ser.data)
            return Response(
                {'detail': 'You are not an invitee for this event'},
                status=status.HTTP_403_FORBIDDEN)
        else:
            if obj.event_type == PUBLIC or (
                obj.event_type == PRIVATE and obj.created_by == user):
                _data = request.data.copy()
                _data['user'] = user.id
                _data['event'] = obj.id
                ser = EventMembersSerializer(data=_data,
                                             context={'request': request})
                if ser.is_valid(raise_exception=True):
                    ser.save()
                    invitation_status = ser.data.get('invitation_status')
                    self.send_response_notification(
                        event=obj,
                        invitation_status=invitation_status)
                    return Response(ser.data)
        return Response({'detail': 'You are not an invitee for this event'},
                        status=status.HTTP_403_FORBIDDEN)

    @action(detail=False)
    def subordinate(self, request, *args, **kwargs):
        subordinate_pks = self.request.user.subordinates_pks
        qs = Event.objects.filter(
            Q(created_by_id__in=subordinate_pks) | Q(
                event_members__user_id__in=subordinate_pks)
        ).distinct()

        def get_queryset(self):
            return qs.select_related('created_by', 'created_by__detail',
                                     'created_by__detail__job_title').prefetch_related(
                Prefetch('event_members',
                         queryset=EventMembers.objects.select_related(
                             'user',
                             'user__detail',
                             'user__detail__job_title'),
                         to_attr='_prefetched_members'))

        self.get_queryset = types.MethodType(get_queryset, self)
        return super().list(self, request)

    #
    # @action(detail=True)
    # def activities(self, request, pk=None, *args, **kwargs):
    #     pass
    @staticmethod
    def remove_member_from_meeting(event, member):
        meeting = getattr(event, 'meeting', None)
        if not meeting:
            return
        meeting.meeting_attendances.filter(member=member).delete()

    @action(detail=True, methods=['delete'],
            url_path='member/(?P<member_id>\d+)')
    def remove_member(self, request, pk=None, member_id=None, *args, **kwargs):
        event = self.get_object()

        try:
            event_member = EventMembers.objects.get(user=member_id, event=event)
        except EventMembers.DoesNotExist:
            return Response(
                {'detail': 'User is not the member of this event.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if event_member and request.user == event.created_by:
            if email.can_send_email(event_member.user, EVENT_CANCELED_DELETED_EMAIL):
                subject = f"Removed from the event {event.title}"
                message = f"You have been removed from the event {event.title}."
                email.send_notification_email(
                    recipients=[event_member.user.email],
                    subject=subject,
                    notification_text=message
                )

            MeetingAttendance.objects.filter(
                meeting__event=event,
                member=event_member.user
            ).delete()
            event_member.delete()
            if event.event_category == MEETING:
                self.remove_member_from_meeting(event, member_id)

            return Response(
                {'detail': 'Successfully removed the member from this event.'},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {'detail': "Event doesn't exist."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'], url_path='top-likes')
    def top_likes(self, request, pk=None, *args, **kwargs):
        event = self.get_object()

        ct = ContentType.objects.get_for_model(Event)
        post_like = User.objects.annotate(like_count=Count(
            'liked_posts',
            filter=Q(liked_posts__post__content_type=ct,
                     liked_posts__post__object_id=event.id,
                     liked_posts__liked=True))).filter(
            like_count__gt=0).order_by(
            '-like_count')[:5]

        serializer = TopLikeSerializer(post_like, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='top-comments')
    def top_comments(self, request, pk=None, *args, **kwargs):
        event = self.get_object()
        ct = ContentType.objects.get_for_model(Event)

        cmt_count = User.objects.annotate(comment_count=Count(
            'post_comments',
            filter=Q(post_comments__post__content_type=ct,
                     post_comments__post__object_id=event.id))).filter(
            comment_count__gt=0).order_by(
            '-comment_count')[:5]

        serializer = TopCommentSerializer(cmt_count, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def post(self, request, pk=None, *args, **kwargs):
        event = self.get_object()
        if not event.interactive_event:
            raise Http404

        if not event.created_by == request.user and (
            not EventMembers.objects.filter(
                event__members=request.user,
                event=event).exists() and validate_permissions(
                        self.request.user.get_hrs_permissions(
                            self.get_organization()
                        ), EVENT_PERMISSION
                    )
        ) and event.event_type.lower() == 'private':
            queryset = Post.objects.none()
        else:
            comment_likes = CommentLike.objects.filter(
                liked=True).select_related(
                'liked_by', 'liked_by__detail',
                'liked_by__detail__organization',
                'liked_by__detail__division'
            )

            ct = ContentType.objects.get_for_model(Event)
            queryset = Post.objects.filter(
                object_id=event.id, content_type=ct
            ).select_related(
                'posted_by', 'posted_by__detail',
                'posted_by__detail__organization',
                'posted_by__detail__division',
            ).prefetch_related(
                Prefetch('comments__likes',
                         queryset=comment_likes,
                         to_attr='liked_comments'),
                Prefetch('comments__likes',
                         queryset=comment_likes.filter(
                             liked_by=self.request.user),
                         to_attr='liked_by_user')
            ).all()

        page = self.paginate_queryset(queryset)
        serializer = PostSerializer(page, many=True,
                                    context=self.get_serializer_context())
        resp = self.get_paginated_response(serializer.data)

        return resp

    @action(detail=True, methods=['get'])
    def meeting(self, request, pk=None, *args, **kwargs):
        _meeting = EventDetail.objects.select_related(
            'event', 'time_keeper', 'minuter', 'time_keeper__user',
            'minuter__user', 'time_keeper__user__detail',
            'minuter__user__detail',
        ).prefetch_related(
            'meeting_agendas', 'event__members', 'meeting_agendas__comments',
            'meeting_agendas__agenda_tasks'
        ).filter(event=self.get_object()).first()
        is_hr = self.request.query_params.get('as', None) != 'hr' \
            or validate_permissions(
            self.request.user.get_hrs_permissions(
                self.get_organization()
            ), EVENT_PERMISSION
        )
        fields = []
        if _meeting and (_meeting.meeting_attendances.filter(
            member=self.request.user).exists() or is_hr):
            fields += ['id', 'time_keeper', 'minuter',
                       'prepared', 'notification_time', 'event',
                       'agenda', 'role', 'members', 'documents',
                       'meeting_room', 'acknowledged']

            if _meeting and _meeting.prepared:
                fields.append('other_information')
        else:
            fields += ['members', 'event']
        serializer = MeetingSerializer(_meeting,
                                       fields=fields,
                                       context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='meeting/acknowledge')
    def meeting_acknowledge(self, request, pk=None, *args, **kwargs):
        event = self.get_object()

        try:
            _meeting = event.eventdetail
        except:
            return Response(
                {
                    'detail': 'Event has no meeting'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if not _meeting.meeting_attendances.filter(
            member=self.request.user).exists():
            return Response(
                {
                    'detail': 'You may not have permission '
                              'to perform this action.'
                }, status=status.HTTP_403_FORBIDDEN
            )
        if _meeting.prepared:
            data = {
                'meeting_id': _meeting.id,
                'acknowledged': True,
                'member_id': self.request.user.id
            }
            MeetingAcknowledgeRecord.objects.create(**data)
            return Response(data)
        return Response(
            {
                'detail': 'Meeting has not been prepared yet.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def send_response_notification(self, event, invitation_status):
        invitation_status_helper = 'is Unsure for' if invitation_status == MAYBE else 'has ' + invitation_status
        notification_text = f"{self.request.user.full_name}" \
                            f" {invitation_status_helper} your event " \
                            f"{event.title}"
        notification_url = get_event_frontend_url(event)
        add_notification(
            recipient=event.created_by,
            text=notification_text,
            actor=self.request.user,
            action=event,
            url=notification_url,
        )

    # @action(detail=False)
    # def invitations(self, request, pk=None):
    #     qs = EventMembers.objects.filter(user=self.request.user)
    #     page = self.paginate_queryset(qs)
    #     serializer = EventMembersSerializer(instance=page, many=True, context={'request': request})
    #     return self.get_paginated_response(serializer.data)

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.db.models import Q, F, Value, When, Case
from django.db.models.functions import Concat
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from irhrs.core.mixins.viewset_mixins import (
    OrganizationCommonsMixin,
    OrganizationMixin, DateRangeParserMixin)
from irhrs.core.utils.common import get_complete_url, get_today, validate_permissions
from irhrs.event.constants import PUBLIC, INSIDE
from irhrs.event.models import Event
from irhrs.hris.utils import upcoming_birthdays, upcoming_anniversaries
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models import LeaveRequest
from irhrs.organization.models import Holiday
from irhrs.permission.constants.permissions import TRAINING_ASSIGN_PERMISSION
from irhrs.task.api.v1.serializers.checklist import TaskChecklistSerializer
from irhrs.task.models import Task
from irhrs.training.models import Training
from irhrs.training.models.helpers import PUBLIC as TRAINING_PUBLIC
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()
CALENDAR_EVENT_TYPES = [
    'leave', 'holiday', 'birthday', 'anniversary', 'event', 'training',
    'travel_attendance', 'task'
]


def is_authority(user, organization):
    return validate_permissions(
        user.get_hrs_permissions(organization),
        TRAINING_ASSIGN_PERMISSION
    )


class OrganizationCalenderView(OrganizationCommonsMixin,
                               DateRangeParserMixin,
                               OrganizationMixin, APIView
                               ):
    """
    get:

    Event list for event_type ['all', 'leaves', 'holidays', 'birthday', 'anniversary', 'events']
    and count for given date range

        param = {
            'start': 'YY-MM-DD',
            'end': 'YY-MM-DD,
            'type': 'leaves', 'holidays', 'birthday', 'anniversary', 'events', 'travel_attendance', 'all'
        }
        :default type = all
    """

    def _process_person_qs(self, queryset, date_field_name, tag, **kwargs):
        data = []
        for person in queryset:
            datum = {
                'title': person.full_name,
                'display_image': person.profile_picture_thumb,
                'start': getattr(person, date_field_name),
                'id': person.id,
                'tag': tag,
                'display_name': 'Work Anniversary' if tag == 'anniversary'
                else tag,
                'className': 'pa-1 px-3 text-xs-center {}'.format(
                    'green' if 'anniversary' in date_field_name else 'orange')
            }
            # datum.update(kwargs)
            data.append(datum)
        return data

    def _apply_filters(self, qs, date_field_name):
        filters = {
            "{}__range".format(date_field_name): [self.start_date,
                                                  self.end_date]
        }

        return qs.filter(**filters)

    def _aggregate_total_counts(self, birthday_count,
                                anniversaries_count, holidays_count,
                                leaves_count, events_count, training_count,
                                travel_attendance_count, task_count):
        data_count = {
            'birthday_count': birthday_count,
            'anniversary_count': anniversaries_count,
            'holidays_count': holidays_count,
            'leaves_count': leaves_count,
            'events_count': events_count,
            'training_count': training_count,
            'travel_attendance_count': travel_attendance_count,
            'task_count': task_count,
            'all_count': (
                birthday_count
                + anniversaries_count
                + holidays_count
                + leaves_count
                + events_count
                + travel_attendance_count
                + training_count
                + task_count
            )
        }
        return data_count

    def get_all(self):
        data = []
        birthday_data = self.get_birthday()
        data.extend(birthday_data)
        anniversaries_data = self.get_anniversary()
        data.extend(anniversaries_data)
        holidays_data = self.get_holiday()
        data.extend(holidays_data)
        leaves_data = self.get_leave()
        data.extend(leaves_data)
        events_data = self.get_event()
        data.extend(events_data)
        training_data = self.get_training()
        data.extend(training_data)
        travel_attendance_data = self.get_travel_attendance()
        data.extend(travel_attendance_data)
        task_data = self.get_task()
        data.extend(task_data)

        _data_container = {
            "event_data": data,
            "event_counts": self._aggregate_total_counts(
                birthday_count=len(birthday_data),
                anniversaries_count=len(anniversaries_data),
                holidays_count=len(holidays_data),
                leaves_count=len(leaves_data),
                events_count=len(events_data),
                training_count=len(training_data),
                travel_attendance_count=len(travel_attendance_data),
                task_count=len(task_data)
            )
        }
        return _data_container

    def get_all_count(self):
        birthday_count = self.get_birthday(count_only=True)
        anniversaries_count = self.get_anniversary(count_only=True)
        holidays_count = self.get_holiday(count_only=True)
        leaves_count = self.get_leave(count_only=True)
        events_count = self.get_event(count_only=True)
        training_count = self.get_training(count_only=True)
        travel_attendance_count = self.get_travel_attendance(count_only=True)
        task_count = self.get_task(count_only=True)

        return self._aggregate_total_counts(birthday_count=birthday_count,
                                            anniversaries_count=anniversaries_count,
                                            holidays_count=holidays_count,
                                            leaves_count=leaves_count,
                                            events_count=events_count,
                                            training_count=training_count,
                                            travel_attendance_count=travel_attendance_count,
                                            task_count=task_count)

    def get_birthday(self, count_only=False):
        qs = upcoming_birthdays(USER.objects.filter(is_active=True).current(),
                                start_date=self.start_date,
                                detail__organization=self.get_organization())
        fqs = self._apply_filters(qs, 'next_birthday')

        if count_only:
            return fqs.count()

        data = self._process_person_qs(fqs, 'next_birthday', tag='birthday')
        return data

    def get_anniversary(self, count_only=False):
        qs = upcoming_anniversaries(USER.objects.filter(is_active=True).current(),
                                    start_date=self.start_date,
                                    detail__organization=self.get_organization())
        fqs = self._apply_filters(qs, 'next_anniversary')

        if count_only:
            return fqs.count()

        data = self._process_person_qs(fqs, 'next_anniversary',
                                       tag='anniversary')
        return data

    def get_holiday(self, count_only=False):
        qs = Holiday.objects.filter(
            Q(organization__isnull=True) |
            Q(organization=self.get_organization()))
        fqs = self._apply_filters(qs, 'date')
        if count_only:
            return fqs.count()
        data = []

        for holiday in fqs:
            datum = {
                'title': holiday.name,
                'display_image': holiday.image.url if holiday.image else '',
                'start': holiday.date,
                'tag': 'holiday',
                'display_name': 'Holiday',
                'id': holiday.id,
                'className': 'pa-1 px-3 text-xs-center blue'
            }

            data.append(datum)
        return data

    def get_leave(self, count_only=False):
        queryset = LeaveRequest.objects.filter(
            Q(start__date=None) | Q(start__date__lte=self.end_date),
            Q(end__date=None) | Q(end__date__gte=self.start_date) &
            Q(user__detail__organization=self.get_organization()),
            Q(status=APPROVED)).select_related('user', 'user__detail')
        if count_only:
            return queryset.count()
        data = []

        for leave in queryset:
            datum = {
                'title': "{} {}".format(leave.user.full_name,
                                        leave.get_part_of_day_display() if leave.part_of_day else 'Full Leave'),
                'start': leave.start.astimezone(),
                'end': leave.end.astimezone(),
                'tag': 'leave',
                'display_name': 'Leave',
                'id': leave.id,
                'className': 'pa-1 px-3 text-xs-center purple'
            }
            data.append(datum)
        return data

    def get_event(self, count_only=False):
        queryset = Event.objects.filter(
            Q(start_at__date=None) | Q(start_at__date__lte=self.end_date),
            Q(end_at__date=None) | Q(end_at__date__gte=self.start_date) &
            (Q(event_type=PUBLIC) | Q(created_by=self.request.user) | Q(
                members__in=[self.request.user]))
        ).distinct()
        if count_only:
            return queryset.count()
        data = []
        for event in queryset:
            datum = {
                'title': "{} | {}".format(event.title.upper(),
                                          event.get_event_type_display()),
                'start': event.start_at,
                'end': event.end_at,
                'tag': 'event',
                'display_name': 'Event',
                'id': event.id,
                'className': 'pa-1 px-3 text-xs-center red'
            }
            data.append(datum)
        return data

    def get_training(self, count_only=False):
        from irhrs.training.models import Training
        fil = {}
        if not is_authority(self.request.user, self.organization):
            fil.update({'visibility': TRAINING_PUBLIC})
        qs = Training.objects.filter(
            training_type__organization=self.get_organization(),
            **fil
        )
        self.start_date_param = 'start'
        self.end_date_param = 'end'
        start, end = self.get_parsed_dates()

        qs = qs.filter(
            Q(start__date=None) | Q(start__date__lte=end),
            Q(end__date=None) | Q(end__date__gte=start)
        )
        if count_only:
            return qs.count()
        data = []

        for training in qs:
            datum = {
                'title': training.name,
                'display_image': get_complete_url(
                    training.image.url
                ) if training.image else '',
                'start': training.start.astimezone(),
                'end': training.end.astimezone(),
                'tag': 'training',
                'display_name': 'Training',
                'id': training.id,
                'className': 'pa-1 px-3 text-xs-center red'
            }
            data.append(datum)
        return data

    def get_travel_attendance(self, count_only=False):
        from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest, TravelAttendanceDays
        queryset = TravelAttendanceDays.objects.filter(
            travel_attendance__user__detail__organization=self.organization,
            travel_attendance__status=APPROVED,
            is_archived=False,
        ).filter(
            Q(travel_attendance__start=None) | Q(travel_attendance__start__lte=self.end_date),
            Q(travel_attendance__end=None) | Q(travel_attendance__end__gte=self.start_date)
        ).distinct()
        if count_only:
            return queryset.filter(day=get_today()).count()
        data = []
        for travel_day in queryset:
            datum = {
                'title': travel_day.travel_attendance.user.full_name,
                'start': travel_day.day,
                'end': travel_day.day,
                'tag': 'travel_attendance',
                'display_name': 'Travel Attendance',
                'id': travel_day.travel_attendance.id,
                'className': 'pa-1 px-3 text-xs-center teal'
            }
            data.append(datum)
        return data

    def get_task(self, count_only=False):
        qs = Task.objects.filter(
            task_associations__user=self.request.user,
            freeze=False, recurring_rule__isnull=True
        )
        self.start_date_param = 'start'
        self.end_date_param = 'end'
        start, end = self.get_parsed_dates()

        qs = qs.filter(
            Q(starts_at__date=None) | Q(starts_at__date__lte=end),
            Q(deadline__date=None) | Q(deadline__date__gte=start)
        )
        if count_only:
            return qs.count()
        data = []

        for task in qs:
            datum = {
                'title': task.title,
                'start': task.starts_at.astimezone(),
                'end': task.deadline.astimezone(),
                'tag': 'task',
                'display_name': 'Task',
                'id': task.id,
                'className': 'pa-1 px-3 text-xs-center red'
            }
            data.append(datum)
        return data

    # from django.utils.decorators import method_decorator
    # from django.views.decorators.cache import cache_page
    # from django.views.decorators.vary import vary_on_cookie
    # @method_decorator(cache_page(60 * 60 * 2))
    # @method_decorator(vary_on_cookie)
    def get(self, request, *args, **kwargs):
        _CALENDER_EVENT_TYPES = CALENDAR_EVENT_TYPES + ['all']
        event_type = request.query_params.get('type', 'all')
        start_date = request.query_params.get('start', None)
        end_date = request.query_params.get('end', None)
        if not event_type:
            event_type = 'all'
        event_types = list(filter(lambda x: x in _CALENDER_EVENT_TYPES,
                                  event_type.split(',')))
        if not event_types:
            return Response(
                {
                    'details': 'Incorrect calender event type, choices are {}'.format(
                        ','.join(_CALENDER_EVENT_TYPES))},
                status=status.HTTP_400_BAD_REQUEST)
        if not (start_date and end_date):
            return Response({"details": "Please provide start and end date"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            self.start_date = parse(start_date)
            self.end_date = parse(end_date)
        except (ValueError, TypeError):
            return Response(
                {"details": "Dates are not in correct format use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST)

        if 'all' in event_types:
            return_data = self.get_all()
        else:
            data = []
            for e in event_types:
                _temp_data = getattr(self, 'get_{}'.format(e))()
                data.extend(_temp_data)
            return_data = {
                "event_data": data,
                "event_counts": self.get_all_count()
            }
        return Response(return_data, status=status.HTTP_200_OK)


class OrganizationCalenderDetailView(OrganizationCommonsMixin,
                                     OrganizationMixin, APIView
                                     ):

    def get(self, request, *args, **kwargs):
        event_type = request.query_params.get('type', None)
        unique_id = request.query_params.get('id', None)
        if not (event_type and unique_id):
            return Response({"details": "Please provide Type and ID"},
                            status=status.HTTP_400_BAD_REQUEST)
        if event_type not in CALENDAR_EVENT_TYPES:
            return Response({"details": "Invalid Choices for Type"},
                            status=status.HTTP_400_BAD_REQUEST)
        _data, _status_code = getattr(self, 'handle_{}'.format(event_type))(
            unique_id)

        return Response(_data, status=_status_code)

    def _prepare_data(self, display_name, value, icon=None,
                      data_type='string'):
        return {
            'display_name': display_name,
            'value': value,
            'icon': icon,
            'data_type': data_type
        }

    def handle_leave(self, unique_id):
        qs = None
        try:
            qs = LeaveRequest.objects.get(
                Q(user__detail__organization=self.get_organization()) &
                Q(status=APPROVED) & Q(id=unique_id))
        except (LeaveRequest.DoesNotExist, ValueError):
            qs = None
        if not qs:
            return {
                       'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST
        _user_data = {
            'id': qs.user.id,
            'name': qs.user.full_name,
            'image': qs.user.profile_picture_thumb,
            'department': qs.user.detail.division.name if hasattr(qs.user,
                                                                  'detail') and getattr(
                qs.user.detail,
                'division') else 'N/A'
        }
        _data = {
            'legend': self._prepare_data('Legend', 'Leave'),
            'user': self._prepare_data('User', _user_data),
            'start_date': self._prepare_data('Start Date',
                                             qs.start.astimezone().strftime(
                                                 "%Y-%m-%d %H:%M:%S")),
            'end_date': self._prepare_data('End Date',
                                           qs.end.astimezone().astimezone().strftime(
                                               "%Y-%m-%d %H:%M:%S")),
            'part_of_day': self._prepare_data('Part of Day',
                                              qs.get_part_of_day_display())
        }

        return _data, status.HTTP_200_OK

    def handle_holiday(self, unique_id):
        qs = None
        try:
            qs = Holiday.objects.get(
                Q(id=unique_id) &
                (Q(organization__isnull=True) |
                 Q(organization=self.get_organization())))
        except (Holiday.DoesNotExist, ValueError):
            qs = None
        if qs:
            def get_rule_data(rule_data):
                """

                :param rule_data: it can be 'branch', 'division', 'ethnicity' and 'religion'
                :type rule_data: str
                :return: string
                """
                data = []
                if hasattr(qs, 'rule') and getattr(qs.rule, rule_data):
                    data = getattr(qs.rule, rule_data).values_list('name', flat=True)
                return data

            _data = {
                'legend': self._prepare_data('Legend', 'Holiday'),
                'user': None,
                'holiday_name': self._prepare_data('Holiday Name', qs.name),
                'date': self._prepare_data('Date', qs.date),
                'organization': self._prepare_data(
                    'Organization', qs.organization.name if qs.organization else 'N/A'
                ),
                'category': self._prepare_data('Category',
                                               qs.category.name if qs.category else 'N/A'),
                'description': self._prepare_data('Description',
                                                  qs.description if qs.description else 'N/A'),
                'division': self._prepare_data(
                    'Division',
                    get_rule_data('division'),
                    data_type='list'
                ),
                'branch': self._prepare_data(
                    'Branch',
                    get_rule_data('branch'),
                    data_type='list'
                ),
                'ethnicity': self._prepare_data(
                    'Ethnicity',
                    get_rule_data('ethnicity'),
                    data_type='list'
                ),
                'religion': self._prepare_data(
                    'Religion',
                    get_rule_data('religion'),
                    data_type='list'
                ),
                'gender': self._prepare_data('Gender',
                                             qs.rule.gender if hasattr(qs,
                                                                       'rule') and getattr(
                                                 qs.rule,
                                                 'gender') else 'N/A'),
            }

            return _data, status.HTTP_200_OK
        else:
            return {
                       'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST

    def handle_birthday(self, unique_id):
        qs = None
        try:
            qs = USER.objects.get(id=unique_id,
                                  detail__organization=self.get_organization())
        except (USER.DoesNotExist, ValueError):
            qs = None
        if not qs:
            return {
                       'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST
        _user_data = {
            'id': qs.id,
            'name': qs.full_name,
            'image': qs.profile_picture_thumb,
            'department': qs.detail.division.name if hasattr(qs,
                                                             'detail') and getattr(
                qs.detail,
                'division') else 'N/A'
        }
        _data = {
            'legend': self._prepare_data('Legend', 'Birthday'),
            'user': self._prepare_data('User', _user_data),
            'birthday_on': self._prepare_data('Birthday On',
                                              qs.detail.date_of_birth.replace(
                                                  year=timezone.now().date().year) if hasattr(
                                                  qs, 'detail') else 'N/A')
        }
        return _data, status.HTTP_200_OK

    def handle_anniversary(self, unique_id):
        qs = None
        try:
            qs = USER.objects.get(id=unique_id,
                                  detail__organization=self.get_organization())
        except (USER.DoesNotExist, ValueError):
            qs = None
        if not qs:
            return {
                       'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST
        _user_data = {
            'id': qs.id,
            'name': qs.full_name,
            'image': qs.profile_picture_thumb,
            'department': qs.detail.division.name if hasattr(qs,
                                                             'detail') and getattr(
                qs.detail,
                'division') else 'N/A'
        }
        _data = {
            'legend': self._prepare_data('Legend', 'Anniversary'),
            'user': self._prepare_data('User', _user_data),
            'anniversary_on': self._prepare_data('Anniversary On',
                                                 qs.detail.joined_date.replace(
                                                     year=timezone.now().date().year) if hasattr(
                                                     qs, 'detail') else 'N/A')
        }
        return _data, status.HTTP_200_OK

    def handle_event(self, unique_id):
        qs = None
        try:
            qs = Event.objects.filter(
                (Q(event_type=PUBLIC) | Q(created_by=self.request.user) | Q(
                    members__in=[self.request.user])) &
                Q(id=unique_id)
            ).select_related('room', 'room__meeting_room').first()
        except ValueError:
            qs = None
        if not qs:
            return {
                       'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST
        _user_data = {
            'id': qs.created_by.id,
            'name': qs.created_by.full_name,
            'image': qs.created_by.profile_picture_thumb,
            'department': qs.created_by.detail.division.name if hasattr(
                qs.created_by, 'detail') and getattr(
                qs.created_by.detail,
                'division') else 'N/A'
        }
        _data = {
            'legend': self._prepare_data('Legend', qs.title),
            'user': self._prepare_data('User', _user_data),
            'start_date': self._prepare_data(
                'Start Date', qs.start_at.astimezone(), data_type='datetime'
            ),
            'end_date': self._prepare_data(
                'End Date', qs.end_at.astimezone(), data_type='datetime'),
            'event_category': self._prepare_data(
                'Event Category', qs.get_event_category_display()
            ),
            'event_type': self._prepare_data('Event Type', qs.event_type),
            'location': self._prepare_data('Location', qs.location),
            'description': self._prepare_data('Description', qs.description),
            'featured_image': self._prepare_data('Featured Image',
                                                 qs.featured_image,
                                                 data_type='image'),
        }

        if qs.event_location == INSIDE:
            _room_data = {'name': None, 'slug': None}
            if qs.room:
                _room_data.update({
                    'name': qs.room.meeting_room.name,
                    'slug': qs.room.meeting_room.slug,
                    'organization_slug': qs.room.meeting_room.organization.slug
                })
            _data.update({
                'event_location': self._prepare_data('Location Type',
                                                     qs.event_location),
                'room': self._prepare_data('Room', _room_data),
                'featured_image': self._prepare_data(
                    'Featured Image',
                    qs.room.meeting_room.featured_image if qs.room else qs.featured_image,
                    data_type='image'
                )
            })
            del _data['location']
        else:
            _data.update({
                'event_location': self._prepare_data('Location Type',
                                                     qs.event_location),
            })

        if qs.repeat_rule:
            _data.update({
                'remarks': self._prepare_data('Remarks',
                                              'Is a recurring Event')
            })

        return _data, status.HTTP_200_OK

    def handle_travel_attendance(self, unique_id):
        from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest
        try:
            qs = TravelAttendanceRequest.objects.get(
                Q(user__detail__organization=self.get_organization()) &
                Q(status=APPROVED) & Q(id=unique_id))
        except (TravelAttendanceRequest.DoesNotExist, ValueError):
            return {'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST
        _user_data = {
            'id': qs.user.id,
            'name': qs.user.full_name,
            'image': qs.user.profile_picture_thumb,
            'department': qs.user.detail.division.name if hasattr(
                qs.user, 'detail'
            ) and getattr(
                qs.user.detail,
                'division'
            ) else 'N/A'
        }
        _data = {
            'legend': self._prepare_data('Legend', 'Travel Attendance'),
            'user': self._prepare_data('User', _user_data),
            'start_date': self._prepare_data(
                'Start Date', qs.start.strftime("%Y-%m-%d %H:%M:%S")
            ),
            'end_date': self._prepare_data(
                'End Date', qs.end.strftime("%Y-%m-%d %H:%M:%S")
            ),
            'part_of_day': self._prepare_data(
                'Part of Day', qs.get_working_time_display()
            )
        }

        return _data, status.HTTP_200_OK

    def handle_training(self, unique_id):
        qs = None
        fil = {}
        try:
            if not is_authority(self.request.user, self.organization):
                fil.update({'visibility': TRAINING_PUBLIC})
            qs = Training.objects.get(
                id=unique_id,
                **fil
            )

        except (Training.DoesNotExist, ValueError):
            qs = None

        if not qs:
            return {'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST

        external_trainers = qs.external_trainers.values_list('full_name', flat=True)
        internal_trainers = qs.internal_trainers.all().annotate(
            full_name=Case(
                When(
                    middle_name='',
                    then=Concat(
                        F('first_name'), Value(' '),
                        F('last_name')
                    )
                ),
                default=Concat(
                    F('first_name'), Value(' '),
                    F('middle_name'), Value(' '),
                    F('last_name')
                )
            )
        ).values_list('full_name', flat=True)

        _data = {
            'legend': self._prepare_data('Legend', qs.name),
            'description': self._prepare_data('Description', qs.description),
            'start_date': self._prepare_data(
                'Start Date', qs.start.astimezone(), data_type='datetime'
            ),
            'end_date': self._prepare_data(
                'End Date', qs.end.astimezone(), data_type='datetime'),
            'nature': self._prepare_data('Nature', qs.get_nature_display()),
            'location': self._prepare_data('Location', qs.location),
            'status': self._prepare_data('Status', qs.get_status_display()),
            'visibility': self._prepare_data('Visibility', qs.get_visibility_display()),
            'image': self._prepare_data('Image', qs.image.url if qs.image else None,
                                        data_type='image'),
            'external_trainers': self._prepare_data('External Trainers', external_trainers),
            'internal_trainers': self._prepare_data('Internal Trainers', internal_trainers),
        }
        if is_authority(self.request.user, self.organization):
            _data.update(
                {'budget_allocated': self._prepare_data('Budget Allocated', qs.budget_allocated)}
            )
        return _data, status.HTTP_200_OK

    def handle_task(self, unique_id):
        qs = None
        try:
            qs = Task.objects.get(
                id=unique_id
            )
        except (Training.DoesNotExist, ValueError):
            qs = None

        if not qs:
            return {'details': 'Incorrect request Parameter'}, status.HTTP_400_BAD_REQUEST

        responsible_persons = UserThinSerializer(
            qs.responsible_persons,
            fields=['id', 'full_name', 'profile_picture', 'cover_picture', 'organization', 'is_current',]
        ).data

        observers = UserThinSerializer(
            qs.observers,
            fields=['id', 'full_name', 'profile_picture', 'cover_picture', 'organization', 'is_current',]
        ).data

        checklists = TaskChecklistSerializer(
            qs.check_lists,
            fields=['id', 'check_list_title']
        ).data

        _data = {
            'legend': self._prepare_data('Legend', qs.title),
            'description': self._prepare_data('Description', qs.description),
            'start_date': self._prepare_data(
                'Start Date', qs.starts_at.astimezone(), data_type='datetime'
            ),
            'end_date': self._prepare_data(
                'End Date', qs.deadline.astimezone(), data_type='datetime'),
            'priority': self._prepare_data('Priority', qs.priority),
            'status': self._prepare_data('Status', qs.get_status_display()),
            'responsible_persons': self._prepare_data(
                'Responsible Persons',
                responsible_persons
            ),
            'observers': self._prepare_data('Observers', observers),
            'checklist': self._prepare_data('Checklists', checklists),
            'image': self._prepare_data('Image', qs.image.url if qs.image else None,
                                        data_type='image'),
        }
        return _data, status.HTTP_200_OK

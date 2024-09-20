import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import transaction
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from config.settings import TEXT_FIELD_MAX_LENGTH
from irhrs.attendance.constants import APPROVED, REQUESTED, FORWARDED
from irhrs.core.constants.organization import ADVANCE_EXPENSE_REQUEST_EMAIL
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, create_dummy_serializer
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.core.utils.common import extract_documents_with_caption
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest
from irhrs.organization.models import FiscalYear
from irhrs.permission.constants.permissions import EXPANSE_APPROVAL_SETTING_PERMISSION, \
    ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
from irhrs.reimbursement.constants import TRAVEL_EXPENSE_OPTIONS, LODGING, PER_DIEM, TRAVEL, \
    EXPENSE_TYPE
from irhrs.reimbursement.models.reimbursement import AdvanceExpenseRequest, \
    AdvanceExpenseRequestDocuments, AdvanceExpenseRequestApproval, \
    AdvanceExpenseRequestHistory, TravelRequestFromAdvanceRequest, AdvanceExpenseCancelHistory, \
    AdvanceExpenseCancelRequestApproval
from irhrs.reimbursement.utils.reimbursement import AdvanceExpenseSerializerMixin
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, \
    UserSignatureSerializer


USER = get_user_model()

RemarksRequiredSerializer = create_dummy_serializer({'remarks': serializers.CharField(
    max_length=600, allow_blank=False)})


class AdvanceExpenseRequestDetailSerializer(serializers.Serializer):
    heading = serializers.CharField(max_length=225, required=True)
    particulars = serializers.CharField(max_length=225, required=True)
    quantity = serializers.IntegerField(validators=[MinValueValidator(1)], required=True)
    rate = serializers.FloatField(validators=[MinValueValidator(0)], required=True)
    remarks = serializers.CharField(max_length=TEXT_FIELD_MAX_LENGTH)
    amount = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_amount(obj):
        return obj.get('quantity', 0) * obj.get('rate', 0)


class AdvanceExpenseRequestDetailForTravelSerializer(serializers.Serializer):
    detail_type = serializers.ChoiceField(choices=TRAVEL_EXPENSE_OPTIONS)
    departure_time = serializers.DateTimeField(allow_null=True, required=False)
    arrival_time = serializers.DateTimeField(allow_null=True, required=False)
    departure_place = serializers.CharField(max_length=255, allow_blank=True, required=False)
    arrival_place = serializers.CharField(max_length=255, allow_blank=True, required=False)
    heading = serializers.CharField(max_length=255, required=False, allow_blank=True)
    date = serializers.DateField(allow_null=True, required=False)
    rate_per_day = serializers.IntegerField(min_value=0, required=True)
    day = serializers.FloatField(validators=[MinValueValidator(0)], required=True)
    description = serializers.CharField(max_length=TEXT_FIELD_MAX_LENGTH, required=False,
                                        allow_blank=True)
    amount = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_amount(obj):
        return obj.get('day', 0) * obj.get('rate_per_day', 0)

    def validate(self, attrs):
        detail_type = attrs.get('detail_type')
        departure_time = attrs.get('departure_time')
        departure_place = attrs.get('departure_place')

        arrival_time = attrs.get('arrival_time')
        arrival_place = attrs.get('arrival_place')

        heading = attrs.get('heading')
        date = attrs.get('date')

        if detail_type in [PER_DIEM, LODGING]:
            if not departure_time:
                raise ValidationError({
                    'departure_time': ['This field is required.']
                })
            elif not departure_place:
                raise ValidationError({
                    'departure_place': ['This field is required.']
                })
            elif not arrival_place:
                raise ValidationError({
                    'arrival_place': ['This field is required.']
                })
            elif not arrival_time:
                raise ValidationError({
                    'arrival_time': ['This field is required.']
                })

            attrs.update({
                'heading': '',
                'date': None
            })
        else:
            if not heading:
                raise ValidationError({
                    'heading': ['This field is required.']
                })
            if not date:
                raise ValidationError({
                    'date': ['This field is required.']
                })
            attrs.update({
                'departure_time': None,
                'arrival_time': None,
                'arrival_place': '',
                'departure_place': ''
            })
        return super().validate(attrs)


class AdvanceExpenseRequestDocumentsSerializer(DynamicFieldsModelSerializer):
    attachment = serializers.FileField(validators=[FileExtensionValidator(
        allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
    )])

    class Meta:
        model = AdvanceExpenseRequestDocuments
        fields = 'id', 'attachment', 'name',

    def create(self, validated_data):
        validated_data['expense'] = self.context.get('expense')
        return super().create(validated_data)


class AdvanceExpenseRequestApprovalsSerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = AdvanceExpenseRequestApproval
        fields = 'id', 'user', 'status', 'role', 'level', 'remarks'

    @staticmethod
    def get_user(obj):
        fields = ['id', 'full_name', 'profile_picture',
                  'cover_picture', 'is_online']
        serializer_data = dict(fields=fields)

        if obj.acted_by:
            fields.append('job_title')
            if obj.add_signature:
                fields.append('signature')
            serializer_data.update({
                'instance': obj.acted_by
            })
        else:
            serializer_data.update({
                'instance': obj.user.all(),
                'many': True
            })

        return UserSignatureSerializer(**serializer_data).data


class AdvanceExpenseRequestHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(fields=['id', 'full_name'])

    class Meta:
        model = AdvanceExpenseRequestHistory
        fields = ['actor', 'action', 'target', 'remarks', 'created_at']


class AdvanceExpenseRequestSerializer(
    AdvanceExpenseSerializerMixin,
    DynamicFieldsModelSerializer
):
    associates = serializers.PrimaryKeyRelatedField(
        queryset=USER.objects.all().current(),
        many=True,
        required=False
    )
    documents = AdvanceExpenseRequestDocumentsSerializer(
        many=True,
        read_only=True
    )
    approvals = AdvanceExpenseRequestApprovalsSerializer(
        many=True,
        read_only=True
    )
    history = AdvanceExpenseRequestHistorySerializer(
        source='histories',
        many=True,
        read_only=True
    )
    travel_request = serializers.SerializerMethodField()
    employee = serializers.SerializerMethodField()
    recipient = UserThinSerializer(
        fields=[
            'id', 'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'is_online', 'organization', 'is_current',
        ],
        read_only=True,
        many=True
    )
    settlement_exists = serializers.ReadOnlyField(default=None, allow_null=True)
    cancel_request_exists = serializers.ReadOnlyField(default=None, allow_null=True)

    class EmployeeApprovalSerializer(serializers.Serializer):
        approval_level = serializers.IntegerField()
        recipient = serializers.PrimaryKeyRelatedField(
            queryset=USER.objects.all()
        )
    selected_approvers = EmployeeApprovalSerializer(
        required=False,
        write_only=True,
        many=True
    )

    class Meta:
        model = AdvanceExpenseRequest
        fields = [
            'id', 'reason', 'advance_code', 'type', 'associates', 'description', 'remarks',
            'created_at', 'currency', 'total_amount', 'status', 'advance_amount', 'detail',
            'documents', 'approvals', 'history', 'employee', 'recipient', 'add_signature',
            'settlement_exists','selected_approvers', 'travel_request','requested_amount',
            'cancel_request_exists'
        ]
        read_only_fields = ['type', 'advance_amount', 'advance_code',
                            'total_amount', 'created_at', 'status']

    @staticmethod
    def _get_details_serializer(expense_type):
        if expense_type.title() == TRAVEL:
            return AdvanceExpenseRequestDetailForTravelSerializer
        return AdvanceExpenseRequestDetailSerializer

    def extract_documents(self):
        return extract_documents_with_caption(
            self.initial_data,
            file_field='attachment',
            filename_field='name'
        )

    def get_fields(self):
        fields = super().get_fields()
        expense_type = self.context.get('expense_type')
        if self.request and self.request.method.lower() == 'get':
            fields['associates'] = UserThinSerializer(
                fields=[
                    'id', 'full_name', 'profile_picture', 'cover_picture',
                    'job_title', 'organization', 'is_current', 'is_online'
                ],
                many=True
            )
            fields['detail'] = serializers.SerializerMethodField()
        if self.request and self.request.method.lower() == 'post':
            fields['detail'] = self._get_details_serializer(expense_type)(
                many=True,
                write_only=True
            )
        return fields

    def get_detail(self, obj):
        detail = json.loads(obj.detail)
        return self._get_details_serializer(obj.type)(
            detail,
            many=True
        ).data

    def get_travel_request(self, instance):
        advance_request = getattr(instance, 'travel_request_from_advance', None)
        if not advance_request:
            return {}
        return {
            'start': advance_request.start,
            'end': advance_request.end,
            'start_time': advance_request.start_time,
            'end_time': advance_request.end_time
        }
    @transaction.atomic
    def create(self, validated_data):
        documents = validated_data.pop('documents',[])
        associates = validated_data.pop('associates', [])
        detail = validated_data.pop('detail')
        expense_type = self.context.get('expense_type')
        travel_data = validated_data.pop('travel_data', [])

        from irhrs.reimbursement.utils.helper import calculate_total, calculate_advance_amount
        validated_data['total_amount'] = calculate_total(detail, expense_type)
        validated_data['advance_amount'] = calculate_advance_amount(
            detail, expense_type, organization=self.context['organization']
        )
        validated_data['employee'] = self.request.user

        from irhrs.reimbursement.utils.helper import convert_to_iso_format
        validated_data['detail'] = json.dumps(detail, default=convert_to_iso_format)

        validated_data['type'] = self.context.get('expense_type')
        selected_approvers = validated_data.pop("selected_approvers", None)
        instance = super().create(validated_data)
        instance.advance_code = self.generate_taarf_code(instance)
        instance.save()
        send_travel_request = self.request.data.get('send_travel_request')
        if send_travel_request == 'true':
            ser = TravelRequestFromAdvanceRequestSerializer(
                data = {'advance_expense_request': instance.id, **travel_data}
            )
            ser.is_valid(raise_exception=True)
            ser.save()

        if associates:
            instance.associates.set(associates)

        for document in documents:
            AdvanceExpenseRequestDocuments.objects.create(expense=instance, **document)

        self.set_approvers(AdvanceExpenseRequestApproval, instance, selected_approvers)

        AdvanceExpenseRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action='requested',
            remarks=instance.reason
        )
        organization = instance.employee.detail.organization
        text_type = {
            'Travel': 'Travel Authorization and Advance Request form'
        }
        text = f"{instance.employee.full_name} has sent " \
               f"{text_type.get(instance.type, 'advance expense request')}."
        add_notification(
            text=text,
            recipient=instance.recipient.all(),
            action=instance,
            actor=instance.employee,
            url='/user/expense-management/request/expense'
        )
        notify_organization(
            text=text,
            action=instance,
            organization=organization,
            actor=instance.employee,
            url=f'/admin/{organization.slug}/expense-management/request',
            permissions=[
                EXPANSE_APPROVAL_SETTING_PERMISSION,
                ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
            ],
        )
        # Send mail to approver when user Request for Advance Expense.
        subject = f"{instance.created_by} has sent an Advance expenses request"
        email_text=(
            f"{instance.created_by} has requested advance expense for {instance.reason}"
        )
        async_task(
            send_email_as_per_settings,
            instance.recipient.all(),
            subject,
            email_text,
            ADVANCE_EXPENSE_REQUEST_EMAIL
        )
        return instance

    @staticmethod
    def generate_taarf_code(instance):
        organization = instance.employee.detail.organization
        expense_request = AdvanceExpenseRequest.objects.filter(
            employee__detail__organization=organization
        ).exclude(id=instance.id).order_by('created_at')
        # to check whether there is any existing expense request or not
        if not expense_request:
            new_code = organization.reimbursement_setting.advance_code
        else:
            fiscal_year = FiscalYear.objects.current(organization)

            if fiscal_year:
                expense_request = expense_request.filter(
                    created_at__range=(fiscal_year.applicable_from, fiscal_year.applicable_to)
                )
            if not expense_request:
                new_code = 1
            else:
                last_request = expense_request.last()
                new_code = last_request.advance_code + 1
        return new_code

    def validate(self, attrs):
        expense_type = self.context.get('expense_type')
        detail = attrs.get('detail')
        if expense_type not in dict(EXPENSE_TYPE):
            raise ValidationError(
                {
                    'non_field_errors': [
                        f'\'expense_type\' can be {",".join(dict(EXPENSE_TYPE))}'
                    ]
                }
            )

        organization = self.context['organization']

        per_diem = list(filter(lambda x: x.get('detail_type') == PER_DIEM, detail))
        lodging = list(filter(lambda x: x.get('detail_type') == LODGING, detail))

        self.validate_advance_expense_request_date(per_diem, PER_DIEM)
        self.validate_advance_expense_request_date(lodging, LODGING)

        selectable_approver_exists = organization.expense_setting.filter(select_employee=True).exists()
        if selectable_approver_exists and 'selected_approvers' not in attrs.keys():
            raise ValidationError({"selected_approvers": "Approvers field required."})

        documents = self.extract_documents()
        serializer = AdvanceExpenseRequestDocumentsSerializer(data=documents, many=True)
        serializer.is_valid(raise_exception=True)
        attrs['documents'] = documents
        send_travel_request = self.request.data.get('send_travel_request')
        if send_travel_request == 'true':
            travel_data = {
                "start": self.request.data['travel_request[start]'],
                "start_time": self.request.data['travel_request[start_time]'],
                "end": self.request.data['travel_request[end]'],
                "end_time": self.request.data['travel_request[end_time]']
            }
            attrs['travel_data'] = travel_data
        requested_amount = attrs.get('requested_amount')
        if requested_amount:
            from irhrs.reimbursement.utils.helper import calculate_total, calculate_advance_amount
            attrs['advance_amount'] = calculate_advance_amount(
            detail, expense_type, organization=self.context['organization'])
            advance_amount = attrs.get('advance_amount')

            if advance_amount is not None and advance_amount < requested_amount:
                raise ValidationError({
                    'requested_advance_amount': 'Cannot be greater than Eligible maximum Amount.'
                })
            if requested_amount < 0:
                raise ValidationError({
                    "requested_advance_amount": 'Cannot request negative amount. '
                })
        return super().validate(attrs)

    @staticmethod
    def validate_advance_expense_request_date(data, detail_type):
        for index, current_data in enumerate(data):
            departure_time = current_data.get('departure_time')
            arrival_time = current_data.get('arrival_time')
            previous_data = None
            if index > 0:
                previous_data = data[index - 1]

            prefix = f'departure_time{index}' if previous_data else f'arrival_time{index}'
            error_prefix = f'{prefix}-lodging' if detail_type == LODGING else prefix

            if previous_data and previous_data.get(
                'arrival_time') and departure_time < previous_data.get('arrival_time'):
                raise ValidationError({
                    f'{error_prefix}': 'Departure date cannot be smaller than previous arrival date.'
                })

            if departure_time > arrival_time:
                raise ValidationError({
                    f'{error_prefix }': 'Arrival date must be greater than departure date.'
                })

    def validate_associates(self, associates):
        if self.request and self.request.user in associates:
            raise ValidationError(
                'User requesting for advance expense can\'t be added as associates.'
            )
        return associates

    @staticmethod
    def validate_detail(detail):
        if not detail:
            raise ValidationError(
                'There must be at least one detail associated with this request.'
            )
        return detail


class AdvanceAmountUpdateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AdvanceExpenseRequest
        fields = ['requested_amount', 'remarks']

    @transaction.atomic
    def update(self, instance, validated_data):
        previous_amount = instance.advance_amount
        remarks = validated_data.pop('remarks', None)
        new_instance = super().update(instance, validated_data)
        if not remarks:
            remarks = f'Updated advance amount from' \
                      f' {previous_amount} - {new_instance.requested_amount}.'

        actor = new_instance.modified_by
        if new_instance.requested_amount > previous_amount:
            raise ValidationError({
                'requested_amount': 'Cannot be greater than Eligible Maximum Advance Amount.'
            })
        if new_instance.requested_amount < 0 :
            raise ValidationError({
                'requested_amount': 'Cannot update negative amount.'
            })
        AdvanceExpenseRequestHistory.objects.create(
            request=instance,
            actor=actor,
            action='Updated',
            remarks=remarks,
            target=f'{previous_amount} - {new_instance.requested_amount}'
        )
        return new_instance


class TravelRequestFromAdvanceRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = TravelRequestFromAdvanceRequest
        fields = '__all__'

    def validate(self, attrs):
        start = attrs.get('start')
        end = attrs.get('end')
        employee = getattr(attrs.get('advance_expense_request'), 'employee', None)
        travel_attendance_request = TravelAttendanceRequest.objects.filter(
            user=employee,
            status__in = [REQUESTED, APPROVED, FORWARDED]
        ).filter(
            Q(start__range=(start, end))
            | Q(end__range=(start, end))
        ).exists()
        if travel_attendance_request:
            raise ValidationError(
                f'There is travel attendance request on this range.'
            )
        if start and end and start > end:
            raise ValidationError({
                'start': ['Start Date must be smaller than End Date.']
            })
        if employee:
            same_request = TravelRequestFromAdvanceRequest.objects.filter(
                advance_expense_request__status__in = [REQUESTED, APPROVED],
                advance_expense_request__employee = employee
            ).filter(
                Q(start__range=(start, end))
                | Q(end__range=(start, end))
            ).first()

            if same_request:
                raise ValidationError(
                    f'There is {same_request.advance_expense_request.status} travel request on this range.'
                )

        return super().validate(attrs)


class AdvanceCancelApprovalSerializer(AdvanceExpenseRequestApprovalsSerializer):
    class Meta(AdvanceExpenseRequestApprovalsSerializer.Meta):
        model = AdvanceExpenseCancelRequestApproval


class AdvanceExpenseCancelHistorySerializer(
    AdvanceExpenseSerializerMixin,
    DynamicFieldsModelSerializer
):
    created_by = UserThinSerializer(read_only=True)
    approvals = AdvanceCancelApprovalSerializer(
        read_only=True,
        many=True
    )
    recipient = UserThinSerializer(
        fields=[
            'id', 'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'is_online', 'organization', 'is_current',
        ],
        read_only=True,
        many=True
    )
    class EmployeeApprovalSerializer(serializers.Serializer):
        approval_level = serializers.IntegerField()
        recipient = serializers.PrimaryKeyRelatedField(
            queryset=USER.objects.all()
        )
    selected_approvers = EmployeeApprovalSerializer(
        required=False,
        write_only=True,
        many=True
    )

    class Meta:
        model = AdvanceExpenseCancelHistory
        fields = (
            'id', 'recipient', 'status', 'remarks',
            'created_by', 'approvals', 'selected_approvers',
        )
        read_only_fields = ('id', 'advance_expense', 'created_by')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['advance_expense'] = AdvanceExpenseRequestSerializer(
                fields=[
                    'id', 'title', 'type', 'reason', 'created_at', 'advance_code',
                    'total_amount', 'status', 'detail', 'employee', 'description',
                    'currency', 'remarks', 'add_signature',  'associates',
                    'advance_amount', 'travel_report_mandatory', 'history',
                    'requested_amount', 'documents'
                ],
                context=self.context,
            )
        return fields

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        selected_approvers = validated_data.pop("selected_approvers", None)
        self.set_approvers(AdvanceExpenseCancelRequestApproval, instance, selected_approvers)

        AdvanceExpenseRequestHistory.objects.create(
            request=instance.advance_expense,
            actor=self.request.user,
            action='requested',
            target='cancel expense request',
            remarks=instance.remarks
        )
        organization = instance.advance_expense.employee.detail.organization
        text_type = {
            'Travel': 'Travel Authorization and Advance Cancel Request form'
        }
        text = f"{instance.advance_expense.employee.full_name} has sent " \
               f"{text_type.get(instance.advance_expense.type, 'advance cancel expense request')}."
        add_notification(
            text=text,
            recipient=instance.recipient.all(),
            action=instance,
            actor=instance.advance_expense.employee,
            url='/user/expense-management/request/cancel-advance-request'
        )
        notify_organization(
            text=text,
            action=instance,
            organization=organization,
            actor=instance.advance_expense.employee,
            url=f'/admin/{organization.slug}/expense-management/cancel-request',
            permissions=[
                EXPANSE_APPROVAL_SETTING_PERMISSION,
                ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
            ],
        )
        return instance

    def validate(self, attrs):
        advance_request = self.context.get('advance-expense-request')
        attrs.update({
            'advance_expense': advance_request
        })
        return super().validate(attrs)


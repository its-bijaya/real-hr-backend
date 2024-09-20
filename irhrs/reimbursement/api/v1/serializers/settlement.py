import json

from django.conf import settings
from django_q.tasks import async_task
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, FileExtensionValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from config.settings import TEXT_FIELD_MAX_LENGTH
from irhrs.core.constants.organization import ADVANCE_EXPENSES_SETTLEMENT_EMAIL
from irhrs.core.constants.payroll import APPROVED, DENIED, CANCELED
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, create_dummy_serializer
from irhrs.core.utils import email, nested_getattr
from irhrs.core.utils.common import extract_documents_with_caption
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import EXPANSE_APPROVAL_SETTING_PERMISSION, \
    ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
from irhrs.reimbursement.api.v1.serializers.reimbursement import AdvanceExpenseRequestSerializer, \
    AdvanceExpenseRequestApprovalsSerializer
from irhrs.reimbursement.constants import TRAVEL_EXPENSE_OPTIONS, PER_DIEM, LODGING, TRAVEL, \
    EXPENSE_TYPE, SETTLEMENT_OPTION
from irhrs.reimbursement.models import SettlementOption, ExpenseSettlement, SettlementApproval, \
    SettlementDocuments, SettlementHistory
from irhrs.reimbursement.models.setting import SettlementOptionSetting, ReimbursementSetting
from irhrs.reimbursement.utils.reimbursement import SettlementSerializerMixin
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()

RemarksRequiredSerializer = create_dummy_serializer({'remarks': serializers.CharField(
    max_length=600, allow_blank=False)})


class SettlementDetailSerializer(serializers.Serializer):
    heading = serializers.CharField(max_length=255, required=True)
    particulars = serializers.CharField(max_length=255, required=True)
    quantity = serializers.IntegerField(validators=[MinValueValidator(1)], required=True)
    rate = serializers.FloatField(validators=[MinValueValidator(0)], required=True)
    remarks = serializers.CharField(max_length=TEXT_FIELD_MAX_LENGTH)
    amount = serializers.SerializerMethodField(read_only=True)
    bill_no = serializers.CharField(max_length=255)

    @staticmethod
    def get_amount(obj):
        return obj.get('quantity', 0) * obj.get('rate', 0)


class SettlementDetailForTravelSerializer(serializers.Serializer):
    detail_type = serializers.ChoiceField(choices=TRAVEL_EXPENSE_OPTIONS)
    departure_time = serializers.DateTimeField(allow_null=True, required=False)
    arrival_time = serializers.DateTimeField(allow_null=True, required=False)
    departure_place = serializers.CharField(max_length=255, allow_blank=True, required=False)
    arrival_place = serializers.CharField(max_length=255, allow_blank=True, required=False)
    heading = serializers.CharField(max_length=255, required=False, allow_blank=True)
    date = serializers.DateField(allow_null=True, required=False)
    rate_per_day = serializers.IntegerField(validators=[MinValueValidator(0)], required=True)
    day = serializers.FloatField(validators=[MinValueValidator(0)], required=True)
    description = serializers.CharField(max_length=TEXT_FIELD_MAX_LENGTH, allow_blank=True,
                                        required=False)
    amount = serializers.SerializerMethodField(read_only=True)
    bill_no = serializers.CharField(max_length=255)

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


class SettlementDocumentsSerializer(DynamicFieldsModelSerializer):
    attachment = serializers.FileField(validators=[FileExtensionValidator(
        allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
    )])

    class Meta:
        model = SettlementDocuments
        fields = 'id', 'attachment', 'name',

    def create(self, validated_data):
        validated_data['expense'] = self.context.get('expense')
        return super().create(validated_data)


class SettlementOptionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = SettlementOption
        fields = ['settle_with', 'attachment', 'remark']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            restricted_options = set()
            actual_options = set(dict(SETTLEMENT_OPTION).values())
            fields['settle_with'] = serializers.ChoiceField(
                choices=list(actual_options - restricted_options)
            )

        return fields

    def validate_settle_with(self, settle_with):
        settle_option = SettlementOptionSetting.objects.filter(
            setting__organization=self.context.get('organization'),
            option=settle_with
        )

        if not settle_option.exists():
            raise ValidationError(f'{settle_with.title()} option not available.')
        return settle_with


class SettlementApprovalsSerializer(AdvanceExpenseRequestApprovalsSerializer):
    class Meta(AdvanceExpenseRequestApprovalsSerializer.Meta):
        model = SettlementApproval


class SettlementHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(fields=['id', 'full_name'])

    class Meta:
        model = SettlementHistory
        fields = ['actor', 'action', 'target', 'remarks', 'created_at']


class ExpenseSettlementSerializer(
    SettlementSerializerMixin,
    DynamicFieldsModelSerializer
):
    documents = SettlementDocumentsSerializer(
        many=True,
        read_only=True
    )
    employee = serializers.SerializerMethodField()
    option = SettlementOptionSerializer(required=False)
    detail = SettlementDetailSerializer(
        many=True,
        write_only=True
    )
    approvals = SettlementApprovalsSerializer(
        many=True,
        read_only=True
    )
    history = SettlementHistorySerializer(
        source='histories',
        many=True,
        read_only=True
    )
    recipient = UserThinSerializer(
        fields=[
            'id', 'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'organization', 'is_current', 'is_online'
        ],
        read_only=True,
        many=True
    )
    has_advance_expense = serializers.BooleanField(read_only=True)
    requested_amount = serializers.SerializerMethodField()
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
        model = ExpenseSettlement
        fields = [
            'id', 'reason', 'description', 'type', 'remark', 'created_at', 'total_amount', 'currency',
            'status', 'employee', 'recipient', 'detail', 'documents', 'option', 'advance_expense',
            'approvals', 'history', 'has_advance_expense', 'add_signature', 'travel_report',
            'is_taxable', 'selected_approvers', 'requested_amount'
        ]
        read_only_fields = ['type', 'advance_amount', 'total_amount', 'created_at', 'status']

    def extract_documents_with_caption(self):
        return extract_documents_with_caption(
            self.initial_data,
            file_field='attachment',
            filename_field='name'
        )

    @staticmethod
    def _get_details_serializer(expense_type):
        if expense_type.title() == TRAVEL:
            return SettlementDetailForTravelSerializer
        return SettlementDetailSerializer

    def get_fields(self):
        fields = super().get_fields()
        expense_type = self.context.get('expense_type')
        if self.request and self.request.method.lower() == 'get':
            fields['detail'] = serializers.SerializerMethodField()
            fields['advance_expense'] = AdvanceExpenseRequestSerializer(
                fields=[
                    'id', 'title', 'type', 'reason', 'created_at', 'advance_code',
                    'total_amount', 'status', 'detail', 'employee',
                    'document', 'associates', 'advance_amount', 'travel_report_mandatory', 'requested_amount'
                ],
                context=self.context
            )
        if self.request and self.request.method.lower() == 'post':
            fields['detail'] = self._get_details_serializer(expense_type)(
                many=True,
                write_only=True
            )
        return fields

    def get_detail(self, obj):
        detail = json.loads(obj.detail)
        expense_type = self.context.get('expense_type')
        return self._get_details_serializer(expense_type)(
            detail,
            many=True
        ).data
    
    def get_requested_amount(self, instance):
        return nested_getattr(instance,'advance_expense.requested_amount')

    def create(self, validated_data):
        documents = validated_data.pop('documents',[])
        detail = validated_data.pop('detail')
        option = validated_data.pop('option', None)

        validated_data['employee'] = self.request.user

        from irhrs.reimbursement.utils.helper import convert_to_iso_format
        validated_data['detail'] = json.dumps(detail, default=convert_to_iso_format)

        validated_data['type'] = self.context.get('expense_type')

        selected_approvers = validated_data.pop("selected_approvers", None)
        instance = super().create(validated_data)

        for document in documents:
            SettlementDocuments.objects.create(settle=instance, **document)

        self.set_approvers(SettlementApproval, instance, selected_approvers)

        if option:
            SettlementOption.objects.create(settle=instance, **option)

        SettlementHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action='requested',
            remarks=instance.remark
        )
        add_notification(
            text=f"{instance.employee.full_name} has sent {instance.type} Expense Report.",
            recipient=instance.recipient.all(),
            action=instance,
            actor=instance.employee,
            url='/user/expense-management/request/settlement'
        )

        organization = instance.employee.detail.organization
        notify_organization(
            text=f"{instance.employee.full_name} has sent {instance.type} Expense Report.",
            action=instance,
            organization=organization,
            actor=instance.employee,
            url=f'/admin/{organization.slug}/expense-management/settle-request',
            permissions=[
                EXPANSE_APPROVAL_SETTING_PERMISSION,
                ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
            ],
        )
        # Send email when user request for settlement of advance expenses requested
        subject = f"{instance.created_by} has requested for settlement of Advance Expenses"
        email_text=(
            f"{instance.created_by} has requested expense settlement for {instance.reason}."
        )
        async_task(
            send_email_as_per_settings,
            instance.recipient.all(),
            subject,
            email_text,
            ADVANCE_EXPENSES_SETTLEMENT_EMAIL
        )
        return instance

    def validate(self, attrs):
        from irhrs.reimbursement.utils.helper import calculate_total, calculate_advance_amount
        expense_type = self.context.get('expense_type')
        organization = self.context['organization']
        reimbursement_setting = ReimbursementSetting.objects.filter(
            organization=organization
        ).first()
        if reimbursement_setting and reimbursement_setting.travel_report_mandatory:
            if self.context.get("expense_type") == TRAVEL and not attrs.get('travel_report'):
                raise ValidationError({'travel_report': ['Travel report file is required.']})
        if expense_type not in dict(EXPENSE_TYPE):
            raise ValidationError(
                {
                    'non_field_errors': [
                        f'\'expense_type\' can be {",".join(dict(EXPENSE_TYPE))}'
                    ]
                }
            )
        selectable_approver_exists = organization.settlement_setting.filter(select_employee=True).exists()
        if selectable_approver_exists and 'selected_approvers' not in attrs.keys():
            raise ValidationError({"selected_approvers": "Approvers field required."})

        documents = self.extract_documents_with_caption()
        serializer = SettlementDocumentsSerializer(data=documents, many=True)
        serializer.is_valid(raise_exception=True)
        attrs['documents'] = documents

        expense = attrs.get('advance_expense')
        option = attrs.get('option')
        detail = attrs.get('detail')

        settlement_total = calculate_total(detail, expense_type)

        if expense and expense.advance_amount > settlement_total and not option:
            raise ValidationError({'detail': ['You must provide option for settlement.']})

        if expense and self.request.user != expense.employee:
            raise ValidationError({
                'advance_expense': ['You can\'t request settlement for other\'s Travel'
                                    ' Authorization and Advance Request Form.']
            })

        if expense and expense.total_amount < settlement_total:
            attrs['option'] = None

        attrs['total_amount'] = settlement_total
        attrs['advance_amount'] = calculate_advance_amount(
            detail, expense_type, organization=self.context['organization']
        )
        return super().validate(attrs)

    @staticmethod
    def validate_advance_expense(expense):
        settlement = expense.settlement.exclude(status__in=[DENIED, CANCELED]).first()
        if settlement:
            raise ValidationError(
                'Settlement for this Travel Authorization and Advance Request Form'
                f' has been {settlement.status}.'
            )

        if expense and not expense.status == APPROVED:
            raise ValidationError(
                'Travel Authorization and Advance Request Form'
                ' has not been approved.'
            )
        return expense

    @staticmethod
    def validate_detail(detail):
        if not detail:
            raise ValidationError(
                'There must be at least one detail associated with this request.'
            )
        return detail

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from irhrs.core.constants.organization import ADVANCE_SALARY_IS_REQUESTED_BY_USER

from irhrs.core.constants.payroll import CANCELED, CASH, CHEQUE
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import extract_documents, DummyObject
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.email import send_email_as_per_settings, send_notification_email
from irhrs.core.validators import validate_past_date_or_today
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.payroll.models import SUPERVISOR
from irhrs.payroll.models.advance_salary_request import AdvanceSalaryRequest, \
    AdvanceSalaryRequestDocument, AdvanceSalaryRequestApproval, PENDING, DENIED, \
    AdvanceSalaryRequestHistory, AdvanceSalaryRepayment, AdvanceSalarySurplusRequest
from irhrs.payroll.utils.advance_salary import AdvanceSalaryRequestValidator
from irhrs.permission.constants.permissions import ADVANCE_SALARY_GENERATE_PERMISSION
from irhrs.users.api.v1.serializers.legal_info import UserLegalInfoSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer, \
    UserThinSerializer
from irhrs.users.api.v1.serializers.user_bank import UserBankSerializer


class AdvanceSalaryRepaymentSerializer(DynamicFieldsModelSerializer):
    payroll_reference = serializers.SerializerMethodField()

    class Meta:
        model = AdvanceSalaryRepayment
        fields = ('id', 'amount', 'order', 'paid', 'paid_on', 'payment_type', 'payroll_reference',
                  'remarks', 'attachment')

    @staticmethod
    def get_payroll_reference(obj):
        if not obj.paid:
            return None
        return obj.payroll_reference.payroll.id if obj.payroll_reference else None


class AdvanceSalaryRequestApprovalSerializer(DynamicFieldsModelSerializer):
    user = UserThumbnailSerializer()

    class Meta:
        model = AdvanceSalaryRequestApproval
        fields = ("id", "user", "status", "role", "level")


class AdvanceSalaryRequestHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThumbnailSerializer()
    log = serializers.ReadOnlyField(source='__str__', allow_null=True)

    class Meta:
        model = AdvanceSalaryRequestHistory
        fields = ("id", "actor", "created_at", "log")


class AdvanceSalaryRequestDocumentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AdvanceSalaryRequestDocument
        fields = ('id', 'attachment', 'name')


class AdvanceSalaryRequestSerializer(DynamicFieldsModelSerializer):

    documents = AdvanceSalaryRequestDocumentSerializer(many=True, read_only=True)
    disbursement_count_for_repayment = serializers.IntegerField(min_value=1)
    surplus_request = serializers.PrimaryKeyRelatedField(
        queryset=AdvanceSalarySurplusRequest.objects.all(),
        allow_null=True,
        required=False,
        write_only=True
    )

    class Meta:
        model = AdvanceSalaryRequest
        fields = [
            "id",
            "amount",
            "requested_for",
            "reason_for_request",
            "disbursement_count_for_repayment",
            "repayment_plan",
            "above_limit",
            "documents",
            "surplus_request"
        ]

    def extract_documents(self):
        return extract_documents(
            self.initial_data,
            file_field='attachment',
            filename_field='name'
        )

    def validate(self, attrs):
        advance_salary = AdvanceSalaryRequestValidator(
            employee=self.request.user,
            amount=attrs.get('amount'),
            disbursement_count_for_repayment=attrs.get('disbursement_count_for_repayment'),
            requested_for=attrs.get('requested_for'),
            above_limit=attrs.get('above_limit'),
            repayment_plan=attrs.get('repayment_plan'),
            surplus_request=attrs.get('surplus_request')
        )
        advance_salary.is_valid()

        if self.request.method.upper() == 'POST':
            # only accept documents in create
            documents = self.extract_documents()
            serializer = AdvanceSalaryRequestDocumentSerializer(data=documents, many=True)
            serializer.is_valid(raise_exception=True)
            attrs['documents'] = documents

            # only need to set these in post
            attrs['employee'] = advance_salary.employee
            attrs['approvals'] = advance_salary.approvals
            attrs['recipient'] = advance_salary.recipient

        return attrs

    def create(self, validated_data):
        documents = validated_data.pop('documents', None)
        approvals = validated_data.pop('approvals', [])
        surplus_request = validated_data.pop('surplus_request', None)
        instance = super().create(validated_data)

        if documents:
            for document_data in documents:
                AdvanceSalaryRequestDocument.objects.create(request=instance, **document_data)

        for approval in approvals:
            AdvanceSalaryRequestApproval.objects.create(request=instance, **approval)
        AdvanceSalaryRequestHistory.objects.create(
            request=instance,
            actor=instance.employee,
            action="requested",
            remarks=instance.reason_for_request
        )
        active_approval = approvals[0]
        requestor_fullname=instance.employee.full_name
        recipients=[]
        user=active_approval.get('user')
        if user:
            recipient=recipients.append(user.email)
        if active_approval['role'] == SUPERVISOR:
            add_notification(
                text=f"{requestor_fullname} sent advance salary request.",
                recipient=instance.recipient,
                action=instance,
                actor=instance.employee,
                url='/user/supervisor/payroll/advance-salary-request'
            )
            send_email_as_per_settings(
                recipients=user,
                subject="Advance Salary Request",
                email_text=f"{requestor_fullname} sent advance salary request.",
                email_type=ADVANCE_SALARY_IS_REQUESTED_BY_USER 
            )
        else:
            add_notification(
                text=f"{requestor_fullname} sent advance salary request.",
                recipient=instance.recipient,
                action=instance,
                actor=instance.employee,
                url='/user/payroll/advance-salary/request/list'
            )
            send_email_as_per_settings(
            recipients=user,
            subject="Advance Salary Request",
            email_text=f"{requestor_fullname} sent advance salary request.",
            email_type=ADVANCE_SALARY_IS_REQUESTED_BY_USER 
            )
        if surplus_request:
            surplus_request.advance_salary_request = instance
            surplus_request.save()

        return instance


class AdvanceSalaryRequestListSerializer(AdvanceSalaryRequestSerializer):
    employee = UserThinSerializer(fields=[
        'id', 'organization', 'full_name', 'profile_picture', 'cover_picture',
        'organization', 'is_current','job_title', 'is_online', 'last_online'])
    recipient = UserThumbnailSerializer()
    request_type = serializers.SerializerMethodField()
    amount_paid = serializers.SerializerMethodField()
    amount_to_be_paid = serializers.SerializerMethodField()

    class Meta(AdvanceSalaryRequestSerializer.Meta):
        fields = [
            'id',
            'employee',
            'amount',
            'requested_for',
            'created_at',
            'modified_at',
            'request_type',
            'amount_paid',
            'amount_to_be_paid',
            'status',
            'recipient'
        ]

    @staticmethod
    def get_request_type(obj):
        return ["Normal", "Surplus"][obj.above_limit]

    @staticmethod
    def get_amount_paid(obj):
        return None if (obj.status in [PENDING, DENIED, CANCELED]) else obj.paid_amount

    @staticmethod
    def get_amount_to_be_paid(obj):
        return None if (obj.status in [PENDING, DENIED, CANCELED]) else (
            obj.amount - (obj.paid_amount or 0))


class AdvanceSalaryRequestDetailSerializer(AdvanceSalaryRequestListSerializer):
    approvals = AdvanceSalaryRequestApprovalSerializer(many=True)
    log = AdvanceSalaryRequestHistorySerializer(source='histories', many=True)
    repayments = AdvanceSalaryRepaymentSerializer(many=True)

    class Meta(AdvanceSalaryRequestSerializer.Meta):
        fields = [
            'id',
            'employee',
            'amount',
            'requested_for',
            'created_at',
            'modified_at',
            'request_type',
            'status',
            'recipient',
            'disbursement_count_for_repayment',
            'repayment_plan',
            'repayments',
            'documents',
            'reason_for_request',
            'approvals',
            'log'
        ]


class AdvanceSalaryPayslipSerializer(DynamicFieldsModelSerializer):
    employee = UserThinSerializer(fields=[
        'id', 'organization', 'full_name', 'division', 'profile_picture', 'cover_picture',
        'organization', 'is_current', 'job_title', 'is_online', 'last_online'])
    legal_info = UserLegalInfoSerializer(source='employee.legal_info',
                                         fields=['pan_number', 'pf_number', 'cit_number'])

    class Meta:
        model = AdvanceSalaryRequest
        fields = (
            "id",
            "employee",
            "requested_for",
            "amount",
            "legal_info",
        )

    def get_fields(self):
        fields = super().get_fields()

        fields['bank'] = UserBankSerializer(
            source='employee.userbank',
            exclude_fields=['user'],
            context=self.context
        )

        return fields


class AdvanceSalarySettlementSerializer(DummySerializer):
    remarks = serializers.CharField(max_length=600, write_only=True)
    attachment = serializers.FileField(validators=[FileExtensionValidator(
        allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)], required=True, write_only=True)
    payment_type = serializers.ChoiceField(choices=[(CASH, "Cash"), (CHEQUE, "Cheque")],
                                           write_only=True)
    paid_on = serializers.DateField(validators=[validate_past_date_or_today], write_only=True)
    message = serializers.ReadOnlyField(default='Successfully settled selected repayments.')
    repayments = serializers.PrimaryKeyRelatedField(
        queryset=AdvanceSalaryRepayment.objects.filter(
            paid=False,
        ),
        many=True,
        write_only=True,
        allow_null=False,
        allow_empty=False
    )

    def validate_paid_on(self, paid_on):

        approved_date = self.advance_salary_request.payslip_generation_date

        if approved_date and paid_on and paid_on < approved_date:
            raise serializers.ValidationError(_("Please ensure this date is "
                                                "after payslip generated"
                                                f" date {approved_date}"))
        return paid_on

    @property
    def request(self):
        return self.context['request']

    def validate_repayments(self, repayments):
        if any(filter(lambda r: r.request != self.advance_salary_request, repayments)):
            raise serializers.ValidationError(
                {'repayments': _("Invalid repayment id for this request.")})
        return repayments

    @property
    def advance_salary_request(self):
        return self.context['view'].advance_salary_request

    def validate(self, attrs):
        advance_salary_request = self.advance_salary_request

        unpaid = list(
            advance_salary_request.repayments.filter(paid=False).order_by('order')
        )
        requested_ids = list(attrs['repayments'])
        for repayment in unpaid:
            if requested_ids:
                try:
                    requested_ids.remove(repayment)
                except ValueError:
                    # raise
                    raise serializers.ValidationError({
                        "non_field_errors": ["Can not skip a repayment."]
                    })
        return attrs

    @transaction.atomic()
    def create(self, validated_data):
        repayments = validated_data['repayments']
        attachment = validated_data['attachment']
        payment_type = validated_data['payment_type']
        paid_on = validated_data['paid_on']
        remarks = validated_data['remarks']

        repayment_orders = []
        for repayment in repayments:
            repayment.paid = True
            repayment.paid_on = paid_on
            repayment.attachment = attachment
            repayment.payment_type = payment_type
            repayment.remarks = remarks
            repayment.save()
            repayment_orders.append(str(repayment.order))

        if repayment_orders:
            AdvanceSalaryRequestHistory.objects.create(
                request=self.advance_salary_request,
                actor=self.request.user,
                action="settled",
                target=f"repayments {','.join(repayment_orders)}",
                remarks=remarks
            )

        return DummyObject()


class AdvanceSalarySurplusRequestSerializer(DynamicFieldsModelSerializer):
    employee = UserThinSerializer(fields=[
        'id', 'organization', 'full_name', 'profile_picture', 'cover_picture',
        'organization', 'is_current', 'job_title', 'is_online', 'last_online'], read_only=True)
    acted_by = UserThumbnailSerializer(allow_null=True, read_only=True)
    advance_salary_request = AdvanceSalaryRequestSerializer(
        fields=["id", "amount", "requested_for"],
        read_only=True
    )

    class Meta:
        model = AdvanceSalarySurplusRequest
        fields = ("id", "employee", "amount", "limit_amount", "reason_for_request", "status",
                  "created_at", "advance_salary_request", "acted_by", "acted_on", "action_remarks",
                  )
        read_only_fields = ('employee', 'status', 'advance_salary_request', 'acted_by', 'acted_on',
                            'action_remarks', "limit_amount")

    def validate(self, attrs):
        amount = attrs.get('amount')
        advance_salary = AdvanceSalaryRequestValidator(employee=self.request.user)
        if advance_salary.limit_amount and amount and amount <= advance_salary.limit_amount:
            raise serializers.ValidationError(
                {'amount': _("The amount is under the limit.")})

        attrs["limit_amount"] = advance_salary.limit_amount
        return attrs

    def create(self, validated_data):
        validated_data['employee'] = self.request.user
        instance = super().create(validated_data)
        org = instance.employee.detail.organization
        notify_organization(
            text=f"{instance.employee.full_name} sent above limit request for advance salary.",
            action=instance,
            actor=instance.employee,
            organization=org,
            permissions=[
                ADVANCE_SALARY_GENERATE_PERMISSION
            ],
            url=f"/admin/{org.slug}/payroll/advance-salary?tab=surplus"
        )

        return instance

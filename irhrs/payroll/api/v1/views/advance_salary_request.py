from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from irhrs.core.constants.organization import ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL, ADVANCE_SALARY_IS_REQUESTED_BY_USER, GENERATE_ADVANCE_SALARY_BY_HR

from irhrs.core.constants.payroll import SUPERVISOR, EMPLOYEE, APPROVED, REPAYMENT, CANCELED
from irhrs.core.mixins.serializers import DummySerializer, create_dummy_serializer
from irhrs.core.mixins.viewset_mixins import OrganizationCommonsMixin, OrganizationMixin, \
    ListCreateRetrieveViewSetMixin
from irhrs.core.utils.common import validate_permissions, get_today
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.email import send_email_as_per_settings, send_notification_email
from irhrs.core.utils.filters import OrderingFilterMap
from irhrs.notification.utils import notify_organization, add_notification
from irhrs.payroll.api.permissions import AdvanceSalaryRequestObjectPermission
from irhrs.payroll.api.v1.serializers.advance_salary_request import AdvanceSalaryRequestSerializer, \
    AdvanceSalaryRequestListSerializer, AdvanceSalaryRequestDetailSerializer, \
    AdvanceSalaryPayslipSerializer, AdvanceSalarySettlementSerializer, \
    AdvanceSalarySurplusRequestSerializer
from irhrs.payroll.models.advance_salary_request import AdvanceSalaryRequest
from irhrs.payroll.models.advance_salary_request import PENDING, DENIED, COMPLETED, \
    AdvanceSalaryRequestHistory, REQUESTED, AdvanceSalaryRepayment, AdvanceSalarySurplusRequest
from irhrs.payroll.utils.advance_salary import AdvanceSalaryRequestValidator
from irhrs.permission.constants.permissions import HAS_PERMISSION_FROM_METHOD, \
    ADVANCE_SALARY_GENERATE_PERMISSION
from irhrs.permission.permission_classes import permission_factory

RemarksRequiredSerializer = create_dummy_serializer({'remarks': serializers.CharField(
    max_length=600, allow_blank=False)})


class AdvanceSalaryRequestViewSet(OrganizationCommonsMixin, OrganizationMixin,
                                  ListCreateRetrieveViewSetMixin):
    """

    #### modes ==> hr, user, supervisor, approver
    #### `?as=hr` for view as hr
    #### `?as=user` for view as normal user(default)
    #### `?as=approver` if employee is assigned to approve
    #### `?as=supervisor` if supervisor is assigned to approve
    create:

    Send advance salary request

        {
            "amount": 3000,
            "requested_for": "2017-01-01",
            "reason_for_request": "I need it",
            "disbursement_count_for_repayment": 3,
            "repayment_plan": [1000, 1000, 1000],
            "above_limit": false,
            "document_1": file1,
            "document_2": file2,
        }

    info:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/info/`
    Info needed for advance salary request form

    cancel:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/{pk}/cancel/`
    Cancel advance salary request.

    deny:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/{pk}/deny/`
    Deny advance salary request.

    Sample post data ->

            {
                "remarks": "Your Remarks"
            }

    approve:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/{pk}/deny/`
    Approve advance salary request.

    Sample post data ->

            {
                "remarks": "Your Remarks"
            }

    pay_slip:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/{pk}/pay-slip/`
    Payslip of advance salary request.

    generate:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/{pk}/generate/`
    Generate Payslip of advance salary request and send to user.

    settle_repayment:
    #### URL -> `api/v1/payroll/{org-slug}/advance-salary/requests/{pk}/settle-repayment/`
    Settle repayment of advance salary

    Sample post data ->

        {
            "remarks": "Your Remarks",
            "attachment": File to support settlement,
            "payment_type": "Cash" / "Cheque",
            "paid_on": Date of payment,
            "repayments": [list of repayment_ids]
        }

    """
    serializer_class = AdvanceSalaryRequestSerializer
    queryset = AdvanceSalaryRequest.objects.all().select_related(
        'employee',
        'employee__detail',
        'employee__detail__organization',
        'employee__detail__job_title',
        'recipient',
        'recipient__detail',
        'recipient__detail__job_title',
    )
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilterMap)

    filter_fields = ('employee', 'status')
    search_fields = (
        'employee__first_name',
        'employee__middle_name',
        'employee__last_name',
    )
    ordering_fields_map = {
        'full_name': (
            'employee__first_name',
            'employee__middle_name',
            'employee__last_name',
        ),
        'amount': 'amount',
        'requested_for': 'requested_for',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }

    permission_classes = [
        permission_factory.build_permission(
            "AdvanceSalaryRequestPermission",
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        ),
        AdvanceSalaryRequestObjectPermission
    ]

    advance_salary_request = None

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['user', 'hr', 'approver', 'supervisor']:
            return 'user'
        return mode

    @staticmethod
    def create_repayments(instance):
        repayments = list()
        for index, repayment_amount in enumerate(instance.repayment_plan, start=1):
            repayments.append(
                AdvanceSalaryRepayment(
                    request=instance,
                    amount=float(repayment_amount),
                    order=index
                )
            )
        AdvanceSalaryRepayment.objects.bulk_create(repayments)

    def has_user_permission(self):
        if self.mode == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                ADVANCE_SALARY_GENERATE_PERMISSION
            )
        elif self.mode == 'user':
            return self.request.user.detail.organization == self.organization

        # other modes are filtered by queryset and objects level actions are handled by object
        # permission
        return True

    def get_serializer_class(self):
        if self.action == 'list':
            return AdvanceSalaryRequestListSerializer
        elif self.action == 'retrieve':
            return AdvanceSalaryRequestDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        base_qs = self.queryset.filter(employee__detail__organization=self.organization)
        if self.mode == 'hr':
            return base_qs
        elif self.mode == 'supervisor':
            return self.queryset.filter(approvals__user=self.request.user, approvals__role=SUPERVISOR)
        elif self.mode == 'approver':
            # this api is requested as normal user, so send all requests to the user
            return self.queryset.filter(
                approvals__user=self.request.user,
                approvals__role__in=[EMPLOYEE, SUPERVISOR]
            ).distinct()
        else:
            return base_qs.filter(employee=self.request.user)

    def get_counts(self):
        queryset = self.get_queryset()
        status_list = [REQUESTED, APPROVED, REPAYMENT, DENIED, COMPLETED, CANCELED]

        agg = self.aggregate_status(queryset, status_list)

        return agg

    @staticmethod
    def aggregate_status(queryset, status_list):
        all_count = queryset.count()
        agg_kwarg = {
            status: Count('id', filter=Q(status=status), distinct=True)
            for status in status_list
        }
        agg = queryset.aggregate(**agg_kwarg)
        agg.update({'All': all_count})
        return agg

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({'counts': self.get_counts()})
        return response

    def get_surplus_request(self, surplus_request_id):
        try:
            surplus_request_id = int(surplus_request_id)
        except (ValueError, TypeError):
            return None
        return AdvanceSalarySurplusRequest.objects.filter(
            id=surplus_request_id, employee=self.request.user,
            status=APPROVED
        ).first()

    @action(detail=False, methods=['GET'])
    def info(self, request, **kwargs):

        surplus_request_id = request.query_params.get('surplus_request')
        surplus = self.get_surplus_request(surplus_request_id)

        advance_salary = AdvanceSalaryRequestValidator(employee=request.user,
                                                       surplus_request=surplus,
                                                       above_limit=bool(surplus))

        return_dict = {
            'limit_amount': advance_salary.limit_amount,
            'disbursement_limit_for_repayment':
                advance_salary.settings.disbursement_limit_for_repayment,
            'salary_payable': advance_salary.salary_payable,
        }

        return Response(return_dict)

    @action(detail=True, methods=['POST'], serializer_class=DummySerializer)
    def cancel(self, request, **kwargs):
        instance = self.get_object()

        instance.status = CANCELED
        instance.save()

        AdvanceSalaryRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action="canceled",
            target="the request"
        )

        return Response({"detail": "Successfully canceled request."})

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def approve(self, request, **kwargs):
        """
        Approve Advance Salary Requests
        """
        instance = self.get_object()

        approval = instance.active_approval
        if not approval:
            raise serializers.ValidationError({
                'non_field_errors': _("Couldn't not approve this request.")
            })

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks')

        with transaction.atomic():
            approval.status = APPROVED
            approval.save()

            AdvanceSalaryRequestHistory.objects.create(
                request=instance,
                actor=self.request.user,
                action="approved",
                remarks=remarks
            )
            next_approval = instance.approvals.filter(status=PENDING).order_by('level').first()
            if next_approval:
                instance.recipient = next_approval.user
                instance.save()
                send_email_as_per_settings(
                        recipients=next_approval.user,
                        subject="Advance Salary Request",
                        email_text=f"{instance.employee.full_name} sent advance salary request.",
                        email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
                    )

                notification_text = "{user} advance salary request has been approved by " \
                                    "{approved_by} and has been sent to {next_approver} for" \
                                    " further approval."
                next_approver_name = instance.recipient.full_name

            else:
                instance.status = APPROVED
                instance.save()
                next_approver_name = None
                notification_text = "{user} advance salary request has been approved by " \
                                    "{approved_by} and awaits generation."

            approved_by_name = request.user.full_name
            hr_notification_text = notification_text.format(
                user=instance.employee.full_name,
                approved_by=approved_by_name,
                next_approver=next_approver_name
            )
            organization = instance.employee.detail.organization
            notify_organization(
                text=hr_notification_text,
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=[ADVANCE_SALARY_GENERATE_PERMISSION],
                url=f'/admin/{organization.slug}/payroll/advance-salary'
            )

            hrs=get_users_list_from_permissions(
                permission_list=[ADVANCE_SALARY_GENERATE_PERMISSION],
                organization=instance.employee.detail.organization
            )
            send_email_as_per_settings(
            recipients=hrs,
            subject="Advance Salary Request Status",
            email_text=hr_notification_text,
            email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
            )

            employee_notification_text = notification_text.format(
                user="Your",
                approved_by=approved_by_name,
                next_approver=next_approver_name
            )
            recipients=instance.employee
            add_notification(
                text=employee_notification_text,
                recipient=recipients,
                action=instance,
                actor=request.user,
                url='/user/payroll/advance-salary'
            )
            send_email_as_per_settings(
                        recipients=recipients,
                        subject="Advance Salary Request Status",
                        email_text=employee_notification_text,
                        email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
                    )

            if next_approver_name:
                if next_approval.role == SUPERVISOR:
                    add_notification(
                        text=f"{instance.employee.full_name} sent advance salary request.",
                        recipient=instance.recipient,
                        action=instance,
                        actor=instance.employee,
                        url='/user/supervisor/payroll/advance-salary-request'
                    )
                    send_email_as_per_settings(
                        recipients=recipients,
                        subject="Advance Salary Request Status",
                        email_text=employee_notification_text,
                        email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
                        )
                else:
                    add_notification(
                        text=f"{instance.employee.full_name} sent advance salary request.",
                        recipient=instance.recipient,
                        action=instance,
                        actor=instance.employee,
                        url='/user/payroll/advance-salary/request/list'
                    )
        return Response({'message': _("Approved Request.")})

    @transaction.atomic()
    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def deny(self, request, **kwargs):
        """
        Deny Advance Salary Requests
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        remarks = serializer.validated_data.get('remarks')

        if not self.mode == 'hr':

            approval = instance.active_approval
            if not approval:
                raise serializers.ValidationError({
                    'non_field_errors': _("Couldn't not deny this request.")
                })

            approval.status = DENIED
            approval.save()

        AdvanceSalaryRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action="denied",
            remarks=remarks
        )

        instance.status = DENIED
        instance.save()

        deny_notification_text = f"{request.user.full_name} declined " \
                                 f"{instance.employee.full_name}'s advance salary request."
        user_notification_text = f"{request.user.full_name} declined " \
                                 f"your advance salary request."

        organization = instance.employee.detail.organization
        notify_organization(
            text=deny_notification_text,
            organization=organization,
            action=instance,
            actor=request.user,
            permissions=[ADVANCE_SALARY_GENERATE_PERMISSION],
            url=f'/admin/{organization.slug}/payroll/advance-salary'
        )
        hrs=get_users_list_from_permissions(
            permission_list=[ADVANCE_SALARY_GENERATE_PERMISSION],
            organization=instance.employee.detail.organization
        )
        send_email_as_per_settings(
            recipients=hrs,
            subject="Advance Salary Request Status",
            email_text=deny_notification_text,
            email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
        )
        recipients=instance.employee
        for approved_approvals in instance.approvals.filter(status=APPROVED):
            add_notification(
                text=deny_notification_text,
                recipient=approved_approvals.user,
                action=instance,
                actor=request.user,
                # url = ADD URL AFTER FE
            )
            send_email_as_per_settings(
                recipients=recipients,
                subject="Advance Salary Request Status",
                email_text=user_notification_text,
                email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
            )
        add_notification(
            text=user_notification_text,
            recipient=recipients,
            action=instance,
            actor=request.user,
            url="/user/payroll/advance-salary"
        )
        send_email_as_per_settings(
            recipients=recipients,
            subject="Advance Salary Request Status",
            email_text=user_notification_text,
            email_type=ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL
        )

        return Response({'message': _("Declined Request.")})

    @action(detail=True, methods=['GET'],
            serializer_class=AdvanceSalaryPayslipSerializer,
            url_path='pay-slip')
    def pay_slip(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @transaction.atomic()
    @action(detail=True, methods=['POST'],
            serializer_class=DummySerializer)
    def generate(self, request, **kwargs):

        instance = self.get_object()
        instance.status = REPAYMENT
        instance.payslip_generation_date = get_today()
        instance.save()

        self.create_repayments(instance)

        AdvanceSalaryRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action="generated payslip",
        )

        generation_notification_text_user = (
            "Payslip has been generated for your advance salary request."
        )
        recipients=instance.employee
        add_notification(
            text=generation_notification_text_user,
            recipient=recipients,
            action=instance,
            actor=request.user,
            url="/user/payroll/advance-salary"
        )
        send_email_as_per_settings(
            recipients=recipients,
            subject="Advance Salary Generated",
            email_text=generation_notification_text_user,
            email_type=GENERATE_ADVANCE_SALARY_BY_HR
        )

        return Response({'message': _("Payslip generated and sent to user.")})

    @action(detail=True, methods=['POST'],
            serializer_class=AdvanceSalarySettlementSerializer,
            url_path='settle-repayment')
    def settle_repayment(self, request, **kwargs):
        self.advance_salary_request = self.get_object()
        return super().create(request, **kwargs)


class AdvanceSalarySurplusRequestViewSet(OrganizationCommonsMixin, OrganizationMixin,
                                         ListCreateRetrieveViewSetMixin):
    serializer_class = AdvanceSalarySurplusRequestSerializer
    queryset = AdvanceSalarySurplusRequest.objects.all().select_related(
        'employee',
        'employee__detail',
        'employee__detail__organization',
        'employee__detail__job_title',
        'acted_by',
        'acted_by__detail',
        'acted_by__detail__job_title',
    )

    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilterMap)

    filter_fields = ('employee', 'status')
    search_fields = (
        'employee__first_name',
        'employee__middle_name',
        'employee__last_name',
    )
    ordering_fields_map = {
        'full_name': (
            'employee__first_name',
            'employee__middle_name',
            'employee__last_name',
        ),
        'amount': 'amount',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }

    permission_classes = [
        permission_factory.build_permission(
            "AdvanceSalarySurplusRequestPermission",
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        )
    ]

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['user', 'hr']:
            return 'user'
        return mode

    def has_user_permission(self):
        if self.mode == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                ADVANCE_SALARY_GENERATE_PERMISSION
            )
        elif self.mode == 'user' and self.action in ['list', 'create', 'retrieve']:
            return self.request.user.detail.organization == self.organization

        return False

    def get_queryset(self):
        base_qs = self.queryset.filter(employee__detail__organization=self.organization)
        if self.mode == 'hr':
            return base_qs
        else:
            return base_qs.filter(employee=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({'counts': AdvanceSalaryRequestViewSet.aggregate_status(
            self.get_queryset(), [REQUESTED, APPROVED, DENIED]
        )})
        return response

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def approve(self, request, **kwargs):
        """
        Approve Advance Salary Surplus Requests
        """
        self.update_status(APPROVED)
        return Response({'message': _("Approved Request.")})

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def deny(self, request, **kwargs):
        """
        Deny Advance Salary Requests
        """
        self.update_status(DENIED)

        return Response({'message': _("Declined Request.")})

    def update_status(self, status):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()

        if not instance.status == REQUESTED:
            self.permission_denied(self.request, "Already acted")

        remarks = serializer.validated_data.get('remarks')

        instance.status = status
        instance.acted_by = self.request.user
        instance.acted_on = timezone.now()
        instance.action_remarks = remarks
        instance.save()

        add_notification(
            text=f"{instance.acted_by.full_name} {status} your above limit advance salary "
                 "request.",
            action=instance,
            actor=instance.acted_by,
            recipient=instance.employee,
            url="/user/payroll/advance-salary?tab=surplus"
        )
        print(f"notification sent to {instance.employee.full_name}")

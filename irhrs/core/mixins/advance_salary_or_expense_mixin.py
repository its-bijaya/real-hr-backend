from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from irhrs.core.constants.payroll import DENIED, APPROVED, PENDING, CANCELED
from irhrs.core.mixins.serializers import create_dummy_serializer
from irhrs.core.utils import nested_getattr
from irhrs.notification.utils import add_notification, notify_organization

RemarksRequiredSerializer = create_dummy_serializer({
    'remarks': serializers.CharField(max_length=600, allow_blank=False),
    'add_signature': serializers.BooleanField(required=False)
})


class BaseForRequestMixin:
    permission_for_hr = None
    history_model = None
    notification_url_for_organization = ""
    notification_url_for_user = ""
    notification_url_for_approver = ""

    def get_type(self, *args, **kwargs):
        return f"{getattr(self, 'notification_for', 'advance expense')} request"

    def get_notification_text(self, action_, next_approver):
        """
        returns string
        """
        notification_text = "{user} " + self.get_type() + " has been {action} by " \
                                                          "{approved_by}"
        notification_text += '.' if action_ == DENIED or not next_approver else \
            f" and has been sent for further approval."
        return notification_text

    def get_user_notification_text(self, user, approved_by, action_, next_approver=None):
        notification_text = self.get_notification_text(action_, next_approver)
        return notification_text.format(
            user=user,
            approved_by=approved_by.full_name,
            action=action_.lower()
        )

    def get_permission_for_org_notification(self):
        assert self.permission_for_hr, 'Must define permission_for_notification variable'
        return self.permission_for_hr

    def get_organization_text(self, employee):
        return f"Approval for {self.get_type().title()} " \
               f"requested by {employee.full_name} has been completed and" \
               f" awaits for the confirmation."

    def get_history_model(self):
        assert self.history_model, 'Must specify history model before using this mixin'
        return self.history_model

    def generate_history(self, instance, **kwargs):
        history_model = self.get_history_model()
        user = kwargs.pop('user', self.request.user)
        if user and not isinstance(user, int):
            user = user.id
        history_model.objects.create(
            request=instance,
            actor_id=user,
            **kwargs
        )

    def get_notification_url_for_organization(self, organization=None):
        return getattr(self, 'notification_url_for_organization')

    def get_notification_url_for_user(self, user=None):
        return getattr(self, 'notification_url_for_user')

    def get_notification_url_for_approver(self, user=None):
        return getattr(self, 'notification_url_for_approver')


class ApproveDenyCancelViewSetMixin(BaseForRequestMixin):
    """
    This mixin is used to perform approve, deny and forward action for requesting
    advance salary and expense.

    To implement this mixin we need to perform following:
    1. Override get_permission_for_notification method
    2. Set history_model attribute or override get_history_model() method
        -> history_model = AdvanceExpenseRequestHistory
    3. Set notification_for attribute
        -> notification_for = 'salary' or 'expense'
    4. Set notification_url_for_organization or override
       get_notification_url_for_organization method
       -> notification_url_for_organization = '/admin/{org.slug}/expense-management/request'
    5. Set notification_url_for_user or override
       get_notification_url_for_user method
       -> notification_url_for_user = '/admin/expense-management/request'
    6. Set notification_url_for_approver or override
       get_notification_url_for_approver method
       -> notification_url_for_approver = '/admin/expense-management/request'
    7. Override post_approve, post_deny and post_cancel for performing
       actions that should be done after request is approved, cancelled or denied.
    """
    send_hr_notification = False

    def post_approve(self, *args, **kwargs):
        pass

    def post_cancel(self, *args, **kwargs):
        pass

    def post_deny(self, *args, **kwargs):
        pass


    @transaction.atomic()
    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def deny(self, request, *args, **kwargs):
        """
        deny advance Requests
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

        self.generate_history(instance, remarks=remarks, action=DENIED)

        instance.status = DENIED
        instance.save()

        self.post_deny(instance)

        employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
        deny_notification_text = self.get_user_notification_text(
            user=employee.full_name,
            approved_by=request.user,
            action_=DENIED
        )
        user_notification_text = self.get_user_notification_text(
            user='Your',
            approved_by=request.user,
            action_=DENIED
        )
        organization = employee.detail.organization
        if request.query_params.get('as') != 'hr' or self.send_hr_notification:
            notify_organization(
                text=deny_notification_text,
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=self.get_permission_for_org_notification(),
                url=self.get_notification_url_for_organization(organization=organization)
            )

        for approved_approvals in instance.approvals.filter(status=APPROVED):
            add_notification(
                text=deny_notification_text,
                recipient=approved_approvals.user,
                action=instance,
                actor=request.user,
                url=self.get_notification_url_for_approver(user=approved_approvals.user)
            )
        add_notification(
            text=user_notification_text,
            recipient=employee,
            action=instance,
            actor=request.user,
            url=self.get_notification_url_for_user(user=employee)
        )

        return Response({'message': _("Declined Request.")})

    @transaction.atomic()
    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def approve(self, request, **kwargs):
        """
        Approve or Forward advance Requests
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
        approval.status = APPROVED
        approval.save()

        self.post_approve(instance)
        self.generate_history(instance, remarks=remarks, action=APPROVED)

        next_approval = instance.approvals.filter(status=PENDING).order_by('level').first()
        employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
        organization = employee.detail.organization

        if next_approval:
            instance.recipient = next_approval.user
            # instance.status = FORWARDED
            instance.save()
            hr_notification_text = self.get_user_notification_text(
                user=employee.full_name,
                approved_by=request.user,
                action_=APPROVED,
                next_approver=next_approval.user if next_approval else None
            )
            notify_organization(
                text=hr_notification_text,
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=self.get_permission_for_org_notification(),
                url=self.get_notification_url_for_organization(organization=organization)
            )
            add_notification(
                text=f"{request.user.full_name} forwarded "
                     f"{getattr(self, 'notification_for', 'advance expense')} request by "
                     f"{employee.full_name}.",
                recipient=next_approval.user,
                action=instance,
                actor=request.user,
                url=self.get_notification_url_for_approver(user=next_approval.user)
            )
        else:
            instance.status = APPROVED
            instance.save()
            notify_organization(
                text=self.get_organization_text(employee),
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=self.get_permission_for_org_notification(),
                url=self.get_notification_url_for_organization(organization=organization)
            )

        employee_notification_text = self.get_user_notification_text(
            user='Your',
            approved_by=request.user,
            action_=APPROVED,
            next_approver=next_approval.user if next_approval else None
        )
        add_notification(
            text=employee_notification_text,
            recipient=employee,
            action=instance,
            actor=request.user,
            url=self.get_notification_url_for_user(user=employee)
        )
        return Response({'message': _("Approved Request.")})

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def cancel(self, request, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks')

        instance.status = CANCELED
        instance.save()

        self.post_cancel(instance)

        employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
        organization = employee.detail.organization
        if self.send_hr_notification:
            notify_organization(
                text=f"{self.get_type().title()} request for {employee.full_name}"
                     f" has been cancelled.",
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=self.get_permission_for_org_notification(),
                url=self.get_notification_url_for_organization(organization=organization)
            )

        self.generate_history(instance, remarks=remarks, action="canceled", target="the request")
        return Response({"detail": "Successfully canceled request."})


class ApproveDenyCancelWithMultipleApproverViewSetMixin(BaseForRequestMixin):
    """
    This mixin is used to perform approve, deny and forward action for requesting
    advance salary and expense.

    To implement this mixin we need to perform following:
    1. Override get_permission_for_notification method
    2. Set history_model attribute or override get_history_model() method
        -> history_model = AdvanceExpenseRequestHistory
    3. Set notification_for attribute
        -> notification_for = 'salary' or 'expense'
    4. Set notification_url_for_organization or override
       get_notification_url_for_organization method
       -> notification_url_for_organization = '/admin/{org.slug}/expense-management/request'
    5. Set notification_url_for_user or override
       get_notification_url_for_user method
       -> notification_url_for_user = '/admin/expense-management/request'
    6. Set notification_url_for_approver or override
       get_notification_url_for_approver method
       -> notification_url_for_approver = '/admin/expense-management/request'

    Optional Overrides:
    1. perform_pre_approval_validation(instance)
        Override this method to perform any extra validation before approving the request

    2. perform_pre_approval_validation(instance)
    Override this method to perform any extra validation before denying the request

   3. To add additional fields except the defaults, override
      get_additional_validated_fields(),
    currently only supports `approve` action
    """

    def perform_pre_approval_validation(self, instance):
        pass

    def perform_pre_denial_validation(self, instance):
        pass

    def get_additional_validated_fields(self):
        return {}

    def post_approve(self, *args, **kwargs):
        pass

    def post_cancel(self, *args, **kwargs):
        pass

    def post_deny(self, *args, **kwargs):
        pass

    @transaction.atomic()
    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def deny(self, request, *args, **kwargs):
        """
        deny advance Requests
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        remarks = serializer.validated_data.get('remarks')

        self.perform_pre_denial_validation(instance)

        if not self.mode == 'hr':
            approval = instance.active_approval
            if not approval:
                raise serializers.ValidationError({
                    'non_field_errors': _("Couldn't not deny this request.")
                })

            approval.status = DENIED
            approval.acted_by = request.user
            approval.save()

        self.generate_history(instance, remarks=remarks, action=DENIED)

        employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
        deny_notification_text = self.get_user_notification_text(
            user=f'{employee.full_name}\'s',
            approved_by=request.user,
            action_=DENIED
        )
        user_notification_text = self.get_user_notification_text(
            user='Your',
            approved_by=request.user,
            action_=DENIED
        )
        organization = employee.detail.organization
        if request.query_params.get('as') != 'hr':
            notify_organization(
                text=deny_notification_text,
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=self.get_permission_for_org_notification(),
                url=self.get_notification_url_for_organization(organization=organization)
            )

        for approved_approvals in instance.approvals.filter(status=APPROVED):
            add_notification(
                text=deny_notification_text,
                recipient=approved_approvals.user.all(),
                action=instance,
                actor=request.user,
                url=self.get_notification_url_for_approver()
            )

        add_notification(
            text=user_notification_text,
            recipient=employee,
            action=instance,
            actor=request.user,
            url=self.get_notification_url_for_user()
        )

        instance.status = DENIED
        instance.save()

        self.post_deny(instance)
        return Response({'message': _("Declined Request.")})

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def approve(self, request, **kwargs):
        """
        Approve or Forward advance Requests
        """
        instance = self.get_object()
        approval = instance.active_approval
        approve_multiple_times = nested_getattr(instance.employee.detail.organization,
                                                'reimbursement_setting.approve_multiple_times',
                                                default=True)

        if not approval:
            raise serializers.ValidationError({
                'non_field_errors': _("Couldn't not approve this request.")
            })

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remarks = serializer.validated_data.get('remarks')
        signature = serializer.validated_data.get('add_signature', False)
        additional_fields = self.get_additional_validated_fields()
        if signature and not request.user.signature:
            raise ValidationError({'add_signature': 'Add signature within your profile.'})

        # perform pre-approval validations if any
        instance.validated_data = serializer.validated_data
        self.perform_pre_approval_validation(instance)

        with transaction.atomic():
            next_approval = self._approve_action(approval, instance, remarks, request.user,
                                                 signature, additional_fields)
            if not approve_multiple_times and next_approval:
                while True:
                    if not next_approval:
                        break

                    new_actors = next_approval.user.values_list('id', flat=True)
                    new_actor = instance.approvals.filter(
                        status=APPROVED, acted_by__id__in=new_actors
                    ).first()

                    if not new_actor:
                        break

                    history = instance.histories.filter(actor=new_actor.acted_by).first()
                    next_approval = self._approve_action(
                        next_approval, instance, history.remarks,
                        new_actor.acted_by, new_actor.add_signature,
                        additional_fields,
                    )

            employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
            organization = employee.detail.organization

            next_approval_users = None
            if next_approval:
                next_approval_users = next_approval.user.all()

                hr_notification_text = self.get_user_notification_text(
                    user=f'{employee.full_name}\'s',
                    approved_by=request.user,
                    action_=APPROVED,
                    next_approver=next_approval.user if next_approval else None
                )
                notify_organization(
                    text=hr_notification_text,
                    organization=organization,
                    action=instance,
                    actor=request.user,
                    permissions=self.get_permission_for_org_notification(),
                    url=self.get_notification_url_for_organization(organization=organization)
                )
                add_notification(
                    text=f"{request.user.full_name} has forwarded {self.get_type()} "
                         f"requested by {employee.full_name}.",
                    recipient=next_approval_users,
                    action=instance,
                    actor=request.user,
                    url=self.get_notification_url_for_approver(user=next_approval.user)
                )
            else:
                instance.status = APPROVED
                notify_organization(
                    text=self.get_organization_text(employee),
                    organization=organization,
                    action=instance,
                    actor=request.user,
                    permissions=self.get_permission_for_org_notification(),
                    url=self.get_notification_url_for_organization(organization=organization)
                )
            employee_notification_text = self.get_user_notification_text(
                user='Your',
                approved_by=request.user,
                action_=APPROVED,
                next_approver=next_approval.user if next_approval else None
            )
            add_notification(
                text=employee_notification_text,
                recipient=employee,
                action=instance,
                actor=request.user,
                url=self.get_notification_url_for_user(user=employee)
            )

            if next_approval_users:
                instance.recipient.set(next_approval_users)
            instance.save()
        self.post_approve(instance)
        return Response({'message': _("Approved Advance Expense Request.")})

    def _approve_action(self, approval, instance, remarks, user, signature,
                        additional_fields):
        approval.status = APPROVED
        approval.add_signature = signature
        approval.acted_by = user
        for key, val in additional_fields.items():
            setattr(approval, key, val)
        approval.save()
        self.generate_history(instance, user=user, remarks=remarks, action=APPROVED)
        next_approval = instance.approvals.filter(status=PENDING).order_by('level').first()
        return next_approval

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def cancel(self, request, **kwargs):
        # In viewset, objects level permission requires status to be in
        # REQUESTED for user. Previously notification text was declared after saving
        # instance into CANCELED status which raised 403.
        # To resolve 403 we declare notification text before saving                                                                                                                                                                                          to pass the test.
        employee_notification_text = self.get_user_notification_text(
            user = 'Your',
            approved_by=request.user,
            action_=CANCELED,
            next_approver=None
        )
        instance = self.get_object()
        employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
        if instance.status in [DENIED, CANCELED]:
            raise ValidationError({'detail': f'This request has already been {instance.status}'})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks')

        instance.status = CANCELED
        instance.save()

        add_notification(
            text=employee_notification_text,
            recipient=employee,
            action=instance,
            actor=request.user,
            url=self.get_notification_url_for_user(user=employee)
        )
        self.post_cancel(instance)

        self.generate_history(instance, remarks=remarks, action="canceled", target="the request")
        return Response({"detail": "Successfully canceled request."})


class ActionOnExpenseCancelRequestWithMultipleApproverViewSetMixin(BaseForRequestMixin):
    """
    This mixin is used to perform approve, deny and forward action for requesting
    advance expense cancel requests with multiple approvers.

    To implement this mixin we need to perform following:
    1. Override get_permission_for_notification method
    2. Set history_model attribute or override get_history_model() method
        -> history_model = AdvanceExpenseRequestHistory
    3. Set notification_for attribute
        -> notification_for = 'expense cancellation'

    Optional Overrides:
    1. perform_pre_approval_validation(instance)
        Override this method to perform any extra validation before approving the request

    2. perform_pre_approval_validation(instance)
    Override this method to perform any extra validation before denying the request

   3. To add additional fields except the defaults, override
      get_additional_validated_fields(),
    currently only supports `approve` action
    """

    def perform_pre_approval_validation(self, instance):
        pass

    def perform_pre_denial_validation(self, instance):
        pass

    def get_additional_validated_fields(self):
        return {}

    def post_approve(self, *args, **kwargs):
        pass

    def post_cancel(self, *args, **kwargs):
        pass

    def post_deny(self, *args, **kwargs):
        pass

    @transaction.atomic()
    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def deny(self, request, *args, **kwargs):
        """
        deny advance cancel Requests
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        remarks = serializer.validated_data.get('remarks')

        self.perform_pre_denial_validation(instance)

        if not self.mode == 'hr':
            approval = instance.active_approval
            if not approval:
                raise serializers.ValidationError({
                    'non_field_errors': _("Couldn't not deny this request.")
                })

            approval.status = DENIED
            approval.acted_by = request.user
            approval.save()

        self.generate_history(
            instance.advance_expense, remarks=remarks, action=DENIED,
            target='cancel expense request'
        )

        employee = nested_getattr(instance.advance_expense,
                                  'employee', default=instance.created_by)
        deny_notification_text = self.get_user_notification_text(
            user=f'{employee.full_name}\'s',
            approved_by=request.user,
            action_=DENIED
        )
        user_notification_text = self.get_user_notification_text(
            user='Your',
            approved_by=request.user,
            action_=DENIED
        )
        organization = employee.detail.organization
        if request.query_params.get('as') != 'hr':
            notify_organization(
                text=deny_notification_text,
                organization=organization,
                action=instance,
                actor=request.user,
                permissions=self.get_permission_for_org_notification(),
                url=self.get_notification_url_for_organization(organization=organization)
            )

        for approved_approvals in instance.approvals.filter(status=APPROVED):
            add_notification(
                text=deny_notification_text,
                recipient=approved_approvals.user.all(),
                action=instance,
                actor=request.user,
                url=self.get_notification_url_for_approver()
            )

        add_notification(
            text=user_notification_text,
            recipient=employee,
            action=instance,
            actor=request.user,
            url=self.get_notification_url_for_user()
        )

        instance.status = DENIED
        instance.save()

        self.post_deny(instance)
        return Response({'message': _("Declined Request.")})

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def approve(self, request, **kwargs):
        """
        Approve or Forward advance cancel Requests
        """
        instance = self.get_object()
        advance_expense = instance.advance_expense
        approval = instance.active_approval

        approve_multiple_times = nested_getattr(
            advance_expense.employee.detail.organization,
            'reimbursement_setting.approve_multiple_times',
            default=True
        )

        if not approval:
            raise serializers.ValidationError({
                'non_field_errors': _("Couldn't not approve this request.")
            })

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remarks = serializer.validated_data.get('remarks')
        signature = serializer.validated_data.get('add_signature', False)
        additional_fields = self.get_additional_validated_fields()
        if signature and not request.user.signature:
            raise ValidationError({'add_signature': 'Add signature within your profile.'})

        # perform pre-approval validations if any
        instance.validated_data = serializer.validated_data
        self.perform_pre_approval_validation(instance)

        with transaction.atomic():
            next_approval = self._approve_action(approval, instance, remarks, request.user,
                                                 signature, additional_fields)
            if not approve_multiple_times and next_approval:
                while True:
                    if not next_approval:
                        break

                    new_actors = next_approval.user.values_list('id', flat=True)
                    new_actor = instance.approvals.filter(
                        status=APPROVED, acted_by__id__in=new_actors
                    ).first()

                    if not new_actor:
                        break

                    history = instance.histories.filter(actor=new_actor.acted_by).first()
                    next_approval = self._approve_action(
                        next_approval, instance, history.remarks,
                        new_actor.acted_by, new_actor.add_signature,
                        additional_fields,
                    )

            employee = nested_getattr(advance_expense,
                                      'employee', default=instance.created_by)
            organization = employee.detail.organization

            next_approval_users = None
            if next_approval:
                next_approval_users = next_approval.user.all()

                hr_notification_text = self.get_user_notification_text(
                    user=f'{employee.full_name}\'s',
                    approved_by=request.user,
                    action_=APPROVED,
                    next_approver=next_approval.user if next_approval else None
                )
                notify_organization(
                    text=hr_notification_text,
                    organization=organization,
                    action=instance,
                    actor=request.user,
                    permissions=self.get_permission_for_org_notification(),
                    url=self.get_notification_url_for_organization(organization=organization)
                )
                add_notification(
                    text=f"{request.user.full_name} has forwarded {self.get_type()} "
                         f"requested by {employee.full_name}.",
                    recipient=next_approval_users,
                    action=instance,
                    actor=request.user,
                    url=self.get_notification_url_for_approver(user=next_approval.user)
                )
            else:
                instance.status = APPROVED
                advance_expense.status = CANCELED
                advance_expense.save()
                notify_organization(
                    text=self.get_organization_text(employee),
                    organization=organization,
                    action=instance,
                    actor=request.user,
                    permissions=self.get_permission_for_org_notification(),
                    url=self.get_notification_url_for_organization(organization=organization)
                )
            employee_notification_text = self.get_user_notification_text(
                user='Your',
                approved_by=request.user,
                action_=APPROVED,
                next_approver=next_approval.user if next_approval else None
            )
            add_notification(
                text=employee_notification_text,
                recipient=employee,
                action=instance,
                actor=request.user,
                url=self.get_notification_url_for_user(user=employee)
            )

            if next_approval_users:
                instance.recipient.set(next_approval_users)
            instance.save()
        self.post_approve(instance)
        return Response({'message': _("Approved Advance Expense Cancel Request.")})

    def _approve_action(self, approval, instance, remarks, user, signature,
                        additional_fields):
        approval.status = APPROVED
        approval.add_signature = signature
        approval.acted_by = user
        for key, val in additional_fields.items():
            setattr(approval, key, val)
        approval.save()

        self.generate_history(
            instance.advance_expense, user=user, remarks=remarks,
            action=APPROVED, target='cancel expense request'
        )
        next_approval = instance.approvals.filter(status=PENDING).order_by('level').first()
        return next_approval

    @action(detail=True, methods=['POST'],
            serializer_class=RemarksRequiredSerializer)
    def cancel(self, request, **kwargs):
        employee_notification_text = self.get_user_notification_text(
            user = 'Your',
            approved_by=request.user,
            action_=CANCELED,
            next_approver=None
        )
        instance = self.get_object()
        employee = instance.advance_expense.employee if hasattr(instance.advance_expense, 'employee') else instance.created_by
        if instance.status in [DENIED, CANCELED]:
            raise ValidationError({'detail': f'This request has already been {instance.status}'})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks')

        instance.status = CANCELED
        instance.save()

        add_notification(
            text=employee_notification_text,
            recipient=employee,
            action=instance,
            actor=request.user,
            url=self.get_notification_url_for_user(user=employee)
        )
        self.post_cancel(instance)

        self.generate_history(
            instance.advance_expense, remarks=remarks, action=CANCELED,
            target="the request"
        )
        return Response({"detail": "Successfully canceled request."})


import re

from django.db.models import Sum, FloatField, F, Q, Case, When
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from rest_framework.fields import ReadOnlyField, SerializerMethodField

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.utils import nested_getattr, get_system_admin
from irhrs.leave.constants.model_constants import APPROVED, CREDIT_HOUR
from irhrs.leave.models.request import LeaveSheet
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer, UserThickSerializer


class TypeBalanceSerializer(DummySerializer):
    type_id = ReadOnlyField(source='rule.leave_type.id')
    name = ReadOnlyField(source='rule.leave_type.name')
    category = ReadOnlyField(source='rule.leave_type.category')
    usable_balance = ReadOnlyField()


class IndividualLeaveBalanceReportSerializer(UserThickSerializer):
    leave_accounts = TypeBalanceSerializer(
        many=True
    )

    class Meta(UserThickSerializer.Meta):
        fields = UserThickSerializer.Meta.fields + ["leave_accounts"]


class SummarizedYearlyLeaveReportSerializer(DummySerializer):
    user = SerializerMethodField()
    results = SerializerMethodField()

    @cached_property
    def system_bot(self):
        return get_system_admin()

    def get_results(self, instance):
        leave_types = self.context.get('selected_leave_types')
        start_date, end_date = self.context.get('date_range')
        queryset = getattr(
            instance,
            'prefetch_leave_accounts',
            None
        )
        if not queryset:
            queryset = instance.leave_accounts.filter(
                rule__leave_type__in=leave_types
            )
        result = list()
        for leave_account in queryset:
            first_history = leave_account.history.filter(
                actor=self.system_bot,
                created_at__date__range=(start_date, end_date),
            ).order_by('-created_at')
            res = dict(
                balance_added=getattr(
                    first_history.filter(
                        renewed__isnull=False
                    ).first(),
                    'renewed', 0),
                carry_forward=getattr(
                    first_history.filter(
                        carry_forward__isnull=False
                    ).first(),
                    'carry_forward', 0),
                encashment_balance=getattr(
                    first_history.filter(
                        encashed__isnull=False
                    ).first(),
                    'encashed', 0),
                collapsed_balance=getattr(
                    first_history.filter(
                        deducted__isnull=False
                    ).first(),
                    'deducted', 0),
                accrued_balance=getattr(
                    first_history.filter(
                        accrued__isnull=False
                    ).first(),
                    'accrued', 0),
            )
            initial_balance = res.get('balance_added') or 0.0
            carry_forwarded = res.get('carry_forward') or 0.0
            res.update({
                'used': LeaveSheet.objects.filter(
                    request__leave_account=leave_account,
                    leave_for__range=(start_date, end_date),
                    request__status=APPROVED,
                    request__is_deleted=False
                ).aggregate(
                    used=Sum(Coalesce(F('balance'), 0.0))
                ).get('used'),
                'total_leave_balance': initial_balance + carry_forwarded,
                'remaining_balance': getattr(
                    leave_account.history.filter(
                        created_at__range=(start_date, end_date)
                    ).order_by('-created_at').first(),
                    'new_usable_balance',
                    0.0
                ),
                'carry_forward_max_limit': nested_getattr(
                    leave_account,
                    'rule.renewal_rule.max_balance_forwarded'
                ) or 0.0,
            })
            next_fiscal = self.context.get('next_fiscal')
            if next_fiscal:
                next_year_history = leave_account.history.filter(
                    actor=self.system_bot,
                    created_at__date__range=(
                        next_fiscal.applicable_from, next_fiscal.applicable_to
                    )
                ).order_by('created_at')
                carry_forward_to_next = getattr(
                    next_year_history.filter(
                        carry_forward__isnull=False
                    ).first(), 'carry_forward', None
                )
                encashed_next_year = getattr(
                    next_year_history.filter(
                        encashed__isnull=False
                    ).first(), 'encashed', None
                )
            else:
                encashed_next_year = None
                carry_forward_to_next = None
            res.update({
                'carry_forward_to_next_year': carry_forward_to_next,
                'encashment': encashed_next_year
            })
            result.append({
                'leave': leave_account.rule.leave_type.name,
                'category': leave_account.rule.leave_type.category,
                'id': leave_account.rule.leave_type.id,
                'balance_details': res
            })
        return result

    @staticmethod
    def get_user(instance):
        return {
            **UserThinSerializer(instance).data,
            "username":instance.username
        }


class CarryForwardLeaveDetailsSerializer(SummarizedYearlyLeaveReportSerializer):

    def get_results(self, instance):
        # selected fiscal is list of tuple (name, start, end)
        selected_fiscals = self.context.get('selected_fiscals')
        leave_types = self.context.get('selected_leave_types')
        queryset = getattr(
            instance,
            'prefetch_leave_accounts',
            None
        )
        if not queryset:
            queryset = instance.leave_accounts.filter(
                rule__leave_type__in=leave_types
            ).select_related(
                'rule',
                'rule__leave_type',
            )
        result = list()
        for year, start_date, end_date, next_start, next_end in \
                selected_fiscals:
            year_res = list()
            for leave_account in queryset:
                fields = list(self.context.get(
                    'extra_fields'
                )) + ['carry_forward', 'encashment_balance']
                first_history = leave_account.history.filter(
                    actor=self.system_bot,
                    created_at__date__range=(start_date, end_date),
                ).order_by('-created_at')
                next_year_history = leave_account.history.filter(
                    actor=self.system_bot,
                    created_at__date__range=(next_start, next_end),
                ).order_by('created_at')
                aggregates = dict(
                    initial_balance=getattr(
                        first_history.filter(
                            renewed__isnull=False
                        ).first(),
                        'renewed', 0),
                    carry_forwarded=getattr(
                        first_history.filter(
                            carry_forward__isnull=False
                        ).first(),
                        'carry_forward', 0),
                    collapsed_balance=getattr(
                        first_history.filter(
                            deducted__isnull=False
                        ).first(),
                        'deducted', 0),
                    accrued_balance=getattr(
                        first_history.filter(
                            accrued__isnull=False
                        ).first(),
                        'accrued', 0),
                )
                if next_year_history.filter(
                    renewed__isnull=False
                ):
                    carry_forward = getattr(
                        next_year_history.filter(
                            carry_forward__isnull=False
                        ).first(),
                        'carry_forward', 0)
                    encashment_balance = getattr(
                        next_year_history.filter(
                            encashed__isnull=False
                        ).first(),
                        'encashed', 0)
                    aggregates['carry_forward'] = carry_forward
                    aggregates['encashment_balance'] = encashment_balance
                else:
                    aggregates['carry_forward'] = None
                    aggregates['collapsed_balance'] = None
                    aggregates['encashment_balance'] = None
                initial_balance = aggregates.get('initial_balance') or 0
                carry_forward = aggregates.get('carry_forwarded') or 0
                aggregates['balance_added'] = initial_balance + carry_forward
                res = {
                    k: v for k, v in aggregates.items() if k in fields
                }
                if 'used' in self.context.get('extra_fields'):
                    res.update(
                        LeaveSheet.objects.filter(
                            leave_for__range=(start_date, end_date),
                            request__status=APPROVED,
                            request__is_deleted=False,
                            request__leave_account=leave_account
                        ).aggregate(
                            used=Sum(
                                Case(
                                    When(
                                        request__leave_rule__leave_type__category=CREDIT_HOUR,
                                        then=F('request__balance')
                                    ),
                                    default=F('balance')
                                )
                            )
                        )
                    )
                year_res.append({
                    'leave': leave_account.rule.leave_type.name,
                    'category': leave_account.rule.leave_type.category,
                    'id': leave_account.rule.leave_type.id,
                    **res
                })
            result.append({
                'year': year,
                'balance_details': year_res
            })
        return result

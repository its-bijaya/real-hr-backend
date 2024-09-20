from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, OrganizationCommonsMixin, DisallowPatchMixin
)
from irhrs.leave.api.v1.permissions import LeaveMasterSettingPermission
from irhrs.leave.api.v1.serializers.rule import LeaveRuleSerializer
from irhrs.leave.models import LeaveRule, MasterSetting


class LeaveRuleViewSet(DisallowPatchMixin,
                       OrganizationMixin,
                       OrganizationCommonsMixin,
                       ModelViewSet):
    """
    create:

    ## Minimum fields or default values

    ```js
        {
            // -- MINIMUM REQUIRED FIELDS -- //
            "name": "Name of leave",
            "description": "Description of the rule",
            "leave_type": "leave_type_id",
            "is_archived": false,
            "is_paid": false,

            // -- SET ALL OTHERS TO THEIR DEFAULT VALUES -- //
            "irregularity_report": false,
            "employee_can_apply": false,
            "admin_can_assign": false,

            "require_prior_approval": false,
            "prior_approval_days": null,

            "accumulation_rule": null,
            "renewal_rule": null,
            "deduction_rule": null,
            "yos_rule": null,

            "compensatory_rule": null,
            "leave_irregularity": null,
            "time_off_rule":null,

            "limit_leave_to": null,
            "limit_leave_duration": null,

            "min_balance": null,
            "max_balance": null,

            "limit_leave_occurrence": null,
            "limit_leave_occurrence_duration": null,

            "maximum_continuous_leave_length": null,
            "minimum_continuous_leave_length": null,

            "holiday_inclusive": null,

            "proportionate_on_joined_date": null,

            "can_apply_half_shift": null,

            "can_apply_beyond_zero_balance": null,
            "beyond_limit": null,

            "required_experience": null,
            "required_experience_duration": null,

            "require_docs": null,
            "require_docs_for": null,

            "depletion_required": null,
            "depletion_leave_types": [],

            "start_date": null,
            "end_date": null
        }
        ```

    ## Full rules

    ```js
    {
        // -- BASIC FIELDS -- //
        "name": "Name of leave",
        "description": "Description of the rule",
        "leave_type": "leave_type_id",
        "is_archived": false,

        // -- Whether leave is paid or not-- //
        "is_paid": false,

        // -- Enable irregularity report -- //
        "irregularity_report": false,

        // -- Irregularity rule -- //
        // Min balance used by user in given duration
        // to consider user as irregular
        // condition = weekly_limit <
        //              fortnightly_limit <
        //				monthly_limit <
        //				quarterly_limit <
        //				semi_annually_limit <
        //				annually_limit
        "leave_irregularity": {
            "weekly_limit": 1,
            "fortnightly_limit": 2,
            "monthly_limit": 3,
            "quarterly_limit": 4,
            "semi_annually_limit": 5,
            "annually_limit": 6
        },

        // -- Determines how leave can be applied -- //
        "employee_can_apply": false,
        "admin_can_assign": false,

        // -- Require prior approval for the leave -- //
        "require_prior_approval": false,
        // no of days before leave should be applied //
        "prior_approval_days": 12,

        // Leave accumulation rule
        "accumulation_rule": {
            "duration": 20,
            "duration_type": "Days", // options ["Years", "Months", "Days"]
            "balance_added": 1,
            "max_balance_encashed": 12,
            "max_balance_forwarded": 5,
            "is_collapsible": true
        },

        // leave renewal rule
        "renewal_rule": {
            "duration": 1,
            "duration_type": "Years", // options ["Years", "Months", "Days"]
            "initial_balance": 30,
            "max_balance_encashed": 0,
            "max_balance_forwarded": 13,
        },

        // leave deduction rule
        "deduction_rule":{
            "duration": 30,
            "duration_type": "Days", // options ["Years", "Months", "Days"]
            "balance_deducted": 1
        },

        // yos rule
        "yos_rule": {
            "years_of_service": 2,
            "balance_added": 60,
            "collapse_after": 30,
            "collapse_after_unit": "Days", // options ["Years", "Months", "Days"]
        },

        // compensatory rule
        //compensatory_rule can be multiple but collapsible_rule is one for all rules
        "compensatory_rule":  [{
            "balance_to_grant": 2,
            "hours_in_off_day": 6
        },
        {
            "balance_to_grant": 3,
            "hours_in_off_day": 8
        }]
        "collapsible_rule": {
            "collapse_after": 3,
            "collapse_after_unit": "Months" // options ["Years", "Months", "Days"]
        },

        // time off rule
        // rule to charge if user is takes more leave then granted
        "time_off_rule":{
            "total_late_minutes": 120,
            "reduce_leave_by": 0.5,  // must be multiple of 0.5
            "leave_type": 2  // leave type id to reduce from
        },

        // max and min balance at any time
        "min_balance": 100,
        "max_balance": 10,

        // limit leave to 6 times in 2 months
        "limit_leave_occurrence": 6,
        "limit_leave_occurrence_duration": 2,
        "limit_leave_occurrence_duration_type": "Months", // options ["Years", "Months"]

        // limit leave to 10 days in 1 month
        "limit_leave_to": 10,
        "limit_leave_duration": 1,
        "limit_leave_duration_type": "Months", // options ["Years", "Months"]

        // allow user to take leave upto 10 continuous days and minimum of 1 day including holidays
        "maximum_continuous_leave_length": 10,
        "minimum_continuous_leave_length": 1,
        "holiday_inclusive": true,

        // proportionate users balance according to joined date
        "proportionate_on_joined_date": true,

        // can apply half shift
        "can_apply_half_shift": true,

        // can apply beyond 12 days of her/his limit
        "can_apply_beyond_zero_balance": true,
        "beyond_limit": 12,

        // require 30 days experience before applying for this leave
        "required_experience": 30,
        "required_experience_duration": "Days", // options ["Years", "Months", "Days"]

        // require docs if user taking leave longer than 10 days
        "require_docs": true,
        "require_docs_for": 10,

        // can apply to this leave only if user has zero balance on these leave types
        "depletion_required": true,
        "depletion_leave_types": [1, 2, 3],  // leave type id

        // user can apply for this leave only between these days
        "start_date": "2017-01-01",
        "end_date": "2018-01-01"
    }
    ```
    """
    serializer_class = LeaveRuleSerializer
    filter_fields = ('leave_type',)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('name', 'modified_at',)
    permission_classes = [LeaveMasterSettingPermission]

    def get_queryset(self):
        queryset = LeaveRule.objects.all().filter(
            leave_type__master_setting__organization=self.get_organization()
        )
        if self.action == 'retrieve':
            return queryset.select_related(
                'accumulation_rule', 'renewal_rule', 'deduction_rule',
                'yos_rule', 'leave_type',
            ).prefetch_related('depletion_leave_types')

        return queryset

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({'fields': [
                'id',
                'cloned_from',
                'name',
                'description',
                'is_paid',
                'cloned_from',
                'created_at',
                'modified_at'
            ]})
        return super().get_serializer(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        idle_settings = MasterSetting.objects.all(
        ).idle()
        if obj.leave_type.master_setting in idle_settings:
            return super().destroy(request, *args, **kwargs)
        return Response(
            {
                'detail': 'You cannot delete Leave rule except for idle master '
                          'setting'
            }, status=status.HTTP_403_FORBIDDEN
        )

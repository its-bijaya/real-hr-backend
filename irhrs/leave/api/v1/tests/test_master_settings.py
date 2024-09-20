import datetime
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import BaseTestCase as TestCase, RHRSAPITestCase

from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, \
    LeaveTypeFactory, LeaveRuleFactory, \
    AccumulationRuleFactory, RenewalRuleFactory, TimeOffRuleFactory, \
    LeaveIrregularitiesRuleFactory, \
    YearsOfServiceRuleFactory, CompensatoryLeaveRuleFactory, \
    DeductionRuleFactory
from irhrs.leave.constants.model_constants import DAYS
from irhrs.leave.models import MasterSetting
from irhrs.leave.models.rule import CompensatoryLeaveCollapsibleRule
from irhrs.leave.utils.master_settings_validator import \
    MasterSettingUpdateValidator


class TestMasterSettingValidator(TestCase):
    master_setting_leave_rule_map = (
        ('leave_limitations', (
            'min_balance',
            'max_balance',
            'limit_leave_to',
            'limit_leave_duration',
            'limit_leave_duration_type',
            'limit_leave_occurrence',
            'limit_leave_occurrence_duration',
            'limit_leave_occurrence_duration_type',
            'maximum_continuous_leave_length',
            'minimum_continuous_leave_length',
        )),
        ('occurrences', (
            'limit_leave_occurrence',
            'limit_leave_occurrence_duration',
            'limit_leave_occurrence_duration_type',
        )),
        ('beyond_balance', (
            'can_apply_beyond_zero_balance',
            'beyond_limit',
        )),
        ('proportionate_leave', (
            'proportionate_on_joined_date',
        )),
        ('depletion_required', (
            'depletion_required',
            'depletion_leave_types',
        )),
        ('require_experience', (
            'required_experience',
            'required_experience_duration',
        )),
        ('require_time_period', (
            'start_date',
            'end_date',
        )),
        ('require_prior_approval', (
            'require_prior_approval',
        )),
        ('require_document', (
            'require_docs',
            'require_docs_for',
        )),
        ('holiday_inclusive', (
            'holiday_inclusive',
        )),
        ('employees_can_apply', (
            'employee_can_apply',
        )),
        ('admin_can_assign', (
            'admin_can_assign',
        )),
        ('half_shift_leave', (
            'can_apply_half_shift',
        )),
        ('continuous', (
            'maximum_continuous_leave_length',
            'minimum_continuous_leave_length',
        )),

        # FK relations
        ("accumulation", ("accumulation_rule",)),
        ("renewal", ("renewal_rule",)),
        ("time_off", ("time_off_rule",)),
        ("leave_irregularities", ("irregularities",)),
        ("years_of_service", ("yos_rule",)),
        ("compensatory", ("compensatory_rule",)),
        ("deductible", ("deduction_rule",))
    )

    field_value_map = {
        'min_balance': 10,
        'max_balance': 20,

        'limit_leave_to': 12,
        'limit_leave_duration': 1,
        'limit_leave_duration_type': 'Durr',

        'limit_leave_occurrence': 2,
        'limit_leave_occurrence_duration': 2,
        'limit_leave_occurrence_duration_type': 'days',

        'maximum_continuous_leave_length': 12,
        'minimum_continuous_leave_length': 5,

        "required_experience": 2,
        "required_experience_duration": "xyz",

        "require_prior_approval": True,
        "prior_approval_rules": [{
            "prior_approval_request_for": 5,
            "prior_approval": 5,
            "prior_approval_unit": DAYS,

        }],
       
        "require_docs": True,
        "require_docs_for": 12,

        "holiday_inclusive": True,

        "can_apply_beyond_zero_balance": True,
        "beyond_limit": 2,

        "proportionate_on_joined_date": True,

        "depletion_required": True,

        "start_date": get_today(),
        "end_date": get_today(),

        "admin_can_assign": True,
        "employee_can_apply": True,
        "can_apply_half_shift": True,
    }

    fields_factory_map = {
        "accumulation_rule": AccumulationRuleFactory,
        "renewal_rule": RenewalRuleFactory,
        "time_off_rule": TimeOffRuleFactory,
        "irregularities": LeaveIrregularitiesRuleFactory,
        "yos_rule": YearsOfServiceRuleFactory,
        "compensatory_rule": CompensatoryLeaveRuleFactory,
        "deduction_rule": DeductionRuleFactory,
    }

    @staticmethod
    def create_master_setting(**kwargs):
        return MasterSettingFactory(**kwargs)

    @staticmethod
    def create_leave_type(master_setting, **kwargs):
        return LeaveTypeFactory(master_setting=master_setting, **kwargs)

    def test_master_setting_update_validator(self):
        """
        test master settings validator for update

        ## test plan
        1. create a master setting with a field enabled
        2. create a leave rule with that field
        3. Use validator to validate master setting update with that field set to False
        """

        for master_setting_field, leave_rule_fields in self.master_setting_leave_rule_map:
            for leave_rule_field in leave_rule_fields:
                master_setting = self.create_master_setting(
                    **{master_setting_field: True}
                )
                leave_type = self.create_leave_type(master_setting)
                if leave_rule_field == 'depletion_leave_types':
                    value = [LeaveTypeFactory(master_setting=master_setting,
                                              name="Random")]
                else:
                    value = self.field_value_map.get(leave_rule_field, None)

                if leave_rule_field in self.fields_factory_map:
                    rule = LeaveRuleFactory(leave_type=leave_type)

                    if leave_rule_field == 'irregularities':
                        self.fields_factory_map[leave_rule_field](
                            leave_rule=rule)
                    else:
                        self.fields_factory_map[leave_rule_field](rule=rule)
                else:
                    LeaveRuleFactory(leave_type=leave_type,
                                     **{leave_rule_field: value})
                status, errors = MasterSettingUpdateValidator.validate(
                    instance=master_setting, data={master_setting_field: False}
                )
                self.assertIn(
                    master_setting_field,
                    errors,
                    (
                        "Validation failed for master setting",
                        master_setting_field,
                        "and leave rule field",
                        leave_rule_field
                    )
                )

    def test_paid_update(self):
        master_setting = self.create_master_setting(paid=True)
        leave_type = self.create_leave_type(master_setting)
        LeaveRuleFactory(leave_type=leave_type, is_paid=True)
        status, errors = MasterSettingUpdateValidator.validate(
            instance=master_setting, data={"paid": False}
        )
        self.assertIn(
            'paid',
            errors,
            (
                "Validation failed for master setting", 'paid',
                "and leave rule field",
                'is_paid'
            )
        )

    def test_unpaid_update(self):
        master_setting = self.create_master_setting(unpaid=True)
        leave_type = self.create_leave_type(master_setting)
        LeaveRuleFactory(leave_type=leave_type, is_paid=False)
        status, errors = MasterSettingUpdateValidator.validate(
            instance=master_setting, data={"unpaid": False}
        )
        self.assertIn(
            'unpaid',
            errors,
            (
                "Validation failed for master setting", 'unpaid',
                "and leave rule field",
                'is_paid'
            )
        )

    def test_renewal_update(self):
        master_settings_renewal_map = (
            ('carry_forward', 'max_balance_forwarded'),
            ('encashment', 'max_balance_encashed'),
            ('collapsible', 'is_collapsible')
        )
        field_value = {
            'max_balance_forwarded': 10,
            'max_balance_encashed': 5,
            'is_collapsible': True
        }

        for ms_field, renewal_field in master_settings_renewal_map:
            master_setting = self.create_master_setting(
                renewal=True,
                **{
                    ms_field: True
                }
            )
            leave_type = self.create_leave_type(master_setting)

            rule = LeaveRuleFactory(leave_type=leave_type)

            RenewalRuleFactory(
                rule=rule, **{renewal_field: field_value.get(renewal_field)})

            status, errors = MasterSettingUpdateValidator.validate(
                instance=master_setting, data={ms_field: False}
            )
            self.assertIn(
                ms_field,
                errors,
                (
                    "Validation failed for master setting", ms_field,
                    "and leave renewal rule field",
                    renewal_field
                )
            )

    def test_yos_update(self):
        master_settings_yos_map = (
            ('collapsible', ('collapse_after', 'collapse_after_unit')),
        )

        field_value = {
            'collapse_after': 10,
            'collapse_after_unit': 'Days',
        }

        for ms_field, yos_fields in master_settings_yos_map:
            master_setting = self.create_master_setting(
                years_of_service=True,
                **{
                    ms_field: True
                }
            )
            leave_type = self.create_leave_type(master_setting)

            rule = LeaveRuleFactory(leave_type=leave_type)

            YearsOfServiceRuleFactory(
                rule=rule, **{
                    field: field_value.get(field)
                    for field in yos_fields
                })

            status, errors = MasterSettingUpdateValidator.validate(
                instance=master_setting, data={ms_field: False}
            )
            self.assertIn(
                ms_field,
                errors,
                (
                    "Validation failed for master setting", ms_field,
                    "and leave yos rule fields",
                    ", ".join(yos_fields)
                )
            )

    def test_compensatory_update(self):
        master_settings_compensatory_map = (
            ('collapsible', ('collapse_after', 'collapse_after_unit')),
        )

        field_value = {
            'collapse_after': 10,
            'collapse_after_unit': 'Days',
        }

        for ms_field, cs_fields in master_settings_compensatory_map:
            master_setting = self.create_master_setting(
                compensatory=True,
                **{
                    ms_field: True
                }
            )
            leave_type = self.create_leave_type(master_setting)

            rule = LeaveRuleFactory(leave_type=leave_type)

            CompensatoryLeaveRuleFactory(
                rule=rule
            )
            CompensatoryLeaveCollapsibleRule.objects.create(
                rule=rule,
                **field_value
            )
            status, errors = MasterSettingUpdateValidator.validate(
                instance=master_setting, data={ms_field: False}
            )
            self.assertIn(
                ms_field,
                errors,
                (
                    "Validation failed for master setting", ms_field,
                    "and leave compensatory rule fields",
                    ", ".join(cs_fields)
                )
            )


class TestMasterSettingAPI(RHRSAPITestCase):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male'),
        ('guest@gmail.com', 'guestnotallowed', 'Other')
    ]

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.master_setting = MasterSettingFactory(
            name="Asar Master Setting",
            effective_from=get_today() - datetime.timedelta(days=10),
            effective_till=None,
            organization=self.organization
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_setting)
        self.rule = LeaveRuleFactory(leave_type=self.leave_type)

    @property
    def url(self):
        return reverse(
            'api_v1:leave:master-setting-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def update_url(self, pk):
        return reverse(
            'api_v1:leave:master-setting-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': pk
            }
        )

    @staticmethod
    def rules():
        return {
            "accumulation": False,
            "renewal": False,
            "deductible": False,
            "paid": True,
            "unpaid": False,
            "half_shift_leave": False,
            "occurrences": False,
            "beyond_balance": False,
            "proportionate_leave": False,
            "depletion_required": False,
            "require_experience": False,
            "require_time_period": False,
            "require_prior_approval": True,
            "prior_approval_rules": [{
                "prior_approval_request_for": 5,
                "prior_approval": 5,
                "prior_approval_unit": "Days"
            }],
            "require_document": False,
            "leave_limitations": False,
            "leave_irregularities": False,
            "employees_can_apply": True,
            "admin_can_assign": False,
            "continuous": False,
            "holiday_inclusive": False,
            "encashment": False,
            "carry_forward": True,
            "collapsible": False,
            "years_of_service": False,
            "time_off": False,
            "compensatory": False,
            "credit_hour": False
        }

    @property
    def payload(self):
        return {
            "cloned_from": "",
            "name": "Shrawan Master Setting",
            "description": "Create master setting",
            "effective_from": get_today() + datetime.timedelta(days=1),
            **self.rules()
        }

    @property
    def update_payload(self):
        return {
            "cloned_from": "",
            "name": "Shrawan Master Setting",
            "description": "Create master setting",
            "effective_from": get_today() + datetime.timedelta(days=3),
            **self.rules()
        }

    def test_master_setting_api(self):
        self.assertEqual(
            MasterSetting.objects.all().count(), 1
        )
        # create master setting
        response = self.client.post(
            self.url,
            self.payload,
            formart='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            MasterSetting.objects.first().effective_till,
            MasterSetting.objects.last().effective_from - datetime.timedelta(days=1)
        )

        # update master setting
        response = self.client.put(
            self.update_url(MasterSetting.objects.last().id),
            self.update_payload,
            formart='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            MasterSetting.objects.first().effective_till,
            MasterSetting.objects.last().effective_from - datetime.timedelta(days=1)
        )

        # delete master setting
        response = self.client.delete(
            self.update_url(MasterSetting.objects.last().id)
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
        self.assertEqual(
            MasterSetting.objects.first().effective_till,
            None
        )
        self.assertEqual(
            MasterSetting.objects.all().count(),
            1
        )

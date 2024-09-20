from django.core.files.temp import NamedTemporaryFile

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.leave.api.v1.tests.factory import CompensatoryLeaveCollapsibleRuleFactory, MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, RenewalRuleFactory, AccumulationRuleFactory, DeductionRuleFactory, \
    YearsOfServiceRuleFactory, TimeOffRuleFactory, CreditHourRuleFactory, \
    CompensatoryLeaveRuleFactory, LeaveIrregularitiesRuleFactory
from irhrs.leave.constants.model_constants import GENERAL, YEARS_OF_SERVICE, COMPENSATORY, \
    TIME_OFF, CREDIT_HOUR
from irhrs.leave.models import MasterSetting
from irhrs.leave.models.rule import CompensatoryLeave, CompensatoryLeaveCollapsibleRule
from irhrs.leave.views.master_setting_import_export import MasterSettingExportView, \
    MasterSettingImportView
from irhrs.organization.api.v1.tests.factory import OrganizationFactory


class MasterSettingImportExportTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.master_setting = MasterSettingFactory()
        self.organization = self.master_setting.organization

        self.general_leave_type = LeaveTypeFactory(
            name="General Leave",
            category=GENERAL,
            master_setting=self.master_setting
        )
        self.required_depletion_1 = LeaveTypeFactory(name="depletion1",
                                                     master_setting=self.master_setting)
        self.required_depletion_2 = LeaveTypeFactory(name="depletion2",
                                                     master_setting=self.master_setting)
        self.offday_inclusive_type_1 = LeaveTypeFactory(name="offday_inclusive_type_1",
                                                        master_setting=self.master_setting)
        self.offday_inclusive_type_2 = LeaveTypeFactory(name="offday_inclusive_type_2",
                                                        master_setting=self.master_setting)

        self.rule1 = LeaveRuleFactory(name="Casual Leave",
                                      leave_type=self.general_leave_type,
                                      depletion_leave_types=[self.required_depletion_1,
                                                             self.required_depletion_2])
        for order, leave_type in enumerate(
            [self.offday_inclusive_type_1, self.offday_inclusive_type_2]
        ):
            self.rule1.adjacent_offday_inclusive_leave_types.create(
                leave_rule=self.rule1,
                order_field=order,
                leave_type=leave_type
            )
        self.rule1_renewal = RenewalRuleFactory(rule=self.rule1)

        self.rule2 = LeaveRuleFactory(
            name="Acc Leave", leave_type=self.general_leave_type)
        self.rule2_accumulation = AccumulationRuleFactory(rule=self.rule2)

        self.rule3 = LeaveRuleFactory(
            name="Deduction", leave_type=self.general_leave_type)
        self.rule3_deduction = DeductionRuleFactory(rule=self.rule3)

        self.yos_type = LeaveTypeFactory(
            name="YOS Category",
            category=YEARS_OF_SERVICE,
            master_setting=self.master_setting
        )
        self.rule4 = LeaveRuleFactory(name="YOS", leave_type=self.yos_type)
        self.rule4_yos = YearsOfServiceRuleFactory(rule=self.rule4)

        self.compensatory_type = LeaveTypeFactory(
            name="Compensatory Leave",
            category=COMPENSATORY,
            master_setting=self.master_setting
        )
        self.rule5 = LeaveRuleFactory(
            name="Compensatory", leave_type=self.compensatory_type)
        self.rule5_compensatory = CompensatoryLeaveRuleFactory(rule=self.rule5)

        self.rule5_collapsible = CompensatoryLeaveCollapsibleRuleFactory(
            rule=self.rule5   
        )

        self.time_off_type = LeaveTypeFactory(
            name="Time Off",
            category=TIME_OFF,
            master_setting=self.master_setting
        )
        self.rule6 = LeaveRuleFactory(
            name="Time Off Rule", leave_type=self.time_off_type)
        self.rule6_time_off = TimeOffRuleFactory(rule=self.rule6)

        self.credit_hour_type = LeaveTypeFactory(
            name="credit hour",
            category=CREDIT_HOUR,
            master_setting=self.master_setting
        )
        self.rule7 = LeaveRuleFactory(
            name='credit hour rule', leave_type=self.credit_hour_type)
        self.rule7_credit_hour = CreditHourRuleFactory(rule=self.rule7)

        self.rule8 = LeaveRuleFactory(
            name='Irregularity Rule', leave_type=self.general_leave_type)
        self.rule8_irregularity_rule = LeaveIrregularitiesRuleFactory(
            leave_rule=self.rule8)

        self.target_organization = OrganizationFactory()

    def test_import_export(self):
        dump_data = MasterSettingExportView.dump_leave_data(
            self.master_setting)

        # to test export store it in file
        with NamedTemporaryFile(suffix='.pikle') as fp:
            fp.write(dump_data)
            fp.seek(0)

            MasterSettingImportView.load_master_setting(
                self.target_organization,
                "New Master Settings",
                fp
            )

        # assertions
        new_master_setting = MasterSetting.objects.filter(
            organization=self.target_organization
        ).idle().first()
        self.assertIsNone(new_master_setting.effective_from)
        self.assertIsNone(new_master_setting.effective_till)
        self.assertIsNotNone(
            new_master_setting,
            MasterSetting.objects.filter(organization=self.target_organization)
        )

        general_leave_type = new_master_setting.leave_types.filter(
            name=self.general_leave_type.name
        ).first()

        self.assertIsNotNone(general_leave_type,
                             new_master_setting.leave_types.all())

        rule1 = general_leave_type.leave_rules.filter(
            name=self.rule1.name).first()
        self.assertIsNotNone(rule1, general_leave_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule1, 'renewal_rule', None))
        depletion_types = set(
            rule1.depletion_leave_types.all().values_list('name', flat=True))

        self.assertEqual(
            depletion_types,
            {self.required_depletion_1.name, self.required_depletion_2.name}
        )

        offday_inclusive_leave_types = list(
            rule1.adjacent_offday_inclusive_leave_types.all().values_list(
                'leave_type__name', flat=True
            )
        )

        self.assertEqual(
            offday_inclusive_leave_types,
            [self.offday_inclusive_type_1.name, self.offday_inclusive_type_2.name]
        )

        rule2 = general_leave_type.leave_rules.filter(
            name=self.rule2.name).first()
        self.assertIsNotNone(rule2, general_leave_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule2, 'accumulation_rule', None))

        rule3 = general_leave_type.leave_rules.filter(
            name=self.rule3.name).first()
        self.assertIsNotNone(rule3, general_leave_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule3, 'deduction_rule', None))

        yos_type = new_master_setting.leave_types.filter(
            name=self.yos_type.name
        ).first()
        self.assertIsNotNone(yos_type, new_master_setting.leave_types.all())
        rule4 = yos_type.leave_rules.filter(name=self.rule4.name).first()
        self.assertIsNotNone(rule4, yos_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule4, 'yos_rule', None))

        compensatory_type = new_master_setting.leave_types.filter(
            name=self.compensatory_type.name
        ).first()
        self.assertIsNotNone(
            compensatory_type, new_master_setting.leave_types.all())
        rule5 = compensatory_type.leave_rules.filter(
            name=self.rule5.name).first()
        self.assertIsNotNone(rule5, compensatory_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule5, 'compensatory_rules', None))
        self.assertTrue(CompensatoryLeave.objects.filter(rule=rule5).exists())

        self.assertIsNotNone(
            compensatory_type, new_master_setting.leave_types.all()
        )
        self.assertIsNotNone(rule5, compensatory_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule5, 'leave_collapsible_rule', None))
        self.assertTrue(CompensatoryLeaveCollapsibleRule.objects.filter(rule=rule5).exists())

        time_off_type = new_master_setting.leave_types.filter(
            name=self.time_off_type.name
        ).first()
        self.assertIsNotNone(
            time_off_type, new_master_setting.leave_types.all())
        rule6 = time_off_type.leave_rules.filter(name=self.rule6.name).first()
        self.assertIsNotNone(rule6, time_off_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule6, 'time_off_rule', None))

        credit_hour_type = new_master_setting.leave_types.filter(
            name=self.credit_hour_type.name
        ).first()
        self.assertIsNotNone(
            credit_hour_type, new_master_setting.leave_types.all())
        rule7 = credit_hour_type.leave_rules.filter(
            name=self.rule7.name).first()
        self.assertIsNotNone(rule7, credit_hour_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule7, 'credit_hour_rule', None))

        rule8 = general_leave_type.leave_rules.filter(
            name=self.rule8.name).first()
        self.assertIsNotNone(rule7, general_leave_type.leave_rules.all())
        self.assertIsNotNone(getattr(rule8, 'leave_irregularity', None))

from datetime import date
from irhrs.leave.models.settings import MasterSetting
from irhrs.leave.tasks import expire_master_settings, get_active_master_setting
from irhrs.attendance.models.breakout_penalty import BreakOutPenaltySetting
from irhrs.common.api.tests.common import BaseTestCase
from unittest.mock import patch

from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.leave.api.v1.tests.factory import LeaveTypeFactory, MasterSettingFactory

class TestMasterSettingExpirationHooks(BaseTestCase):
    
    def test_penalty_setting_leave_types_autoremoved(self):
        organization = OrganizationFactory()
        master_setting_active = MasterSettingFactory(
            effective_from=date(2020, 1, 1), 
            effective_till=date(2020, 12, 31)
        )
        leave_types = [LeaveTypeFactory(master_setting=master_setting_active) for _ in range(4)]

        penalty_setting = BreakOutPenaltySetting.objects.create(
            organization=organization, 
            title="Penalty Setting"
        )
        for leave_type in leave_types:
            penalty_setting.leave_types_to_reduce.create(leave_type_to_reduce=leave_type)

        with patch('irhrs.core.utils.common.get_today', return_value=date(2020, 12, 31)):
            expire_master_settings()

        self.assertEqual(penalty_setting.leave_types_to_reduce.count(), 4)

        with patch('irhrs.core.utils.common.get_today', return_value=date(2021, 1, 2)):
            expire_master_settings()
        self.assertEqual(penalty_setting.leave_types_to_reduce.count(), 0)

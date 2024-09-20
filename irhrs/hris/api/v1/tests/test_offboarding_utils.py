from unittest import TestCase

from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmployeeSeparationSerializer
from irhrs.hris.constants import LEAVE_REVIEWED, ATTENDANCE_REVIEWED
from irhrs.hris.models import EmployeeSeparation, EmployeeSeparationType


class TestEmployeeSeparationStatus(TestCase):

    def test_separation_status(self):
        offboarding_instance = EmployeeSeparation(
            separation_type=EmployeeSeparationType(
                **{
                    'display_leave': True,
                    'display_payroll': True,
                    'display_attendance_details': True,
                    'display_pending_tasks': True,
                }
            )
        )
        sequence = EmployeeSeparationSerializer.get_separation_sequence(offboarding_instance)
        self.assertIn(LEAVE_REVIEWED, sequence)

        offboarding_instance.separation_type.display_leave = False
        sequence = EmployeeSeparationSerializer.get_separation_sequence(offboarding_instance)
        self.assertNotIn(LEAVE_REVIEWED, sequence)

        sequence = EmployeeSeparationSerializer.get_separation_sequence(offboarding_instance)
        self.assertIn(ATTENDANCE_REVIEWED, sequence)

        offboarding_instance.separation_type.display_attendance_details = False
        sequence = EmployeeSeparationSerializer.get_separation_sequence(offboarding_instance)
        self.assertNotIn(ATTENDANCE_REVIEWED, sequence)

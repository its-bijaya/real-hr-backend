from django.urls import path

from irhrs.attendance.views import AssignShiftToUserFromDate

app_name = 'attendance_admin'

urlpatterns = [
    path('assign-shift-from-date/<slug:organization>',
         AssignShiftToUserFromDate.as_view(),
         name='assign_shift_from_date')
]

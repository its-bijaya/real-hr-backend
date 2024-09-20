from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.db import IntegrityError, transaction
from django_q.tasks import async_task

from irhrs.attendance.forms import AssignShiftToUserFromDateForm
from irhrs.attendance.models import IndividualAttendanceSetting, TimeSheet, IndividualUserShift
from irhrs.attendance.tasks.timesheets import populate_timesheet_for_user
from irhrs.core.mixins.admin import AdminFormMixin
from irhrs.core.utils.common import get_today


class AssignShiftToUserFromDate(AdminFormMixin):
    form_class = AssignShiftToUserFromDateForm
    extra_context = {
        "title": "Assign Work Shift To User From Given Date"
    }
    success_url = reverse_lazy('admin:attendance_workshift_changelist')

    def form_valid(self, form):
        work_shift = form.cleaned_data.get('work_shift')
        users = form.cleaned_data.get('users')
        from_date = form.cleaned_data.get('from_date')
        try:
            self.assign_shift(users, from_date, work_shift)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        except IntegrityError:
            form.add_error(
                None,
                "Cannot assign work shift to user! User already has timesheet or work shift."
            )
            return self.form_invalid(form)
        return super().form_valid(form)

    @staticmethod
    @transaction.atomic
    def assign_shift(users, from_date, work_shift):
        applicable_from = work_shift.work_days.first().applicable_from or from_date
        if from_date >= get_today():
            raise ValidationError("From date must be past date.")
        if from_date < applicable_from:
            from_date = applicable_from
        if not (isinstance(users, QuerySet) or isinstance(users, list)):
            users = [users]
        for user in users:
            if user.detail.joined_date > from_date:
                raise ValidationError(
                    f"Cannot assign work shift before joined date for {user}"
                )
            setting = IndividualAttendanceSetting.objects.filter(
                user=user
            ).first()
            individual_user_shift = IndividualUserShift.objects.filter(
                individual_setting=setting,
                shift=work_shift,
                applicable_from__lte=from_date
            ).exists() if setting else False

            timesheet = TimeSheet.objects.filter(
                timesheet_user=user,
                work_shift=work_shift,
                timesheet_for__lte=from_date
            ).exists()
            if any([timesheet, individual_user_shift]):
                raise ValidationError(
                    "Cannot assign work shift to user! User already has timesheet or work shift."
                )
            if not setting:
                raise ValidationError(
                    "Cannot assign work shift to user! No individual user setting found."
                )
            IndividualUserShift.objects.create(
                individual_setting=setting,
                shift=work_shift,
                applicable_from=from_date
            )
            async_task(populate_timesheet_for_user, user, from_date, get_today())

    def get_form_kwargs(self, ):
        kw = super(AssignShiftToUserFromDate, self).get_form_kwargs()
        kw['slug'] = self.kwargs.get('organization')
        return kw

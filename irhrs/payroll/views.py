import pickle
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse_lazy

from irhrs.core.mixins.admin import AdminFormMixin
from irhrs.core.utils.common import get_today
from irhrs.payroll.forms import HeadingExportForm, HeadingImportForm
from irhrs.payroll.models import Heading, HeadingDependency

logger = logging.getLogger(__name__)

heading_fields = [
    "name",
    "verbose_name",
    "type",
    "payroll_setting_type",
    "duration_unit",
    "taxable",
    "benefit_type",
    "absent_days_impact",
    "year_to_date",
    "hourly_heading_source",
    "deduct_amount_on_leave",
    "pay_when_present_holiday_offday",
    "deduct_amount_on_remote_work",
    "order",
    "is_editable",
    "rules",
    "is_hidden",
    "visible_in_package_basic_view"
]


class HeadingExportView(AdminFormMixin):
    form_class = HeadingExportForm
    extra_context = {
        "title": "Export Heading"
    }

    def form_valid(self, form):
        organization = form.cleaned_data.get('organization')
        filename = f'{organization.name} - {get_today()} - Headings'
        return self.get_pickle_response(self.dump_payroll_data(organization), filename)

    @staticmethod
    def dump_payroll_data(organization):
        dump_data = list()
        for heading in organization.headings.order_by('order'):
            heading_data = {
                field: getattr(heading, field, None)
                for field in heading_fields
            }
            dump_data.append(heading_data)
        return pickle.dumps(dump_data)

    @staticmethod
    def get_pickle_response(content, filename):
        response = HttpResponse(
            content,
            content_type="application/octet-stream",
        )
        response['Content-Disposition'] = \
            f'attachment; filename="{filename}.pickle"'
        return response


class HeadingImportView(AdminFormMixin):
    form_class = HeadingImportForm
    extra_context = {
        "title": "Import Heading"
    }
    success_url = reverse_lazy('admin:payroll_heading_changelist')

    def form_valid(self, form):
        organization = form.cleaned_data.get('organization')
        import_file = form.cleaned_data.get('import_file')
        try:
            self.load_heading(import_file, organization)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return super().form_valid(form)

    @staticmethod
    def load_heading(import_file, organization):
        try:
            headings = pickle.load(import_file)
            with transaction.atomic():
                for heading_data in headings:
                    instance = Heading(organization=organization)
                    for attr in heading_fields:
                        setattr(instance, attr, heading_data.get(attr))
                    is_valid, validator = instance.rule_is_valid()
                    if not is_valid:
                        logger.debug(validator.error_messages)
                        print(validator.error_messages)
                        non_field_errors = validator.error_messages.get('non_field_errors')
                        if non_field_errors:
                            error_msg = f"{heading_data.get('name')} {non_field_errors}"
                        raise ValidationError(
                           error_msg
                        )
                    instance.save()

                    if validator.actual_dependent_headings:
                        HeadingDependency.objects.bulk_create(
                            [
                                HeadingDependency(source=instance, target=target)
                                for target in validator.actual_dependent_headings
                            ]
                        )

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValidationError(
                'Corrupt File Loaded',
                code='invalid'
            )


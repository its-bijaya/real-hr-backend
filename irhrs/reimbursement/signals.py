# # This file has been included and commented
# # in ReimbursementConfig: ready()
# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# from irhrs.organization.models import FiscalYear
# from irhrs.reimbursement.models import AdvanceExpenseRequest
#
#
# @receiver(post_save, sender=AdvanceExpenseRequest)
# def create_advance_code(sender, instance, created, **kwargs):
#     if created:
#         organization = instance.employee.detail.organization
#         expense_request = AdvanceExpenseRequest.objects.filter(
#             employee__detail__organization=organization
#         ).exclude(id=instance.id)
#         # to check whether there is any existing expense request or not
#         if not expense_request:
#             new_code = organization.reimbursement_setting.advance_code
#         else:
#             fiscal_year = FiscalYear.objects.current(organization)
#
#             request_for_fiscal_year = expense_request.filter(
#                 created_at__range=(fiscal_year.applicable_from, fiscal_year.applicable_to)
#             ).order_by('created_at')
#             if not request_for_fiscal_year:
#                 new_code = 1
#             else:
#                 last_request = request_for_fiscal_year.last()
#                 new_code = last_request.advance_code + 1
#         instance.advance_code = new_code
#         instance.save()

# import multiprocessing
# import random
# import datetime
# from timeit import default_timer as timer
# from dateutil.relativedelta import relativedelta

# from faker import Faker

# from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
# from irhrs.payroll.models import ReportRowRecord
# from irhrs.organization.api.v1.tests.factory import OrganizationFactory
# from irhrs.payroll.tests.factory import (
#     ReportRowRecordFactory,
#     PackageFactory,
#     EmployeePayrollFactory,
#     HeadingFactory,
#     PayrollFactory
# )
# from irhrs.users.api.v1.tests.factory import SimpleUserFactory

# def perform_create_report_row(employee_payrolls, users, start_year, heading) :
#     start = timer()
#     report_rows = []
#     # --- for each year
#     for year in range(5):
#         # ---- for each month
#         for month in range(12):
#             from_date = start_year.replace(month=month+1)
#             to_date = from_date + relativedelta(days=31)
#             for index, user in enumerate(users):
#                 # -- populate ReportRowRecord all users for the current month
#                 repord_row = ReportRowRecord(
#                     employee_payroll=employee_payrolls[index],
#                     from_date=from_date,
#                     to_date=to_date,
#                     heading=heading,
#                     amount=random.randint(10000, 50000)
#                 )
#                 report_rows.append(repord_row)
#     ReportRowRecord.objects.bulk_create(report_rows)
#     end = timer()
#     print(f"Time taken to populate reportrows for all users in org = {end-start}")

# class TestReportRowRecordIndex(RHRSTestCaseWithExperience):
#     users = [
#         ('hr@email.com', 'secret', 'Male', 'Programmer'),
#         ('finance@email.com', 'secret', 'Female', 'Accountant'),
#         ('general@email.com', 'secret', 'Male', 'General Manager')
#     ]
#     organization_name = 'Organization'

#     def setUp(self):
#         super().setUp()
#         self.user1 = self.created_users[1]
#         self.user2 = self.created_users[2]
#         self.client.force_login(self.admin)


#     def create_fake_report_row(self, organizations):
#         fake = Faker()

#         start_year = datetime.datetime(2020, 1, 1)
#         pool = multiprocessing.Pool(processes=4)
#         # we need manager list for sharing list among processes
#         processes = []
#     # ---- for each organization
#         for organization in organizations:
#             org_start = timer()
#             # Each organization has 1000 users
#             users = SimpleUserFactory.create_batch(1000, _organization=organization)
#             package = PackageFactory(
#                 organization=organization
#             )
#             heading = HeadingFactory(
#                 organization=organization
#             )
#             payroll = PayrollFactory(
#                 organization=organization
#             )
#             employee_payrolls = []
#             start = timer()
#             for user in users:
#                 emp_payroll = EmployeePayrollFactory(
#                     employee=user,
#                     payroll=payroll,
#                     package=package
#                 )
#                 employee_payrolls.append(emp_payroll)
#             end = timer()
#             print(f"time taken to create {len(users)} employee_payroll = {end-start}")
#             kwargs = dict(
#                 employee_payrolls=employee_payrolls,
#                 users=users,
#                 start_year=start_year,
#                 heading=heading,
#             )
#             # create report row in new process
#             pool.apply_async(perform_create_report_row, kwds=kwargs)
#             org_loop_end = timer()
#             print(f"Org loop time: {org_loop_end - org_start}")
#         pool.close()
#         pool.join()
#         print(f"Total report rows in DB = {ReportRowRecord.objects.all().count()}")


#     def test_x(self):
#         start = timer()
#         organizations = OrganizationFactory.create_batch(3)
#         report_rows = self.create_fake_report_row(organizations)
#         end = timer()
#         print("Total time elapsed: ", end-start)

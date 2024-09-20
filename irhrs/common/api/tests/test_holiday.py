"""
All tests related to holiday are created here.
Currently, the following tests are present.
i. Holiday Category.
"""
# from django.urls import reverse
# from rest_framework import status
#
# from irhrs.common.models import HolidayCategory
# from irhrs.users.models import User
# from ...api.tests.common import RHRSAPITestCase

#  TODO: @Shital sir revamp this test case according to new changes
# class PrivateTestCase(RHRSAPITestCase):
#     """
#     A private test case for DRY test cases
#     """
#     organization_name = "Necrophos"
#     users = [
#         ('admin@gmail.com', 'hellonepal', 'Male'),
#         ('luffy@onepiece.com', 'passwordissecret', 'Female'),
#         ('guest@admin.com', 'guestnotallowed', 'Other')
#     ]
#
#     def setUp(self):
#         super().setUp()
#         self.client.login(email=self.users[0][0], password=self.users[0][1])
#         self.users = User.objects.all()
#
#     def url(self, **kwargs):
#         create = not bool(kwargs.get('slug'))
#         if self.require_organization:
#             kwargs.update({'organization_slug': self.organization.slug})
#         if create:
#             return reverse('api_v1:{0}:{1}-list'.format(
#                 self.app_name, self.base_name), kwargs=kwargs)
#         return reverse('api_v1:{0}:{1}-detail'.format(
#             self.app_name, self.base_name), kwargs=kwargs)
#
#     def do_create(self, data):
#         return self.client.post(self.url(), data=data)
#
#     def create_url(self, **kwargs):
#         if self.require_organization:
#             kwargs.update({'organization_slug': self.organization.slug})
#         return reverse('api_v1:{0}:{1}-list'.format(
#             self.app_name, self.base_name), kwargs=kwargs)
#
#     def update_url(self, **kwargs):
#         if self.require_organization:
#             kwargs.update({'organization_slug': self.organization.slug})
#         return reverse('api_v1:{0}:{1}-detail'.format(
#             self.app_name, self.base_name), kwargs=kwargs)
#
#
# class HolidayCategoryTestCase(PrivateTestCase):
#     app_name = 'commons'
#     base_name = 'holiday-category'
#     require_organization = False
#
#     def test_create(self):
#         data = {'name': 'New Holiday Category',
#                 'description': 'New Holiday Description'}
#         response = self.do_create(data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         for key, value in data.items():
#             self.assertEqual(value, response.data.get(key))
#
#     def test_delete(self):
#         data = {
#             'name': 'Festival'
#         }
#         self.do_create(data)
#         self.client.delete(self.url(slug='festival'))
#
#     def test_update(self):
#         data = {
#             'name': 'Bakr Id'
#         }
#         new_data = {
#             'name': 'Bakhr Eid',
#             'description': 'Festival of Eid'
#         }
#         self.do_create(data)
#         response = self.client.put(self.url(slug='bakr-id'),
#                                    data=new_data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         for key, values in new_data.items():
#             self.assertEqual(values, response.data.get(key))
#         response = self.client.patch(self.url(slug='bakr-id'),
#                                      data={'description': 'New Description'})
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data.get('description'), 'New Description')
#
#     def test_list(self):
#         HolidayCategory.objects.all().delete()
#         # Create Multiple
#         for count in range(100):
#             data = {'name': 'Category {}'.format(count)}
#             response = self.do_create(data=data)
#         response = self.client.get(self.url())
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data.get('count'), 100)
#         self.assertIsNotNone(response.data.get('next'))

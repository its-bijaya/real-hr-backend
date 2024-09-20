# TODO: @Shital sir revamp this test case according to new changes
# import json
#
# from django.urls import reverse
# from rest_framework import status
#
# from ...api.tests.common import RHRSAPITestCase
#
#
# class ReligionEthnicityTestCase(RHRSAPITestCase):
#     organization_name = 'Aayulogic Pvt. Ltd.'
#     users = [
#         ('username@username.com', 'password', 'Male'),
#         ('usernametwo@username.com', 'password', 'Male'),
#     ]
#
#     def setUp(self):
#         super().setUp()
#         self.client.login(email='username@username.com',
#                           password='password')
#
#     def test_create_religion_ethnicity(self):
#         list_url = reverse('api_v1:commons:religion-ethnicity-list')
#         data = {
#             'name': 'Judaism',
#             'category': 'Religion'
#         }
#         response = self.client.post(list_url,
#                                     data=data)
#         self.assertEqual(response.status_code,
#                          status.HTTP_201_CREATED)
#         self.assertEqual(response.data.get('name'),
#                          data.get('name'))
#         self.assertEqual(response.data.get('category'),
#                          data.get('category'))
#         data = {
#             'name': 'ABCDEF',
#             'category': 'Ethnicity'
#         }
#         response = self.client.post(list_url,
#                                     data=data)
#         self.assertEqual(response.status_code,
#                          status.HTTP_201_CREATED)
#         self.assertEqual(response.data.get('name'),
#                          data.get('name'))
#         self.assertEqual(response.data.get('category'),
#                          data.get('category'))
#
#         # Invalid Data
#         data = {
#             'name': '',
#             'category': "Religion"
#         }
#         response = self.client.post(list_url,
#                                     data=data)
#         self.assertEqual(response.status_code,
#                          status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data.get('name')[0].__str__(),
#                          'This field may not be blank.')
#         data = {
#             'name': '',
#             'category': 'Ethnicity'
#         }
#         response = self.client.post(list_url, data=data)
#         self.assertEqual(response.status_code,
#                          status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data.get('name')[0].__str__(),
#                          'This field may not be blank.')
#
#         # Not dumping into str, and not sending application/json breaks the
#         # TestClient as it cannot parse the None Type. As the test is against,
#         # not nullable, it has been dumped into string and content_type is set.
#         data = json.dumps({
#             'name': 'XYZ ABC',
#             'category': None
#         })
#         response = self.client.post(list_url,
#                                     content_type='application/json',
#                                     data=data)
#         self.assertEqual(response.status_code,
#                          status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data.get('category')[0].__str__(),
#                          'This field may not be null.')
#
#     def test_list_ethnicity_religion(self):
#         list_url = reverse('api_v1:commons:religion-ethnicity-list')
#         response = self.client.get(list_url)
#         self.assertEqual(response.status_code,
#                          status.HTTP_200_OK)
#
#     def test_list_ethnicity(self):
#         list_url = reverse('api_v1:commons:religion-ethnicity-list') + \
#                    '?category=Ethnicity'
#         # Test Pagination
#         # Create 20+ data
#         import itertools
#         # Cycle through the categories as Religion, Ethnicity, Religion, . . .
#         cat = itertools.cycle(['Religion', 'Ethnicity'])
#         for name in range(100):
#             self.client.post(list_url,
#                              data={
#                                  'name': 'name_' + str(name),
#                                  'category': next(cat)
#                              })
#         response = self.client.get(list_url)
#         self.assertEqual(response.status_code,
#                          status.HTTP_200_OK)
#         self.assertNotIn('category', response.data.keys())
#         self.assertTrue(response.data.get('next'))
#
#     def test_list_religion(self):
#         list_url = reverse('api_v1:commons:religion-ethnicity-list') + \
#                    '?category=Religion'
#         response = self.client.get(list_url)
#         self.assertEqual(response.status_code,
#                          status.HTTP_200_OK)
#
#     def test_put_religion_ethnicity(self):
#         # Create
#         list_url = reverse('api_v1:commons:religion-ethnicity-list')
#         self.client.post(list_url, data={
#             "name": "Christianity",
#             "category": "Religion"
#         })
#         detail_url = reverse(
#             'api_v1:commons:religion-ethnicity-detail', kwargs={
#                 'slug': 'christianity'
#             })
#         response = self.client.put(detail_url, data={
#             'name': 'Hail Hitler',
#             'category': 'Ethnicity'
#         })
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertTrue(response.data.get('name'), 'Hail Hitler')
#         self.assertTrue(response.data.get('category'), 'Ethnicity')
#
#         response = self.client.put(detail_url, data={
#             'name': 'Raja Raam',
#             'category': 'Religion'
#         })
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertTrue(response.data.get('name'), 'Raja Raam')
#         self.assertTrue(response.data.get('category'), 'Religion')
#
#         response = self.client.put(detail_url, data={
#             'name': '',
#             'category': 'Religion'
#         })
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue(str(response.data.get('name')[0]),
#                         'This field may not be blank')
#
#     def test_delete_religion_ethnicity(self):
#         # Initially Create
#         list_url = reverse('api_v1:commons:religion-ethnicity-list')
#         self.client.post(list_url, data={
#             "name": "Christianity",
#             "category": "Religion"
#         })
#
#         # Now Delete
#         detail_url = reverse(
#             'api_v1:commons:religion-ethnicity-detail', kwargs={
#                 'slug': 'christianity'
#             })
#         response = self.client.delete(detail_url)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#
#         # Delete Non Existing URL
#         detail_url = reverse(
#             'api_v1:commons:religion-ethnicity-detail', kwargs={
#                 'slug': 'non-existent'
#             })
#         response = self.client.delete(detail_url)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

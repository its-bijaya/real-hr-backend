import json
import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.common.api.tests.common import RHRSUnitTestCase
from irhrs.organization.api.v1.tests.factory import EquipmentFactory, \
    EquipmentAssignedToFactory
from irhrs.core.utils.common import get_today
from irhrs.common.models.commons import EquipmentCategory
from irhrs.core.constants.common import TANGIBLE
from irhrs.core.constants.organization import IDLE, DAMAGED, USER, \
    DIVISION_BRANCH, MEETING_ROOM, USED
from irhrs.organization.api.v1.tests.factory import (OrganizationBranchFactory,
                                                     OrganizationDivisionFactory)
from irhrs.organization.models import OrganizationEquipment, EquipmentAssignedTo, \
    OrganizationBranch, MeetingRoom


class EquipmentAssignmentTest(RHRSUnitTestCase):
    def setUp(self):
        super().setUp()
        self.kwargs = {'organization_slug': self.organization.slug}
        self.category = EquipmentCategory.objects.create(
            name='Chair', type=TANGIBLE)
        OrganizationBranchFactory(organization=self.organization)
        OrganizationDivisionFactory(organization=self.organization)

    @property
    def assigned_equipments_list_url(self):
        return reverse(
            'api_v1:organization:assigned-equipment-list',
            kwargs=self.kwargs
        )

    @property
    def organization_equipments_list_url(self):
        return reverse(
            'api_v1:organization:organization-equipment-list',
            kwargs=self.kwargs
        )

    def test_adding_equipments_to_organization(self):
        equipment = self._create_organization_equipment()
        # adding equipment to an organization with similar code

        _data = {
            "name": "Monitor 123",
            "code": "1231",
            "brand_name": 'Apple Dot Come',
            "amount": 11111,
            "purchased_date": "2016-12-12",
            "service_order": "12312",
            "bill_number": "12312",
            "reference_number": "12312",
            "assigned_to": USER,
            "specifications": "",
            "equipment_picture": "",
            "remark": ""
        }

        self.data = _data

        response = self.client.post(self.organization_equipments_list_url,
                                    data=_data)
        self.assertEqual(response.status_code, 400)

        # validation for future purchased_date
        _data['code'] = '1212'
        _data['name'] = 'Monitor 1212'
        _data['purchased_date'] = timezone.now() + datetime.timedelta(days=10)
        response = self.client.post(self.organization_equipments_list_url,
                                    data=_data)
        self.assertEqual(response.status_code, 400)
        # self._update_of_organization_equipments(equipment)

    def test_list_of_organization_equipments(self):
        equipment = self._create_organization_equipment()
        equipments = OrganizationEquipment.objects.filter(
            organization=self.organization)
        response = self.client.get(self.organization_equipments_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(equipments.count(), response.data['count'])
        self._detail_of_organization_equipment(equipment)

    def _detail_of_organization_equipment(self, equipment):
        detail_url = reverse(
            'api_v1:organization:organization-equipment-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': equipment.slug
            })
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['slug'], equipment.slug)

    # def _update_of_organization_equipments(self, equipment):
    #     update_url = reverse(
    #         'api_v1:organization:organization-equipment-detail',
    #         kwargs={
    #             'organization_slug': self.organization.slug,
    #             'slug': equipment.slug
    #         }
    #     )
    #     response = self.client.patch(update_url, data={'status': DAMAGED})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data['status'], DAMAGED)
    #     self.assertNotEqual(equipment.status, response.data['status'])

    def _create_organization_equipment(self, data=None):
        if not data:
            data = {
                "name": "Monitor 123",
                "code": "1231",
                "amount": 11111,
                "purchased_date": "2016-12-12",
                "service_order": "12312",
                "bill_number": "12312",
                "reference_number": "12312",
                "assigned_to": USER,
                "specifications": "",
                "category": self.category.slug,
                "equipment_picture": "",
                "remark": ""
            }
        response = self.client.post(self.organization_equipments_list_url,
                                    data=data)
        self.assertEqual(response.status_code, 201)

        equipment = OrganizationEquipment.objects.get(
            id=response.data.get('id'))
        self.assertEqual(equipment.name, data.get('name'))
        self.assertEqual(equipment.category.slug, data.get('category'))

        return equipment

    def test_assign_equipment_to_user(self):
        """
        test for assigning equipment to employee
        :return:
        """
        user = self.USER
        equipment = self._create_organization_equipment()
        data = {
            'equipment': equipment.id,
            'user': user.id,
            'branch': '',
            'division': '',
            'meeting_room': '',
            'assigned_date': timezone.now() + datetime.timedelta(days=10)
        }
        user.detail.organization = self.organization
        user.detail.save()

        # to validate future assign date
        response = self.client.post(self.assigned_equipments_list_url,
                                    data=data)
        self.assertEqual(response.status_code, 400)

        # to validate whether equipment can be assigned or not with valida data
        data.update({
            'assigned_date': '2019-10-02'
        })
        response = self.client.post(self.assigned_equipments_list_url,
                                    data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user'], user.id)
        self.assertEqual(response.data['equipment'], equipment.id)

    def test_assign_equipment_to_division_and_branch(self):
        """
        test for assigning equipment to department and branch
        :return:
        """
        organization = self.organization
        division = organization.divisions.first()
        branch = OrganizationBranch.objects.create(
            organization=organization,
            branch_manager=None,
            name='Kathmandu',
            description='',
            contacts=json.dumps({
                'Mobile': '1234567890'
            }),
            email='',
            code='',
            mailing_address='',
        )
        equipment = self._create_organization_equipment(
            data={
                "name": "Monitor 123",
                "code": "1231456",
                "amount": 11111,
                "purchased_date": "2016-12-12",
                "service_order": "12312",
                "bill_number": "12312",
                "reference_number": "12312",
                "assigned_to": DIVISION_BRANCH,
                "specifications": "",
                "equipment_picture": "",
                "category": self.category.slug,
                "remark": "",
            }
        )
        data = {
            'equipment': equipment.id,
            'user': '',
            'branch': branch.slug,
            'division': division.slug,
            'meeting_room': '',
            'assigned_date': timezone.now() + datetime.timedelta(days=10)
        }

        # to validate future assign date
        response = self.client.post(self.assigned_equipments_list_url,
                                    data=data)
        self.assertEqual(response.status_code, 400)

        # to validate whether equipment can be assigned or not with valida data
        data.update({
            'assigned_date': '2019-10-02'
        })
        response = self.client.post(self.assigned_equipments_list_url,
                                    data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['division'], division.slug)
        self.assertEqual(response.data['branch'], branch.slug)
        self.assertEqual(response.data['equipment'], equipment.id)

    def test_assign_equipment_to_meeting_room(self):
        organization = self.organization
        branch = OrganizationBranch.objects.create(
            organization=organization,
            branch_manager=None,
            name='Kathmandu',
            description='',
            contacts=json.dumps({
                'Mobile': '1234567890'
            }),
            email='',
            code='',
            mailing_address='',
        )
        meeting_room = MeetingRoom.objects.create(
            organization=organization,
            branch=branch,
            name='Sagarmatha Hall',
            description='',
            location='Kathmandu',
            floor='First Floor',
            area='',
            capacity=1
        )

        equipment = self._create_organization_equipment(
            data={
                "name": "Monitor 123",
                "code": "1231456",
                "amount": 11111,
                "purchased_date": "2016-12-12",
                "service_order": "12312",
                "bill_number": "12312",
                "reference_number": "12312",
                "assigned_to": MEETING_ROOM,
                "specifications": "",
                "equipment_picture": "",
                "category": self.category.slug,
                "remark": ""
            }
        )
        future_date = (timezone.now() + datetime.timedelta(days=10)).date()
        data = {
            'equipment': equipment.id,
            'user': '',
            'branch': '',
            'division': '',
            'meeting_room': meeting_room.id,
            'assigned_date': '2019-10-02'
        }
        response = self.client.post(self.assigned_equipments_list_url,
                                    data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['meeting_room'], meeting_room.id)

    def test_list_of_equipment_category(self):
        equipment_category_url = reverse(
            'api_v1:commons:equipment-category-list')
        response = self.client.get(equipment_category_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EquipmentCategory.objects.count(),
                         response.data['count'])
        equipment_category_id = EquipmentCategory.objects.first().id
        self.assertTrue(
            filter(
                lambda x: x['id'] == equipment_category_id,
                response.data.get('results')
            )
        )

    def test_equipment_list_filters(self):
        laptop_category_data = {
            "name": "Monitor 123",
            "code": "1231",
            "amount": 11111,
            "purchased_date": "2016-12-12",
            "service_order": "12312",
            "bill_number": "12312",
            "reference_number": "12312",
            "assigned_to": USER,
            "specifications": "",
            "category": "laptop",
            "equipment_picture": "",
            "remark": ""
        }
        laptop_equipment = EquipmentFactory(
            category__name='laptop',
            organization=self.organization
        )
        response = self.client.get(
            self.organization_equipments_list_url +
            f"?category=laptop"
        )
        self.assertEqual(
            response.json()['count'],
            1
        )
        self.assertTrue(
            list(filter(
                lambda x: x['id'] == laptop_equipment.id,
                response.data.get('results')
            ))
        )

    def test_equipment_bulk_assign_works(self):
        laptop_equipment = EquipmentFactory(
            category__name='laptop',
            organization=self.organization
        )
        mobile_equipment = EquipmentFactory(
            category__name='mobile',
            organization=self.organization
        )
        user = self.USER
        self.bulk_assign_equipment_url = reverse(
            'api_v1:organization:assigned-equipment-bulk',
            kwargs=self.kwargs
        )
        repeated_data = {
            "assignments":
            [
                {
                    'equipment': laptop_equipment.id,
                    'user': user.id,
                    'branch': '',
                    'division': '',
                    'meeting_room': '',
                    'assigned_date': get_today()
                },
                {
                    'equipment': laptop_equipment.id,
                    'user': user.id,
                    'branch': '',
                    'division': '',
                    'meeting_room': '',
                    'assigned_date': get_today()
                }
            ]
        }
        response = self.client.post(
            self.bulk_assign_equipment_url,
            data=repeated_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['equipment'],
                         ['Multiple equipments cannot be assigned at the same time.']
                         )
        data = {
            "assignments":
            [
                {
                    'equipment': laptop_equipment.id,
                    'user': user.id,
                    'branch': '',
                    'division': '',
                    'meeting_room': '',
                    'assigned_date': get_today()
                },
                {
                    'equipment': mobile_equipment.id,
                    'user': user.id,
                    'branch': '',
                    'division': '',
                    'meeting_room': '',
                    'assigned_date': get_today()
                }
            ]
        }
        response = self.client.post(
            self.bulk_assign_equipment_url,
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        equipments_assigned_to_user = EquipmentAssignedTo.objects.filter(
            user=user
        )
        self.assertEqual(
            equipments_assigned_to_user.count(),
            2
        )

    def test_user_equipment_in_user_profile_works(self):
        """
        test if equipment list shows up correctly in user profile
        :return:
        """
        equipments = EquipmentAssignedToFactory.create_batch(
            2,
            user=self.USER,
            equipment__assigned_to=USER,
        )
        user_equipment_url = 'api_v1:users:user-equipment-list'
        user_equipments_url = reverse(
            user_equipment_url,
            kwargs={
                'user_id': self.USER.id
            })
        response = self.client.get(
            user_equipments_url
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 2)
        self.assertTrue(
            EquipmentAssignedTo.objects.filter(user=self.USER).count(),
            2
        )

    def test_user_equipment_history_works(self):
        """
        test if equipment assignment history shows up correctly
        :return:
        """
        past_equipment = EquipmentAssignedToFactory(
            user=self.USER,
            equipment__assigned_to=USER,
            equipment__organization=self.organization,
            assigned_date=get_today() - timezone.timedelta(days=5),
            released_date=get_today() - timezone.timedelta(days=3),
        )
        current_equipment = EquipmentAssignedToFactory(
            user=self.USER,
            equipment__assigned_to=USER,
            equipment__organization=self.organization,
            assigned_date=get_today() - timezone.timedelta(days=2),
        )
        equipment_history_name = 'api_v1:organization:organization-equipment-history'
        past_equipment_history_url = reverse(
            equipment_history_name,
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': past_equipment.equipment.slug
            }
        )
        response = self.client.get(
            past_equipment_history_url
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertTrue(
            EquipmentAssignedTo.objects.filter(
                user=self.USER,
                equipment=past_equipment.equipment
            ).count(),
            1
        )
        past_assignment = next(
            filter(lambda x: x['id'] == past_equipment.id,
                   response.json()['results']
                   ))
        self.assertEqual(
            past_assignment['assigned_date'],
            (get_today() - timezone.timedelta(days=5)).strftime('%Y-%m-%d')
        )
        self.assertEqual(
            past_assignment['released_date'],
            (get_today() - timezone.timedelta(days=3)).strftime('%Y-%m-%d')
        )
        current_equipment_history_url = reverse(
            equipment_history_name,
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': current_equipment.equipment.slug
            }
        )
        response = self.client.get(
            current_equipment_history_url
        )
        current_assignment = next(
            filter(lambda x: x['id'] == current_equipment.id,
                   response.json()['results']
                   ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertTrue(
            EquipmentAssignedTo.objects.filter(
                user=self.USER,
                equipment=current_equipment.equipment
            ).count(),
            1
        )
        self.assertEqual(
            current_assignment['released_date'],
            None
        )

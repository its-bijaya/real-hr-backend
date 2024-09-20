"""
HRIS-1415 HRIS>>Employees>>Assign KSAO
HRIS-1430 HRIS>>Employees>>Assign KSAO>>Assign bottom sheet (For bulk)
HRIS-1431 HRIS>>Employees>>Assign KSAO>>Edit (For single)
HRIS-1403 Normal User>>My Profile>>More>>KSAO
HRIS-1405 Normal User>>My Profile>>More>>KSAO>>Edit
"""
import random

from django.urls import reverse
from faker import Faker

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.common import KNOWLEDGE, SKILL, ABILITY, OTHER_ATTRIBUTES
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.permission.constants.permissions import HRIS_ASSIGN_KSAO_PERMISSION
from irhrs.users.models import UserKSAO

KSA_CHOICES = (KNOWLEDGE, SKILL, ABILITY, OTHER_ATTRIBUTES)


class KnowledgeSkillAbilityTestHelper:
    testing_models = [UserKSAO]
    users = [
        ('admin@ksao.com', 'hello', 'Male', 'JobTitleA'),
        ('user@ksao.com', 'hello', 'Male', 'JobTitleB')
    ]
    organization_name = 'KSAO Pvt. Ltd.'

    def setUp(self):
        super().setUp()
        self.fake = Faker()
        names = set()
        while len(names) < 10:
            names.add(self.fake.first_name())
        self._ksao = KnowledgeSkillAbility.objects.bulk_create(
            [
                KnowledgeSkillAbility(
                    name=name,
                    organization=self.organization,
                    ksa_type=random.choice(KSA_CHOICES),
                    slug=f"{name}-{i}".lower()
                ) for i, name in enumerate(names)
            ]
        )

    def validate_ksa(self, ksa_names, resp):
        # Validate that KSAO in response is included in sent names, and none others.
        self.assertEqual(
            set(
                map(
                    lambda ksa: ksa.get('ksa'),
                    resp.json().get('ksao')
                )
            ),
            set(ksa_names)  # This will verify old ones are deleted as well.
        )


class TestAssignKSAO(KnowledgeSkillAbilityTestHelper, RHRSTestCaseWithExperience):
    """
    Test Scenarios:
    (+) Admin Should be able to assign KSAO to an individual User.
    (+) Admin Should be able to view KSAO for an individual User.
    (+) Normal User should be able to view assigned KSAO for themselves.
    (-) Normal User Should not be able to assign KSAO for themselves.
    (-) Normal User Should receive PermissionDenied for other users' KSAO.
    """
    def test_assign_ksao(self):
        admin, normal = self.created_users
        url = reverse('api_v1:users:user-ksao-list', kwargs={'user_id': normal.id})
        self.client.force_login(admin)

        # Test Create
        random_ksas1 = random.choices(self._ksao, k=5)
        random_ksas2 = random.choices(self._ksao, k=5)
        """
        The implementation of KSAO is POST only.
        # The db_write is update_or_create. This covers the ability to update KSAOs.
        # The delete operation is done with the difference in db_ksao vs recieved_ksao.
       """
        for random_ksas in (random_ksas1, random_ksas2):
            payload = {
                'ksao': [
                    {
                        'ksa': slug,
                        'is_key': random.choice((True, False))
                    } for slug in [o.slug for o in random_ksas]
                ]
            }
            resp = self.client.post(url, data=payload, format='json')
            self.assertEqual(resp.status_code, self.status.HTTP_201_CREATED)

            # Validate the assigned ones is correct.
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, self.status.HTTP_200_OK)
            ksa_names = [o.name for o in random_ksas]
            self.validate_ksa(ksa_names, resp)

        # Validate the user can view.
        self.client.force_login(normal)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, self.status.HTTP_200_OK)
        self.validate_ksa(ksa_names, resp)

        # Validate the user can not post.
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, self.status.HTTP_403_FORBIDDEN,
                         "Normal User cannot assign KSAO")

        # Validate the user can not view other's ksao.
        resp = self.client.get(reverse('api_v1:users:user-ksao-list', kwargs={'user_id': admin.id}))
        self.assertEqual(resp.status_code, self.status.HTTP_403_FORBIDDEN,
                         "Normal user can't view other's KSAO.")


class TestBulkAssignKSAO(KnowledgeSkillAbilityTestHelper, RHRSTestCaseWithExperience):
    """
        Test Scenarios:
        (+) Admin Should be able to assign KSAO users in bulk.
        (+) Admin Should be able to override previously assigned KSAO for an user.
        (-) Normal User should receive a PermissionDenied for this page.
        """
    def test_assign_ksao(self):
        admin, normal = self.created_users
        url = reverse('api_v1:hris:ksao-list-list', kwargs={'organization_slug': self.organization.slug})
        self.client.force_login(admin)

        # Test Create
        random_ksas = random.choices(self._ksao, k=5)

        # Create new KSAO.
        payload1 = {
            'users': [admin.id, normal.id],
            'ksao': [
                {
                    'ksa': slug,
                    'is_key': random.choice((True, False))
                } for slug in [o.slug for o in random_ksas]
            ]
        }

        # Update KSAO/Delete KSAO/Update KSAO.
        """
        The users have already been assigned KSAOs. 
        Setting them here, should perform delete/create/update for new ones.
        """
        payload2 = {
            'users': [admin.id, normal.id],
            'ksao': [
                {
                    'ksa': slug,
                    'is_key': random.choice((True, False))
                } for slug in [o.slug for o in random_ksas]
            ]
        }

        for payload in (payload1, payload2):

            resp = self.client.post(url, data=payload, format='json')
            self.assertEqual(resp.status_code, self.status.HTTP_201_CREATED)
            # Validate the assigned ones is correct.
            for user in self.created_users:
                url = reverse('api_v1:users:user-ksao-list', kwargs={'user_id': user.id})
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, self.status.HTTP_200_OK)
                ksa_names = [o.name for o in random_ksas]
                self.validate_ksa(ksa_names, resp)

        self.client.force_login(normal)
        resp = self.client.post(url, data=payload1, format='json')
        self.assertEqual(
            resp.status_code,
            self.status.HTTP_403_FORBIDDEN,
            "Normal User should receive Forbidden Response for bulk-create page."
        )

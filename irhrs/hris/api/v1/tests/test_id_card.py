import factory
from factory.django import DjangoModelFactory
import os

from django.conf import settings
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase, FileHelpers
from irhrs.core.utils.common import get_today
from irhrs.hris.api.v1.serializers.id_card import get_user_details
from irhrs.hris.api.v1.tests.factory import IdCardTemplateFactory
from irhrs.hris.models import IdCard
from irhrs.users.api.v1.tests.factory import UserDetailFactory, UserFactory


class IdCardTest(RHRSAPITestCase):
    users = [("admin@gmail.com", "password", "Male")]
    organization_name = "TestOrg"

    def test_copy_user_details(self):
        user = UserFactory(
            _organization=self.organization
        )

        user.profile_picture.save('profile_pic.jpg', FileHelpers.get_image())
        user.signature.save('signature_u.jpg', FileHelpers.get_image())
        user.save()

        template = IdCardTemplateFactory(organization=self.organization)
        url = reverse('api_v1:hris:id-card-list', kwargs={
            'organization_slug': self.organization.slug
        })

        self.client.force_login(self.admin)
        post_data = {
            'template': template.id,
            'user': user.id,
            'issued_on': str(get_today())
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 201)

        instance = IdCard.objects.get(id=response.data.get('id'))
        user_details = get_user_details(user)
        for field, value in user_details.items():
            self.assertEqual(value, getattr(instance, field))

    def test_get_user_details(self):
        user = UserFactory(
            _organization=self.organization
        )

        user.signature.save('signature_u.jpg', FileHelpers.get_image())
        user.save()

        user_details = get_user_details(user, send_representation=True)
        self.assertEqual(user_details["full_name"], user.full_name)
        self.assertIsNone(user_details["profile_picture"])

        # this case added here because it caused 500 error in FE
        # add more cases if any error occurs
        # now try adding profile picture
        user.profile_picture.save('profile_pic.jpg', FileHelpers.get_image())

        user_details = get_user_details(user, send_representation=True)
        self.assertIsNotNone(user_details["profile_picture"])

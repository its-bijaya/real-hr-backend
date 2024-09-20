import os
import random
from random import randint

from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from rest_framework import status
from xhtml2pdf.document import pisaDocument

from irhrs.common.api.tests.factory import DocumentCategoryFactory
from irhrs.core.constants.common import ORGANIZATION
from irhrs.organization.api.v1.tests.setup import OrganizationSetUp
from irhrs.organization.api.v1.tests.factory import OrganizationDocumentFactory


class TestOrganizationDocument(OrganizationSetUp):
    files = []

    def setUp(self):
        super().setUp()
        self.generate_document()

    def tearDown(self) -> None:
        super().tearDown()
        for file in self.files:
            try:
                os.remove(file.name)
            except FileNotFoundError:
                pass

    def generate_document(self):
        category = DocumentCategoryFactory(associated_with=ORGANIZATION)
        for _ in range(randint(1, 10)):
            file = default_storage.open(f'test_{self.fake.word()}.pdf', 'wb')
            pisaDocument(
                f'{self.fake.text()}'.encode(),
                file
            )
            file.close()
            OrganizationDocumentFactory(
                organization=self.organization,
                category=category,
                attachment=self.file_path(file),
                is_public=random.choice([True, False])
            )
            self.files.append(file)

    @staticmethod
    def file_path(file):
        return os.path.join(
            settings.MEDIA_ROOT,
            file.name.split('media')[-1]
        )

    def test_organization_document(self):
        """
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        accessed by normal user
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.get(
            reverse(
                'api_v1:organization:organization-document-list',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        documents = self.organization.org_documents.filter(is_archived=False, is_public=True)
        self.assertEqual(response.json().get('count'), documents.count())
        results = response.json().get('results')
        for i, document in enumerate(documents):
            self.assertEqual(document.title, results[i].get('title'))
            self.assertEqual(document.slug, results[i].get('slug'))
            self.assertEqual(document.description, results[i].get('description'))
            self.assertEqual(document.organization_id, results[i].get('organization'))

    def test_user_can_acknowledge_ack_document(self):
        ack_document = OrganizationDocumentFactory(
            require_acknowledgement=True,
            is_downloadable=False,
            organization=self.organization
        )
        self.client.force_login(self.created_users[0])
        url = reverse(
            'api_v1:organization:organization-document-acknowledge',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': ack_document.slug
            }
        )
        resp = self.client.post(url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED
        )
        resp = self.client.post(url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST
        )

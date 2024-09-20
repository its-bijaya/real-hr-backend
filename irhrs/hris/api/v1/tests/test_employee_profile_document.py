import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from rest_framework import status
from xhtml2pdf.document import pisaDocument

from irhrs.common.api.tests.common import RHRSUnitTestCase
from irhrs.common.api.tests.factory import DocumentCategoryFactory
from irhrs.core.utils import nested_get, nested_getattr
from irhrs.users.api.v1.tests.factory import UserDocumentFactory
from irhrs.users.models.other import UserDocument


class TestEmployeeProfileDocument(RHRSUnitTestCase):
    files = []

    def setUp(self):
        super().setUp()
        self.create_documents_for_user()

    def create_users(self, count=10):
        return super().create_users(count=5)

    def tearDown(self) -> None:
        super().tearDown()
        for file in self.files:
            try:
                os.remove(file.name)
            except FileNotFoundError:
                pass

    @property
    def user_document_url(self):
        return reverse(
            'api_v1:users:user-document-list',
            kwargs=self.kwargs
        )

    @staticmethod
    def file_path(file):
        return os.path.join(
            settings.MEDIA_ROOT,
            file.name.split('media')[-1]
        )

    def create_documents_for_user(self):
        category = DocumentCategoryFactory(associated_with=self.organization)
        for user in self.SYS_USERS[1:]:
            file = default_storage.open(f'test_{self.fake.word()}.pdf', 'wb')
            pisaDocument(
                f'{self.fake.text()}'.encode(),
                file
            )
            file.close()
            UserDocumentFactory(
                user=user,  # whose file is being uploaded
                uploaded_by=self.USER,  # file uploader
                document_type=category,
                file=self.file_path(file),
            )
            self.files.append(file)

    def test_employee_profile_document(self):
        """
        test for viewing users document
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        viewing other documents as hr
        """
        user = self.SYS_USERS[0]
        documents = UserDocument.objects.filter(user=user)
        self.kwargs = {
            'user_id': user.id
        }
        response = self.client.get(
            self.user_document_url
        )
        self.validate_user_profile_document(response=response, documents=documents)

        """
        --------------------------------------------------------------------------------------------
        viewing employee profile document by other user who is not hr
        """
        self.client.force_login(user=self.SYS_USERS[2])
        response = self.client.get(
            self.user_document_url
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json().get('detail'),
            "You do not have permission to perform this action."
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee profile document by self
        """
        user = self.SYS_USERS[1]
        self.client.force_login(user=user)
        self.kwargs['user_id'] = user.id
        response = self.client.get(
            self.user_document_url
        )
        documents = UserDocument.objects.filter(user=user)
        self.validate_user_profile_document(response=response, documents=documents)

    def validate_user_profile_document(self, response, documents):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), documents.count())

        results = response.json().get('results')
        for index, document in enumerate(documents):
            self.assertEqual(
                nested_getattr(document, 'uploaded_by.id'),
                nested_get(results[index], 'uploaded_by.id'),
                ""
            )
            self.assertEqual(
                nested_getattr(document, 'document_type.slug'),
                nested_get(results[index], 'document_type.slug'),
                "Document type must be equal."
            )
            self.assertEqual(
                nested_getattr(document, 'slug'),
                nested_get(results[index], 'slug'),
                "Slug for document must be equal."
            )

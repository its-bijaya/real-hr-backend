"""
Here different models which are dependent to meeting model such as MeetingDocument, MeetingAgenda,
AgendaTask, MeetingAttendance, AgendaComment,etc are tested
"""
import os

from django.core.files.storage import default_storage
from django.urls import reverse
from rest_framework import status
from xhtml2pdf.document import pisaDocument

from irhrs.event.api.v1.tests.setup import MeetingSetup
from irhrs.event.models import AgendaComment, MeetingDocument


class TestMeetingDocuments(MeetingSetup):
    file = []

    def setUp(self):
        super().setUp()
        self.generate_document()

    def tearDown(self) -> None:
        super().tearDown()
        if self.file:
            for file in self.file:
                try:
                    os.remove(file.name)
                except FileNotFoundError:
                    continue

    @property
    def meeting_document_list_url(self):
        return reverse(
            "api_v1:event:meeting-document-list",
            kwargs=self.kwargs if self.kwargs else None
        )

    @property
    def meeting_document_detail_url(self):
        return reverse(
            "api_v1:event:meeting-document-detail",
            kwargs=self.kwargs
        )

    def test_meeting_document(self):
        """
        test for meeting document
        :return:
        """
        self._test_create_meeting_document()
        self._test_list_meeting_document()
        self._test_delete_meeting_document()

    def generate_document(self):
        file = default_storage.open(f'test_{self.fake.word()}.pdf', 'wb')
        pisaDocument(
            f'{self.fake.text()}'.encode(),
            file
        )
        file.close()
        self.file.append(file)

    def _test_create_meeting_document(self):
        self.kwargs = {
            'event_id': self.meeting.event_id
        }

        """
        by meeting organizer and minuter
        """
        for user in self.SYS_USERS[0:1]:
            self.client.force_login(user=user)
            with open(self.file[-1].name, 'rb') as file:
                response = self.client.post(
                    self.meeting_document_list_url,
                    data={
                        'document': file,
                        'meeting': self.meeting.id,
                        'caption': self.fake.text(max_nb_chars=200)
                    }
                )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            result = response.json()
            del result['document']
            self.validate_data(
                data=MeetingDocument.objects.filter(id=response.json().get('id')),
                results=[result]
            )

        """
        by meeting time keeper, members and non members
        """
        for user in self.SYS_USERS[2:8]:
            self.client.force_login(user=user)
            with open(self.file[-1].name, 'rb') as file:
                response = self.client.post(
                    self.meeting_document_list_url,
                    data={
                        'document': file,
                        'meeting': self.meeting.id,
                        'caption': self.fake.text(max_nb_chars=200)
                    }
                )

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _test_list_meeting_document(self):
        self.client.force_login(user=self.USER)
        for _ in range(4):
            self.generate_document()
            with open(self.file[-1].name, 'rb') as file:
                _ = self.client.post(
                    self.meeting_document_list_url,
                    data={
                        'document': file,
                        'meeting': self.meeting.id,
                        'caption': self.fake.text(max_nb_chars=200)
                    }
                )

        """
        trying to view by all user associated with meeting
        """
        for user in self.SYS_USERS[0:6]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_document_list_url
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results')
            for result in results:
                del result['document']

            self.validate_data(
                data=self.meeting.documents.all(),
                results=results,
            )

        """
        trying to view document by non member user
        """
        for user in self.SYS_USERS[6:-1]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_document_list_url
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _test_delete_meeting_document(self):
        document = self.meeting.documents.all()
        """
        by meeting organizer and minuter
        """
        for user in self.SYS_USERS[0:2]:
            self.kwargs.update(
                {
                    'pk': document.last().id
                }
            )
            self.client.force_login(user=user)
            response = self.client.delete(
                self.meeting_document_detail_url
            )
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        """
        by meeting time keeper, members and non members
        """
        for user in self.SYS_USERS[2:8]:
            self.kwargs.update(
                {
                    'pk': document.last().id
                }
            )
            self.client.force_login(user=user)
            response = self.client.delete(
                self.meeting_document_detail_url
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestMeetingAgenda(MeetingSetup):

    @property
    def meeting_agenda_url(self):
        action = 'detail' if 'pk' in self.kwargs else 'list'
        return reverse(
            f"api_v1:event:meeting-agenda-{action}",
            kwargs=self.kwargs if self.kwargs else None
        )

    def test_meeting_agenda(self):
        """
        test for meeting document
        :return:
        """

        self._test_list_meeting_agenda()
        self._test_retrieve_meeting_agenda()
        self._test_delete_meeting_agenda()
        self._test_update_meeting_agenda()

    def _test_retrieve_meeting_agenda(self):
        agenda = self.meeting.meeting_agendas.first()
        self.kwargs = {
            'event_id': self.meeting.event_id,
            'pk': agenda.id
        }

        """
        by meeting organizer, minuter, time keeper and members
        """
        for user in self.SYS_USERS[0:5]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_agenda_url,
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            result = response.json()
            self.validate_data(
                data=[agenda],
                results=[result]
            )

        """
        by users who are not member of event
        """
        for user in self.SYS_USERS[7:-1]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_agenda_url,
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _test_list_meeting_agenda(self):
        self.kwargs = {
            'event_id': self.meeting.event_id
        }
        """
        trying to view by all user associated with meeting
        """
        for user in self.SYS_USERS[0:6]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_agenda_url
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results')
            self.validate_data(
                data=self.meeting.meeting_agendas.all(),
                results=results,
            )

        """
        trying to view document by non member user
        """
        for user in self.SYS_USERS[6:-1]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_agenda_url
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _test_delete_meeting_agenda(self):
        agenda = self.meeting.meeting_agendas.all()
        """
        by meeting organizer and minuter
        """
        for user in self.SYS_USERS[0:2]:
            self.kwargs = {
                'event_id': self.meeting.event_id,
                'pk': agenda.last().id
            }
            self.client.force_login(user=user)
            response = self.client.delete(
                self.meeting_agenda_url
            )
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        """
        by meeting time keeper, members and non members
        """
        for user in self.SYS_USERS[2:8]:
            self.kwargs.update(
                {
                    'pk': agenda.last().id
                }
            )
            self.client.force_login(user=user)
            response = self.client.delete(
                self.meeting_agenda_url
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _test_update_meeting_agenda(self):
        agenda = self.meeting.meeting_agendas.first()
        self.kwargs = {
            'event_id': self.meeting.event_id,
            'pk': agenda.id
        }

        """
        by meeting organizer and minuter
        """
        for user in self.SYS_USERS[0:2]:
            self.client.force_login(user=user)
            response = self.client.patch(
                self.meeting_agenda_url,
                data={
                    'discussion': self.fake.text(max_nb_chars=100),
                    'decision': self.fake.text(max_nb_chars=100),
                    'discussed': True
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            result = response.json()
            self.validate_data(
                data=self.meeting.meeting_agendas.filter(id=agenda.id),
                results=[result]
            )

        """
        by time keeper and members of meeting and also users who are not member of event
        """
        for user in self.SYS_USERS[2:8]:
            self.client.force_login(user=user)
            response = self.client.patch(
                self.meeting_agenda_url,
                data={
                    'discussion': self.fake.text(max_nb_chars=100),
                    'decision': self.fake.text(max_nb_chars=100),
                    'discussed': True
                }
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestAgendaComment(MeetingSetup):

    def setUp(self):
        super().setUp()
        self.agenda = self.meeting.meeting_agendas.first()

    @property
    def meeting_agenda_comment_url(self):
        action = 'detail' if 'pk' in self.kwargs else 'list'
        return reverse(
            f"api_v1:event:agenda-comment-{action}",
            kwargs=self.kwargs if self.kwargs else None
        )

    def test_agenda_comment(self):
        self._test_add_agenda_comment()

    def _test_add_agenda_comment(self):
        self.kwargs = {
            'agenda_id': self.agenda.id
        }
        self.request_data = dict(
            path=self.meeting_agenda_comment_url,
            data={
                'content': self.fake.text()
            },
            format='json'
        )
        """
        by meeting organizer, minuter, time keeper and members
        """
        # when meeting is not prepared
        for user in self.SYS_USERS[0:5]:
            self.client.force_login(user=user)
            response = self.client.post(
                **self.request_data
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(
                response.json().get('detail'),
                'Making any comment until meeting is prepared'
            )

        # when meeting is prepared
        self.meeting.prepared = True
        self.meeting.save()
        for user in self.SYS_USERS[0:5]:
            self.client.force_login(user=user)
            response = self.client.post(
                **self.request_data
            )
            # import ipdb
            # ipdb.set_trace()
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            result = response.json()
            del result['created_at']
            self.validate_data(
                data=AgendaComment.objects.filter(id=result.get('id')),
                results=[result]
            )

        """
        by users who are not member of event
        """
        for user in self.SYS_USERS[7:-1]:
            self.client.force_login(user=user)
            response = self.client.post(
                **self.request_data
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self._test_list_agenda_comment()
        self._test_delete_agenda_comment()

    def _test_list_agenda_comment(self):
        """
        trying to view by all user associated with meeting
        """
        for user in self.SYS_USERS[0:6]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_agenda_comment_url
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results')
            for result in results:
                del result['created_at']
            self.validate_data(
                data=self.agenda.comments.all(),
                results=results,
            )

        """
        trying to view document by non member user
        """
        for user in self.SYS_USERS[6:-1]:
            self.client.force_login(user=user)
            response = self.client.get(
                self.meeting_agenda_comment_url
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _test_delete_agenda_comment(self):
        """
        trying to delete comment by own self
        :return:
        """
        comments = self.agenda.comments.exclude(created_by__in=self.SYS_USERS[:2])

        # trying to delete comment by meeting organizer
        self.client.force_login(user=self.USER)
        self.kwargs.update(
            {
                'pk': comments[0].id
            }
        )
        response = self.client.delete(
            self.meeting_agenda_comment_url
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # trying to delete comment by minuter
        self.client.force_login(user=self.SYS_USERS[1])
        self.kwargs.update(
            {
                'pk': comments[1].id
            }
        )
        response = self.client.delete(
            self.meeting_agenda_comment_url
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # trying to delete own comment
        commenter = comments[0].created_by
        self.client.force_login(user=commenter)
        self.kwargs.update(
            {
                'pk': comments[0].id
            }
        )
        response = self.client.delete(
            self.meeting_agenda_comment_url
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

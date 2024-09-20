from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.noticeboard import NORMAL_POST, DIVISION_NOTICE, \
    HR_NOTICE, ORGANIZATION_NOTICE
from irhrs.noticeboard.models import Post
from irhrs.users.models import UserDetail


class PostTestCase(RHRSTestCaseWithExperience):
    users = [('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
             ('hello@hello.com', 'secretThing', 'Male', 'Clerk')]
    organization_name = "Google"
    division_name = "Programming"
    division_ext = 123

    post_list_url = reverse('api_v1:noticeboard:post-list')

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])

    def test_normal_post(self):
        # try to create with blank content
        data = {
            'post_content': '',
            "category": NORMAL_POST
        }
        response = self.client.post(self.post_list_url, data=data)
        self.assertEqual(response.status_code, 400)

        # create with no content
        data.pop('category', None)
        response = self.client.post(self.post_list_url, data=data)
        self.assertEqual(response.status_code, 400)

        # create a post
        post = self._create_post()
        user = UserDetail.objects.get(user__email=self.users[0][0]).user
        self.assertEqual(post.posted_by, user)

        # check post in list
        response = self.client.get(self.post_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)

        # check post detail
        detail_url = reverse('api_v1:noticeboard:post-detail', kwargs={
            'pk': post.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('post_content'), post.post_content)

        # check update normal post
        data = {
            'post_content': 'This is test post update'
        }
        update = self._update_post(detail_url, data)
        self._delete_post(detail_url)

    def test_division_notice(self):
        data = {
            "post_content": "Division Notice",
            "category": DIVISION_NOTICE,
            "is_notice": True
        }
        post = self._create_post(data=data)

        # update test
        data = {
            "post_content": "New Division Notice"
        }
        update_url = reverse('api_v1:noticeboard:post-detail',
                             kwargs={
                                 'pk': post.id
                             })
        updated_data = self._update_post(update_url, data)
        self._delete_post(update_url)

    def test_organization_post(self):
        # test create organization post by normal user
        # this should return 400 because normal user cannot create organization notice
        data = {
            "post_content": "This is organization post.",
            "category": ORGANIZATION_NOTICE,
            "is_notice": True
        }
        response = self.client.post(self.post_list_url, data=data)
        if response.data.get('posted_by'):
            if get_user_model().objects.get(
                id=response.data.get('posted_by').get('id')
            ).groups.all().values('name')[0].get('name') == 'Admin':
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data.get('post_content'), data.get('post_content'))
        else:
            # if user is not admin then user is not allowed to post
            self.assertEqual(response.status_code, 400)

    def test_hr_post(self):
        # test create hr post
        # should return 400 if it is normal user because normal user is not allowed to create hr post
        data = {
            "post_content": "This is hr notice post.",
            "category": HR_NOTICE,
            "is_notice": True
        }
        response = self.client.post(self.post_list_url, data=data)
        if response.data.get('posted_by'):
            if get_user_model().objects.get(
                id=response.data.get('posted_by').get('id')
            ).groups.all().values('name')[0].get('name') == 'Admin':
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data.get('post_content'), data.get('post_content'))
        else:
            # if user is not admin then user is not allowed to post
            self.assertEqual(response.status_code, 400)

    def test_post_like(self):
        post = self._create_post()
        like_url = reverse('api_v1:noticeboard:post-like-list', kwargs={
            'post_id': post.id})
        post_detail_url = reverse('api_v1:noticeboard:post-detail', kwargs={
            'pk': post.id})
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])

        # like the post
        response = self.client.post(like_url, {'liked': True})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get('liked'))

        # likes count
        post_detail = self.client.get(post_detail_url)
        self.assertEqual(post_detail.status_code, 200)
        likes = post_detail.data.get('likes')
        self.assertEqual(likes.get('count'), 1)

        # now unlike it
        response = self.client.post(like_url, {'liked': False})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data.get('liked'))

        # again count
        post_detail = self.client.get(post_detail_url)
        self.assertEqual(post_detail.status_code, 200)
        likes = post_detail.data.get('likes')
        self.assertEqual(likes.get('count'), 0)

        # now test sending random data in like url
        response = self.client.post(like_url, {'sdfsdfs': 'ssssf'})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data.get('liked'))

        # now test sending random data in like
        response = self.client.post(like_url, {'liked': 'Null'})
        self.assertEqual(response.status_code, 400)

    def _update_post(self, update_url, data=None):
        # test post update
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, 200)

        updated_data = Post.objects.get(id=response.data.get('id'))
        self.assertEqual(updated_data.post_content, data.get('post_content'))

        return updated_data

    def _create_post(self, data=None):
        if not data:
            data = {
                "post_content": "This is a test post",
                "category": NORMAL_POST
            }
        response = self.client.post(self.post_list_url, data=data)
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(id=response.data.get('id'))
        self.assertEqual(post.post_content, data.get('post_content'))
        self.assertEqual(post.category, data.get('category'))

        return post

    def _delete_post(self, delete_url):
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 204)

from django.urls import reverse

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience

from irhrs.core.constants.noticeboard import NORMAL_POST
from irhrs.noticeboard.models import Post, PostComment
from irhrs.users.models import UserDetail


class CommentTestCase(RHRSTestCaseWithExperience):
    users = [('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager')]
    organization_name = "Google"
    organization_name = "Google"
    division_name = "Programming"
    division_ext = 123

    post_list_url = reverse('api_v1:noticeboard:post-list')

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.post = self._create_post()
        self.comment_list_url = reverse('api_v1:noticeboard:post-comment-list',
                                        kwargs={'post_id': self.post.id})
        self.userdetail = UserDetail.objects.get(user__email=self.users[0][0])

    def test_comment(self):
        data = {
            'content': 'This is first comment'
        }
        post_response = self.client.post(self.comment_list_url, data=data)
        self.assertEqual(post_response.status_code, 201)
        comment_id = post_response.data.get('id')
        comment = PostComment.objects.get(id=comment_id)
        self.assertEqual(comment.content, data.get('content'))
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.commented_by, self.userdetail.user)

        # like that comment
        like_url = reverse('api_v1:noticeboard:comment-like-list',
                           kwargs={
                               'comment_id': comment_id
                           })
        response = self.client.post(like_url, {'liked': True})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get('liked'))

        # unlike that comment
        response = self.client.post(like_url, {'liked': False})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data.get('liked'))
        self._comment_reply(comment_id)

        # test delete comment reply
        comment_delete_url = reverse('api_v1:noticeboard:post-comment-detail',
                                     kwargs={
                                         'post_id': self.post.id,
                                         'pk': post_response.data.get('id')
                                     })

        response = self.client.delete(comment_delete_url)
        self.assertEqual(response.status_code, 204)

    def _comment_reply(self, comment_id):
        # test comment reply
        comment_url = reverse('api_v1:noticeboard:comment-reply-list',
                              kwargs={
                                  'comment_id': comment_id
                              })
        data = {
            'reply': 'No you are wrong. This is second comment'
        }
        response = self.client.post(comment_url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data.get('reply'), data.get('reply'))

        # test delete comment reply
        comment_reply_delete_url = reverse('api_v1:noticeboard:comment-reply-detail',
                                           kwargs={
                                               'comment_id': comment_id,
                                               'pk': response.data.get('id')
                                           })

        response = self.client.delete(comment_reply_delete_url)
        self.assertEqual(response.status_code, 204)

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

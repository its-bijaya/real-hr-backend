from django.urls import reverse
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.users.models.experience import UserExperience

class UserStatusTestCase(RHRSTestCaseWithExperience):
    users = [
        ("user@aayu.com","pkpk", "male","user"),
        ("two@aayu.com","pk", "female","user")
    ]
    organization_name = "aayubank"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
    
    @property
    def user_auto_complete_url(self):
        return reverse(
            "api_v1:users:users-autocomplete-list",
        )
        
    def test_user_auto_complete(self):
        user = self.created_users[1]
        user_xp =UserExperience.objects.get(user=user)
        from irhrs.core.utils.common import get_today
        from datetime import timedelta
        user_xp.start_date = get_today() - timedelta(days=365)
        user_xp.end_date = user_xp.start_date + timedelta(days=1)
        user_xp.save()
        url= self.user_auto_complete_url + "?user_status=current"
        response=self.client.get(url)
       
        self.assertEquals(response.status_code,200,response.json())
        self.assertEquals(len(response.json()), 1, response.json())
        



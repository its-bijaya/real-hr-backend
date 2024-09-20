
from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from faker import Factory

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.common.api.tests.factory import BankFactory
from irhrs.common.models import ReligionAndEthnicity
from irhrs.core.constants.user import MARRIED, PARENT, TEMPORARY
from irhrs.core.utils.common import get_today
from irhrs.core.utils.subordinates import find_immediate_subordinates
from irhrs.hris.api.v1.tests.factory import ChangeTypeFactory
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory
from irhrs.organization.models import EmploymentStatus
from irhrs.recruitment.models import Country, Province, District
from irhrs.users.models import UserDetail, UserContactDetail, UserSupervisor, UserAddress
from irhrs.users.models.other import UserBank


class UserDetailTestCase(RHRSTestCaseWithExperience):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('hello@hello.com', 'secretThing', 'Male', 'Clerk'),
        ('helloa@hello.com', 'secretThing', 'Male', 'Clerka'),
        ('hellob@hello.com', 'secretThing', 'Male', 'Clerkb'),
        ('helloc@hello.com', 'secretThing', 'Male', 'Clerkc'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.today = get_today()
        self.user = get_user_model()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        # get user object
        self.user_check = self.user.objects.get(email=self.users[0][0])
        self.phone_one = '98898345'
        self.phone_two = '98898395'

    def test_user_detail(self):
        org_branch = OrganizationBranchFactory(organization=self.organization)
        change_type = ChangeTypeFactory(organization=self.organization)
        employment_status = EmploymentStatus.objects.create(
            title=self.fake.text(max_nb_chars=150),
            organization=self.organization,
            description=self.fake.text(max_nb_chars=500)
        )

        # update user experience information
        user_experience = self.user_check.current_experience
        user_experience.branch = org_branch
        user_experience.employment_status = employment_status
        user_experience.change_type = change_type
        user_experience.save()

        # create the contact details of users
        user_contact = UserContactDetail.objects.create(user=self.user_check,
                                                        number=self.phone_one,
                                                        email=self.users[0][0])
        # request for employee directory
        response = self.client.get(reverse(
            'api_v1:users:users-detail',
            kwargs={
                'user_id': self.user_check.id
            }
        ))
        # test all created data is accurate or not
        self.assertEqual(response.data.get('user').get('id'), self.user_check.id)
        self.assertEqual(parse(response.data.get('joined_date')).date(),
                         UserDetail.objects.get(
                             user=self.user_check.id).joined_date)
        self.assertEqual(response.data.get('self_contacts')[0].get('number'),
                         user_contact.number)
        self.assertEqual(response.data.get('self_contacts')[0].get('email'), self.users[0][0])
        self.assertEqual(response.data.get('current_experience').get('division').get('name'),
                         self.division_name)
        self.assertEqual(response.data.get('current_experience').get('branch').get('name'),
                         org_branch.name)
        self.assertEqual(
            response.data.get('current_experience').get('job_title').get('title'),
            self.users[0][3])
        self.assertEqual(response.data.get('current_experience').get('employment_status').get(
            'title'),
            employment_status.title)
        self.assertEqual(response.data.get('current_experience').get('current_step'),
                         user_experience.current_step)

        # get information of all users expect logged in user
        sys_user = self.user.objects.filter(
            email__in=[
                user[0] for user in self.users[1:]
            ]
        )

        # bulk create supervisor and subordinates
        bulk_create = list()
        for index, user in enumerate(sys_user):
            if index == 0:
                bulk_create.append(UserSupervisor(
                    user=self.user_check,
                    supervisor=user,
                    approve=True,
                    deny=True,
                    forward=False
                ))
            else:
                bulk_create.append(UserSupervisor(
                    user=user,
                    supervisor=self.user_check,
                    approve=True,
                    deny=True,
                    forward=False
                ))
        UserSupervisor.objects.bulk_create(bulk_create)

        # get list of subordinates
        subordinates = self.user.objects.filter(
            id__in=find_immediate_subordinates(self.user_check.id)
        )

        # get list of supervisor
        supervisor = self.user_check.first_level_supervisor
        url = reverse(
            'api_v1:users:users-detail',
            kwargs={
                'user_id': self.user_check.id
            }
        )

        # url to get response
        response_data = self.client.get(
            url,
            data={
                'send_supervisor': 'true',
                'send_subordinates': 'true'
            }
        )

        # test supervisor and subordinates are accurate
        self.assertEqual(response_data.data.get('first_level_supervisor').get('id'),
                         supervisor.id)
        self.assertEqual(len(response_data.data.get('sub_ordinates')), subordinates.count())
        response_subordinates = response_data.json().get('sub_ordinates')
        for i, subordinate in enumerate(subordinates):
            self.assertEqual(subordinate.id, response_subordinates[i].get('id'))
            self.assertEqual(response_subordinates[i].get('full_name'), subordinate.full_name)

    def test_general_information(self):
        """
        test the general information of user ,
        we create the religion and ethnicity of user
        """

        religion = ReligionAndEthnicity.objects.create(
            name=self.fake.name(),
            category="Religion"
        )
        ethnicity = ReligionAndEthnicity.objects.create(
            name=self.fake.name(),
            category="Religion"
        )
        user_detail = self.user_check.detail
        user_detail.ethnicity = ethnicity
        user_detail.religion = religion
        user_detail.save()

        # response url
        response = self.client.get(reverse(
            'api_v1:users:users-detail',
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        # test user detail
        self.assertEqual(response.data.get('religion').get('name'), religion.name)
        self.assertEqual(response.data.get('ethnicity').get('name'), ethnicity.name)
        self.assertEqual(response.data.get('user').get('first_name'),
                         self.user_check.first_name)
        self.assertEqual(response.data.get('user').get('middle_name'),
                         self.user_check.middle_name)
        self.assertEqual(response.data.get('user').get('last_name'),
                         self.user_check.last_name)
        self.assertEqual(response.data.get('gender'),
                         user_detail.gender)
        self.assertEqual(response.data.get('nationality'),
                         user_detail.nationality)
        self.assertEqual(response.data.get('marital_status'),
                         user_detail.marital_status)

        # now let's change the marital status
        user_detail.marital_status = MARRIED
        user_detail.marriage_anniversary = timezone.now().date() - timezone.timedelta(days=364)
        user_detail.save()

        # again response for marriage test
        response = self.client.get(reverse(
            'api_v1:users:users-detail',
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        # test marriage status
        self.assertEqual(response.data.get('marital_status'),
                         user_detail.marital_status)
        self.assertEqual(parse(response.data.get('marriage_anniversary')).date(),
                         user_detail.marriage_anniversary)

    def test_contact_details(self):
        """
        test contact information of user
        """

        # Here we create the contact information of user

        contact = {
            'user': self.user_check,
            'number': self.phone_one,
            'email': self.users[0][0],
            'address': self.fake.address(),
            'slug': self.fake.name()
        }

        # create normal contact
        normal_contact = UserContactDetail.objects.create(**contact)
        emergency = {
            'contact_of': PARENT,
            'number': self.phone_two,
            'emergency': True,
            'slug': self.fake.name()
        }

        # create emergency contact
        contact.update(emergency)
        emergency_contact = UserContactDetail.objects.create(**contact)

        # Here is the response from contact detail url
        response = self.client.get(reverse(
            'api_v1:users:user-contact-details-list',
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        # now we make sure that information is correct
        for contact in response.json().get('results'):
            self.assertEqual(contact.get('user').get('id'),
                             self.user_check.id)
            if contact.get('emergency') == emergency_contact.emergency:
                self.assertEqual(contact.get('address'),
                                 emergency_contact.address)
                self.assertEqual(contact.get('email'), emergency_contact.email)
                self.assertEqual(contact.get('number'),
                                 emergency_contact.number)
                self.assertEqual(contact.get('contact_of'),
                                 emergency_contact.contact_of)
                self.assertTrue(contact.get('emergency'))
            else:
                self.assertEqual(contact.get('address'),
                                 normal_contact.address)
                self.assertEqual(contact.get('email'), normal_contact.email)
                self.assertEqual(contact.get('number'),
                                 normal_contact.number)
                self.assertEqual(contact.get('contact_of'),
                                 normal_contact.contact_of)
                self.assertFalse(contact.get('emergency'))

    def test_address_detail(self):
        """
        test address detail of user
        """

        # create temporary address
        country = Country.objects.get(name="Nepal")
        user_temporary_address = UserAddress.objects.create(user=self.user_check,
                                                            address_type=TEMPORARY,
                                                            street=self.fake.street_name(),
                                                            city=self.fake.city(),
                                                            country_ref=country,
                                                            address=self.fake.address(),
                                                            latitude=self.fake.latitude(),
                                                            longitude=self.fake.longitude()
                                                            )

        # create permanent address by default address type is permanent
        user_permanent_address = UserAddress.objects.create(user=self.user_check,
                                                            street=self.fake.street_name(),
                                                            city=self.fake.city(),
                                                            country_ref=country,
                                                            address=self.fake.address(),
                                                            latitude=self.fake.latitude(),
                                                            longitude=self.fake.longitude()
                                                            )

        # response for permanent and temporary address of user
        response = self.client.get(reverse(
            'api_v1:users:user-address-list',
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        # here is the list of temporary and permanent address
        for user_address in response.data.get('results'):
            if user_address.get('address_type') == TEMPORARY:
                # test the temporary address of user
                self.assertEqual(user_address.get('address_type'),
                                 user_temporary_address.address_type)
                self.assertEqual(user_address.get('street'),
                                 user_temporary_address.street)
                self.assertEqual(user_address.get('city'),
                                 user_temporary_address.city)
                self.assertEqual(user_address.get('country').get('name'),
                                 user_temporary_address.country)
                self.assertEqual(user_address.get('address'),
                                 user_temporary_address.address)
                self.assertEqual(user_address.get('longitude'),
                                 float(user_temporary_address.longitude))
                self.assertEqual(user_address.get('latitude'),
                                 float(user_temporary_address.latitude))
            else:
                # test the permanent address of user
                self.assertEqual(user_address.get('address_type'),
                                 user_permanent_address.address_type)
                self.assertEqual(user_address.get('street'),
                                 user_permanent_address.street)
                self.assertEqual(user_address.get('city'),
                                 user_permanent_address.city)
                self.assertEqual(user_address.get('country').get('name'),
                                 user_permanent_address.country)
                self.assertEqual(user_address.get('address'),
                                 user_permanent_address.address)
                self.assertEqual(user_address.get('longitude'),
                                 float(user_permanent_address.longitude))
                self.assertEqual(user_address.get('latitude'),
                                 float(user_permanent_address.latitude))

    def test_overall_user_address(self):
        # test normal create method

        url = reverse(
            'api_v1:users:user-address-list',
            kwargs={
                'user_id': self.admin.id
            }
        ) + "?as=hr"
        country = Country.objects.get(name="Nepal")
        province = Province.objects.get(name="Bagmati Pradesh")
        district = District.objects.get(name="Lalitpur")
        india = Country.objects.get(name="India")
        payload = {
            "address_type": "Permanent",
            "street": "",
            "city": "",
            "country": country.id,
            "address": "lalitpur, lalitpur",
            "province": province.id,
            "district": district.id,
            "postal_code": 1234
        }

        response = self.client.post(
            url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            201
        )

        # update country beside Nepal and provide province and district; this should raise
        # validation error.
        patch_url = reverse(
            'api_v1:users:user-address-detail',
            kwargs={
                'user_id': self.admin.id,
                'pk': UserAddress.objects.first().id
            }
        ) + "?as=hr"
        new_payload = payload
        new_payload["country"] = india.id
        new_payload["address_type"] = "Temporary"

        response = self.client.patch(
            patch_url,
            data=new_payload,
            format="json"
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            ['Currently province and district is not supported.']
        )

        # select country Nepal and don't send province; this should raise
        # validation error.
        new_payload["province"] = None
        new_payload["country"] = country.id

        response = self.client.patch(
            patch_url,
            data=new_payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            response.json().get('non_field_errors'),
            ['Province/district is required while selecting Nepal.']
        )

        # select country Nepal and don't send district; this should raise
        # validation error.
        new_payload["province"] = province.id
        new_payload["district"] = None

        response = self.client.patch(
            patch_url,
            data=new_payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            response.json().get('non_field_errors'),
            ['Province/district is required while selecting Nepal.']
        )

        # send country Nepal, province and district. This should work fine.
        new_payload["province"] = province.id
        new_payload["district"] = district.id
        new_payload["address"] = "patan, lalitpur"

        response = self.client.patch(
            patch_url,
            data=new_payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_bank_information(self):
        """
        test bank detail of user
        """

        # create user bank detail
        bank = BankFactory()
        user_bank_detail = UserBank.objects.create(user=self.user_check, bank=bank,
                                                   account_number=self.fake.bban(),
                                                   branch=self.fake.address()
                                                   )
        # response from user bank info list
        response = self.client.get(reverse(
            'api_v1:users:user-bank-info',
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        self.assertEqual(response.data.get('bank').get('name'),
                         bank.name)
        self.assertEqual(response.data.get('branch'),
                         user_bank_detail.branch)
        self.assertEqual(response.data.get('account_number'),
                         user_bank_detail.account_number)

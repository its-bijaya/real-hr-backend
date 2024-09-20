import datetime

from factory.declarations import SubFactory
from irhrs.core.utils.common import get_today, get_tomorrow
from irhrs.core.constants.user import BACHELOR
from irhrs.recruitment.models import QuestionSet
from irhrs.users.api.v1.tests.factory import ExternalUserFactory, UserFactory
from irhrs.recruitment.constants import CANDIDATE_LETTER, JOB_STATUS_CHOICES, PENDING, SCREENED, \
    ASSESSMENT
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.common.api.tests.factory import DocumentCategoryFactory, IndustryFactory, JobBenefitFactory, SalaryFactory
from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, EmploymentLevelFactory, EmploymentStatusFactory, KnowledgeSkillAbilityFactory, OrganizationBranchFactory, OrganizationDivisionFactory, OrganizationFactory
from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.applicant import Applicant
from irhrs.recruitment.models.job_apply import JobApply, NoObjection, PostScreening, Assessment, \
    AssessmentAnswer, Interview, InterViewAnswer
import random
from irhrs.recruitment.models.common import Template

import factory
from factory.django import DjangoModelFactory

class ApplicantFactory(DjangoModelFactory):
    class Meta:
        model = Applicant

    user = factory.SubFactory(ExternalUserFactory)
    education_degree =  BACHELOR
    # skills = factory.SubFactory(KnowledgeSkillAbilityFactory)
    expected_salary = factory.SubFactory(SalaryFactory)


class JobFactory(DjangoModelFactory):
    class Meta:
        model = Job

    title = factory.SubFactory(EmploymentJobTitleFactory)
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(OrganizationBranchFactory)
    division = factory.SubFactory(OrganizationDivisionFactory)
    industry = factory.SubFactory(IndustryFactory)
    vacancies = factory.Faker('random_number', digits=1)
    deadline = get_tomorrow(with_time=True)
    employment_status = factory.SubFactory(EmploymentStatusFactory)
    preferred_shift = factory.Faker('word')
    employment_level = factory.SubFactory(EmploymentLevelFactory)
    location = factory.Faker('word')
    offered_salary = factory.SubFactory(SalaryFactory)
    salary_visible_to_candidate = factory.Faker('pybool')
    alternate_description = factory.Faker('text')
    description = factory.Faker('text')
    specification = factory.Faker('text')
    is_skill_specific = factory.Faker('pybool')
    # skills = factory.SubFactory(KnowledgeSkillAbilityFactory)
    education_degree = factory.Faker('word')
    # education_program = factory.Faker()
    is_education_specific = factory.Faker('pybool')
    is_document_required = factory.Faker('pybool')
    # document_categories = factory.SubFactory(DocumentCategoryFactory)
    # benefits = factory.SubFactory(JobBenefitFactory)
    apply_online = factory.Faker('pybool')
    apply_online_alternative = factory.Faker('text')
    status = factory.Faker('random_element', elements=[x[0] for x in JOB_STATUS_CHOICES])
    hit_count = factory.Faker('random_number', digits=1)
    posted_at = get_tomorrow(with_time=True)
    is_internal = factory.Faker('pybool')
    requested_by = None

class JobApplyFactory(DjangoModelFactory):
    class Meta:
        model = JobApply

    job = factory.SubFactory(JobFactory)
    applicant = factory.SubFactory(ApplicantFactory)
    status = PENDING

class TemplateFactory(DjangoModelFactory):

    class Meta:
        model = Template

    title = factory.Faker('name')
    message = factory.Faker('text',max_nb_chars=512)
    type = CANDIDATE_LETTER
    organization = factory.SubFactory(OrganizationFactory)

class NoObjectionFactory(DjangoModelFactory):

    class Meta:
        model = NoObjection

    title = factory.Faker('name')
    job_apply = factory.SubFactory(JobApplyFactory)
    job = factory.SubFactory(JobFactory)
    stage = SCREENED
    score = factory.Faker('random_number', digits=2)
    status = PENDING
    responsible_person = factory.SubFactory(UserFactory)
    report_template = factory.SubFactory(TemplateFactory)


class PostScreeningFactory(DjangoModelFactory):
    class Meta:
        model = PostScreening

    responsible_person = factory.SubFactory(UserFactory)
    job_apply = factory.SubFactory(JobApplyFactory)


class QuestionSetFactory(DjangoModelFactory):
    class Meta:
        model = QuestionSet

    name = factory.Faker('name')
    description = factory.Faker('text')
    form_type = ASSESSMENT
    is_archived = False


class AssessmentFactory(DjangoModelFactory):
    class Meta:
        model = Assessment

    responsible_person = factory.SubFactory(UserFactory)
    job_apply = factory.SubFactory(JobApplyFactory)
    question_set = factory.SubFactory(QuestionSetFactory)
    email_template = factory.SubFactory(TemplateFactory)
    email_template_external = factory.SubFactory(TemplateFactory)


class AssessmentAnswerFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentAnswer

    assessment = factory.SubFactory(AssessmentFactory)


class InterviewFactory(DjangoModelFactory):
    class Meta:
        model = Interview

    job_apply = factory.SubFactory(JobApplyFactory)
    question_set = factory.SubFactory(QuestionSetFactory)
    email_template = factory.SubFactory(TemplateFactory)
    email_template_external = factory.SubFactory(TemplateFactory)


class InterViewAnswerFactory(DjangoModelFactory):
    class Meta:
        model = InterViewAnswer

    interview = factory.SubFactory(InterviewFactory)

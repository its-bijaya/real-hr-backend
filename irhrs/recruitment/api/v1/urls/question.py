from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views.question import QuestionSetViewSet, \
    RecruitmentQuestionSectionViewSet, RecruitmentQuestionsViewSet

app_name = 'question_set'

router = DefaultRouter()


question_set_types = [
    'vacancy', 'reference-check', 'interview-evaluation',
    'post-screening', 'pre-screening', 'pre-screening-interview',
    'assessment'
]

url_string = r'(?P<organization_slug>[\w-]+)/(?P<form_type>({}))/question-set'.format(
    '|'.join(question_set_types)
)

router.register(
    url_string,
    QuestionSetViewSet,
    basename='recruitment-question-set'
    # private all
)

router.register(
    url_string + r'/(?P<question_set>\d+)/section',
    RecruitmentQuestionSectionViewSet,
    basename='recruitment-question-section'
    # private all
)

router.register(
    url_string + r'/(?P<question_set>\d+)/section/(?P<question_section>\d+)/question',
    RecruitmentQuestionsViewSet,
    basename='recruitment-question'
    # private all
)

urlpatterns = router.urls

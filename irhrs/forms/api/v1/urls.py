from django.urls import re_path
from rest_framework.routers import DefaultRouter

from irhrs.forms.api.v1.views.forms import (
    FormViewSet,
    AnonymousFormViewSet,
    UserFormViewSet,
)
from irhrs.forms.api.v1.views.form_approval import FormApprovalSettingLevelViewSet
from irhrs.forms.api.v1.views.questions import (
    FormQuestionSectionViewSet,
    FormQuestionSetViewSet,
    FormQuestionViewSet,
)
from irhrs.forms.api.v1.views.answer import (
    UserFormAnswerSheetSubmitViewSet,
    UserFormAnswerSheetViewSet,
    AnonymousFormAnswerSheetViewSet,
    AnonymousFormAnswerSheetSubmitViewSet,
)
from irhrs.forms.api.v1.views.report import (
    FormReportViewSet,
    AnonymousFormReportViewSet
)

app_name = 'forms'

router = DefaultRouter()


router.register(
    r'(?P<organization_slug>[\w\-]+)/(?P<form>\d+)/approval-setting',
    FormApprovalSettingLevelViewSet,
    basename='form-approval-setting'
)

# url for questions
question_url_string = r'(?P<organization_slug>[\w-]+)/question-set'

router.register(
    question_url_string,
    FormQuestionSetViewSet,
    basename='form-question-set'
    # private all
)

router.register(
    question_url_string + r'/(?P<question_set>\d+)/section',
    FormQuestionSectionViewSet,
    basename='form-question-section'
    # private all
)

router.register(
    question_url_string +
    r'/(?P<question_set>\d+)/section/(?P<question_section>\d+)/question',
    FormQuestionViewSet,
    basename='form-question'
    # private all
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/(?P<form_id>\d+)/assignment',
    UserFormViewSet,
    basename="forms-assignment"
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/(?P<form_id>\d+)/summary-report',
    FormReportViewSet,
    basename="forms-report"
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/(?P<form_id>\d+)/submit',
    UserFormAnswerSheetSubmitViewSet,
    basename="forms-submit"
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/answer-sheets',
    UserFormAnswerSheetViewSet,
    basename="forms-answer-sheets"
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/anonymous-answer-sheets',
    AnonymousFormAnswerSheetViewSet,
    basename="forms-anonymous-answer-sheets"
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/anonymous-form/(?P<form_id>\d+)/summary-report',
    AnonymousFormReportViewSet,
    basename="anonymous-forms-report"
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/anonymous/(?P<uuid>[\w\-]+)/submit',
    AnonymousFormAnswerSheetSubmitViewSet,
    basename="anonymous-form-submit"
)

router.register(
    r'(?P<organization_slug>[\w\-]+)',
    FormViewSet,
    basename="forms"
)


urlpatterns = router.urls

urlpatterns += [
    re_path(
        '(?P<organization_slug>[\w\-]+)/anonymous/(?P<uuid>[\w\-]+)', AnonymousFormViewSet.as_view(),
        name="anonymous-form-detail"
    )
]

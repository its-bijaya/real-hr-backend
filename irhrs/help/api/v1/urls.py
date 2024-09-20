from rest_framework.routers import DefaultRouter

from irhrs.help.api.v1.views import (
    HelpModuleViewSet, HelpCategoryViewSet, \
    HelpQuestionViewSet, #HelpQuestionImageViewSet, 
    HelpQuestionFeedbackViewSet
)

app_name = 'help'

router = DefaultRouter()
router.register('modules', HelpModuleViewSet)
router.register('categories', HelpCategoryViewSet)
router.register('questions', HelpQuestionViewSet)
# router.register('images', HelpQuestionImageViewSet)
router.register('feedback', HelpQuestionFeedbackViewSet)

urlpatterns = router.urls

# urlpatterns = []
